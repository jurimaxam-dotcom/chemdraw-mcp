"""Verbrückte Ringe (Chinin, Morphin, Cuban): CoordGen, wenn das Standardlayout ein Atom auf eine Bindung legt.

Befund 22.11.2026: Chinin bekam im Chinuclidin ein einzeln beschriftetes „C“ an einer Bindungskreuzung.
Umgeschaltet wird nur, wenn CoordGen messbar weiter Abstand hält — Tropane (Kokain, Atropin) bleiben.
"""

import pytest
from rdkit import Chem

from chempane.generator import closest_atom_to_foreign_bond, generate_2d

SWITCHED = {
    "quinine": "COC1=CC2=C(C=CN=C2C=C1)[C@H]([C@@H]3C[C@@H]4CCN3C[C@@H]4C=C)O",
    "morphine": "CN1CC[C@]23[C@@H]4[C@H]1CC5=C2C(=C(C=C5)O)O[C@H]3[C@H](C=C4)O",
    "cubane": "C12C3C4C1C5C2C3C45",
    "strychnine": "O=C1C[C@H]2OCC=C3CN4CC[C@]56[C@@H]4C[C@H]3[C@H]2[C@H]6N1c1ccccc15",
}
KEPT = {
    "cocaine": "CN1[C@H]2CC[C@@H]1[C@H]([C@H](C2)OC(=O)c1ccccc1)C(=O)OC",
    "atropine": "CN1[C@H]2CC[C@@H]1CC(C2)OC(=O)C(CO)c1ccccc1",
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
}


@pytest.mark.parametrize("name", sorted(SWITCHED))
def test_cage_gets_more_room_than_the_standard_layout(name):
    from rdkit.Chem import AllChem

    standard = Chem.MolFromSmiles(SWITCHED[name])
    AllChem.Compute2DCoords(standard)
    mol = generate_2d(Chem.MolFromSmiles(SWITCHED[name]))
    assert closest_atom_to_foreign_bond(mol) > closest_atom_to_foreign_bond(standard)


def test_quinine_has_no_atom_on_a_bond():
    mol = generate_2d(Chem.MolFromSmiles(SWITCHED["quinine"]))
    assert closest_atom_to_foreign_bond(mol) >= 0.4


@pytest.mark.parametrize("name", sorted(SWITCHED))
def test_drawing_keeps_the_stereo(name):
    # Stereo aus Koordinaten + Keilen zurücklesen: dasselbe InChIKey wie die Eingabe.
    smiles = SWITCHED[name]
    mol = generate_2d(Chem.MolFromSmiles(smiles))
    Chem.WedgeMolBonds(mol, mol.GetConformer())
    back = Chem.MolFromMolBlock(Chem.MolToMolBlock(mol))
    assert Chem.MolToInchiKey(back) == Chem.MolToInchiKey(Chem.MolFromSmiles(smiles))


@pytest.mark.parametrize("name", sorted(KEPT))
def test_others_keep_the_standard_layout(name):
    from rdkit.Chem import AllChem

    ref = Chem.MolFromSmiles(KEPT[name])
    AllChem.Compute2DCoords(ref)
    mol = generate_2d(Chem.MolFromSmiles(KEPT[name]))
    a, b = ref.GetConformer().GetPositions(), mol.GetConformer().GetPositions()
    assert (abs(a - b) < 1e-6).all()


def test_bond_length_matches_the_standard_layout():
    mol = generate_2d(Chem.MolFromSmiles(SWITCHED["quinine"]))
    conf = mol.GetConformer()
    lengths = [
        (conf.GetAtomPosition(b.GetBeginAtomIdx()) - conf.GetAtomPosition(b.GetEndAtomIdx())).Length()
        for b in mol.GetBonds()
    ]
    assert 1.4 < sum(lengths) / len(lengths) < 1.6
