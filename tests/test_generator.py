from rdkit import Chem

from chemdraw_tool.generator import generate_2d, get_atom_positions


def test_generate_2d_adds_conformer():
    mol = Chem.MolFromSmiles("c1ccccc1")
    result = generate_2d(mol)
    assert result.GetNumConformers() == 1


def test_generate_2d_does_not_mutate_input():
    mol = Chem.MolFromSmiles("c1ccccc1")
    assert mol.GetNumConformers() == 0
    generate_2d(mol)
    assert mol.GetNumConformers() == 0


def test_get_atom_positions_count():
    mol = Chem.MolFromSmiles("c1ccccc1")
    mol = generate_2d(mol)
    positions = get_atom_positions(mol)
    assert len(positions) == 6


def test_get_atom_positions_are_floats():
    mol = Chem.MolFromSmiles("CCO")
    mol = generate_2d(mol)
    positions = get_atom_positions(mol)
    for x, y in positions:
        assert isinstance(x, float)
        assert isinstance(y, float)


def test_positions_differ():
    mol = Chem.MolFromSmiles("CCO")
    mol = generate_2d(mol)
    positions = get_atom_positions(mol)
    assert positions[0] != positions[1]
    assert positions[1] != positions[2]
