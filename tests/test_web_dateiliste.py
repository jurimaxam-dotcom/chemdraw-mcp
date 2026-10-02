"""Die Browser-Seite lädt den Rechenkern Datei für Datei — drei Listen müssen passen.

index.html (DATEIEN), scripts/build-web.sh (Kopierliste) und der Ordner
chemdraw_tool/aufgaben/. Fehlt ein neues Modul in einer davon, lädt die Seite
im Repo, aber nicht in web/dist — oder umgekehrt. Genau das fällt erst beim
Kunden auf.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
AUFGABEN = {p.name for p in (ROOT / "chemdraw_tool" / "aufgaben").glob("*.py")}


def test_index_html_laedt_jedes_aufgabenmodul():
    html = (ROOT / "web" / "praktikumsrechner" / "index.html").read_text()
    geladen = set(re.findall(r'"chemdraw_tool/aufgaben/([\w]+\.py)"', html))
    assert geladen == AUFGABEN


def test_build_kopiert_jedes_aufgabenmodul():
    sh = (ROOT / "scripts" / "build-web.sh").read_text()
    zeile = next(z for z in sh.splitlines() if "basis.py" in z and z.strip().startswith("for f in"))
    kopiert = set(re.findall(r"([\w]+\.py)", zeile))
    assert kopiert == AUFGABEN


def test_index_html_importiert_jedes_modul():
    html = (ROOT / "web" / "praktikumsrechner" / "index.html").read_text()
    imp = re.search(r"from chemdraw_tool\.aufgaben import ([\w, ]+)", html).group(1)
    module = {m.strip() + ".py" for m in imp.split(",")} | {"__init__.py"}
    assert module == AUFGABEN
