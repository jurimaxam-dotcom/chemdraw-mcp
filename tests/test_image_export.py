"""Unit-Tests für image_export.py — serverseitiges PNG/SVG-Rendering.

Das ist der ChemDraw-unabhängige Primärpfad: RDKit rendert PNG (Cairo) und
SVG direkt, ohne dass ChemDraw installiert sein muss. Kein Netz.
"""

import io
import re

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.image_export import (
    PNG_MAGIC,
    _compose_reaction,
    render_molecule_png,
    render_molecule_svg,
    render_reaction_png,
    render_reaction_svg,
    write_files,
)


def _aspirin():
    mol = Chem.MolFromSmiles("CC(=O)OC1=CC=CC=C1C(=O)O")
    AllChem.Compute2DCoords(mol)
    return mol


def _mols(*smiles_list):
    out = []
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        AllChem.Compute2DCoords(mol)
        out.append(mol)
    return out


# Fischer-Veresterung: Ethanol + Essigsäure → Ethylacetat + Wasser.
# Regressionsfall für zwei DrawReaction-Bugs (2026-06-11): H₂O (Ein-Atom-
# Molekül) wurde gar nicht gezeichnet, und die '+' kollidierten mit
# Atomlabels (lasen sich als Ladungen).
FISCHER_REACTANTS = ("CCO", "CC(=O)O")
FISCHER_PRODUCTS = ("CCOC(C)=O", "O")


def test_render_molecule_png_is_valid_png():
    png = render_molecule_png(_aspirin(), legend="Aspirin")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    assert len(png) > 1000


def test_render_molecule_svg_contains_svg_tag_and_legend():
    """RDKit rendert die Legende als Vektor-Pfade (nicht <text>) — prüfbar
    ist sie als deutlicher Mehrinhalt gegenüber dem legendenlosen Rendering."""
    svg_plain = render_molecule_svg(_aspirin())
    svg_legend = render_molecule_svg(_aspirin(), legend="Aspirin")
    assert "<svg" in svg_legend
    assert len(svg_legend) > len(svg_plain) + 500


def test_export_svg_matches_ui_line_width():
    """Export-Datei und UI-Vorschau müssen dieselbe Strichstärke haben — sonst
    sieht das gelieferte Bild anders aus als die Chat-Vorschau. Zielwert: 1.5
    (feiner, ACS-naher Stil)."""
    import re

    from chemdraw_tool.svg_renderer import render_svg

    def widths(svg):
        return sorted(set(re.findall(r"stroke-width:([\d.]+)", svg)))

    export = widths(render_molecule_svg(_aspirin()))
    ui = widths(render_svg(_aspirin()))
    assert export == ui, f"Divergenz Export {export} vs UI {ui}"
    assert export == ["1.5"], f"erwartet feine 1.5-Linien, war {export}"


def _fragment_x_ranges(layout):
    """x-Bereiche der platzierten Fragmente, aus den Conformer-Koordinaten
    des kombinierten Mols berechnet (unabhängig von Layout-Interna)."""
    conf = layout.mol.GetConformer()
    ranges = []
    for frag_atoms in Chem.GetMolFrags(layout.mol):
        xs = [conf.GetAtomPosition(i).x for i in frag_atoms]
        ranges.append((min(xs), max(xs)))
    return ranges


def test_compose_reaction_keeps_every_atom():
    """Wasser (1 Atom) darf nicht verloren gehen — alle 14 Schweratome da."""
    layout = _compose_reaction(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    assert layout.mol.GetNumAtoms() == 3 + 4 + 6 + 1
    assert len(Chem.GetMolFrags(layout.mol)) == 4


def test_compose_reaction_plus_positions_clear_of_fragments():
    """Jedes '+' braucht Sicherheitsabstand zu allen Atomkoordinaten — auch zu
    überstehenden Atomlabels (OH ragt ~0.6 Einheiten über die Koordinate)."""
    layout = _compose_reaction(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    assert len(layout.plus_positions) == 2  # 2 Edukte, 2 Produkte
    for px, py in layout.plus_positions:
        assert py == 0.0  # auf der Mittellinie
        for xmin, xmax in _fragment_x_ranges(layout):
            outside = px < xmin - 0.85 or px > xmax + 0.85
            assert outside, f"'+' bei x={px:.2f} zu nah an Fragment [{xmin:.2f}, {xmax:.2f}]"


def test_compose_reaction_arrow_separates_reactants_from_products():
    layout = _compose_reaction(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    (tail_x, tail_y), (head_x, head_y) = layout.arrow
    assert tail_y == head_y == 0.0
    assert tail_x < head_x  # zeigt nach rechts
    ranges = _fragment_x_ranges(layout)
    reactant_max = max(xmax for _, xmax in ranges[:2])
    product_min = min(xmin for xmin, _ in ranges[2:])
    assert tail_x > reactant_max + 0.85
    assert head_x < product_min - 0.85


def test_render_reaction_png_is_valid_png():
    png = render_reaction_png(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    assert len(png) > 1000


def test_render_reaction_svg_draws_water():
    """End-to-End: das letzte Atom (Wasser, Index 13) hinterlässt Tinte im SVG.
    RDKit annotiert Label-Glyphen mit class='atom-N'."""
    svg = render_reaction_svg(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    assert "<svg" in svg
    assert "atom-13" in svg


def test_render_reaction_svg_with_conditions_adds_text_element():
    """Conditions über dem Pfeil — als natives <text>-Element (Unicode-fest;
    RDKits DrawString würde 'H₂SO₄' als Atomformel parsen und stapeln)."""
    plain = render_reaction_svg(_mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS))
    with_cond = render_reaction_svg(
        _mols(*FISCHER_REACTANTS),
        _mols(*FISCHER_PRODUCTS),
        conditions="H₂SO₄ (cat.), Δ",
    )
    assert "<text" not in plain
    assert "H₂SO₄ (cat.), Δ" in with_cond


def test_render_reaction_svg_escapes_conditions_markup():
    """Conditions kommen vom LLM — XML-Metazeichen dürfen das SVG nicht brechen."""
    svg = render_reaction_svg(
        _mols(*FISCHER_REACTANTS),
        _mols(*FISCHER_PRODUCTS),
        conditions="<100 °C & HCl",
    )
    assert "<100" not in svg
    assert "&lt;100 °C &amp; HCl" in svg


def test_write_files_writes_bytes_and_text(tmp_path):
    base = tmp_path / "sub" / "aspirin"
    paths = write_files(base, {"png": b"\x89PNGxxxx", "svg": "<svg/>"})
    assert set(paths) == {"png", "svg"}
    assert (tmp_path / "sub" / "aspirin.png").read_bytes() == b"\x89PNGxxxx"
    assert (tmp_path / "sub" / "aspirin.svg").read_text() == "<svg/>"
    # Rückgabe sind absolute Pfade als Strings
    assert paths["png"].endswith("aspirin.png")


def test_write_files_overwrites_idempotently(tmp_path):
    base = tmp_path / "mol"
    write_files(base, {"svg": "<svg>alt</svg>"})
    paths = write_files(base, {"svg": "<svg>neu</svg>"})
    assert (tmp_path / "mol.svg").read_text() == "<svg>neu</svg>"
    assert len(list(tmp_path.iterdir())) == 1, "kein -2-Suffix: Regenerieren = Update"
    assert paths["svg"].endswith("mol.svg")


def test_render_molecule_svg_with_stereo_annotation():
    """annotate_stereo=True schreibt CIP-Labels (R/S) ins Bild — RDKit
    annotiert sie mit class='CIP_Code'."""
    mol = Chem.MolFromSmiles("C[C@H](N)C(=O)O")  # L-Alanin, (S)
    AllChem.Compute2DCoords(mol)
    assert "CIP_Code" in render_molecule_svg(mol, annotate_stereo=True)
    assert "CIP_Code" not in render_molecule_svg(mol)


# ---------------------------------------------------------------------------
# Etappe 3: Pfeiltypen + Bedingungen unter dem Pfeil (Opt-in)
# ---------------------------------------------------------------------------

ARROWS = ("forward", "equilibrium", "retro")


def _fischer():
    return _mols(*FISCHER_REACTANTS), _mols(*FISCHER_PRODUCTS)


def _text_ys(svg):
    return [float(y) for y in re.findall(r"<text x='[\d.]+' y='([\d.-]+)'", svg)]


def _svg_height(svg):
    return float(re.search(r"height='([\d.]+)px'", svg).group(1))


@pytest.mark.parametrize("render", [render_reaction_png, render_reaction_svg])
def test_default_arrow_is_byte_identical_to_explicit_forward(render):
    """Opt-in: die Standardwerte dürfen nichts am bisherigen Bild ändern."""
    r, p = _fischer()
    assert render(r, p, "Δ") == render(r, p, "Δ", arrow="forward", conditions_below="")


@pytest.mark.parametrize("render", [render_reaction_png, render_reaction_svg])
def test_each_arrow_type_draws_differently(render):
    r, p = _fischer()
    outputs = {a: render(r, p, arrow=a) for a in ARROWS}
    assert len(set(outputs.values())) == 3


@pytest.mark.parametrize("render", [render_reaction_png, render_reaction_svg])
def test_unknown_arrow_is_rejected(render):
    r, p = _fischer()
    with pytest.raises(ValueError, match="arrow"):
        render(r, p, arrow="resonance")


def test_equilibrium_svg_has_two_shafts_and_two_half_heads():
    """⇌: zwei parallele Schäfte, je eine gefüllte Halbspitze — statt eines
    Schafts mit Vollspitze. Gezählt wird gegen den Vorwärtspfeil."""
    r, p = _fischer()
    fwd = render_reaction_svg(r, p)
    eq = render_reaction_svg(r, p, arrow="equilibrium")
    assert eq.count("<path") > fwd.count("<path")


@pytest.mark.parametrize("arrow", ARROWS)
def test_svg_conditions_above_and_below_the_arrow(arrow):
    r, p = _fischer()
    svg = render_reaction_svg(
        r, p, "H₂SO₄ (cat.)", arrow=arrow, conditions_below="80 °C, 2 h"
    )
    above, below = _text_ys(svg)
    mid = _svg_height(svg) / 2
    assert above < mid < below
    assert "H₂SO₄ (cat.)" in svg and "80 °C, 2 h" in svg


def test_svg_only_below_text():
    """Leerer Obertext + Untertext: genau ein <text>, und der liegt unten."""
    r, p = _fischer()
    svg = render_reaction_svg(r, p, "", arrow="equilibrium", conditions_below="Δ")
    ys = _text_ys(svg)
    assert len(ys) == 1
    assert ys[0] > _svg_height(svg) / 2


def test_svg_multiline_conditions_stack_away_from_the_arrow():
    """Zeilenumbrüche werden echte Zeilen (ein <text> je Zeile, SVG würde
    '\\n' zu einem Leerzeichen zusammenfalten), oben nach oben gestapelt,
    unten nach unten — und alles bleibt auf der Leinwand."""
    r, p = _fischer()
    svg = render_reaction_svg(
        r,
        p,
        "H₂SO₄ (cat.)\nEtOH (excess)\nreflux",
        arrow="equilibrium",
        conditions_below="80 °C\n12 h",
    )
    ys = _text_ys(svg)
    assert len(ys) == 5
    above, below = ys[:3], ys[3:]
    assert above == sorted(above)  # erste Zeile zuoberst
    assert below == sorted(below)
    mid = _svg_height(svg) / 2
    assert max(above) < mid < min(below)
    assert all(0 < y < _svg_height(svg) for y in ys)
    assert "\n</text>" not in svg.replace("</text>\n", "")


def test_svg_long_conditions_are_kept_whole():
    r, p = _fischer()
    long = "Pd(PPh₃)₄ (5 mol%), K₂CO₃ (2 eq), toluene/H₂O 4:1, 100 °C, 18 h"
    svg = render_reaction_svg(r, p, long, conditions_below=long)
    assert svg.count(long) == 2


def _ink_rows(png_with, png_without):
    """Zeilen (y), in denen sich zwei PNGs unterscheiden."""
    from PIL import Image, ImageChops

    a = Image.open(io.BytesIO(png_with)).convert("RGB")
    b = Image.open(io.BytesIO(png_without)).convert("RGB")
    box = ImageChops.difference(a, b).getbbox()
    assert box is not None, "Text hat keine Tinte hinterlassen"
    return box[1], box[3], a.height


@pytest.mark.parametrize("arrow", ARROWS)
def test_png_below_text_lands_below_the_arrow(arrow):
    r, p = _fischer()
    bare = render_reaction_png(r, p, arrow=arrow)
    top, bottom, height = _ink_rows(
        render_reaction_png(r, p, arrow=arrow, conditions_below="80 °C"), bare
    )
    assert top > height / 2
    assert bottom <= height


@pytest.mark.parametrize("arrow", ARROWS)
def test_png_above_text_lands_above_the_arrow(arrow):
    r, p = _fischer()
    bare = render_reaction_png(r, p, arrow=arrow)
    top, bottom, height = _ink_rows(
        render_reaction_png(r, p, "H₂SO₄", arrow=arrow), bare
    )
    assert bottom < height / 2
    assert top >= 0


def test_png_multiline_both_sides_is_valid_and_inside_the_canvas():
    r, p = _fischer()
    bare = render_reaction_png(r, p, arrow="equilibrium")
    png = render_reaction_png(
        r, p, "H₂SO₄ (cat.)\nreflux", arrow="equilibrium", conditions_below="80 °C\n12 h"
    )
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    top, bottom, height = _ink_rows(png, bare)
    assert 0 < top < height / 2 < bottom < height
