"""Tool-`title` und Annotationen: was der Host Menschen zeigt und wie er fragt.

Claude entscheidet an `readOnlyHint`, ob ein Tool ohne Freigabe-Klick laufen
darf (Anthropic-Leitfaden, siehe docs/anthropic/moeglichkeiten.md §1). Ein
lesend markiertes Tool, das doch Dateien schreibt, wäre also eine stille
Rechteausweitung. Deshalb steht die Liste der schreibenden Tools hier
ausdrücklich — ein neues Tool oder eine umgedeutete Markierung fällt im Review
auf, statt aus einer Ableitung zu rutschen.

`save_png` ist nur fürs Panel: `_meta.ui.visibility = ["app"]` (ext-apps
`McpUiToolMeta.visibility`). Es bleibt in `tools/list` — filtern muss der Host —
und zählt nicht als Panel-Tool, weil es keine `resourceUri` trägt.
"""

import asyncio

import pytest

from chemdraw_tool.server import _RESOURCE_URI, create_server
from tests.server_catalog import mcp
from tests.test_server_profiles import _data

# Legen Dateien unter ~/ChemDraw-Output an (bzw. ein Anki-Deck). Geprüft am
# Code: write_files / write_text / write_deck / save_png_bytes im Tool-Körper.
WRITING = {
    "generate_molecule", "batch_generate", "compare_molecules",
    "generate_reaction", "generate_scope_table", "generate_3d",
    "generate_protein_or_antibody", "generate_spectrum", "generate_tlc",
    "generate_titration_curve", "generate_species_distribution",
    "generate_calibration_curve", "generate_pk_curve", "generate_dose_response",
    "export_anki_deck", "save_png",
}
# Kein Netz: weder resolve() auf einen Namen noch eine Datenbank-Abfrage.
OFFLINE = {
    "generate_spectrum", "generate_tlc", "generate_titration_curve",
    "generate_species_distribution", "generate_calibration_curve",
    "generate_pk_curve", "generate_dose_response",
    "calculate_solution", "calculate_content", "calculate_ph",
    "calculate_pharmacokinetics", "save_png",
}
# Ändert beim Wiederholen Fremdes: ein Re-Export aktualisiert vorhandene Karten
# (per „open“/AnkiConnect auch in der Anki-Sammlung des Nutzers).
DESTRUCTIVE = {"export_anki_deck"}
VAULT = {"search_vault", "read_vault_entry"}


def _tools(server=mcp):
    """Ohne Vault-Tools (nur mit CHEMDRAW_VAULT_PATH da) — die prüft ein eigener Test."""
    return {t.name: t for t in asyncio.run(server.list_tools()) if t.name not in VAULT}


def test_every_tool_has_a_short_title_and_annotations():
    for name, tool in _tools().items():
        assert tool.title and len(tool.title) <= 40, name
        assert tool.title[0].isupper() and "_" not in tool.title, name
        hints = tool.annotations
        assert hints is not None, name
        assert hints.read_only_hint is not None, name
        assert hints.open_world_hint is not None, name


def test_titles_are_unique():
    titles = [t.title for t in _tools().values()]
    assert len(titles) == len(set(titles))


def test_writing_tools_are_listed_explicitly():
    writing = {n for n, t in _tools().items() if not t.annotations.read_only_hint}
    assert writing == WRITING


def test_writing_tools_state_whether_they_destroy():
    for name in WRITING:
        hints = _tools()[name].annotations
        assert hints.destructive_hint is (name in DESTRUCTIVE), name


def test_save_png_is_not_idempotent_but_regenerating_files_is():
    # save_png hängt -2, -3 … an; die generate_*-Tools schreiben denselben Pfad neu.
    tools = _tools()
    assert tools["save_png"].annotations.idempotent_hint is False
    for name in WRITING - DESTRUCTIVE - {"save_png"}:
        assert tools[name].annotations.idempotent_hint is True, name


def test_read_only_tools_carry_no_write_hints():
    for name, tool in _tools().items():
        if tool.annotations.read_only_hint:
            assert tool.annotations.destructive_hint is None, name
            assert tool.annotations.idempotent_hint is None, name


def test_open_world_marks_exactly_the_tools_that_can_go_online():
    online = {n for n, t in _tools().items() if t.annotations.open_world_hint}
    assert online == set(_tools()) - OFFLINE


def test_mvp_carries_the_same_titles_and_annotations():
    full = _tools()
    for name, tool in _tools(create_server("mvp")).items():
        assert tool.title == full[name].title, name
        assert tool.annotations == full[name].annotations, name


def test_vault_tools_are_annotated_too():
    tools = {t["name"]: t for t in _data("full", vault=True)["tools"]}
    for name in VAULT:
        assert tools[name]["title"], name
        hints = {k: v for k, v in (tools[name]["annotations"] or {}).items() if v is not None}
        assert hints == {"readOnlyHint": True, "openWorldHint": False}, name


@pytest.mark.parametrize("profile", ["mvp", "full"])
def test_save_png_is_visible_to_the_panel_only(profile):
    tool = _tools(create_server(profile))["save_png"]
    assert tool.meta == {"ui": {"visibility": ["app"]}}


@pytest.mark.parametrize("profile", ["mvp", "full"])
def test_only_save_png_hides_from_the_model(profile):
    hidden = {
        n for n, t in _tools(create_server(profile)).items()
        if "model" not in ((t.meta or {}).get("ui") or {}).get("visibility", ["model"])
    }
    assert hidden == {"save_png"}


def test_save_png_is_no_panel_tool():
    tool = _tools()["save_png"]
    assert ((tool.meta or {}).get("ui") or {}).get("resourceUri") != _RESOURCE_URI
