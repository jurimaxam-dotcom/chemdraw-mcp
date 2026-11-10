import logging

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
    if tetrapyrrole_core(mol) is not None:
        try:
            laid_out = _macrocycle_layout(mol)
        except Exception:  # noqa: BLE001 — ungemessene Struktur: altes Bild statt Absturz
            logging.getLogger(__name__).warning("Makrozyklus-Layout fehlgeschlagen", exc_info=True)
            laid_out = None
        if laid_out is not None:
            return laid_out
    mol_copy = Chem.RWMol(mol)
    if is_linear_peptide(mol_copy):
        rdCoordGen.AddCoords(mol_copy)
        _scale_coordgen(mol_copy)
    else:
        AllChem.Compute2DCoords(mol_copy)
    return mol_copy.GetMol()


def _scale_coordgen(mol: Chem.Mol) -> None:
    # CoordGen legt Bindungen auf 1,0, Compute2DCoords auf 1,5 (gemessen
    # 10.11.2026) — CDXML, Reaktions- und Vergleichsbilder brauchen einen
    # Maßstab.
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, (p.x * 1.5, p.y * 1.5, 0.0))


# Metall-Tetrapyrrole (E11, 10.11.2026): Häm, Sirohäm, Chlorophyll, Phthalo-
# cyanine. PubChem liefert den Makrozyklus als Dianion und das Metall als
# EIGENES Fragment; das Standard-Layout staucht die Pyrrole zu Dreiecken und
# legt das Metall irgendwo daneben. Umgeschaltet wird nach der Struktur, nicht
# nach dem Namen — wie bei den Peptiden.
#
# Arbeitsteilung, damit die Identität unangetastet bleibt:
# - generate_2d ändert nur Koordinaten (Ausnahme: lose [H+], s. u.). Graph,
#   Ladungen, Formel, InChIKey, Stereo-Hinweise und funktionelle Gruppen
#   bleiben die der Quelle.
# - Die vier N–Metall-Bindungen entstehen erst beim Zeichnen
#   (coordination_drawing), aufgerufen von UI-Vorschau UND Datei-Export.
#
# Layout: Der innere Kern (vier Pyrrolringe, Brückenatome, Metall mit vier
# Hilfsbindungen) bekommt CoordGen-Koordinaten — das ergibt das Quadrat mit dem
# Metall in der Mitte; der Rest wird mit RDKits Standard-Layout um den
# festgehaltenen Kern gelegt. Volles CoordGen scheitert an Chlorophyll und
# Cobalamin. Kreuzen sich danach Bindungen, fallen Atome aufeinander oder ist
# eine Bindung verzerrt, gilt das Bild als schlechter als das alte und es
# bleibt beim Standard-Layout (gemessen: Chlorophyll a, Bakteriochlorophyll a,
# die Cobalamine).
_NON_METALS = frozenset({1, 2, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 33, 34, 35, 36, 52, 53, 54, 85, 86})
_ALKALI = frozenset({3, 11, 19, 37, 55, 87})
_MIN_ATOM_DISTANCE = 0.5  # bei Bindungslänge 1,5
# Jede Bindung höchstens 25 % neben 1,5. Chlorophyll a fiel sonst durch:
# der fünfte Ring mit Bindungen von 0,80 und 2,06 (gemessen 10.11.2026).
_BOND_LENGTH_RANGE = (1.125, 1.875)


def _is_metal(atom: Chem.Atom) -> bool:
    # Ordnungszahl 0 = Dummy-Atom (abgekürzte Gruppe „Ph“, „OAc“), kein Metall.
    return atom.GetAtomicNum() not in _NON_METALS and atom.GetAtomicNum() != 0


def _pyrrole_units(mol: Chem.Mol) -> list[tuple[int, frozenset, tuple[int, int]]]:
    """Fünfringe mit genau einem N, das außer den zwei Ring-α-Atomen nur ein
    Metall (oder H) als Nachbarn hat — das N zeigt also in den Makrozyklus."""
    units = []
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 5:
            continue
        ns = [i for i in ring if mol.GetAtomWithIdx(i).GetAtomicNum() == 7]
        if len(ns) != 1:
            continue
        heavy = [
            x.GetIdx()
            for x in mol.GetAtomWithIdx(ns[0]).GetNeighbors()
            if x.GetAtomicNum() != 1 and not _is_metal(x)
        ]
        if len(heavy) == 2 and all(i in ring for i in heavy):
            units.append((ns[0], frozenset(ring), (heavy[0], heavy[1])))
    return units


def tetrapyrrole_core(mol: Chem.Mol) -> tuple[list[int], set[int]] | None:
    """Vier Pyrrol-N eines Makrozyklus (Porphyrin, Chlorin, Bakteriochlorin,
    Corrin, Phthalocyanin) und die Atome des inneren Kerns — oder None.

    Zwei Pyrrolringe hängen zusammen, wenn ihre α-Atome direkt (Corrin) oder
    über genau ein Brückenatom (Methin-C, Aza-N) verbunden sind. Ein
    Makrozyklus sind genau vier Ringe, die so einen geschlossenen Kreis bilden;
    eine offene Kette (Bilirubin) oder zwei Makrozyklen zählen nicht.
    """
    units = _pyrrole_units(mol)
    if len(units) < 4:
        return None
    ring_atoms = set().union(*(u[1] for u in units))
    links: dict[int, set[int]] = {i: set() for i in range(len(units))}
    bridge_of: dict[tuple[int, int], set[int]] = {}
    for i, (_, ring_i, alpha_i) in enumerate(units):
        for j in range(i + 1, len(units)):
            _, ring_j, alpha_j = units[j]
            if ring_i & ring_j:
                continue
            for a in alpha_i:
                nb_a = {x.GetIdx() for x in mol.GetAtomWithIdx(a).GetNeighbors()}
                for b in alpha_j:
                    if b in nb_a:
                        links[i].add(j)
                        links[j].add(i)
                    nb_b = {x.GetIdx() for x in mol.GetAtomWithIdx(b).GetNeighbors()}
                    common = {
                        c
                        for c in (nb_a & nb_b) - ring_atoms
                        if not _is_metal(mol.GetAtomWithIdx(c))
                    }
                    if common:
                        links[i].add(j)
                        links[j].add(i)
                        bridge_of.setdefault((i, j), set()).update(common)
    cycles = []
    seen: set[int] = set()
    for start in links:
        if start in seen or not links[start]:
            continue
        comp, stack = set(), [start]
        while stack:
            x = stack.pop()
            if x not in comp:
                comp.add(x)
                stack.extend(links[x])
        seen |= comp
        if len(comp) == 4 and all(len(links[x] & comp) == 2 for x in comp):
            cycles.append(comp)
    if len(cycles) != 1:
        return None
    comp = cycles[0]
    ns = sorted(units[k][0] for k in comp)
    core = set().union(*(units[k][1] for k in comp))
    for (i, j), bridges in bridge_of.items():
        if i in comp and j in comp:
            core |= bridges
    return ns, core


def central_metal(mol: Chem.Mol, ns: list[int]) -> int | None:
    """Index des Zentralmetalls, oder None.

    Genau ein Metallatom im ganzen Mol, kein Alkalimetall (Na⁺ eines Salzes ist
    Gegenion, kein Zentralatom), und höchstens an die vier Pyrrol-N gebunden —
    eigenes Fragment wie bei PubChem oder schon koordiniert.
    """
    metals = [a for a in mol.GetAtoms() if _is_metal(a)]
    if len(metals) != 1 or metals[0].GetAtomicNum() in _ALKALI:
        return None
    metal = metals[0]
    if any(nb.GetIdx() not in ns for nb in metal.GetNeighbors() if nb.GetAtomicNum() != 1):
        return None
    return metal.GetIdx()


def _with_metal_bonds(mol: Chem.Mol, ns: list[int], metal: int) -> Chem.Mol:
    """Kopie mit den fehlenden N–Metall-Bindungen.

    Lehrbuchform: Je ein N⁻ und eine positive Metallladung werden zu einer
    kovalenten Bindung (Strich, beide Ladungen verschwinden); die übrigen N
    binden koordinativ (Pfeil N→M). Häm: zwei Striche, zwei Pfeile, Fe ohne
    Ladung. Die Nettoladung und die Summenformel bleiben gleich — es ist eine
    andere gültige Lewis-Formel desselben Stoffs, keine Schönfärberei.
    """
    rw = Chem.RWMol(mol)
    charge = rw.GetAtomWithIdx(metal).GetFormalCharge()
    for n in ns:
        if rw.GetBondBetweenAtoms(n, metal) is not None:
            continue
        atom = rw.GetAtomWithIdx(n)
        if atom.GetFormalCharge() == -1 and charge > 0:
            atom.SetFormalCharge(0)
            charge -= 1
            rw.AddBond(n, metal, Chem.BondType.SINGLE)
        else:
            rw.AddBond(n, metal, Chem.BondType.DATIVE)
    rw.GetAtomWithIdx(metal).SetFormalCharge(charge)
    out = rw.GetMol()
    Chem.SanitizeMol(out)
    return out


def _protonate_carboxylates(mol: Chem.Mol) -> Chem.Mol:
    """Lose [H+] zurück auf Carboxylat-O⁻ setzen (Häm d1: vier [H+] + Tetraanion).

    Gleiche Summenformel, Masse und Nettoladung; gezeichnet die Säure statt
    vier schwebender H⁺. Nur wenn jedes Proton ein Carboxylat findet, sonst
    unverändert.
    """
    protons = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 1 and a.GetDegree() == 0 and a.GetFormalCharge() == 1]
    if not protons:
        return mol
    carboxylates = [
        m[0] for m in mol.GetSubstructMatches(Chem.MolFromSmarts("[OX1-][CX3]=O"))
    ]
    if len(carboxylates) < len(protons):
        return mol
    rw = Chem.RWMol(mol)
    for o in carboxylates[: len(protons)]:
        atom = rw.GetAtomWithIdx(o)
        atom.SetFormalCharge(0)
        atom.SetNumExplicitHs(atom.GetNumExplicitHs() + 1)
    for h in sorted(protons, reverse=True):
        rw.RemoveAtom(h)
    out = rw.GetMol()
    Chem.SanitizeMol(out)
    return out


def _segments_cross(p1, p2, p3, p4) -> bool:
    def orient(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    return (
        orient(p3, p4, p1) * orient(p3, p4, p2) < 0
        and orient(p1, p2, p3) * orient(p1, p2, p4) < 0
    )


def _layout_is_clean(mol: Chem.Mol) -> bool:
    conf = mol.GetConformer()
    pos = [conf.GetAtomPosition(i) for i in range(mol.GetNumAtoms())]
    bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in mol.GetBonds()]
    low, high = _BOND_LENGTH_RANGE
    # Metallbindungen ausgenommen: N–M liegt im Quadrat bei ~2,1.
    organic = [
        (a, b)
        for a, b in bonds
        if not (_is_metal(mol.GetAtomWithIdx(a)) or _is_metal(mol.GetAtomWithIdx(b)))
    ]
    if any(not low <= (pos[a] - pos[b]).Length() <= high for a, b in organic):
        return False
    for k, (a, b) in enumerate(bonds):
        for c, d in bonds[k + 1 :]:
            if len({a, b, c, d}) == 4 and _segments_cross(pos[a], pos[b], pos[c], pos[d]):
                return False
    return all(
        (pos[i] - pos[j]).Length() >= _MIN_ATOM_DISTANCE
        for i in range(len(pos))
        for j in range(i + 1, len(pos))
    )


# Ab dieser Schräglage (Grad) wird der Makrozyklus achsparallel gedreht (E17):
# CoordGen legt metallfreies Porphin um 11,5° schief, Häm (0,7°) und
# Phthalocyanin (0,1°) bleiben darunter und unverändert.
_MAX_TILT = 2.0


def _align_square(mol: Chem.Mol, ns: list[int]) -> None:
    """Konformer so drehen, dass die vier Pyrrol-N auf den Achsen liegen."""
    import math

    conf = mol.GetConformer()
    pts = [conf.GetAtomPosition(n) for n in ns]
    cx, cy = sum(p.x for p in pts) / 4, sum(p.y for p in pts) / 4
    a = math.degrees(math.atan2(pts[0].y - cy, pts[0].x - cx)) % 90
    tilt = a if a <= 45 else a - 90
    if abs(tilt) < _MAX_TILT:
        return
    c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        x, y = p.x - cx, p.y - cy
        conf.SetAtomPosition(i, (cx + c * x - s * y, cy + s * x + c * y, 0.0))


def _macrocycle_layout(mol: Chem.Mol, align: bool = True) -> Chem.Mol | None:
    """Lehrbuch-Koordinaten für einen Tetrapyrrol-Makrozyklus, oder None."""
    mol = _protonate_carboxylates(mol)
    ns, core = tetrapyrrole_core(mol)
    metal = central_metal(mol, ns)
    work = Chem.Mol(mol)
    if metal is not None:
        work = _with_metal_bonds(mol, ns, metal)
        core = core | {metal}
    # Erst mit den anellierten Ringen im festen Kern (Phthalocyanin: die
    # Benzoringe), dann ohne (Chlorophyll: der fünfte Ring passt nur, wenn
    # das Standard-Layout ihn um den Kern legen darf).
    for fixed_atoms in (core | _fused_rings(work, core), core):
        if _lay_out_around(work, fixed_atoms) and _layout_is_clean(work):
            out = Chem.Mol(mol)
            out.RemoveAllConformers()
            out.AddConformer(Chem.Conformer(work.GetConformer()), assignId=True)
            if align:
                _align_square(out, ns)
            return out
    return None


def _fused_rings(mol: Chem.Mol, core: set[int]) -> set[int]:
    """Atome der Ringe, die mit dem Kern eine Bindung teilen (transitiv)."""
    grown = set(core)
    rings = [set(r) for r in mol.GetRingInfo().AtomRings() if len(r) <= 8]
    changed = True
    while changed:
        changed = False
        for ring in rings:
            if ring <= grown or any(_is_metal(mol.GetAtomWithIdx(i)) for i in ring):
                continue
            shared = ring & grown
            if any(
                mol.GetBondBetweenAtoms(a, b) is not None
                for a in shared
                for b in shared
                if a < b
            ):
                grown |= ring
                changed = True
    return grown - core


def _lay_out_around(work: Chem.Mol, fixed_atoms: set[int]) -> bool:
    """CoordGen für den Kern, Standard-Layout für den Rest um ihn herum."""
    from rdkit.Geometry import Point2D

    keep = sorted(fixed_atoms)
    trimmed = Chem.RWMol(work)
    for i in sorted(set(range(work.GetNumAtoms())) - fixed_atoms, reverse=True):
        trimmed.RemoveAtom(i)
    # CoordGen kennt keine koordinative Bindung („unrecognized bond type“ im
    # Log); für die Geometrie genügt eine Einfachbindung. Nur in dieser
    # unsanitisierten Hilfskopie.
    for bond in trimmed.GetBonds():
        if bond.GetBondType() == Chem.BondType.DATIVE:
            bond.SetBondType(Chem.BondType.SINGLE)
    core_mol = trimmed.GetMol()
    core_mol.UpdatePropertyCache(strict=False)
    rdCoordGen.AddCoords(core_mol)
    _scale_coordgen(core_mol)
    conf = core_mol.GetConformer()
    fixed = {
        orig: Point2D(conf.GetAtomPosition(k).x, conf.GetAtomPosition(k).y)
        for k, orig in enumerate(keep)
    }
    AllChem.Compute2DCoords(work, coordMap=fixed)
    return True


def coordination_drawing(mol: Chem.Mol) -> Chem.Mol:
    """Das Mol zum ZEICHNEN: mit N–Metall-Bindungen, wenn das Metall in der
    Ringmitte liegt (generate_2d hat das Lehrbuch-Layout gewählt); sonst
    unverändert `mol` selbst.

    Aufgerufen von UI-Vorschau und Datei-Export — beide zeichnen dasselbe.
    Atome und Atomreihenfolge bleiben gleich, Atomlisten passen also weiter.
    """
    if mol.GetNumConformers() == 0:
        return mol
    found = tetrapyrrole_core(mol)
    if found is None:
        return mol
    ns, _ = found
    metal = central_metal(mol, ns)
    if metal is None:
        return mol
    conf = mol.GetConformer()
    m = conf.GetAtomPosition(metal)
    dists = [(conf.GetAtomPosition(n) - m).Length() for n in ns]
    cx = sum(conf.GetAtomPosition(n).x for n in ns) / 4
    cy = sum(conf.GetAtomPosition(n).y for n in ns) / 4
    centred = abs(m.x - cx) < 0.15 and abs(m.y - cy) < 0.15
    if not centred or max(dists) - min(dists) > 0.25 * min(dists):
        return mol
    if all(mol.GetBondBetweenAtoms(n, metal) is not None for n in ns):
        return mol
    try:
        return _with_metal_bonds(mol, ns, metal)
    except Exception:  # noqa: BLE001 — die Zeichnung geht vor, notfalls ohne Bindungen
        logging.getLogger(__name__).warning("Metallbindungen nicht zeichenbar", exc_info=True)
        return mol


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


def _tautomeric_c_n(bond: Chem.Bond) -> bool:
    """C=N eines Amidins/Guanidins, deren Lage die Tautomerie festlegt (E17).

    Trägt das C außer dem Imin-N noch ein N mit H (Arginin: H2N–C(=NH)–NHR),
    wandert die Doppelbindung per 1,3-H-Verschiebung zwischen den N; welches N
    doppelt gebunden ist, wählt die Schreibweise, nicht der Stoff. Eine E/Z-
    Angabe an dieser Bindung beschreibt dann kein Isomer. Eng gefasst: Das
    Imin-N hängt nur an C/H — Oxime, Hydrazone und Amidoxime (N–O, N–N) haben
    messbare E/Z-Isomere und bleiben eine Warnung, ebenso Amidine ohne N–H.
    """
    if bond.GetBondType() != Chem.BondType.DOUBLE:
        return False
    a, b = bond.GetBeginAtom(), bond.GetEndAtom()
    if {a.GetAtomicNum(), b.GetAtomicNum()} != {6, 7}:
        return False
    carbon, imine = (a, b) if a.GetAtomicNum() == 6 else (b, a)
    if any(n.GetAtomicNum() not in (1, 6) for n in imine.GetNeighbors() if n.GetIdx() != carbon.GetIdx()):
        return False
    return any(
        n.GetAtomicNum() == 7
        and n.GetIdx() != imine.GetIdx()
        and n.GetTotalNumHs() > 0
        and carbon.GetOwningMol().GetBondBetweenAtoms(carbon.GetIdx(), n.GetIdx()).GetBondType()
        == Chem.BondType.SINGLE
        for n in carbon.GetNeighbors()
    )


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
            if _tautomeric_c_n(bond):
                continue
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
