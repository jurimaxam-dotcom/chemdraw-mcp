"""Nutzerdoku gegen Verrotten: jeder Link und jedes Bild führt irgendwohin.

test_docs_consistency.py prüft Toolnamen, Befehle und Repo-Pfade in Backticks.
Hier steht, was ein Leser anklickt: relative Links und Bilder in README und den
Nutzerseiten unter docs/ (samt #Anker), die absoluten GitHub-Links des README
auf eigene Dateien, und dass Tools, die nur das Profil `full` registriert, nur
dort erwähnt werden, wo `full` dabeisteht. Kein Netz.
"""

import asyncio
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote

import pytest

from chemdraw_tool.server import create_server
from tests.test_docs_consistency import USER_DOCS, VAULT_TOOLS

ROOT = Path(__file__).resolve().parents[1]
REPO = "jurimaxam-dotcom/chemdraw-mcp"
EIGENE_URL = re.compile(
    rf"https://(?:github\.com/{REPO}/(?:blob|tree)/main|raw\.githubusercontent\.com/{REPO}/main)/([^)\s\"'#?]+)(#[^)\s\"']*)?"
)
LINK = re.compile(r"\]\(([^)\s]+)\)|<img[^>]*\bsrc=\"([^\"]+)\"")
# Seiten, die E14 neu schreibt; README und tools.md erwähnen full-Tools in eigener Form.
NEUE_SEITEN = [n for n in USER_DOCS if n.startswith("docs/") and n not in {
    "docs/tools.md", "docs/installation.md", "docs/development.md"}]


def _ohne_code(text: str) -> str:
    """Code zählt nicht: Beispiel-JSON und SMILES wie `N[C@@H](Cc1ccccc1)` sind keine Links."""
    return re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))


def _slug(titel: str) -> str:
    titel = re.sub(r"[`*_]", "", titel).strip().lower()
    titel = re.sub(r"[^\w\- ]", "", titel)
    return titel.replace(" ", "-")


@lru_cache
def _anker(datei: Path) -> frozenset[str]:
    text = re.sub(r"```.*?```", "", datei.read_text(encoding="utf-8"), flags=re.S)
    return frozenset(_slug(t) for t in re.findall(r"^#{1,6} (.+)$", text, flags=re.M))


def _ziel_fehlt(quelle: str, pfad: str, anker: str | None) -> str | None:
    ziel = (ROOT / quelle).parent / unquote(pfad) if pfad else ROOT / quelle
    ziel = ziel.resolve()
    if not ziel.exists():
        return f"{quelle}: {pfad} fehlt"
    if anker and ziel.suffix == ".md" and anker not in _anker(ziel):
        return f"{quelle}: {pfad}#{anker} — Anker fehlt"
    return None


def _links(quelle: str) -> list[tuple[str, str | None]]:
    text = _ohne_code((ROOT / quelle).read_text(encoding="utf-8"))
    raus = []
    for treffer in LINK.finditer(text):
        ziel = treffer.group(1) or treffer.group(2)
        if re.match(r"[a-z]+:", ziel):
            continue
        pfad, _, anker = ziel.partition("#")
        raus.append((pfad, anker or None))
    return raus


@pytest.mark.parametrize("quelle", USER_DOCS)
def test_relative_links_und_bilder_fuehren_irgendwohin(quelle):
    fehlt = [f for pfad, anker in _links(quelle) if (f := _ziel_fehlt(quelle, pfad, anker))]
    assert not fehlt, f"Toter Link oder fehlendes Bild: {fehlt}"


def test_nutzerseiten_haben_links():
    """Gegenprobe: der Link-Finder findet überhaupt etwas (sonst wäre der Test oben stumm)."""
    assert len(_links("docs/README.md")) >= 12
    assert any(p.startswith("images/") for p, _ in _links("docs/drawing.md"))


def test_eigene_github_links_im_readme_zeigen_auf_dateien():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    funde = EIGENE_URL.findall(text)
    assert len(funde) >= 10, "README verlinkt keine eigenen Dateien mehr? Muster prüfen."
    fehlt = []
    for pfad, anker in funde:
        if (f := _ziel_fehlt("README.md", pfad, anker.lstrip("#") or None)):
            fehlt.append(f)
    assert not fehlt, f"README zeigt auf Dateien oder Anker, die es nicht gibt: {fehlt}"


@lru_cache
def _nur_full() -> frozenset[str]:
    def namen(profil):
        return {t.name for t in asyncio.run(create_server(profil).list_tools())}

    return frozenset((namen("full") - namen("mvp")) | VAULT_TOOLS)


def _full_verstoesse(quelle: str) -> list[str]:
    raus, abschnitt = [], ""
    text = re.sub(r"```.*?```", "", (ROOT / quelle).read_text(encoding="utf-8"), flags=re.S)
    for zeile in text.splitlines():
        if zeile.startswith("#"):
            abschnitt = zeile
        for name in re.findall(r"`([a-z]+_[a-z0-9_]+)`", zeile):
            if name in _nur_full() and "full" not in abschnitt.lower() and "full" not in zeile.lower():
                raus.append(f"{quelle}: `{name}` unter {abschnitt!r}")
    return raus


def test_full_tools_stehen_nur_unter_full():
    """Ein mvp-Nutzer sucht ein Tool, das ihm nicht registriert ist — nur, wenn die Doku es verschweigt."""
    assert _nur_full() >= {"generate_scope_table", "calculate_content"}
    verstoesse = [v for quelle in NEUE_SEITEN for v in _full_verstoesse(quelle)]
    assert not verstoesse, f"full-Tool ohne Hinweis auf das Profil: {verstoesse}"
