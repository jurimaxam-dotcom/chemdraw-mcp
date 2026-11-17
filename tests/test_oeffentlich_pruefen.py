"""Die Sperre vor dem Commit: was nicht ins öffentliche Repo darf, bleibt hängen.

`scripts/oeffentlich_pruefen.py` läuft als pre-commit-Hook über den Index. Die
Regeln stehen in CLAUDE.md („Public repo: what may be committed"); hier steht,
was davon eine Maschine prüfen kann. Jeder Fall legt ein Wegwerf-Repo an.
"""

from __future__ import annotations

import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

SKRIPT = Path(__file__).resolve().parent.parent / "scripts" / "oeffentlich_pruefen.py"
NOREPLY = "1+probe@users.noreply.github.com"


def _png(breite: int, hoehe: int) -> bytes:
    def chunk(typ: bytes, daten: bytes) -> bytes:
        return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten))

    kopf = struct.pack(">IIBBBBB", breite, hoehe, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", kopf) + chunk(b"IDAT", zlib.compress(b"\0" * 8)) + chunk(b"IEND", b"")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for name in list(os.environ):
        if name.startswith("GIT_") or name.startswith("OEFFENTLICH_"):
            monkeypatch.delenv(name)
    # Der echte Benutzername sperrt überall; auf GitHub heißt er "runner" und stünde
    # damit im Platzhalter-Test. Die Fälle legen ihn deshalb selbst fest.
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        monkeypatch.setenv(name, "probe")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))  # keine private Begriffsliste, keine globale Git-Config
    (tmp_path / "home").mkdir()
    r = tmp_path / "repo"
    r.mkdir()
    for cmd in (["init", "-q"], ["config", "user.email", NOREPLY], ["config", "user.name", "probe"]):
        subprocess.run(["git", *cmd], cwd=r, check=True)
    return r


def _pruefe(repo: Path, dateien: dict[str, bytes | str], env: dict[str, str] | None = None):
    for pfad, inhalt in dateien.items():
        ziel = repo / pfad
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_bytes(inhalt if isinstance(inhalt, bytes) else inhalt.encode())
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    return subprocess.run(
        [sys.executable, str(SKRIPT), "--ohne-gitleaks"],
        cwd=repo, capture_output=True, text=True, env={**os.environ, **(env or {})},
    )


def test_gewoehnlicher_commit_geht_durch(repo):
    r = _pruefe(repo, {"a.py": "x = 1\n", "docs/b.md": "Pfad: ~/ChemDraw-Output/a.png\n"})
    assert r.returncode == 0, r.stdout + r.stderr


def test_jedes_bild_braucht_die_bestaetigung_dass_es_angesehen_wurde(repo):
    """Messen findet nur Vollbilder. Ein zugeschnittenes Fenster mit Vorname oder
    Chat-Titeln sähe für die Maschine harmlos aus — also bestätigt jemand jedes Bild."""
    dateien = {"assets/panel.png": _png(1500, 975)}
    r = _pruefe(repo, dateien)
    assert r.returncode == 1 and "assets/panel.png" in r.stdout and "ansehen" in r.stdout
    assert _pruefe(repo, dateien, {"OEFFENTLICH_GESEHEN": "assets/panel.png"}).returncode == 0


def test_gerenderte_test_fixtures_sind_frei(repo):
    dateien = {"tests/__fixtures__/a.golden.png": _png(600, 400), "ui/src/utils/__fixtures__/b.expected.png": _png(600, 400)}
    assert _pruefe(repo, dateien).returncode == 0


@pytest.mark.parametrize(
    "zeile, stichwort",
    [
        ("Config unter /Users/erika/Library/x.json", "Heimatverzeichnis"),
        ("Kontakt: erika.muster@example.org", "E-Mail"),
        ("Link: https://uni-x.zoom-x.de/j/123456", "Besprechung"),
        ("Meeting-ID: 635 0000 0000", "Besprechung"),
    ],
)
def test_personenbezug_im_text_wird_gesperrt(repo, zeile, stichwort):
    r = _pruefe(repo, {"docs/notiz.md": zeile + "\n"})
    assert r.returncode == 1
    assert stichwort in r.stdout and "docs/notiz.md" in r.stdout


def test_erlaubte_adressen_und_platzhalter_gehen_durch(repo):
    text = "noreply@anthropic.com\n1+x@users.noreply.github.com\n/Users/<name>/x\n/Users/runner/work\n"
    assert _pruefe(repo, {"docs/ok.md": text}).returncode == 0


def test_testdateien_duerfen_erfundene_pfade_tragen_aber_nie_den_echten(repo):
    zeile = 'pfad = "/Users/erika/ChemDraw-Output/a.png"\n'
    assert _pruefe(repo, {"tests/test_x.py": zeile, "ui/src/__tests__/a.test.mjs": zeile}).returncode == 0
    r = _pruefe(repo, {"tests/test_y.py": zeile}, {"USER": "erika", "LOGNAME": "erika"})
    assert r.returncode == 1 and "tests/test_y.py:1" in r.stdout


def test_binaerdateien_liefern_keine_textbefunde(repo):
    """Gemessen an 150 Commits: GIF-Bytes sahen dreimal wie eine E-Mail-Adresse aus."""
    daten = _png(400, 300) + b"\nn@p.AX /Users/erika/x\n\0"
    r = _pruefe(repo, {"assets/klein.png": daten}, {"OEFFENTLICH_GESEHEN": "assets/klein.png"})
    assert r.returncode == 0, r.stdout


def test_nur_neue_zeilen_zaehlen(repo):
    """Altbestand macht keinen Commit rot — sonst wäre die Sperre am ersten Tag abgeschaltet."""
    (repo / "alt.md").write_text("Pfad /Users/erika/x\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "alt", "--no-verify"], cwd=repo, check=True)
    r = _pruefe(repo, {"alt.md": "Pfad /Users/erika/x\nneue Zeile ohne Befund\n"})
    assert r.returncode == 0, r.stdout


@pytest.mark.parametrize(
    "pfad, bild, stichwort",
    [
        ("assets/gross.png", _png(3456, 2234), "Vollbild"),
        ("assets/klein-vollbild.png", _png(2000, 1293), "Vollbild"),   # verkleinert, gleiches Seitenverhältnis
        ("docs/evidence/lauf/01.png", _png(800, 600), "docs/evidence"),
        ("assets/clip.mp4", b"\0\0\0\x18ftypmp42", "Video"),
        ("assets/unbekannt.webp", b"RIFF0000WEBP", "nicht lesbar"),
    ],
)
def test_bilder_die_nach_bildschirm_aussehen_werden_gesperrt(repo, pfad, bild, stichwort):
    r = _pruefe(repo, {pfad: bild})
    assert r.returncode == 1
    assert stichwort in r.stdout and pfad in r.stdout


def test_angesehenes_bild_geht_mit_ausdruecklicher_freigabe_durch(repo):
    """Die Freigabe nennt die Datei — ein pauschales „alles ok" gibt es nicht."""
    dateien = {"assets/clip.mp4": b"\0\0\0\x18ftypmp42"}
    assert _pruefe(repo, dateien, {"OEFFENTLICH_GESEHEN": "assets/anderes.mp4"}).returncode == 1
    assert _pruefe(repo, dateien, {"OEFFENTLICH_GESEHEN": "assets/clip.mp4"}).returncode == 0


def test_freigabe_hebt_keinen_textbefund_auf(repo):
    r = _pruefe(repo, {"docs/n.md": "/Users/erika/x\n"}, {"OEFFENTLICH_GESEHEN": "docs/n.md"})
    assert r.returncode == 1


def test_falsche_commit_adresse_wird_gesperrt(repo):
    subprocess.run(["git", "config", "user.email", "erika@uni-beispiel.de"], cwd=repo, check=True)
    r = _pruefe(repo, {"a.py": "x = 1\n"})
    assert r.returncode == 1 and "noreply" in r.stdout


def test_private_begriffsliste_ausserhalb_des_repos(repo, tmp_path):
    """Die Liste selbst ist privat; im Bericht steht die Fundstelle, nie der Begriff."""
    liste = tmp_path / "begriffe.txt"
    liste.write_text("# Kommentar\ngeheimprojekt\n")
    r = _pruefe(repo, {"docs/n.md": "Arbeit am Geheimprojekt läuft\n"}, {"OEFFENTLICH_BEGRIFFE": str(liste)})
    assert r.returncode == 1
    assert "docs/n.md:1" in r.stdout and "geheimprojekt" not in r.stdout.lower()


# --- Wege an pre-commit vorbei: Merge, Rebase, Commit-Betreff, Push ----------------


def _lauf(repo: Path, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        [sys.executable, str(SKRIPT), "--ohne-gitleaks", *args],
        cwd=repo, capture_output=True, text=True, env={**os.environ, **(env or {})},
    )


def _commit(repo: Path, dateien: dict[str, bytes | str], betreff: str = "x", env: dict[str, str] | None = None) -> str:
    for pfad, inhalt in dateien.items():
        ziel = repo / pfad
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_bytes(inhalt if isinstance(inhalt, bytes) else inhalt.encode())
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", betreff, "--no-verify"], cwd=repo, check=True, env={**os.environ, **(env or {})})
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def test_auch_andere_binaerdateien_brauchen_die_bestaetigung(repo):
    """Ein PDF oder eine Office-Datei kann dasselbe zeigen wie ein Screenshot."""
    r = _pruefe(repo, {"docs/bericht.pdf": b"%PDF-1.7\n\0\0\xff\xfe binaer"})
    assert r.returncode == 1 and "docs/bericht.pdf" in r.stdout


def test_umbenannte_und_geaenderte_datei_wird_gelesen(repo):
    _commit(repo, {"docs/alt.md": "eins\nzwei\ndrei\nvier\nfuenf\nsechs\n"})
    subprocess.run(["git", "mv", "docs/alt.md", "docs/neu.md"], cwd=repo, check=True)
    r = _pruefe(repo, {"docs/neu.md": "eins\nzwei\ndrei\nvier\nfuenf\nsechs\nKontakt: erika.muster@example.org\n"})
    assert r.returncode == 1 and "docs/neu.md" in r.stdout


def test_commit_betreff_wird_geprueft(repo, tmp_path):
    nachricht = tmp_path / "MSG"
    nachricht.write_text("Fix für erika.muster@example.org\n\n# Kommentar mit /Users/erika/x zählt nicht\n")
    r = _lauf(repo, "--nachricht", str(nachricht))
    assert r.returncode == 1 and "E-Mail" in r.stdout
    nachricht.write_text("Panel: Knopf sitzt jetzt rechts\n\n# /Users/erika/x\n")
    assert _lauf(repo, "--nachricht", str(nachricht)).returncode == 0


def test_bereich_findet_was_an_pre_commit_vorbeikam(repo):
    """Fast-Forward-Merge, Rebase und Cherry-Pick lösen keinen pre-commit aus —
    der Push ist die letzte Stelle vor der Veröffentlichung."""
    basis = _commit(repo, {"a.py": "x = 1\n"})
    spitze = _commit(repo, {"docs/n.md": "Config unter /Users/erika/x\n", "assets/p.png": _png(600, 400)})
    r = _lauf(repo, "--bereich", basis, spitze)
    assert r.returncode == 1
    assert "docs/n.md:1" in r.stdout and "assets/p.png" in r.stdout


def test_bereich_prueft_betreff_und_adresse_jedes_commits(repo):
    basis = _commit(repo, {"a.py": "x = 1\n"})
    mitte = _commit(repo, {"b.py": "y = 1\n"}, betreff="Abnahme per Meeting-ID 635")
    fremd = {"GIT_COMMITTER_EMAIL": "erika@uni-beispiel.de", "GIT_COMMITTER_NAME": "erika"}
    spitze = _commit(repo, {"c.py": "z = 1\n"}, env=fremd)
    r = _lauf(repo, "--bereich", basis, spitze)
    assert r.returncode == 1
    assert mitte[:7] in r.stdout and "Besprechung" in r.stdout
    assert spitze[:7] in r.stdout and "noreply" in r.stdout
    assert "uni-beispiel" not in r.stdout, "die Adresse selbst gehört nicht in den Bericht"


def test_einmal_angesehen_gilt_auch_beim_push(repo):
    """Die Freigabe hängt am Inhalt (Blob), nicht am Aufruf: sonst bliebe jedes
    freigegebene Bild beim Push erneut hängen, wo niemand eine Variable setzt."""
    basis = _commit(repo, {"a.py": "x = 1\n"})
    bild = {"assets/p.png": _png(600, 400)}
    assert _pruefe(repo, bild, {"OEFFENTLICH_GESEHEN": "assets/p.png"}).returncode == 0
    subprocess.run(["git", "commit", "-qm", "bild", "--no-verify"], cwd=repo, check=True)
    spitze = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
    assert _lauf(repo, "--bereich", basis, spitze).returncode == 0
    # derselbe Pfad mit anderem Inhalt ist ein anderes Bild
    neu = _commit(repo, {"assets/p.png": _png(640, 400)})
    assert _lauf(repo, "--bereich", spitze, neu).returncode == 1
