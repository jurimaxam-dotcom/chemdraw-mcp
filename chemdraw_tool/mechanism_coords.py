"""Coordinate stabilization across mechanism steps.

Step 1 molecules are freely positioned. Subsequent steps constrain
atoms that share atom-map IDs with prior steps to prevent "jumping".
"""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Geometry import Point2D, Point3D


def build_atom_map_index(mol: Chem.Mol) -> dict[int, int]:
    """Map atom-map-ID → atom-index for all mapped atoms."""
    return {
        atom.GetAtomMapNum(): atom.GetIdx()
        for atom in mol.GetAtoms()
        if atom.GetAtomMapNum() != 0
    }


def _parse_mol_safe(smiles: str) -> Chem.Mol:
    """Parse SMILES with partial sanitization for intermediates."""
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    Chem.SanitizeMol(
        mol,
        sanitizeOps=Chem.SANITIZE_ALL ^ Chem.SANITIZE_PROPERTIES,
    )
    return mol


def compute_step_coords(
    mols: list[Chem.Mol],
    prior_positions: dict[int, tuple[float, float]] | None = None,
    mol_gap: float = 4.0,
) -> list[Chem.Mol]:
    """Compute 2D coords for all mols in a step.

    If prior_positions is given, mapped atoms are constrained to their
    prior positions. New atoms are freely placed.

    Molecules are offset horizontally so they don't overlap (cursor-x pattern).
    """
    result = []
    cursor_x = 0.0

    for mol in mols:
        rw = Chem.RWMol(mol)
        map_idx = build_atom_map_index(rw)

        if prior_positions:
            coord_map = {}
            for map_id, atom_idx in map_idx.items():
                if map_id in prior_positions:
                    x, y = prior_positions[map_id]
                    coord_map[atom_idx] = Point2D(x + cursor_x, y)

            if coord_map:
                AllChem.Compute2DCoords(rw, coordMap=coord_map)
            else:
                AllChem.Compute2DCoords(rw)
        else:
            AllChem.Compute2DCoords(rw)

        if cursor_x != 0.0 and not (
            prior_positions and any(mid in prior_positions for mid in map_idx)
        ):
            conf = rw.GetConformer()
            for i in range(rw.GetNumAtoms()):
                pos = conf.GetAtomPosition(i)
                conf.SetAtomPosition(i, Point3D(pos.x + cursor_x, pos.y, 0.0))

        result_mol = rw.GetMol()
        result.append(result_mol)

        if result_mol.GetNumConformers() == 0:
            raise ValueError(
                f"Compute2DCoords erzeugte keinen Konformer für "
                f"{Chem.MolToSmiles(result_mol)} — Koordinaten nicht berechenbar."
            )
        conf = result_mol.GetConformer()
        xs = [conf.GetAtomPosition(i).x for i in range(result_mol.GetNumAtoms())]
        if xs:
            cursor_x = max(xs) + mol_gap

    return result


def extract_positions(mols: list[Chem.Mol]) -> dict[int, tuple[float, float]]:
    """Extract atom-map-ID → (x, y) positions from rendered mols."""
    positions = {}
    for mol in mols:
        if mol.GetNumConformers() == 0:
            raise ValueError(
                "Molekül hat keine 2D-Koordinaten (Konformer fehlt) — "
                "Compute2DCoords muss zuvor erfolgreich gelaufen sein."
            )
        conf = mol.GetConformer()
        for atom in mol.GetAtoms():
            map_id = atom.GetAtomMapNum()
            if map_id != 0:
                pos = conf.GetAtomPosition(atom.GetIdx())
                positions[map_id] = (pos.x, pos.y)
    return positions


def stabilize_sequence(
    steps_smiles: list[list[str]],
) -> list[list[Chem.Mol]]:
    """Compute stabilized coordinates for an entire mechanism sequence.

    Returns list of lists of RDKit Mol objects with 2D conformers.
    """
    result = []
    prior_positions = None

    for smiles_list in steps_smiles:
        mols = [_parse_mol_safe(smi) for smi in smiles_list]
        computed = compute_step_coords(mols, prior_positions=prior_positions)
        result.append(computed)
        prior_positions = extract_positions(computed)

    return result
