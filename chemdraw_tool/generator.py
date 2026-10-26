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


# Unbestimmte Stereoelemente: ein getipptes SMILES ohne @/@@ bzw. / \ zeichnet
# still ein unbestimmtes Isomer. Bewusst getrennt von generate_2d — die
# Erkennung ändert nichts an Koordinaten oder Zeichnung und läuft auf einer
# Kopie, damit FindPotentialStereo das gezeichnete Mol nicht anfassen kann.
# Die Atomindizes sind dieselben wie im übergebenen Mol (und damit wie im
# `atoms`-Feld, das aus demselben Mol gebaut wird).
_STEREO_LABELS = {
    "atom": "Unspecified stereocenter",
    "double_bond": "Unspecified double bond geometry (E/Z)",
}


def find_unspecified_stereo(mol: Chem.Mol) -> list[dict]:
    """Return unspecified tetrahedral centers and double bonds of `mol`.

    Each entry: {"kind": "atom"|"double_bond", "atoms": [idx, ...], "label": str}.
    """
    probe = Chem.Mol(mol)
    warnings = []
    for info in Chem.FindPotentialStereo(probe):
        if info.specified != Chem.StereoSpecified.Unspecified:
            continue
        if info.type == Chem.StereoType.Atom_Tetrahedral:
            kind, atoms = "atom", [info.centeredOn]
        elif info.type == Chem.StereoType.Bond_Double:
            bond = probe.GetBondWithIdx(info.centeredOn)
            kind, atoms = "double_bond", [bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()]
        else:
            # Atropisomere, quadratisch-planare Zentren usw. sind (noch) kein Thema.
            continue
        warnings.append({"kind": kind, "atoms": atoms, "label": _STEREO_LABELS[kind]})
    return warnings


def stereo_note(warnings: list) -> str:
    """One English sentence for the model; "" when nothing is unspecified."""

    def kind_of(w):
        return w["kind"] if isinstance(w, dict) else w.kind

    centers = sum(kind_of(w) == "atom" for w in warnings)
    bonds = sum(kind_of(w) == "double_bond" for w in warnings)
    parts = []
    if centers:
        parts.append(f"{centers} stereocenter{'s' if centers != 1 else ''}")
    if bonds:
        parts.append(f"{bonds} double bond{'s' if bonds != 1 else ''} (E/Z)")
    if not parts:
        return ""
    verb = "is" if centers + bonds == 1 else "are"
    pronoun = "its" if centers + bonds == 1 else "their"
    return (
        f"{' and '.join(parts)} {verb} unspecified; "
        f"the drawing does not fix {pronoun} configuration."
    )
