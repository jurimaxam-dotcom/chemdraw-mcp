"""„All H“ bei verbrückten Polycyclen: keine H übereinander (11.11.2026).

`Chem.AddHs(addCoords=True)` setzte die H ohne Blick auf die Nachbarschaft:
Bei Morphin lagen im Käfig mehrere H-Beschriftungen aufeinander, eines
verdeckte das N. Gemessen wird der kleinste Abstand eines H zu einem anderen H
oder einem nicht mit ihm gebundenen Schweratom, in mittleren Bindungslängen.

Schwelle: Ein H-Label ist im Bild etwa 0,3 Bindungslängen breit (Adamantan bei
1200 px: Bindung ≈ 218 px, „H“ ≈ 55–65 px). Ab 0,4 berühren sich zwei Labels
nicht mehr. Vorher lagen die Käfige bei 0,07–0,26, flache Moleküle bei ≥ 0,61.
"""

import math

import pytest
from rdkit import Chem

from chemdraw_tool import server as srv
from chemdraw_tool.generator import generate_2d

MIN_CLEARANCE = 0.4

CAGES = {
    "morphine": "CN1CC[C@]23c4c5ccc(O)c4O[C@H]2[C@@H](O)C=C[C@H]3[C@H]1C5",
    "camphor": "CC1(C)C2CCC1(C)C(=O)C2",
    "adamantane": "C1C2CC3CC1CC(C2)C3",
    "testosterone": "C[C@]12CC[C@H]3[C@@H](CCC4=CC(=O)CC[C@]34C)[C@@H]1CC[C@@H]2O",
    "cubane": "C12C3C4C1C5C2C3C45",
}
FLAT = {
    "ethanol": "CCO",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "caffeine": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
}


def _all_h_mol(smiles: str, monkeypatch) -> tuple[Chem.Mol, Chem.Mol]:
    """Skelett wie generate_molecule und das Molekül, das die All-H-Ansicht zeichnet."""
    from chemdraw_tool import svg_renderer

    mol = generate_2d(Chem.MolFromSmiles(smiles))
    captured = {}
    original = svg_renderer.extract_atom_data

    def spy(mol_h, *args, **kwargs):
        captured["mol_h"] = mol_h
        return original(mol_h, *args, **kwargs)

    monkeypatch.setattr(svg_renderer, "extract_atom_data", spy)
    srv._view_drawing("all_h", smiles, mol, False, "")
    return mol, captured["mol_h"]


def _clearance(mol_h: Chem.Mol) -> float:
    pos = [(float(p[0]), float(p[1])) for p in mol_h.GetConformer().GetPositions()]
    heavy = [
        math.dist(pos[b.GetBeginAtomIdx()], pos[b.GetEndAtomIdx()])
        for b in mol_h.GetBonds()
        if b.GetBeginAtom().GetAtomicNum() > 1 and b.GetEndAtom().GetAtomicNum() > 1
    ]
    unit = sum(heavy) / len(heavy)
    worst = math.inf
    for atom in mol_h.GetAtoms():
        if atom.GetAtomicNum() != 1:
            continue
        i = atom.GetIdx()
        bonded = {n.GetIdx() for n in atom.GetNeighbors()}
        for j in range(len(pos)):
            if j != i and j not in bonded:
                worst = min(worst, math.dist(pos[i], pos[j]) / unit)
    return worst


@pytest.mark.parametrize("name", [*CAGES, *FLAT])
def test_no_hydrogen_sits_on_another_atom(name, monkeypatch):
    smiles = {**CAGES, **FLAT}[name]
    _, mol_h = _all_h_mol(smiles, monkeypatch)
    assert _clearance(mol_h) >= MIN_CLEARANCE, f"{name}: {_clearance(mol_h):.3f}"


@pytest.mark.parametrize("name", [*CAGES, *FLAT])
def test_skeleton_stays_where_generate_2d_put_it(name, monkeypatch):
    smiles = {**CAGES, **FLAT}[name]
    mol, mol_h = _all_h_mol(smiles, monkeypatch)
    n = mol.GetNumAtoms()
    assert [a.GetSymbol() for a in mol_h.GetAtoms()][:n] == [
        a.GetSymbol() for a in mol.GetAtoms()
    ]
    before = mol.GetConformer().GetPositions()
    after = mol_h.GetConformer().GetPositions()[:n]
    assert (before == after).all()


@pytest.mark.parametrize("name", list(FLAT))
def test_clean_molecules_keep_the_addhs_drawing(name, monkeypatch):
    mol, mol_h = _all_h_mol(FLAT[name], monkeypatch)
    plain = Chem.AddHs(mol, addCoords=True)
    assert (
        mol_h.GetConformer().GetPositions() == plain.GetConformer().GetPositions()
    ).all()


@pytest.mark.parametrize("name", ["morphine", "testosterone"])
def test_moved_hydrogens_keep_the_stereochemistry(name, monkeypatch):
    """Keile werden aus den Koordinaten abgeleitet — ein verschobenes H darf
    kein Zentrum kippen."""
    _, mol_h = _all_h_mol(CAGES[name], monkeypatch)
    back = Chem.MolFromMolBlock(Chem.MolToMolBlock(mol_h), removeHs=False)
    # Stereo kommt beim Einlesen aus Keilen + 2D-Koordinaten.
    back = Chem.RemoveHs(back)
    expected = Chem.MolToSmiles(Chem.MolFromSmiles(CAGES[name]))
    assert Chem.MolToSmiles(back) == expected
