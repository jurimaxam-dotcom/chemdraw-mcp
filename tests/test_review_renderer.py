"""Renderer-Befunde aus dem Review 09.11.2026 (jeder Fall einmal rot gesehen)."""

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool import image_export
from chemdraw_tool.cdxml_writer import mol_to_cdxml
from chemdraw_tool.generator import generate_2d
from chemdraw_tool.mechanism_substrate import UnsupportedSubstrates, build_steps
from chemdraw_tool.structure3d import embed_3d
from chemdraw_tool.validator import validate_roundtrip


@pytest.mark.parametrize(
    "smiles",
    ["[2H]C([2H])([2H])O", "[13CH4]", "C[CH2]", "[O]", "C[C](C)C", "[CH2]"],
    ids=["methanol-d3", "13C-methan", "ethyl-radikal", "o-atom", "tert-butyl-radikal", "carben"],
)
def test_cdxml_keeps_isotopes_and_radicals(smiles):
    """Ohne Isotope/Radical liest ChemDraw D als H und füllt Radikale mit H auf: anderer Stoff."""
    mol = generate_2d(Chem.MolFromSmiles(smiles))
    result = validate_roundtrip(mol, mol_to_cdxml(mol))
    assert result.valid, [i.message for i in result.issues]


def test_cdxml_writer_leaves_the_callers_molecule_alone():
    mol = generate_2d(Chem.MolFromSmiles("C/C=C/C(=O)Oc1ccccc1"))
    before = [(b.GetBondType(), b.GetBondDir()) for b in mol.GetBonds()]
    mol_to_cdxml(mol)
    assert [(b.GetBondType(), b.GetBondDir()) for b in mol.GetBonds()] == before


def test_comparison_searches_the_common_scaffold_once(monkeypatch):
    """SVG und PNG desselben Vergleichs: eine MCS-Suche, nicht zwei (je bis 10 s)."""
    from rdkit.Chem import rdFMCS

    calls = []
    real = rdFMCS.FindMCS

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(rdFMCS, "FindMCS", counting)
    mols = [generate_2d(Chem.MolFromSmiles(s)) for s in ("CCOC(C)=O", "CCOC(=O)CC")]
    svg = image_export.render_comparison_svg(mols, ["a", "b"])
    png = image_export.render_comparison_png(mols, ["a", "b"])
    assert svg.startswith("<?xml") and png.startswith(b"\x89PNG")
    assert len(calls) == 1


def test_3d_falls_back_to_uff_when_mmff_has_no_parameters(monkeypatch):
    """MMFF meldet fehlende Parameter per Rückgabewert, nicht per Exception."""
    calls = []
    real = AllChem.UFFOptimizeMolecule
    monkeypatch.setattr(
        AllChem, "UFFOptimizeMolecule", lambda m, *a, **k: (calls.append(1), real(m, *a, **k))[1]
    )
    embed_3d(Chem.MolFromSmiles("OB(O)c1ccccc1"))  # Bor: kein MMFF94
    assert calls


@pytest.mark.parametrize(
    "substrates",
    [["CC(F)(F)Br", "[OH-].[Na+]"], ["CC(C)(O)Br", "[C-]#N.[K+]"]],
)
def test_sn2_with_three_heavy_neighbours_is_refused_with_a_reason(substrates):
    with pytest.raises(UnsupportedSubstrates):
        build_steps("sn2", substrates)
