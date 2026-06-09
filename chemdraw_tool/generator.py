from rdkit import Chem
from rdkit.Chem import AllChem


def generate_2d(mol: Chem.Mol) -> Chem.Mol:
    mol_copy = Chem.RWMol(mol)
    AllChem.Compute2DCoords(mol_copy)
    return mol_copy.GetMol()


def get_atom_positions(mol: Chem.Mol) -> list[tuple[float, float]]:
    conf = mol.GetConformer()
    positions = []
    for i in range(mol.GetNumAtoms()):
        pos = conf.GetAtomPosition(i)
        positions.append((pos.x, pos.y))
    return positions
