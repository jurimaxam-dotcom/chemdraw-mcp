# tests/test_mechanism_coords.py
"""Tests for coordinate stabilization across mechanism steps."""

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.mechanism_coords import (
    build_atom_map_index,
    compute_step_coords,
    extract_positions,
    stabilize_sequence,
)


def test_build_atom_map_index():
    mol = Chem.MolFromSmiles("[CH3:1][Br:2]")
    idx = build_atom_map_index(mol)
    assert 1 in idx
    assert 2 in idx
    assert idx[1] != idx[2]


def test_build_atom_map_index_unmapped_atoms_excluded():
    mol = Chem.MolFromSmiles("[CH3:1]C")
    idx = build_atom_map_index(mol)
    assert 1 in idx
    assert len(idx) == 1


def test_compute_step_coords_first_step_no_constraints():
    mols = [Chem.MolFromSmiles("[OH-:3]"), Chem.MolFromSmiles("[CH3:1][Br:2]")]
    result = compute_step_coords(mols, prior_positions=None)
    assert len(result) == 2
    for mol in result:
        assert mol.GetNumConformers() == 1


def test_compute_step_coords_with_prior_positions():
    mol1 = Chem.MolFromSmiles("[CH3:1][Br:2]")
    AllChem.Compute2DCoords(mol1)
    idx = build_atom_map_index(mol1)

    prior = {}
    conf = mol1.GetConformer()
    for map_id, atom_idx in idx.items():
        pos = conf.GetAtomPosition(atom_idx)
        prior[map_id] = (pos.x, pos.y)

    mol2 = Chem.MolFromSmiles("[OH:3][CH3:1]")
    result = compute_step_coords([mol2], prior_positions=prior)
    assert len(result) == 1
    assert result[0].GetNumConformers() == 1

    new_idx = build_atom_map_index(result[0])
    new_conf = result[0].GetConformer()
    if 1 in new_idx:
        new_pos = new_conf.GetAtomPosition(new_idx[1])
        assert abs(new_pos.x - prior[1][0]) < 0.5
        assert abs(new_pos.y - prior[1][1]) < 0.5


def test_extract_positions_without_conformer_raises_clear_error():
    """A mol without computed 2D coords must raise a clear ValueError,
    not a cryptic RDKit ConformerException."""
    mol = Chem.MolFromSmiles("[CH3:1][Br:2]")  # no Compute2DCoords called
    with pytest.raises(ValueError, match="[Kk]onformer|[Cc]oord"):
        extract_positions([mol])


def test_stabilize_sequence_preserves_mapped_positions():
    steps_smiles = [
        ["[OH-:3]", "[CH3:1][Br:2]"],
        ["[OH:3][CH3:1]", "[Br-:2]"],
    ]
    result = stabilize_sequence(steps_smiles)
    assert len(result) == 2
    assert all(len(mols) > 0 for mols in result)
