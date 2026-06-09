"""Tests for SVG Bezier arrow rendering."""

import re

from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep
from chemdraw_tool.mechanism_renderer import render_step_svg


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    Chem.SanitizeMol(mol, sanitizeOps=Chem.SANITIZE_ALL ^ Chem.SANITIZE_PROPERTIES)
    AllChem.Compute2DCoords(mol)
    return mol


def test_render_step_svg_produces_valid_svg():
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert "<svg" in svg.lower()
    assert "</svg>" in svg.lower()


def test_render_step_svg_contains_arrow_path():
    mols = [_make_mol("[O-:3].[CH3:1].[Br-:2]")]
    step = MechanismStep(
        label="Übergangszustand",
        molecules=["[O-:3].[CH3:1].[Br-:2]"],
        arrows=[
            CurvedArrow(
                source=(3, "lone_pair"),
                target=(1, "atom"),
                style="full",
            ),
        ],
        is_transition_state=True,
        partial_bonds=[(3, 1)],
    )
    svg = render_step_svg(step, mols)
    assert "path" in svg.lower()


def test_render_step_svg_transition_state_has_dashed_line():
    mols = [_make_mol("[O-:3].[CH3:1].[Br-:2]")]
    step = MechanismStep(
        label="TS",
        molecules=["[O-:3].[CH3:1].[Br-:2]"],
        arrows=[],
        is_transition_state=True,
        partial_bonds=[(3, 1)],
    )
    svg = render_step_svg(step, mols)
    assert "stroke-dasharray" in svg


def test_render_step_svg_no_arrows_no_paths():
    mols = [_make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    path_count = len(re.findall(r"<path[^>]*class=['\"]arrow", svg))
    assert path_count == 0


def test_render_step_svg_multi_molecule():
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert "<svg" in svg.lower()


def test_render_step_svg_has_exactly_one_viewbox():
    """RDKit emits a viewBox; the renderer must replace it, not add a second."""
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert svg.lower().count("viewbox") == 1
