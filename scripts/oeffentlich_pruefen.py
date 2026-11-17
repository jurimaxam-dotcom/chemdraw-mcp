#!/usr/bin/env python3
"""Sperre vor dem Commit: hält zurück, was nicht ins öffentliche Repo darf.

Regeln: CLAUDE.md, Abschnitt „Public repo: what may be committed". Dieses Skript
prüft den Teil davon, den eine Maschine prüfen kann, und nur den Index — also
genau das, was der Commit veröffentlichen würde (der post-commit-Hook pusht sofort).

    scripts/oeffentlich_pruefen.py            # als pre-commit-Hook
    OEFFENTLICH_GESEHEN="assets/a.gif:assets/b.mp4" git commit …

Bewusst nur Standardbibliothek: der Hook läuft mit dem System-Python, ohne venv.

Was geprüft wird
- Commit-Adresse: nur die GitHub-noreply-Adresse.
- Neue Textzeilen: ausgeschriebenes Heimatverzeichnis, E-Mail-Adressen,
  Besprechungs-Links; dazu eine private Begriffsliste außerhalb des Repos.
- Bilder und Videos: jedes neue oder geänderte außerhalb von __fixtures__/ bleibt
  hängen, bis es jemand angesehen hat und die Datei in OEFFENTLICH_GESEHEN nennt.
  Messen (Vollbild-Größe, Bildschirm-Seitenverhältnis, docs/evidence/) sagt nur,
  wie dringend — in ein Bild hineinsehen kann das Skript nicht. Textbefunde hebt
  die Freigabe nicht auf.
- Schlüssel: gitleaks über den Index, wenn es installiert ist.
"""

from __future__ import annotations

import getpass
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# Dateien, deren Inhalt fremder oder gebauter Text ist (Lizenztexte, Lockfiles, Bundle)
# oder die diese Sperre selbst testen.
OHNE_TEXTPRUEFUNG = re.compile(
    r"(^|/)(uv\.lock|package-lock\.json|THIRD_PARTY_LICENSES|LICENSE|NOTICE)$"
    r"|^chemdraw_tool/ui/dist/"
    r"|^tests/test_oeffentlich_pruefen\.py$|^scripts/oeffentlich_pruefen\.py$"
)
ERLAUBTE_ADRESSEN = re.compile(
    r"@users\.noreply\.github\.com$|^noreply@(anthropic|github)\.com$|^git@github\.com$|^mcp-apps@anthropic\.com$",
    re.I,
)
ADRESSE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
HEIMAT = re.compile(r"/(?:Users|home)/([A-Za-z0-9._-]+)")
HEIMAT_OK = {"runner", "name", "user", "username", "you", "Shared", "USER", "work", "linuxbrew"}
# Tests brauchen erfundene Pfade (das Panel zeigt Dateipfade an); dort sperrt nur der echte Benutzername.
TESTDATEI = re.compile(r"(^|/)(tests|__tests__)/|\.(test|e2e)\.mjs$")
BESPRECHUNG = re.compile(
    r"zoom(?:-x)?\.(?:us|de)/|meet\.google\.com/|teams\.microsoft\.com/l/|Meeting[- ]ID|Kenncode", re.I
)

FIXTURE = re.compile(r"(^|/)__fixtures__/")
BILD = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
VOLLBILD_BREITE = 1800          # breitestes Bild im Repo am 17.11.2026: 1760 px
BILDSCHIRM = 3456 / 2234        # MacBook-Anzeige; auch verkleinerte Aufnahmen behalten das Verhältnis
BILDSCHIRM_TOLERANZ = 0.004     # 1500×975-Diagramme liegen 0,0085 daneben und bleiben frei


def git(*args: str, binaer: bool = False):
    out = subprocess.run(["git", *args], capture_output=True, check=True).stdout
    return out if binaer else out.decode("utf-8", "replace")


def bildgroesse(daten: bytes) -> tuple[int, int] | None:
    if daten[:8] == b"\x89PNG\r\n\x1a\n" and len(daten) >= 24:
        return struct.unpack(">II", daten[16:24])
    if daten[:6] in (b"GIF87a", b"GIF89a") and len(daten) >= 10:
        return struct.unpack("<HH", daten[6:10])
    if daten[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(daten):
            if daten[i] != 0xFF:
                i += 1
                continue
            marke = daten[i + 1]
            if marke in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                hoehe, breite = struct.unpack(">HH", daten[i + 5 : i + 9])
                return breite, hoehe
            if marke in (0xD8, 0x01) or 0xD0 <= marke <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", daten[i + 2 : i + 4])[0]
    return None


def neue_zeilen() -> list[tuple[str, int, str]]:
    """(Datei, Zeilennummer, Text) für jede Zeile, die der Commit hinzufügt."""
    diff = git("diff", "--cached", "-U0", "--no-color", "--diff-filter=AM")  # Binärdateien liefern keine Zeilen
    zeilen, datei, nr = [], None, 0
    for z in diff.split("\n"):
        if z.startswith("+++ "):
            datei = z[6:] if z.startswith("+++ b/") else None
        elif z.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", z)
            nr = int(m.group(1)) if m else 0
        elif z.startswith("+") and not z.startswith("+++") and datei:
            zeilen.append((datei, nr, z[1:]))
            nr += 1
    return zeilen


def private_begriffe() -> list[re.Pattern]:
    pfad = os.environ.get("OEFFENTLICH_BEGRIFFE")
    if not pfad:
        # Worktrees teilen die Liste des Haupt-Repos
        gemeinsam = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").strip())
        pfad = str(Path.home() / ".claude" / "oeffentlich-begriffe" / f"{gemeinsam.parent.name}.txt")
    p = Path(pfad)
    if not p.is_file():
        return []
    muster = []
    for z in p.read_text(encoding="utf-8").splitlines():
        z = z.strip()
        if z and not z.startswith("#"):
            muster.append(re.compile(z, re.I))
    return muster


def main() -> int:
    befunde: list[str] = []
    gesehen = {p.strip() for p in re.split(r"[:,\n]", os.environ.get("OEFFENTLICH_GESEHEN", "")) if p.strip()}

    # 1. Commit-Adresse
    for rolle in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        ident = subprocess.run(["git", "var", rolle], capture_output=True, text=True).stdout
        if "users.noreply.github.com>" not in ident:
            befunde.append(
                f"Commit-Adresse ({rolle.split('_')[1].lower()}) ist nicht die GitHub-noreply-Adresse — "
                "`git config user.email` in diesem Klon setzen"
            )

    # 2. Neue Textzeilen
    begriffe = private_begriffe()
    ich = getpass.getuser()
    for datei, nr, text in neue_zeilen():
        if OHNE_TEXTPRUEFUNG.search(datei) or "\0" in text:
            continue
        ort = f"{datei}:{nr}"
        for m in HEIMAT.finditer(text):
            if m.group(1) == ich or (m.group(1) not in HEIMAT_OK and not TESTDATEI.search(datei)):
                befunde.append(f"{ort}: Heimatverzeichnis ausgeschrieben — `~` schreiben")
                break
        for m in ADRESSE.finditer(text):
            if not ERLAUBTE_ADRESSEN.search(m.group(0)):
                befunde.append(f"{ort}: E-Mail-Adresse")
                break
        if BESPRECHUNG.search(text):
            befunde.append(f"{ort}: Besprechungs-Link oder -Kennung")
        if any(b.search(text) for b in begriffe):
            befunde.append(f"{ort}: Treffer der privaten Begriffsliste")

    # 3. Dateinamen, Bilder, Videos
    for datei in git("diff", "--cached", "--name-only", "--diff-filter=AMR", "-z").split("\0"):
        if not datei:
            continue
        if any(b.search(datei) for b in begriffe):
            befunde.append(f"{datei}: Dateiname trifft die private Begriffsliste")
        endung = Path(datei).suffix.lower()
        if endung not in BILD | VIDEO or datei in gesehen:
            continue
        hinweis = f" — ansehen, dann OEFFENTLICH_GESEHEN={datei}"
        if endung in VIDEO:
            befunde.append(f"{datei}: Video{hinweis}")
            continue
        if datei.startswith("docs/evidence/"):
            befunde.append(f"{datei}: Bild unter docs/evidence/ — Belege gehören als Text ins Repo{hinweis}")
            continue
        if FIXTURE.search(datei):
            continue  # von unserem Code gerendert, nie eine Aufnahme
        groesse = bildgroesse(git("show", f":{datei}", binaer=True))
        if groesse is None or not all(groesse):
            befunde.append(f"{datei}: Bildgröße nicht lesbar{hinweis}")
        elif groesse[0] >= VOLLBILD_BREITE or (
            groesse[0] >= 1000 and abs(groesse[0] / groesse[1] - BILDSCHIRM) < BILDSCHIRM_TOLERANZ
        ):
            befunde.append(f"{datei}: sieht nach Vollbild aus ({groesse[0]}×{groesse[1]}){hinweis}")
        else:
            # Messen findet nur die groben Fälle; ein Ausschnitt mit Seitenleiste sähe harmlos aus.
            befunde.append(f"{datei}: neues oder geändertes Bild{hinweis}")

    # 4. Schlüssel
    if "--ohne-gitleaks" not in sys.argv and shutil.which("gitleaks"):
        lauf = subprocess.run(
            ["gitleaks", "git", "--pre-commit", "--staged", "--no-banner", "--redact", "--log-level", "error"],
            capture_output=True, text=True,
        )
        if lauf.returncode != 0:
            befunde.append("gitleaks meldet einen Schlüssel im Index:\n" + (lauf.stdout + lauf.stderr).strip())

    if not befunde:
        return 0
    print("Commit gesperrt — das Repo ist öffentlich, jeder Commit wird sofort gepusht.")
    for b in befunde:
        print(f"  ✗ {b}")
    print("Regeln: CLAUDE.md, „Public repo: what may be committed“. Die Sperre nicht mit --no-verify umgehen.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
