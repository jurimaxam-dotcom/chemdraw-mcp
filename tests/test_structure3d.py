"""Tests für chempane/structure3d.py — 3D-Konformer für den Panel-Viewer.

Spec (2026-06-11): ETKDGv3-Embedding + MMFF-Optimierung mit expliziten
Wasserstoffen (die tetraedrische Geometrie ist das Lernziel). Der Payload
trägt Atome (Symbol + xyz) und Bindungen (Indizes + Ordnung) für den
leichtgewichtigen SVG-Viewer der UI; die SDF-Datei ist der Datei-Export.
"""

import math
import subprocess
import sys
import time

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chempane.structure3d import atoms_and_bonds, embed_3d

C60_SMILES = (
    "c12c3c4c5c1c1c6c7c2c2c8c3c3c9c4c4c%10c5c5c1c1c6c6c%11c7c2c2c7c8c3c3c8c9c4c4"
    "c9c%10c5c5c1c1c6c6c%11c2c2c7c3c3c8c4c4c9c5c1c1c6c2c3c41"
)


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


def test_cage_embedding_respects_time_limit():
    """Kein Embedding darf minutenlang blockieren: C60 (hing ~3 min) bleibt klar unter 10 s."""
    code = (
        "from rdkit import Chem; from chempane.structure3d import embed_3d; "
        f"m = embed_3d(Chem.MolFromSmiles({C60_SMILES!r})); print(m.GetNumAtoms())"
    )
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    dt = time.perf_counter() - t0
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "60"
    assert dt < 10.0


def test_c60_fullerene_geometry():
    """C60 gelingt offline: 60 Atome, 90 Bindungen, alle C-C-Abstände in 1.36–1.48 Å."""
    mol3d = embed_3d(Chem.MolFromSmiles(C60_SMILES))
    assert mol3d.GetNumAtoms() == 60
    assert mol3d.GetNumBonds() == 90
    conf = mol3d.GetConformer()
    assert conf.Is3D()
    dists = [
        conf.GetAtomPosition(b.GetBeginAtomIdx()).Distance(conf.GetAtomPosition(b.GetEndAtomIdx()))
        for b in mol3d.GetBonds()
    ]
    assert all(1.36 <= d <= 1.48 for d in dists), f"C-C außerhalb 1.36–1.48 Å: {min(dists):.3f}..{max(dists):.3f}"
    atoms, _ = atoms_and_bonds(mol3d)
    radii = [math.sqrt(a["x"] ** 2 + a["y"] ** 2 + a["z"] ** 2) for a in atoms]
    assert max(radii) - min(radii) < 0.05, f"C60 nicht kugelförmig: R={min(radii):.3f}..{max(radii):.3f}"


def test_failed_embedding_raises_honest_error(monkeypatch):
    """Scheitern alle Embedding-Versuche, bleibt die Fehlermeldung ehrlich."""
    monkeypatch.setattr(AllChem, "EmbedMolecule", lambda *a, **kw: -1)
    with pytest.raises(ValueError, match="3D embedding failed"):
        embed_3d(Chem.MolFromSmiles("C"))
