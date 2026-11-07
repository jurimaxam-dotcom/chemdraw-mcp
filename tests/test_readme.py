"""README-Gate: Toolliste, Zahlen und Bilder im README gegen den echten Server.

Seit 05.11.2026 ist das README kurz (Galerie statt Vollbild je Tool); die
Referenzteile liegen in docs/tools.md (Tools im Detail, Profiles, Limitations).
Die Prüfungen laufen deshalb über README + DOCS — Absicht unverändert.

Das README ist die erste Seite, die ein Nutzer sieht — eine Toolzeile ohne Tool
oder ein Tool ohne Zeile ist dort ein stiller Fehler. Darum:

(a) jede MVP-Registrierung steht in der Tooltabelle, keine Zeile ohne Tool;
    die Zusatztools des Vollprofils stehen im Abschnitt Profiles;
(b) „16 tools“ / „23 tools“ stimmen mit create_server("mvp"/"full");
(c) jedes referenzierte assets/-Bild existiert;
(d) jedes Skript-Bild (scripts/readme_bilder.py) trägt den SHA-256 aus
    tests/__fixtures__/readme_bilder.sha256 — ein Bild von Hand ersetzt, ist rot.

Bewusst neu segnen, nachdem das Skript die Bilder neu erzeugt hat:
    uv run python scripts/readme_bilder.py
    UPDATE_README_BILDER=1 uv run pytest tests/test_readme.py

(d) vergleicht nur Dateien, es rendert nicht neu: Pixel aus matplotlib/Cairo
unterscheiden sich zwischen macOS und dem Linux-CI, ein Neu-Rendern im Gate
wäre falsch-rot. Dass das Skript deterministisch ist, prüft es selbst
(`--pruefen`: zweimal rendern, Hashes vergleichen).
"""

import asyncio
import hashlib
import importlib.util
import os
import re
from functools import lru_cache
from pathlib import Path

from chemdraw_tool.server import create_server

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
# Nutzer-Doku, auf die das README verlinkt; trägt Profiles und die übrigen Bilder.
TOOLS_DOC = (ROOT / "docs" / "tools.md").read_text(encoding="utf-8")
DOCS = [README, TOOLS_DOC, *(
    (ROOT / "docs" / n).read_text(encoding="utf-8") for n in ("installation.md", "development.md")
)]
MANIFEST = ROOT / "tests" / "__fixtures__" / "readme_bilder.sha256"
UPDATE_HINT = (
    "Bewusst neu segnen:  uv run python scripts/readme_bilder.py && "
    "UPDATE_README_BILDER=1 uv run pytest tests/test_readme.py"
)
# Erscheinen nur mit CHEMDRAW_VAULT_PATH — das README nennt sie im Fließtext.
VAULT_TOOLS = {"search_vault", "read_vault_entry"}


@lru_cache
def _tools(profile: str) -> frozenset[str]:
    tools = asyncio.run(create_server(profile).list_tools())
    return frozenset(t.name for t in tools)


def _section(start: str, end: str, text: str = README) -> str:
    """Text zwischen zwei Überschriften (start inklusive, end exklusive)."""
    begin = text.index(start)
    return text[begin : text.index(end, begin + len(start))]


def _table_tools() -> set[str]:
    rows = [line for line in _section("## Tools", "\n## ").splitlines() if line.startswith("|")]
    return {m for line in rows for m in re.findall(r"\| `(\w+)` \|", line)}


def test_tooltabelle_nennt_genau_die_mvp_tools():
    erwartet = set(_tools("mvp")) - {"save_png"}
    tabelle = _table_tools()
    assert not erwartet - tabelle, f"registriert, aber ohne README-Zeile: {sorted(erwartet - tabelle)}"
    assert not tabelle - erwartet, f"README-Zeile ohne MVP-Tool: {sorted(tabelle - erwartet)}"


def test_save_png_ist_im_toolabschnitt_erklaert():
    assert "save_png" in _tools("mvp")
    assert "`save_png`" in _section("## Tools", "\n## ")


def test_profilabschnitt_nennt_genau_die_zusatztools_des_vollprofils():
    erwartet = set(_tools("full")) - set(_tools("mvp")) - VAULT_TOOLS
    genannt = set(re.findall(r"\*\*`(\w+)`\*\*", _section("## Profiles", "\n## ", TOOLS_DOC)))
    assert not erwartet - genannt, f"im Vollprofil, aber nicht unter Profiles: {sorted(erwartet - genannt)}"
    assert not genannt - erwartet, f"unter Profiles, aber kein Zusatztool: {sorted(genannt - erwartet)}"


def test_toolzahlen_stimmen_mit_den_profilen():
    mvp, full = len(_tools("mvp")), len(_tools("full"))
    assert f"registers {mvp} tools" in README
    assert f"The {mvp}th tool, `save_png`" in README
    profile = _section("## Profiles", "The `full` profile adds", TOOLS_DOC)
    assert f"| `mvp` (default) | {mvp}," in profile
    assert f"| `full` | {full}," in profile
    assert f"# all {full} tools" in TOOLS_DOC
    # Keine andere „N tools“-Zahl, die stehen geblieben ist — in keiner der Dateien.
    for zahl in re.findall(r"\b(\d+) tools\b", "\n".join(DOCS)):
        assert int(zahl) in {mvp, full}, f"„{zahl} tools“ in README/docs passt zu keinem Profil"


def _asset_refs(texte: list[str] = DOCS) -> list[str]:
    return sorted({m for x in texte for m in re.findall(r"assets/([\w.-]+\.(?:png|gif|svg|jpg))", x)})


def test_jedes_referenzierte_bild_existiert():
    refs = _asset_refs()
    assert refs, "README referenziert keine Bilder — Regex kaputt?"
    fehlend = [r for r in refs if not (ROOT / "assets" / r).is_file()]
    assert not fehlend, f"README zeigt auf fehlende Bilder: {fehlend}"


def _skript_bilder() -> list[str]:
    spec = importlib.util.spec_from_file_location("readme_bilder", ROOT / "scripts" / "readme_bilder.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul.BILDER


def _sha(name: str) -> str:
    return hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()


def test_jedes_skriptbild_steht_im_readme():
    fehlend = sorted(set(_skript_bilder()) - set(_asset_refs()))
    assert not fehlend, f"Skript erzeugt Bilder, die weder README noch docs zeigen: {fehlend}"


def test_skriptbilder_tragen_den_gesegneten_hash():
    bilder = _skript_bilder()
    if os.environ.get("UPDATE_README_BILDER") == "1":
        MANIFEST.write_text("".join(f"{_sha(n)}  {n}\n" for n in bilder), encoding="utf-8")
        return
    assert MANIFEST.is_file(), f"Hash-Manifest fehlt: {MANIFEST}\n{UPDATE_HINT}"
    gesegnet = dict(
        reversed(line.split("  ", 1)) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line
    )
    assert sorted(gesegnet) == sorted(bilder), (
        f"Manifest und Skript nennen verschiedene Bilder.\n{UPDATE_HINT}"
    )
    anders = [n for n in bilder if _sha(n) != gesegnet[n]]
    assert not anders, (
        f"assets/ weicht vom gesegneten Skript-Stand ab: {anders} — von Hand ersetzt "
        f"oder Skript geändert, ohne neu zu segnen?\n{UPDATE_HINT}"
    )


# --- README = PyPI-Beschreibung (pyproject: readme = "README.md") -------------


def test_readme_verlinkt_nur_absolut():
    """PyPI löst relative Pfade nicht auf: dort wäre jedes Bild und jede docs-Seite tot."""
    ziele = re.findall(r"\]\(([^)\s]+)\)", README) + re.findall(r'(?:src|href)="([^"]+)"', README)
    relativ = [z for z in ziele if not z.startswith(("https://", "#", "mailto:"))]
    assert not relativ, f"relative Links im README (auf PyPI tot): {relativ}"


def test_readme_verweist_auf_die_ausgelagerten_docs():
    for name in ("tools.md", "installation.md", "development.md"):
        url = f"https://github.com/jurimaxam-dotcom/chemdraw-mcp/blob/main/docs/{name}"
        assert url in README, f"README verlinkt docs/{name} nicht"


def test_anker_und_registry_kennung_bleiben():
    # #tools/#installation verlinken Quick start, Release-Notes und Posts;
    # die mcp-name-Zeile braucht die MCP-Registry für die PyPI-Zuordnung.
    assert "\n## Tools\n" in README and "\n## Installation\n" in README
    assert "<!-- mcp-name: io.github.jurimaxam-dotcom/chemdraw-mcp -->" in README


def test_readme_erklaert_beide_konnektoren():
    """Welle 3 (Jay 06.11.2026): zwei Konnektoren aus einer Installation, einer je Chat."""
    profile = _section("### Profiles", "\n## ", README)
    for name in ("`chemdraw`", "`chemdraw-pharma`", "`mvp`", "`full`"):
        assert name in profile, name
    assert "chemdraw-mcp-pharma-<version>.mcpb" in profile
    assert "no restart" in profile
    for doc in (README, TOOLS_DOC):
        assert "chemdraw-pharma" in doc
