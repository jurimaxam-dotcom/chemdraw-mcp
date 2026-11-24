#!/usr/bin/env python3
"""Sperre vor dem Commit: hält zurück, was nicht ins öffentliche Repo darf.

Regeln: CLAUDE.md, Abschnitt „Public repo: what may be committed". Dieses Skript
prüft den Teil davon, den eine Maschine prüfen kann, und nur den Index — also
genau das, was der Commit veröffentlichen würde (der post-commit-Hook pusht sofort).

    scripts/oeffentlich_pruefen.py                      # pre-commit, pre-merge-commit: der Index
    scripts/oeffentlich_pruefen.py --nachricht <datei>  # commit-msg: Betreff und Text
    scripts/oeffentlich_pruefen.py --bereich <alt> <neu>  # pre-push: alles, was der Push veröffentlicht
    OEFFENTLICH_GESEHEN="assets/a.gif:assets/b.mp4" git commit …

Der Bereichslauf ist das Netz unter den anderen: Fast-Forward-Merge, Rebase und
Cherry-Pick lösen keinen pre-commit aus, und ein Worktree auf altem Stand hat
dieses Skript noch gar nicht.

Bewusst nur Standardbibliothek: der Hook läuft mit dem System-Python, ohne venv.

Was geprüft wird
- Commit-Adresse: nur die GitHub-noreply-Adresse.
- Neue Textzeilen: ausgeschriebenes Heimatverzeichnis, E-Mail-Adressen,
  Besprechungs-Links; dazu eine private Begriffsliste außerhalb des Repos.
- Bilder, Videos und jede andere Binärdatei: jede neue oder geänderte außerhalb
  von __fixtures__/ bleibt hängen, bis sie jemand angesehen hat und die Datei in
  OEFFENTLICH_GESEHEN nennt. Die Freigabe wird am Inhalt festgemacht (Blob-Hash in
  .git/oeffentlich-gesehen) und gilt damit auch beim Push.
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
    r"|^chempane/ui/dist/"
    r"|^tests/test_oeffentlich_pruefen\.py$|^scripts/oeffentlich_pruefen\.py$"
)
ERLAUBTE_ADRESSEN = re.compile(
    r"@users\.noreply\.github\.com$|^noreply@(anthropic|github)\.com$|^git@github\.com$|^mcp-apps@anthropic\.com$",
    re.I,
)
BOT_TRAILER = re.compile(
    r"^(?:Signed-off-by|Co-authored-by):\s+[A-Za-z0-9._-]+\[bot\]\s+"
    r"<(?:support@github\.com|\d+\+[A-Za-z0-9._-]+\[bot\]@users\.noreply\.github\.com)>\s*$",
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
# Regel 5 (Jay 21.11.2026): Session-Links sind kontoprivat — weder in Nachricht noch in Dateien.
SITZUNG = re.compile(r"^\s*Claude-Session:|claude\.ai/code/session_", re.I | re.M)

FIXTURE = re.compile(r"(^|/)__fixtures__/")
BILD = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
VOLLBILD_BREITE = 1800          # breitestes Bild im Repo am 17.11.2026: 1760 px
BILDSCHIRM = 3456 / 2234        # MacBook-Anzeige; auch verkleinerte Aufnahmen behalten das Verhältnis
BILDSCHIRM_TOLERANZ = 0.004     # 1500×975-Diagramme liegen 0,0085 daneben und bleiben frei
LEERER_BAUM = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


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


def neue_zeilen(quelle: list[str]) -> list[tuple[str, int, str]]:
    """(Datei, Zeilennummer, Text) für jede Zeile, die hinzukommt. Binärdateien liefern keine."""
    diff = git("-c", "core.quotepath=false", "diff", *quelle, "-U0", "--no-color", "--diff-filter=AMRT")
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


def gemeinsames_git_verzeichnis() -> Path:
    """Worktrees teilen Begriffsliste und Freigaben des Haupt-Repos."""
    return Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").strip())


def private_begriffe() -> list[re.Pattern]:
    pfad = os.environ.get("OEFFENTLICH_BEGRIFFE")
    if not pfad:
        pfad = str(Path.home() / ".claude" / "oeffentlich-begriffe" / f"{gemeinsames_git_verzeichnis().parent.name}.txt")
    p = Path(pfad)
    # Der Name bleibt in der lokalen Git-Konfiguration, die Wortgrenzen lassen
    # längere Fachbegriffe durch. Der deutsche Genitiv zählt ebenfalls.
    name = git("config", "--local", "--default", "", "--get", "publicguard.privateName").strip()
    muster = [re.compile(rf"\b{re.escape(name)}s?\b", re.I)] if name else []
    if not p.is_file():
        return muster
    for z in p.read_text(encoding="utf-8").splitlines():
        z = z.strip()
        if z and not z.startswith("#"):
            muster.append(re.compile(z, re.I))
    return muster


def textbefunde(text: str, datei: str, begriffe: list[re.Pattern], ich: str) -> list[str]:
    funde = []
    for m in HEIMAT.finditer(text):
        if m.group(1) == ich or (m.group(1) not in HEIMAT_OK and not TESTDATEI.search(datei)):
            funde.append("Heimatverzeichnis ausgeschrieben — `~` schreiben")
            break
    if any(not ERLAUBTE_ADRESSEN.search(m.group(0)) for m in ADRESSE.finditer(text)):
        funde.append("E-Mail-Adresse")
    if BESPRECHUNG.search(text):
        funde.append("Besprechungs-Link oder -Kennung")
    if SITZUNG.search(text):
        funde.append("Claude-Session-Link (kontoprivat) — Zeile streichen")
    if any(b.search(text) for b in begriffe):
        funde.append("Treffer der privaten Begriffsliste")
    return funde


def pruefe_nachricht(
    zeilen: list[str], ort: str, begriffe: list[re.Pattern], ich: str, *, kommentare_ueberspringen: bool = False
) -> list[str]:
    befunde = []
    for nr, z in enumerate(zeilen, 1):
        if kommentare_ueberspringen and z.startswith("#"):
            continue
        if BOT_TRAILER.match(z):
            continue
        befunde += [f"{ort}, Zeile {nr} der Commit-Nachricht: {f}" for f in textbefunde(z, "", begriffe, ich)]
    return befunde


def pruefe_inhalt(quelle: list[str], blob_von: str, begriffe: list[re.Pattern], ich: str) -> list[str]:
    """Text, Dateinamen und Binärdateien eines Diffs; `blob_von` ist "" (Index) oder ein Commit."""
    befunde: list[str] = []
    merkzettel = gemeinsames_git_verzeichnis() / "oeffentlich-gesehen"
    freigegeben = set(merkzettel.read_text().split()) if merkzettel.is_file() else set()
    gesehen = {p.strip() for p in re.split(r"[:,\n]", os.environ.get("OEFFENTLICH_GESEHEN", "")) if p.strip()}

    for datei, nr, text in neue_zeilen(quelle):
        if OHNE_TEXTPRUEFUNG.search(datei) or "\0" in text:
            continue
        befunde += [f"{datei}:{nr}: {f}" for f in textbefunde(text, datei, begriffe, ich)]

    binaer = set()
    for z in git("diff", *quelle, "--numstat", "--diff-filter=AMRT", "-z", "--no-renames").split("\0"):
        teile = z.split("\t")
        if len(teile) == 3 and teile[0] == "-":
            binaer.add(teile[2])
    neu_freigegeben = []
    for datei in git("diff", *quelle, "--name-only", "--diff-filter=AMRT", "-z", "--no-renames").split("\0"):
        if not datei:
            continue
        if any(b.search(datei) for b in begriffe):
            befunde.append(f"{datei}: Dateiname trifft die private Begriffsliste")
        endung = Path(datei).suffix.lower()
        if endung not in BILD | VIDEO and datei not in binaer:
            continue
        blob = git("rev-parse", f"{blob_von}:{datei}").strip()
        if blob in freigegeben:
            continue
        if datei in gesehen:
            neu_freigegeben.append(blob)
            continue
        hinweis = f" — ansehen, dann OEFFENTLICH_GESEHEN={datei}"
        if endung in VIDEO:
            befunde.append(f"{datei}: Video{hinweis}")
        elif datei.startswith("docs/evidence/"):
            befunde.append(f"{datei}: Datei unter docs/evidence/ — Belege gehören ins private Archiv{hinweis}")
        elif FIXTURE.search(datei):
            continue  # von unserem Code erzeugt, nie eine Aufnahme
        elif endung not in BILD:
            befunde.append(f"{datei}: Binärdatei{hinweis}")
        else:
            groesse = bildgroesse(git("cat-file", "blob", blob, binaer=True))
            if groesse is None or not all(groesse):
                befunde.append(f"{datei}: Bildgröße nicht lesbar{hinweis}")
            elif groesse[0] >= VOLLBILD_BREITE or (
                groesse[0] >= 1000 and abs(groesse[0] / groesse[1] - BILDSCHIRM) < BILDSCHIRM_TOLERANZ
            ):
                befunde.append(f"{datei}: sieht nach Vollbild aus ({groesse[0]}×{groesse[1]}){hinweis}")
            else:
                # Messen findet nur die groben Fälle; ein Ausschnitt mit Seitenleiste sähe harmlos aus.
                befunde.append(f"{datei}: neues oder geändertes Bild{hinweis}")
    if neu_freigegeben:
        with merkzettel.open("a") as f:
            f.write("".join(b + "\n" for b in neu_freigegeben))
    return befunde


def pruefe_commit_inhalt(voll: str, eltern: list[str], begriffe: list[re.Pattern], ich: str) -> list[str]:
    """Prüft den Inhalt eines einzelnen Commits gegen seine Eltern (Merge: nur eigene Neuerungen)."""
    if not eltern:
        return pruefe_inhalt([LEERER_BAUM, voll], voll, begriffe, ich)
    if len(eltern) == 1:
        return pruefe_inhalt([eltern[0], voll], voll, begriffe, ich)
    erster = pruefe_inhalt([eltern[0], voll], voll, begriffe, ich)
    if not erster:
        return []
    gemeinsam = set(erster)
    for p in eltern[1:]:
        gemeinsam &= set(pruefe_inhalt([p, voll], voll, begriffe, ich))
    return [b for b in erster if b in gemeinsam]


def main() -> int:
    args = sys.argv[1:]
    begriffe, ich = private_begriffe(), getpass.getuser()
    befunde: list[str] = []
    mit_gitleaks = "--ohne-gitleaks" not in args and shutil.which("gitleaks")
    gitleaks = ["gitleaks", "git", "--no-banner", "--redact", "--log-level", "error"]

    if "--nachricht" in args:
        was = "Commit"
        text = Path(args[args.index("--nachricht") + 1]).read_text(encoding="utf-8", errors="replace")
        befunde = pruefe_nachricht(text.splitlines(), "Nachricht", begriffe, ich, kommentare_ueberspringen=True)
    elif "--bereich" in args:
        was = "Push"
        alt, neu = args[args.index("--bereich") + 1 : args.index("--bereich") + 3]
        for eintrag in git("log", "--format=%H%x1f%h%x1f%P%x1f%ae%x1f%ce%x1f%B%x1e", f"{alt}..{neu}").split("\x1e"):
            if not eintrag.strip():
                continue
            voll, kurz, eltern_str, autor, committer, nachricht = eintrag.strip("\n").split("\x1f", 5)
            for rolle, adresse in (("Autor", autor), ("Committer", committer)):
                if not ERLAUBTE_ADRESSEN.search(adresse):
                    befunde.append(f"{kurz}: {rolle}-Adresse ist keine noreply-Adresse")
            befunde += pruefe_nachricht(nachricht.splitlines(), kurz, begriffe, ich, kommentare_ueberspringen=False)
            befunde += [f"{kurz}: {b}" for b in pruefe_commit_inhalt(voll, eltern_str.split(), begriffe, ich)]
        if mit_gitleaks:
            lauf = subprocess.run([*gitleaks, f"--log-opts={alt}..{neu}"], capture_output=True, text=True)
            if lauf.returncode != 0:
                befunde.append("gitleaks meldet einen Schlüssel:\n" + (lauf.stdout + lauf.stderr).strip())
    else:
        was = "Commit"
        for rolle in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
            ident = subprocess.run(["git", "var", rolle], capture_output=True, text=True).stdout
            if "users.noreply.github.com>" not in ident:
                befunde.append(
                    f"Commit-Adresse ({rolle.split('_')[1].lower()}) ist nicht die GitHub-noreply-Adresse — "
                    "`git config user.email` in diesem Klon setzen"
                )
        befunde += pruefe_inhalt(["--cached"], "", begriffe, ich)
        if mit_gitleaks:
            lauf = subprocess.run([*gitleaks, "--pre-commit", "--staged"], capture_output=True, text=True)
            if lauf.returncode != 0:
                befunde.append("gitleaks meldet einen Schlüssel im Index:\n" + (lauf.stdout + lauf.stderr).strip())

    if not befunde:
        return 0
    print(f"{was} gesperrt — das Repo ist öffentlich.")
    for b in befunde:
        print(f"  ✗ {b}")
    print("Regeln: CLAUDE.md, „Public repo: what may be committed“. Die Sperre nicht mit --no-verify umgehen.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
