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
    gaps: list[float] | None = None,
) -> list[list[Chem.Mol]]:
    """Compute stabilized coordinates for an entire mechanism sequence.

    Returns list of lists of RDKit Mol objects with 2D conformers.
    """
    result = []
    prior_positions = None

    for i, smiles_list in enumerate(steps_smiles):
        mols = [_parse_mol_safe(smi) for smi in smiles_list]
        gap = gaps[i] if gaps else 4.0
        computed = compute_step_coords(mols, prior_positions=prior_positions, mol_gap=gap)
        result.append(computed)
        prior_positions = extract_positions(computed)

    return result


# --- Verankertes Layout (Substratweg) ------------------------------------------------
#
# stabilize_sequence übernimmt die Positionen des Vorschritts. Bei Nutzer-Substraten führte das
# zu langen Bindungen (das Nucleophil behielt seinen Platz aus Schritt 1) und zu einem
# Nucleophil, das nicht von der Rückseite kam (Sichtung 04.11.2026). Hier gibt jeder Schritt
# die Lage des Reaktionszentrums selbst vor; RDKit legt den Rest des Moleküls drumherum.

BOND = 1.5  # RDKit-Bindungslänge in Konformer-Einheiten
_MIN_DIST = 0.8 * BOND
_FREE_GAP = 1.6 * BOND


def _xs(mol: Chem.Mol) -> list[float]:
    conf = mol.GetConformer()
    return [conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())]


def _shift(mol: Chem.Mol, dx: float, dy: float) -> None:
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + dx, p.y + dy, 0.0))


def _min_distance(a: Chem.Mol, others: list[Chem.Mol]) -> float:
    ca = a.GetConformer()
    best = float("inf")
    for o in others:
        co = o.GetConformer()
        for i in range(a.GetNumAtoms()):
            pi = ca.GetAtomPosition(i)
            for j in range(o.GetNumAtoms()):
                best = min(best, (pi - co.GetAtomPosition(j)).Length())
    return best


def _anchored_mol(smiles: str, anchors: dict[int, tuple[float, float]]) -> Chem.Mol:
    mol = Chem.RWMol(_parse_mol_safe(smiles))
    # Übergangszustand/Kation sind keine Radikale: kein Punkt am Kohlenstoff
    for atom in mol.GetAtoms():
        atom.SetNumRadicalElectrons(0)
    index = build_atom_map_index(mol)
    coord_map = {index[m]: Point2D(x * BOND, y * BOND) for m, (x, y) in anchors.items() if m in index}
    if coord_map:
        AllChem.Compute2DCoords(mol, coordMap=coord_map)
    else:
        AllChem.Compute2DCoords(mol)
    if mol.GetNumConformers() == 0:
        raise ValueError(f"Compute2DCoords erzeugte keinen Konformer für {smiles}")
    return mol.GetMol()


def layout_anchored(steps) -> list[list[Chem.Mol]]:
    """Koordinaten für Schritte mit `anchors` (siehe MechanismStep).

    1. Verankerte Moleküle: RDKit-Layout mit festen Positionen der Ankeratome.
    2. Stößt ein verankertes Nebenmolekül (Nucleophil, Alkohol, H⁺) an ein früheres, wird es
       in seiner Richtung (Vorzeichen der Anker-x) nach außen geschoben, bis es frei ist.
    3. Freie Moleküle ({}) rechts neben alles Bisherige, vertikal auf y = 0 zentriert.
    """
    result = []
    for step in steps:
        anchors = step.anchors or [{} for _ in step.molecules]
        if len(anchors) != len(step.molecules):
            raise ValueError(f"Schritt '{step.label}': {len(anchors)} Anker für {len(step.molecules)} Moleküle")
        placed: list[Chem.Mol] = []
        for smiles, anchor in zip(step.molecules, anchors):
            mol = _anchored_mol(smiles, anchor)
            if anchor:
                if placed:
                    direction = 1.0 if sum(x for x, _ in anchor.values()) >= 0 else -1.0
                    for _ in range(12):
                        if _min_distance(mol, placed) >= _MIN_DIST:
                            break
                        _shift(mol, direction * 0.5 * BOND, 0.0)
            else:
                conf = mol.GetConformer()
                ys = [conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())]
                right = max((max(_xs(m)) for m in placed), default=0.0)
                _shift(mol, right + _FREE_GAP - min(_xs(mol)), -(max(ys) + min(ys)) / 2)
            placed.append(mol)
        result.append(placed)
    return result
