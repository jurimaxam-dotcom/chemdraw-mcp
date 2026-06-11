"""Unit-Tests für image_export.py — serverseitiges PNG/SVG-Rendering.

Das ist der ChemDraw-unabhängige Primärpfad: RDKit rendert PNG (Cairo) und
SVG direkt, ohne dass ChemDraw installiert sein muss. Kein Netz.
"""

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
