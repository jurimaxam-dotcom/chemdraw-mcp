"""Tests für chemdraw_tool/structure3d.py — 3D-Konformer für den Panel-Viewer.

Spec (2026-06-11): ETKDGv3-Embedding + MMFF-Optimierung mit expliziten
Wasserstoffen (die tetraedrische Geometrie ist das Lernziel). Der Payload
trägt Atome (Symbol + xyz) und Bindungen (Indizes + Ordnung) für den
leichtgewichtigen SVG-Viewer der UI; die SDF-Datei ist der Datei-Export.
"""

import pytest
from rdkit import Chem

from chemdraw_tool.structure3d import atoms_and_bonds, embed_3d


def test_methane_becomes_tetrahedral_with_hydrogens():
    mol3d = embed_3d(Chem.MolFromSmiles("C"))
    assert mol3d.GetNumAtoms() == 5  # C + 4 explizite H
    conf = mol3d.GetConformer()
    assert conf.Is3D()
    zs = [conf.GetAtomPosition(i).z for i in range(5)]
    assert max(zs) - min(zs) > 0.5, "Methan muss räumlich sein, nicht planar"


def test_benzene_stays_planar():
    mol3d = embed_3d(Chem.MolFromSmiles("c1ccccc1"))
    conf = mol3d.GetConformer()
    ring = [i for i, a in enumerate(mol3d.GetAtoms()) if a.GetSymbol() == "C"]
    zs = [conf.GetAtomPosition(i).z for i in ring]
    assert max(zs) - min(zs) < 0.3, "Benzolring muss (nahezu) planar bleiben"


def test_atoms_and_bonds_payload_shape():
    mol3d = embed_3d(Chem.MolFromSmiles("CO"))
    atoms, bonds = atoms_and_bonds(mol3d)
    assert len(atoms) == 6  # C, O + 4 H
    assert {a["symbol"] for a in atoms} == {"C", "O", "H"}
    assert all(set(a) == {"symbol", "x", "y", "z"} for a in atoms)
    assert len(bonds) == 5
    assert all(set(b) == {"a", "b", "order"} for b in bonds)
    # Bindungsindizes zeigen auf gültige Atome
    for b in bonds:
        assert 0 <= b["a"] < len(atoms)
        assert 0 <= b["b"] < len(atoms)


def test_double_bond_order_is_reported():
    mol3d = embed_3d(Chem.MolFromSmiles("C=C"))
    _, bonds = atoms_and_bonds(mol3d)
    orders = sorted(b["order"] for b in bonds)
    assert orders[-1] == pytest.approx(2.0)


def test_coordinates_are_centered():
    """Schwerpunkt im Ursprung — der Viewer rotiert ums Zentrum."""
    mol3d = embed_3d(Chem.MolFromSmiles("CCO"))
    atoms, _ = atoms_and_bonds(mol3d)
    for axis in ("x", "y", "z"):
        mean = sum(a[axis] for a in atoms) / len(atoms)
        assert abs(mean) < 1e-6
