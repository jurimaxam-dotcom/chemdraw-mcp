from rdkit import Chem
from rdkit.Chem import AllChem, rdCoordGen

# Lineare Peptide (E4, 09.11.2026): Das Standard-Layout faltet ab fünf Resten
# das Rückgrat zur Haarnadel (Pentapeptid: N- und C-Terminus nebeneinander),
# CoordGen legt es als Lehrbuch-Zickzack. Umgeschaltet wird nach der Struktur,
# nicht nach dem Eingabeweg — sonst sähe dasselbe Peptid im Datenblatt (das
# Panel ruft es per SMILES ab) anders aus als in der Strukturansicht. Ringe
# im Rückgrat (Oxytocin, Cyclopeptide) bleiben beim Standard-Layout.
# rdCoordGen.AddCoords statt SetPreferCoordGen: der Schalter wäre prozessweit,
# die Tools laufen in Worker-Threads.
_PEPTIDE_LINK = Chem.MolFromSmarts("[NX3][CX4][CX3](=O)!@[NX3][CX4][CX3]=O")
_RING_LINK = Chem.MolFromSmarts("[NX3][CX4][CX3](=O)@[NX3][CX4][CX3]=O")
MIN_PEPTIDE_LINKS = 4  # fünf Reste; bis vier sieht das Standard-Layout gut aus


def is_linear_peptide(mol: Chem.Mol) -> bool:
    """Mindestens fünf α-Reste in Kette, keine Amidbindung des Rückgrats im Ring."""
    if mol.HasSubstructMatch(_RING_LINK):
        return False
    links = {(m[2], m[4]) for m in mol.GetSubstructMatches(_PEPTIDE_LINK)}
    return len(links) >= MIN_PEPTIDE_LINKS


def generate_2d(mol: Chem.Mol) -> Chem.Mol:
    mol_copy = Chem.RWMol(mol)
    if is_linear_peptide(mol_copy):
        rdCoordGen.AddCoords(mol_copy)
    else:
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


# Stereo-Varianten (Grundlagen, Etappe 3): alle Isomere der OFFENEN Elemente,
# die festgelegten bleiben. Mehr als drei offene Elemente wären 16+ Bilder —
# dann gibt es keine Auswahl, sondern den Rat, das SMILES festzulegen.
MAX_OPEN_STEREO = 3
MAX_STEREO_VARIANTS = 2**MAX_OPEN_STEREO


def _cip_descriptor(mol: Chem.Mol) -> str:
    """„(R)“, „(R,S)“, „(E)“ — CIP-Codes in Atom-/Bindungsreihenfolge.

    Ohne Lokanten (Atomindizes sind keine IUPAC-Ziffern); welches Zentrum
    welches ist, zeigt das annotierte Vorschaubild.
    """
    from rdkit.Chem import rdCIPLabeler

    rdCIPLabeler.AssignCIPLabels(mol)
    codes = []
    for info in Chem.FindPotentialStereo(mol):
        if info.type == Chem.StereoType.Atom_Tetrahedral:
            item = mol.GetAtomWithIdx(info.centeredOn)
        elif info.type == Chem.StereoType.Bond_Double:
            item = mol.GetBondWithIdx(info.centeredOn)
        else:
            continue
        if item.HasProp("_CIPCode"):
            codes.append(item.GetProp("_CIPCode"))
    return f"({','.join(codes)})" if codes else ""


def stereo_variants(mol: Chem.Mol) -> list[dict]:
    """Alle Stereoisomere der unbestimmten Elemente von `mol`.

    Je Eintrag {"smiles": isomeres SMILES, "descriptor": "(R)"}. Leer, wenn
    nichts offen ist oder mehr als MAX_OPEN_STEREO Elemente offen sind.
    Meso-Formen zählen einmal (kanonisches SMILES entscheidet).
    """
    from rdkit.Chem.EnumerateStereoisomers import (
        EnumerateStereoisomers,
        StereoEnumerationOptions,
    )

    open_count = len(find_unspecified_stereo(mol))
    if not 0 < open_count <= MAX_OPEN_STEREO:
        return []
    options = StereoEnumerationOptions(onlyUnassigned=True, unique=True)
    variants, seen = [], set()
    for isomer in EnumerateStereoisomers(Chem.Mol(mol), options=options):
        smiles = Chem.MolToSmiles(isomer)
        if smiles in seen:
            continue
        seen.add(smiles)
        probe = Chem.MolFromSmiles(smiles)
        variants.append({"smiles": smiles, "descriptor": _cip_descriptor(probe)})
    return variants
