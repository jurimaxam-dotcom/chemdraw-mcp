"""Unit-Tests für image_export.py — serverseitiges PNG/SVG-Rendering.

Das ist der ChemDraw-unabhängige Primärpfad: RDKit rendert PNG (Cairo) und
SVG direkt, ohne dass ChemDraw installiert sein muss. Kein Netz.
"""

from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.image_export import (
    PNG_MAGIC,
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


def test_render_reaction_png_is_valid_png():
    png = render_reaction_png("CCO.CC(=O)O>>CC(=O)OCC")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    assert len(png) > 1000


def test_render_reaction_svg_contains_svg_tag():
    svg = render_reaction_svg("CCO.CC(=O)O>>CC(=O)OCC")
    assert "<svg" in svg


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
