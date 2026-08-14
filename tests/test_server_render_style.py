"""Vertragstests für die opt-in-Renderoptionen der generate_*-Tools.

Spec: `render_style` und `abbreviate_groups` sind beide opt-in. Ohne sie muss
das Ergebnis Zeichen für Zeichen das bisherige sein — der erste Test hier ist
genau diese Zusicherung, alles andere sind die neuen Fähigkeiten.
SMILES-Inputs → resolve() geht nie ins Netz; PubChem-Enrichment ist gemockt.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from chemdraw_tool.server import batch_generate, generate_molecule, generate_reaction

ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"
TRIPHENYLPHOSPHINE = "c1ccccc1P(c1ccccc1)c1ccccc1"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    monkeypatch.setattr("chemdraw_tool.server.REACTION_DIR", tmp_path / "rxn")
    with patch("chemdraw_tool.server._enrich_properties", return_value={}):
        yield tmp_path


def _stroke_widths(svg: str) -> list[str]:
    return sorted(set(re.findall(r"stroke-width:([\d.]+)", svg)))


# --- Der Default darf sich nicht bewegen ------------------------------------


def test_default_call_renders_exactly_like_the_untouched_pipeline():
    """Referenz ist der alte Codepfad, direkt nachgebaut: resolve → 2D →
    render_svg ohne jede neue Option. Weicht das Tool davon ab, hat eine der
    neuen Optionen sich in den Default geschlichen."""
    from chemdraw_tool.generator import generate_2d
    from chemdraw_tool.resolver import resolve
    from chemdraw_tool.svg_renderer import render_svg

    _, mol = resolve(ASPIRIN)
    expected = render_svg(generate_2d(mol), fill_container=True)

    assert generate_molecule(ASPIRIN, label="Aspirin").svg == expected


def test_default_call_keeps_the_shared_line_width():
    payload = generate_molecule(ASPIRIN, label="Aspirin")
    assert _stroke_widths(payload.svg) == ["1.5"]
    assert _stroke_widths(Path(payload.files["svg"]).read_text()) == ["1.5"]


def test_unknown_style_raises_before_anything_is_written(tmp_path):
    with pytest.raises(ValueError, match="render_style"):
        generate_molecule(ASPIRIN, render_style="nature")
    assert not list((tmp_path / "mol").glob("*"))


# --- Stil-Presets -----------------------------------------------------------


def test_presentation_style_thickens_preview_and_exported_file():
    payload = generate_molecule(ASPIRIN, label="Aspirin", render_style="presentation")
    assert _stroke_widths(payload.svg) == ["3.0"]
    assert _stroke_widths(Path(payload.files["svg"]).read_text()) == ["3.0"]


def test_compact_style_thins_preview_and_exported_file():
    payload = generate_molecule(ASPIRIN, label="Aspirin", render_style="compact")
    assert _stroke_widths(payload.svg) == ["1.2"]
    assert _stroke_widths(Path(payload.files["svg"]).read_text()) == ["1.2"]


def test_grayscale_style_drops_element_colors():
    payload = generate_molecule("CC(=O)Nc1ccccc1O", render_style="grayscale")
    colored = re.findall(r"fill='#(?!000000|FFFFFF)[0-9A-F]{6}'", payload.svg)
    assert not colored, f"Farbreste im Graustufenstil: {colored[:3]}"


def test_reaction_and_batch_take_the_style_too():
    rxn = generate_reaction(
        ["CCO"], ["CC=O"], name="Oxidation", render_style="presentation"
    )
    assert _stroke_widths(Path(rxn.files["svg"]).read_text()) == ["3.0"]

    batch = batch_generate([ASPIRIN], render_style="compact")
    assert _stroke_widths(batch.molecules[0].svg) == ["1.2"]


# --- Gruppen-Kontraktion ----------------------------------------------------


def test_abbreviate_groups_shrinks_the_drawn_structure():
    """Triphenylphosphin: drei ausgezeichnete Ringe (19 Atome) werden zu drei
    Ph-Labels. Messbar an den Bindungslinien der Vorschau."""
    plain = generate_molecule(TRIPHENYLPHOSPHINE, label="PPh3")
    short = generate_molecule(TRIPHENYLPHOSPHINE, label="PPh3", abbreviate_groups=True)
    assert plain.svg.count("<path") > short.svg.count("<path")
    assert "Ph" not in plain.svg
    assert short.svg != plain.svg


def test_abbreviate_groups_reaches_the_exported_files_too():
    plain = generate_molecule(TRIPHENYLPHOSPHINE, label="PPh3-plain")
    short = generate_molecule(
        TRIPHENYLPHOSPHINE, label="PPh3-kurz", abbreviate_groups=True
    )
    plain_svg = Path(plain.files["svg"]).read_text()
    short_svg = Path(short.files["svg"]).read_text()
    assert short_svg.count("<path") < plain_svg.count("<path")


def test_abbreviated_analysis_still_describes_the_full_molecule():
    """Abkürzen ist eine Zeichenentscheidung, keine chemische: die
    funktionellen Gruppen müssen weiter am vollen Molekül bestimmt werden."""
    plain = generate_molecule(ASPIRIN, label="Aspirin")
    short = generate_molecule(ASPIRIN, label="Aspirin", abbreviate_groups=True)
    names = {g.name for g in plain.functionalGroups}
    assert names == {g.name for g in short.functionalGroups}
    assert "Ester" in names


def test_abbreviated_payload_drops_the_atom_overlay():
    """Die Atomliste positioniert Tooltip und Highlight über dem SVG. Nach dem
    Abkürzen stimmt sie nicht mehr mit dem Gezeichneten überein — dann lieber
    keine Overlay-Daten als falsch platzierte."""
    short = generate_molecule(ASPIRIN, abbreviate_groups=True)
    assert short.atoms == []
    assert generate_molecule(ASPIRIN).atoms != []


def test_cdxml_export_keeps_the_full_structure(tmp_path):
    """CDXML geht zum Weiterbearbeiten nach ChemDraw — dort will niemand
    Dummy-Atome mit Textlabel, sondern die echte Struktur."""
    payload = generate_molecule(
        TRIPHENYLPHOSPHINE,
        label="PPh3",
        formats=["cdxml"],
        abbreviate_groups=True,
    )
    cdxml = Path(payload.cdxml_path).read_text()
    assert cdxml.count("<n ") == 19, "CDXML muss alle 19 Atome enthalten"


def test_batch_and_reaction_take_abbreviations_too():
    batch = batch_generate([TRIPHENYLPHOSPHINE], abbreviate_groups=True)
    plain = batch_generate([TRIPHENYLPHOSPHINE])
    assert batch.molecules[0].svg.count("<path") < plain.molecules[0].svg.count("<path")

    rxn_short = generate_reaction(
        [TRIPHENYLPHOSPHINE], ["O=P(c1ccccc1)(c1ccccc1)c1ccccc1"],
        name="Wittig-Oxid",
        abbreviate_groups=True,
    )
    rxn_plain = generate_reaction(
        [TRIPHENYLPHOSPHINE], ["O=P(c1ccccc1)(c1ccccc1)c1ccccc1"], name="Wittig-Oxid2"
    )
    short_svg = Path(rxn_short.files["svg"]).read_text()
    plain_svg = Path(rxn_plain.files["svg"]).read_text()
    assert short_svg.count("<path") < plain_svg.count("<path")
