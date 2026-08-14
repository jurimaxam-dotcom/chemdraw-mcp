"""Tests für render_style.py — Zeichenstile und Gruppen-Abkürzungen.

Beide Features sind opt-in. Der wichtigste Test hier ist der langweiligste:
ohne Stil darf an den MolDrawOptions KEIN Feld anders sein als vorher —
sonst kippt der committete Pixel-Snapshot der UI-Vorschau.
"""

import re

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.render_style import (
    STYLES,
    apply_style,
    condense_groups,
    get_style,
)

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
TRIPHENYLPHOSPHINE = "c1ccccc1P(c1ccccc1)c1ccccc1"


def _mol(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def _option_snapshot(opts) -> dict:
    """Alle skalaren MolDrawOptions-Felder als Vergleichsabbild."""
    snap = {}
    for name in dir(opts):
        if name.startswith("_"):
            continue
        value = getattr(opts, name)
        if isinstance(value, (bool, int, float, str, tuple)):
            snap[name] = value
    return snap


def _stroke_widths(svg: str) -> list[str]:
    return sorted(set(re.findall(r"stroke-width:([\d.]+)", svg)))


def _fill_colors(svg: str) -> set[str]:
    return {
        a or b
        for a, b in re.findall(
            r"fill:\s*#([0-9A-Fa-f]{6})|fill='#([0-9A-Fa-f]{6})'", svg
        )
    }


def _render(mol, style: str = "") -> str:
    """Zeichnet wie die Produktion: erst die geteilte Basis, dann das Preset."""
    from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

    drawer = rdMolDraw2D.MolDraw2DSVG(500, 400)
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    apply_style(drawer.drawOptions(), style)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


# --- Stile: Default muss ein echtes No-op sein -------------------------------


def test_empty_style_touches_no_single_option():
    """Der Default-Pfad ruft apply_style ebenfalls auf — er darf nachweislich
    nichts verändern, sonst driftet jedes Default-Rendering."""
    touched = rdMolDraw2D.MolDraw2DSVG(300, 300).drawOptions()
    untouched = rdMolDraw2D.MolDraw2DSVG(300, 300).drawOptions()
    before = _option_snapshot(untouched)
    apply_style(touched, "")
    assert _option_snapshot(touched) == before


def test_get_style_returns_none_for_default():
    assert get_style("") is None
    assert get_style(None) is None


def test_unknown_style_raises_and_names_the_valid_ones():
    with pytest.raises(ValueError, match="presentation"):
        get_style("nature-2024")


def test_style_names_are_case_and_space_insensitive():
    assert get_style("  Presentation ") is STYLES["presentation"]


# --- Stile: die Presets müssen sichtbar etwas tun ---------------------------


def test_compact_draws_thinner_than_default_presentation_thicker():
    mol = _mol(ASPIRIN)
    default = _stroke_widths(_render(mol))
    assert default == ["1.5"], f"Default-Strichstärke verschoben: {default}"
    assert _stroke_widths(_render(mol, "compact")) == ["1.2"]
    assert _stroke_widths(_render(mol, "presentation")) == ["3.0"]


def test_grayscale_removes_every_element_color():
    """Heteroatome sind im Default rot/blau — im Graustufendruck werden daraus
    ununterscheidbare Grautöne, deshalb der Schwarz-Weiß-Palettenwechsel."""
    mol = _mol("CC(=O)Oc1ccccc1C(=O)NCCN")
    assert _fill_colors(_render(mol)) & {"FF0000", "0000FF"}
    assert _fill_colors(_render(mol, "grayscale")) <= {"000000", "FFFFFF"}


def test_grayscale_keeps_default_geometry():
    """Graustufe ist nur ein Palettenwechsel — wer sie wählt, soll nicht
    zusätzlich eine andere Strichstärke bekommen."""
    mol = _mol(ASPIRIN)
    assert _stroke_widths(_render(mol, "grayscale")) == _stroke_widths(_render(mol))


# --- Parität Export ↔ UI-Vorschau, für JEDEN Stil ---------------------------


@pytest.mark.parametrize("style", ["", *sorted(STYLES)])
def test_export_and_ui_preview_share_the_stroke_width(style):
    """Die geteilte Konstante BOND_LINE_WIDTH bleibt die Basis; ein Preset
    überschreibt sie nur pro Zeichenvorgang — und zwar in BEIDEN Pfaden.
    Deshalb gilt die Parität nicht nur im Default, sondern je Stil."""
    from chemdraw_tool.image_export import render_molecule_svg
    from chemdraw_tool.svg_renderer import render_svg

    mol = _mol(ASPIRIN)
    export = _stroke_widths(render_molecule_svg(mol, style=style))
    preview = _stroke_widths(render_svg(mol, style=style))
    assert export == preview, f"Stil {style!r}: Export {export} vs UI {preview}"


def test_presets_also_scale_the_conditions_text_above_the_arrow():
    """Der Bedingungstext läuft NICHT über MolDrawOptions — die Backends
    overlayen ihn selbst. Ohne eigenen Faktor bliebe er im Präsentationsstil
    als einziges Element klein und der Stil hielte sein Versprechen nicht."""
    from chemdraw_tool.image_export import render_reaction_svg

    def font_px(style: str) -> float:
        svg = render_reaction_svg(
            [_mol("CCO")], [_mol("CC=O")], "H2SO4, 60 °C", style=style
        )
        return float(re.search(r"font-size='([\d.]+)px'", svg).group(1))

    assert font_px("presentation") > font_px("") > font_px("compact")


def test_conditions_text_and_arrow_gap_stay_in_proportion():
    """Ein größerer Bedingungstext ohne größeren Zwischenraum schiebt sich in
    die Strukturen (gesehen bei 'presentation'). Beide Maße müssen deshalb mit
    demselben Faktor wachsen — dann bleibt das Kollisionsverhalten das des
    Standardstils."""
    from chemdraw_tool.image_export import ARROW_LENGTH, _reaction_metrics

    base_arrow, base_font = _reaction_metrics("")
    assert base_arrow == ARROW_LENGTH
    for style in sorted(STYLES):
        arrow, font = _reaction_metrics(style)
        assert font / arrow == pytest.approx(base_font / base_arrow), style


def test_bond_line_width_constant_is_untouched_by_presets():
    """Presets dürfen die Single Source of Truth nicht umdefinieren."""
    from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

    _render(_mol(ASPIRIN), "presentation")
    assert BOND_LINE_WIDTH == 1.5


# --- Gruppen-Abkürzungen ----------------------------------------------------


def _labels(mol) -> list[str]:
    return [a.GetProp("atomLabel") for a in mol.GetAtoms() if a.HasProp("atomLabel")]


def test_condense_groups_uses_rdkit_defaults():
    condensed = condense_groups(_mol(ASPIRIN))
    assert set(_labels(condensed)) == {"OAc", "CO2H"}
    assert condensed.GetNumAtoms() < _mol(ASPIRIN).GetNumAtoms()


def test_condense_groups_contracts_phenyl_rings():
    """Der Kern des Features: RDKits Default-Liste kennt kein Ph — ohne die
    Zusatzdefinitionen bliebe Triphenylphosphin voll ausgezeichnet."""
    full = _mol(TRIPHENYLPHOSPHINE)
    condensed = condense_groups(full)
    assert _labels(condensed) == ["Ph", "Ph", "Ph"]
    assert full.GetNumAtoms() == 19
    assert condensed.GetNumAtoms() == 4


def test_condense_groups_leaves_fused_and_biaryl_rings_alone():
    """Falsch-positive Ph wären schlimmer als gar keine Abkürzung: in Naphthalin
    und Biphenyl darf kein Ring verschwinden."""
    for smiles in ("c1ccc2ccccc2c1", "c1ccccc1-c1ccccc1"):
        full = _mol(smiles)
        assert condense_groups(full).GetNumAtoms() == full.GetNumAtoms(), smiles


def test_condense_groups_keeps_a_conformer_and_renders():
    condensed = condense_groups(_mol(TRIPHENYLPHOSPHINE))
    assert condensed.GetNumConformers() == 1
    assert "<svg" in _render(condensed)


def test_condense_groups_does_not_mutate_the_input():
    mol = _mol(ASPIRIN)
    before = mol.GetNumAtoms()
    condense_groups(mol)
    assert mol.GetNumAtoms() == before


def test_max_coverage_caps_how_much_of_a_molecule_collapses():
    """RDKits maxCoverage verhindert, dass ein kleines Molekül zu einem
    einzigen Label zusammenfällt — belegt am Boc-Piperazin."""
    mol = _mol("CC(C)(C)OC(=O)N1CCNCC1")
    assert "Boc" not in _labels(condense_groups(mol))
    assert "Boc" in _labels(condense_groups(mol, max_coverage=0.9))
