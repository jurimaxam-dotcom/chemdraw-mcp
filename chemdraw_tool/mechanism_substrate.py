"""Mechanismus-Schritte aus den Molekülen des Nutzers (Design: docs/mechanismus-substrate-design.md).

Ablauf je Familie:
1. Eingaben in Fragmente zerlegen, Gegenionen und Katalysatoren verwerfen.
2. Rollen per SMARTS finden; das Reaktionszentrum bekommt die Map-IDs der Vorlagen (1–9),
   alle anderen Atome Map-IDs ab 100 — so bleibt jedes Atom über alle Schritte identifizierbar;
   das Layout (mechanism_coords.layout_anchored) setzt das Reaktionszentrum je Schritt fest.
3. Grenze prüfen (UnsupportedSubstrates mit Grund im Klartext).
4. Zwischenstufen/Produkte: gültige Moleküle per Reaktions-SMARTS (rdChemReactions),
   Bruchstücke (Übergangszustand, Carbokation) per RWMol.

Ergebnis ist eine Liste MechanismStep mit gemappten SMILES — dieselbe Schnittstelle wie die
festen Vorlagen in chemdraw_tool/templates/.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem import rdChemReactions, rdCIPLabeler

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep

FAMILIES = ("sn2", "sn1", "fischer_ester")

# Unterstützungsgrenze je Familie, ein Satz — steht wörtlich in Fehlermeldungen.
SUPPORT = {
    "sn2": ("SN2 draws a methyl, primary or secondary alkyl chloride, bromide or iodide with one "
            "anionic nucleophile: OH⁻, CN⁻, I⁻, Br⁻, RO⁻, N₃⁻ or RS⁻/HS⁻."),
    "sn1": ("SN1 draws a tertiary, benzylic or allylic alkyl chloride, bromide or iodide with water, "
            "an alcohol or one of the SN2 anions."),
    "fischer_ester": ("Fischer esterification draws one carboxylic acid (a single COOH) with one "
                      "primary or secondary alcohol."),
}

# Map-IDs des Reaktionszentrums — identisch mit den Vorlagen, damit die Pfeile gleich bleiben.
C, X, NU = 1, 2, 3
C_ACID, O_CARBONYL, O_HYDROXY, O_ALCOHOL, H_PLUS = 1, 2, 3, 4, 7
FIRST_FREE_MAP = 100


class UnsupportedSubstrates(ValueError):
    """Die Eingaben liegen außerhalb der Unterstützungsgrenze der Familie (Grund im Text)."""


class MechanismBuildError(RuntimeError):
    """Die Eingaben passen, aber die Ableitung der Schritte ist gescheitert (→ Vorlage)."""


# --- Rollen ---------------------------------------------------------------------

# Anionische Nucleophile (SN2 und SN1). Das angreifende Atom trägt :3.
ANIONIC_NUCLEOPHILES: list[tuple[str, str]] = [
    ("hydroxide (OH⁻)", "[OX1H1-:3]"),
    ("cyanide (CN⁻)", "[CX1-:3]#[NX1]"),
    ("iodide (I⁻)", "[I-:3]"),
    ("bromide (Br⁻)", "[Br-:3]"),
    ("alkoxide (RO⁻)", "[OX1-:3][CX4]"),
    ("azide (N₃⁻)", "[NX1-:3]=[NX2+]=[NX1-]"),
    ("thiolate (RS⁻)", "[SX1-:3][#6]"),
    ("hydrosulfide (HS⁻)", "[SX1H1-:3]"),
]
# Neutrale Nucleophile, nur SN1 (Solvolyse).
NEUTRAL_NUCLEOPHILES: list[tuple[str, str]] = [
    ("water", "[OX2H2:3]"),
    ("alcohol (ROH)", "[OX2H1:3][CX4]"),
]

_ANION_LIST = "OH⁻, CN⁻, I⁻, Br⁻, RO⁻, N₃⁻, RS⁻/HS⁻"

_HALIDE = Chem.MolFromSmarts("[CX4:1]-[Cl,Br,I:2]")
_ANY_C_HALOGEN = Chem.MolFromSmarts("[#6]-[F,Cl,Br,I]")
_C_F = Chem.MolFromSmarts("[CX4]-F")
_ACID = Chem.MolFromSmarts("[CX3;$([CX3][#6]),$([CX3H1]):1](=[OX1:2])[OX2H1:3]")
_ALCOHOL = Chem.MolFromSmarts("[OX2H1:4][CX4]")
_PHENOL = Chem.MolFromSmarts("[OX2H1]c")

# Säurekatalysatoren der Fischer-Veresterung: werden als H⁺ gezeichnet, nicht als Rolle gelesen.
_CATALYSTS = {
    Chem.CanonSmiles(s)
    for s in ("OS(=O)(=O)O", "Cl", "Cc1ccc(S(=O)(=O)O)cc1", "OP(=O)(O)O", "[OH3+]")
} | {"[H+]"}  # [H+] nicht kanonisieren: RDKit warnt beim Parsen eines nackten H


def _is_spectator(frag: Chem.Mol) -> bool:
    """Gegenion: einatomiges Kation (Na⁺, K⁺ …) oder Ammonium."""
    if frag.GetNumAtoms() == 1:
        atom = frag.GetAtomWithIdx(0)
        return atom.GetFormalCharge() > 0 and atom.GetSymbol() != "H"
    return Chem.MolToSmiles(frag) == "[NH4+]"


@dataclass
class _Frag:
    label: str  # Eingabe des Nutzers, aus der das Fragment stammt
    mol: Chem.Mol


def _fragments(smiles_list: list[str]) -> list[_Frag]:
    frags: list[_Frag] = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            raise UnsupportedSubstrates(f"'{smi}' could not be read as a structure")
        for frag in Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True):
            if not _is_spectator(frag):
                frags.append(_Frag(smi, frag))
    return frags


def _match_nucleophile(frag: Chem.Mol, table: list[tuple[str, str]]) -> tuple[str, int] | None:
    """(Name, Atomindex des angreifenden Atoms), wenn das GANZE Fragment ein Nucleophil der Tabelle ist."""
    for name, smarts in table:
        patt = Chem.MolFromSmarts(smarts)
        mapped = [a.GetIdx() for a in patt.GetAtoms() if a.GetAtomMapNum() == NU][0]
        for match in frag.GetSubstructMatches(patt):
            # Nur kleine Ionen/Moleküle, keine Gruppe in einem größeren Stoff mit weiteren Ladungen
            if name.startswith(("hydroxide", "cyanide", "iodide", "bromide", "azide", "hydrosulfide", "water")):
                if frag.GetNumAtoms() != patt.GetNumAtoms():
                    continue
            return name, match[mapped]
    return None


# --- Atom-Maps --------------------------------------------------------------------


def _assign_maps(mols_with_centre: list[tuple[Chem.Mol, dict[int, int]]]) -> list[Chem.Mol]:
    """Zentrum: feste Map-IDs (Atomindex → Map), Rest fortlaufend ab FIRST_FREE_MAP."""
    nxt = FIRST_FREE_MAP
    out = []
    for mol, centre in mols_with_centre:
        rw = Chem.RWMol(mol)
        for atom in rw.GetAtoms():
            if atom.GetIdx() in centre:
                atom.SetAtomMapNum(centre[atom.GetIdx()])
            else:
                atom.SetAtomMapNum(nxt)
                nxt += 1
        out.append(rw.GetMol())
    return out


def _idx(mol: Chem.Mol, map_id: int) -> int:
    for atom in mol.GetAtoms():
        if atom.GetAtomMapNum() == map_id:
            return atom.GetIdx()
    raise MechanismBuildError(f"atom map {map_id} missing")


def unmapped(mol: Chem.Mol) -> Chem.Mol:
    """Kopie ohne Atom-Maps, Atomindizes unverändert.

    Für CIP immer diese Kopie nehmen: Map-Nummern fließen in die Ränge ein, kippen R/S und
    machen zwei gleiche Substituenten scheinbar verschieden (falsches Stereozentrum).
    """
    plain = Chem.Mol(mol)
    for atom in plain.GetAtoms():
        atom.SetAtomMapNum(0)
    return plain


def cip_labels(mol: Chem.Mol) -> dict[int, str]:
    """{Atomindex: "R"/"S"} nach dem neuen CIP-Labeler (rdCIPLabeler), Maps vorher entfernt."""
    plain = unmapped(mol)
    rdCIPLabeler.AssignCIPLabels(plain)
    return {a.GetIdx(): a.GetProp("_CIPCode") for a in plain.GetAtoms() if a.HasProp("_CIPCode")}


def _smi(mol: Chem.Mol) -> str:
    return Chem.MolToSmiles(mol)


# --- Reaktions-SMARTS --------------------------------------------------------------


def _react(rxn_smarts: str, reactants: list[Chem.Mol]) -> list[Chem.Mol]:
    """Reaktions-SMARTS anwenden, die Treffer auf das gemappte Zentrum festlegen, Maps zurückschreiben.

    Die Map-IDs im Reaktions-SMARTS sind dieselben wie die des Zentrums im Nutzer-Molekül; ein
    Produktsatz zählt nur, wenn jedes Template-Atom aus dem Reaktanten-Atom mit genau dieser Map
    stammt (sonst hätte die Reaktion an einer anderen Stelle angegriffen).
    """
    rxn = rdChemReactions.ReactionFromSmarts(rxn_smarts)
    rxn.Initialize()
    for products in rxn.RunReactants(tuple(reactants)):
        fixed: list[Chem.Mol] = []
        ok = True
        for prod in products:
            rw = Chem.RWMol(prod)
            for atom in rw.GetAtoms():
                src = reactants[atom.GetIntProp("react_idx")].GetAtomWithIdx(atom.GetIntProp("react_atom_idx"))
                if atom.HasProp("old_mapno"):
                    if src.GetAtomMapNum() != atom.GetIntProp("old_mapno"):
                        ok = False
                    # Heteroatom im Template: Wasserstoffe aus der Valenz neu bestimmen
                    # (Protonierung/Deprotonierung). Kohlenstoff behält seine H-Zahl — in diesen
                    # Mechanismen ändert sie sich nie, und ein Neusetzen am Stereozentrum ließ
                    # MolToSmiles die Konfiguration verkehrt herum schreiben (gemessen 04.11.).
                    if atom.GetAtomicNum() != 6:
                        atom.SetNoImplicit(False)
                        atom.SetNumExplicitHs(0)
                atom.SetAtomMapNum(src.GetAtomMapNum())
            if not ok:
                break
            try:
                Chem.SanitizeMol(rw)
            except Exception as exc:  # noqa: BLE001 — jeder RDKit-Fehler heißt: Vorlage zeichnen
                raise MechanismBuildError(f"product failed sanitization: {exc}") from exc
            fixed.append(rw.GetMol())
        if ok:
            return fixed
    raise MechanismBuildError(f"reaction SMARTS produced no product at the mapped centre: {rxn_smarts}")


def _cut(mol: Chem.Mol, a_map: int, b_map: int, charges: dict[int, int],
         keep_h: tuple[int, ...] = ()) -> list[Chem.Mol]:
    """Bindung a–b lösen (Bruchstücke für Übergangszustand/Carbokation), Ladungen setzen.

    keep_h: Atome, deren Wasserstoffzahl fest bleibt (der Kohlenstoff im Übergangszustand ist
    weder Radikal noch Kation — RDKit würde ihm sonst ein H ergänzen).
    """
    rw = Chem.RWMol(mol)
    for map_id in keep_h:
        atom = rw.GetAtomWithIdx(_idx(rw, map_id))
        atom.SetNumExplicitHs(atom.GetTotalNumHs())
        atom.SetNoImplicit(True)
    rw.RemoveBond(_idx(rw, a_map), _idx(rw, b_map))
    for map_id, charge in charges.items():
        atom = rw.GetAtomWithIdx(_idx(rw, map_id))
        atom.SetFormalCharge(charge)
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        if map_id not in keep_h:
            atom.SetNoImplicit(False)
            atom.SetNumExplicitHs(0)
    rw.UpdatePropertyCache(strict=False)
    frags = Chem.GetMolFrags(rw.GetMol(), asMols=True, sanitizeFrags=False)
    for frag in frags:
        frag.UpdatePropertyCache(strict=False)
        for atom in frag.GetAtoms():
            atom.SetNumRadicalElectrons(0)
    return list(frags)


def _frag_with(frags: list[Chem.Mol], map_id: int) -> Chem.Mol:
    for frag in frags:
        if any(a.GetAtomMapNum() == map_id for a in frag.GetAtoms()):
            return frag
    raise MechanismBuildError(f"fragment with map {map_id} missing")


# --- SN2 / SN1 ----------------------------------------------------------------------


def _halide_and_nucleophile(frags: list[_Frag], family: str):
    """Substrat (Mol, Index C, Index X) und Nucleophil (Name, Mol, Index Nu) mit Grund-Prüfung."""
    halides = [f for f in frags if f.mol.HasSubstructMatch(_HALIDE)]
    if not halides:
        if any(f.mol.HasSubstructMatch(_C_F) for f in frags):
            raise UnsupportedSubstrates(
                "fluoride is not a leaving group here; use an alkyl chloride, bromide or iodide")
        if any(f.mol.HasSubstructMatch(_ANY_C_HALOGEN) for f in frags):
            raise UnsupportedSubstrates(
                "needs an alkyl halide (Cl, Br or I on an sp3 carbon); aryl and vinyl halides "
                "do not undergo SN1/SN2")
        raise UnsupportedSubstrates("no alkyl halide (Cl, Br or I on an sp3 carbon) among the substrates")
    if len(halides) > 1:
        raise UnsupportedSubstrates("more than one alkyl halide among the substrates; pass exactly one")
    substrate = halides[0]
    matches = substrate.mol.GetSubstructMatches(_HALIDE)
    if len(matches) > 1:
        raise UnsupportedSubstrates(
            "the substrate has more than one leaving group; pass a halide with exactly one")
    c_idx, x_idx = matches[0]

    table = ANIONIC_NUCLEOPHILES + (NEUTRAL_NUCLEOPHILES if family == "sn1" else [])
    others = [f for f in frags if f is not substrate]
    found = [(f, hit) for f in others if (hit := _match_nucleophile(f.mol, table))]
    if family == "sn2" and not found and any(_match_nucleophile(f.mol, NEUTRAL_NUCLEOPHILES)
                                             or f.mol.HasSubstructMatch(Chem.MolFromSmarts("[NX3,SX2]"))
                                             for f in others):
        raise UnsupportedSubstrates(
            f"SN2 here needs an anionic nucleophile from the list {_ANION_LIST}; "
            "a neutral nucleophile (water, alcohol, amine) is not drawn")
    if not found:
        allowed = _ANION_LIST + (", water, alcohol" if family == "sn1" else "")
        raise UnsupportedSubstrates(f"no supported nucleophile among the substrates (supported: {allowed})")
    if len(found) > 1:
        raise UnsupportedSubstrates("more than one nucleophile among the substrates; pass exactly one")
    unused = [f.label for f in others if f is not found[0][0]]
    if unused:
        raise UnsupportedSubstrates(f"'{unused[0]}' has no role in this mechanism")
    nuc_frag, (nuc_name, nu_idx) = found[0]
    return substrate, c_idx, x_idx, nuc_frag, nuc_name, nu_idx


def _carbon_class(mol: Chem.Mol, c_idx: int, x_idx: int) -> tuple[int, bool, bool]:
    """(Zahl der C-Nachbarn, benzylisch, allylisch) am Halogen-Kohlenstoff."""
    atom = mol.GetAtomWithIdx(c_idx)
    carbons = [n for n in atom.GetNeighbors() if n.GetSymbol() == "C" and n.GetIdx() != x_idx]
    benzylic = any(n.GetIsAromatic() for n in carbons)
    allylic = any(
        not n.GetIsAromatic() and any(
            b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(n).GetSymbol() == "C"
            for b in n.GetBonds())
        for n in carbons)
    return len(carbons), benzylic, allylic


# --- Anker (Lage des Reaktionszentrums je Schritt, in Bindungslängen) -----------------


def _ray(deg: float, r: float = 1.0) -> tuple[float, float]:
    return (round(r * math.cos(math.radians(deg)), 4), round(r * math.sin(math.radians(deg)), 4))


def _neighbours(mol: Chem.Mol, map_id: int, exclude: tuple[int, ...] = ()) -> list[int]:
    """Map-IDs der Schweratom-Nachbarn eines gemappten Atoms (sortiert, deterministisch)."""
    atom = mol.GetAtomWithIdx(_idx(mol, map_id))
    return sorted(n.GetAtomMapNum() for n in atom.GetNeighbors() if n.GetAtomMapNum() not in exclude)


def _fan(maps: list[int], angles: list[float]) -> dict[int, tuple[float, float]]:
    return {m: _ray(a) for m, a in zip(maps, angles)}


def _ring_pair(mol: Chem.Mol, centre: int, subs: list[int]) -> tuple[int, int] | None:
    """Zwei Substituenten, die mit dem Zentrum in einem Ring liegen (Map-IDs), sonst None."""
    c = _idx(mol, centre)
    for ring in Chem.GetSymmSSSR(mol):
        if c in ring:
            in_ring = [m for m in subs if _idx(mol, m) in ring]
            if len(in_ring) >= 2:
                return in_ring[0], in_ring[1]
    return None


def _fan_centre(mol: Chem.Mol, subs: list[int], angles: dict, ring_angles: dict) -> dict[int, tuple[float, float]]:
    """Substituenten des Reaktions-C auf ihre Winkel; liegt das Zentrum in einem Ring, bekommen die
    beiden Ring-Nachbarn ein eigenes Winkelpaar mit 120° Abstand.

    Ohne diese Ausnahme legte der Fächer die Ring-Nachbarn auf 90°/270° (Übergangszustand, 180°
    auseinander) oder 180°/270° (SN1, 90°) — RDKit faltete den Sechsring zum Bicyclus bzw. zog ein
    Ringatom gerade und beschriftete es mit „C“ (Kontaktbogen 05.11.2026).
    """
    pair = _ring_pair(mol, C, subs)
    if pair is None or len(subs) not in ring_angles:
        return _fan(subs, angles[len(subs)])
    pair_angles, rest_angles = ring_angles[len(subs)]
    rest = [m for m in subs if m not in pair]
    return {**_fan(list(pair), pair_angles), **_fan(rest, rest_angles)}


def _tail(mol: Chem.Mol, map_id: int, at: tuple[float, float], direction: float,
          exclude: tuple[int, ...] = (), tilt: float = 0.0) -> dict[int, tuple[float, float]]:
    """Angreifendes Atom bei `at`, sein erster Nachbar eine Bindung weiter in x-Richtung `direction`,
    um `tilt` Grad nach unten gekippt."""
    anchor = {map_id: at}
    nbrs = _neighbours(mol, map_id, exclude)
    if nbrs:
        dx, dy = _ray(-tilt)
        anchor[nbrs[0]] = (at[0] + direction * dx, at[1] + dy)
    return anchor


# Winkel der übrigen Substituenten am Reaktions-C (Abgangsgruppe/Nucleophil liegen auf der x-Achse)
_SN2_BEFORE = {0: [], 1: [120], 2: [120, 240]}  # Edukt: weg vom Rückseitenangriff
_SN2_TS = {0: [], 1: [90], 2: [90, 270]}  # Übergangszustand: planar, senkrecht zur Achse
_SN2_AFTER = {0: [], 1: [60], 2: [60, 300]}  # Produkt: Regenschirm umgeklappt (Walden)
_SN1 = {1: [180], 2: [120, 240], 3: [90, 180, 270]}
# Zentrum im Ring: (Winkel der zwei Ring-Nachbarn, Winkel der übrigen). Übergangszustand: der Ring
# steht über der Achse Nu···C···X (−x und +x sind besetzt); SN1: Ring nach links unten, der dritte
# Substituent nach oben, +x bleibt für Abgangsgruppe und Nucleophil frei.
_SN2_TS_RING = {2: ([30, 150], [])}
_SN1_RING = {3: ([150, 270], [90])}


def _sn2(frags: list[_Frag]) -> list[MechanismStep]:
    substrate, c_idx, x_idx, nuc, _nuc_name, nu_idx = _halide_and_nucleophile(frags, "sn2")
    n_c, _benzylic, _allylic = _carbon_class(substrate.mol, c_idx, x_idx)
    if n_c >= 3:
        raise UnsupportedSubstrates(
            "tertiary halide — SN2 needs a methyl, primary or secondary alkyl halide; use sn1")
    nuc_m, sub_m = _assign_maps([(nuc.mol, {nu_idx: NU}), (substrate.mol, {c_idx: C, x_idx: X})])

    ts = _cut(sub_m, C, X, {X: -1}, keep_h=(C,))
    ts_c, ts_x = _frag_with(ts, C), _frag_with(ts, X)
    ts_c.GetAtomWithIdx(_idx(ts_c, C)).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    product = _react("[C@:1]-[Cl,Br,I:2].[*-:3]>>[C@@:1]-[*+0:3].[*-:2]", [sub_m, nuc_m])
    prod = _frag_with(product, NU)
    leaving = _frag_with(product, X)
    # Konfiguration des Produktzentrums ausschreiben — der Keil allein ist keine Aussage
    # (Desktop-Abnahme 05.11.2026). Ohne @ in der Eingabe bleibt das Label ohne Deskriptor.
    label = "Products"
    if descriptor := cip_labels(prod).get(_idx(prod, C)):
        label += f", ({descriptor})"

    subs = _neighbours(sub_m, C, exclude=(X,))
    # Nur Kohlenstoff-/Heteroatom-Substituenten zählen für den Fächer (H ist implizit)
    before = {C: (0.0, 0.0), X: (1.0, 0.0), **_fan(subs, _SN2_BEFORE[len(subs)])}
    return [
        MechanismStep(
            label="Reactants", molecules=[_smi(sub_m), _smi(nuc_m)], arrows=[],
            anchors=[before, _tail(nuc_m, NU, (-2.6, 0.0), -1.0)],
        ),
        MechanismStep(
            label="Backside attack (transition state)",
            molecules=[_smi(ts_c), _smi(nuc_m), _smi(ts_x)],
            arrows=[
                CurvedArrow(source=(NU, "lone_pair"), target=(C, "atom"), style="full"),
                CurvedArrow(source=(C, "bond_to", X), target=(X, "atom"), style="full"),
            ],
            is_transition_state=True,
            partial_bonds=[(NU, C), (C, X)],
            mol_gap=1.8,
            anchors=[
                {C: (0.0, 0.0), **_fan_centre(sub_m, subs, _SN2_TS, _SN2_TS_RING)},
                _tail(nuc_m, NU, (-2.0, 0.0), -1.0),
                {X: (2.0, 0.0)},
            ],
        ),
        MechanismStep(
            label=label, molecules=[_smi(prod), _smi(leaving)], arrows=[],
            anchors=[
                {C: (0.0, 0.0), **_fan(subs, _SN2_AFTER[len(subs)]),
                 **_tail(prod, NU, (-1.0, 0.0), -1.0, exclude=(C,))},
                {},
            ],
        ),
    ]


def _sn1(frags: list[_Frag]) -> list[MechanismStep]:
    substrate, c_idx, x_idx, nuc, _nuc_name, nu_idx = _halide_and_nucleophile(frags, "sn1")
    n_c, benzylic, allylic = _carbon_class(substrate.mol, c_idx, x_idx)
    if n_c < 3 and not (benzylic or allylic):
        raise UnsupportedSubstrates(
            "SN1 needs a tertiary, benzylic or allylic halide (a carbocation that is stabilised); "
            "for a methyl, primary or secondary alkyl halide use sn2")
    sub_m, nuc_m = _assign_maps([(substrate.mol, {c_idx: C, x_idx: X}), (nuc.mol, {nu_idx: NU})])

    cation_parts = _cut(sub_m, C, X, {C: +1, X: -1})
    cation, halide = _frag_with(cation_parts, C), _frag_with(cation_parts, X)
    neutral = nuc_m.GetAtomWithIdx(_idx(nuc_m, NU)).GetFormalCharge() == 0
    product = _react("[C+:1].[*:3]>>[C+0:1]-[*+0:3]", [Chem.Mol(cation), nuc_m])[0]
    for atom in product.GetAtoms():
        if atom.GetAtomMapNum() == C:
            atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    stereogenic = any(
        idx == _idx(product, C)
        for idx, _ in Chem.FindMolChiralCenters(unmapped(product), includeUnassigned=True,
                                             useLegacyImplementation=False))

    label = "Product (after deprotonation)" if neutral else "Product"
    if stereogenic:
        label += ", racemic"
    subs = _neighbours(sub_m, C, exclude=(X,))
    centre = {C: (0.0, 0.0), **_fan_centre(sub_m, subs, _SN1, _SN1_RING)}
    return [
        MechanismStep(
            label="Reactants", molecules=[_smi(sub_m), _smi(nuc_m)], arrows=[],
            anchors=[{**centre, X: (1.0, 0.0)}, {}],
        ),
        MechanismStep(
            label="Leaving group departs",
            molecules=[_smi(sub_m)],
            arrows=[CurvedArrow(source=(C, "bond_to", X), target=(X, "atom"), style="full")],
            anchors=[{**centre, X: (1.0, 0.0)}],
        ),
        MechanismStep(
            label="Carbocation (intermediate)", molecules=[_smi(cation), _smi(halide)], arrows=[],
            anchors=[centre, {X: (2.6, 0.0)}],
        ),
        MechanismStep(
            label="Nucleophilic attack",
            molecules=[_smi(cation), _smi(nuc_m)],
            arrows=[CurvedArrow(source=(NU, "lone_pair"), target=(C, "atom"), style="full")],
            # Nachbar schräg nach unten: RDKit setzt die Ladung oben rechts an das angreifende Atom,
            # eine waagrechte Bindung nach rechts lief durch das „⁻“ von C⁻≡N (Kontaktbogen 05.11.)
            anchors=[centre, _tail(nuc_m, NU, (2.6, 0.0), 1.0, tilt=40.0)],
        ),
        MechanismStep(
            label=label, molecules=[_smi(product), _smi(halide)], arrows=[],
            anchors=[{**centre, **_tail(product, NU, (1.0, 0.0), 1.0, exclude=(C,))}, {}],
        ),
    ]


# --- Fischer -----------------------------------------------------------------------


def _fischer(frags: list[_Frag]) -> list[MechanismStep]:
    frags = [f for f in frags if Chem.MolToSmiles(f.mol) not in _CATALYSTS]
    acids = [f for f in frags if f.mol.HasSubstructMatch(_ACID)]
    if not acids:
        raise UnsupportedSubstrates("no carboxylic acid (–COOH) among the substrates")
    if len(acids) > 1:
        raise UnsupportedSubstrates("more than one carboxylic acid among the substrates; pass exactly one")
    acid = acids[0]
    acid_hits = acid.mol.GetSubstructMatches(_ACID)
    if len(acid_hits) > 1:
        raise UnsupportedSubstrates(
            "the acid has more than one COOH group; pass a carboxylic acid with exactly one")
    others = [f for f in frags if f is not acid]
    if not others:
        raise UnsupportedSubstrates(
            "needs two separate molecules, a carboxylic acid and an alcohol "
            "(an intramolecular ester/lactone is not drawn)")
    alcohols = [f for f in others if f.mol.HasSubstructMatch(_ALCOHOL)]
    if not alcohols:
        if any(f.mol.HasSubstructMatch(_PHENOL) for f in others):
            raise UnsupportedSubstrates(
                "a phenol is not esterified by the Fischer mechanism; needs a primary or secondary alcohol")
        raise UnsupportedSubstrates("no alcohol among the substrates (needs a primary or secondary alcohol)")
    if len(alcohols) > 1:
        raise UnsupportedSubstrates("more than one alcohol among the substrates; pass exactly one")
    alcohol = alcohols[0]
    unused = [f.label for f in others if f is not alcohol]
    if unused:
        raise UnsupportedSubstrates(f"'{unused[0]}' has no role in this mechanism")
    alc_hits = alcohol.mol.GetSubstructMatches(_ALCOHOL)
    if len(alc_hits) > 1:
        raise UnsupportedSubstrates("the alcohol has more than one OH group; pass an alcohol with exactly one")
    o_idx, c_idx = alc_hits[0]
    if alcohol.mol.GetAtomWithIdx(c_idx).GetTotalNumHs() == 0:
        raise UnsupportedSubstrates(
            "tertiary alcohol — the Fischer esterification needs a primary or secondary alcohol "
            "(a tertiary one eliminates instead)")

    c1, o2, o3 = acid_hits[0]
    acid_m, alc_m = _assign_maps([
        (acid.mol, {c1: C_ACID, o2: O_CARBONYL, o3: O_HYDROXY}),
        (alcohol.mol, {o_idx: O_ALCOHOL}),
    ])
    proton = Chem.MolFromSmiles(f"[H+:{H_PLUS}]")

    # Protonierte Säure, gezeichnet als Carbokation-Grenzformel C⁺(OH)₂ (Design (b), (g)9)
    cation = _react("[C:1]=[O:2].[H+]>>[C+:1]-[O+0:2]", [acid_m, proton])[0]
    # Angriff des Alkohols: Oxonium am Alkohol-O, dessen H als eigenes Atom (wandert gleich weiter)
    oxonium = _explicit_h(_react("[C+:1].[O:4]>>[C+0:1]-[O+:4]", [cation, alc_m])[0], O_ALCOHOL, H_MOVING)
    # Protonentransfer O4–H → O3: aus dem OH wird OH₂⁺, die Abgangsgruppe ist Wasser
    # In Schritt 5 trägt kein Pfeil mehr das gewanderte H: es wird wieder implizit („OH₂⁺“), sonst
    # landet der Pfeil der Wasserabspaltung auf seiner Bindung (Kontaktbogen 05.11.2026)
    water_on = _implicit_h(_move_h(oxonium, H_MOVING, O_ALCOHOL, O_HYDROXY), H_MOVING)
    # Wasser geht, O2 bildet C=O⁺H zurück: protonierter Ester (H an O2 als Atom, es geht im nächsten Schritt)
    prot_ester, water = _lose_water(water_on)
    ester = _deprotonate(prot_ester)

    rest = _neighbours(acid_m, C_ACID, exclude=(O_CARBONYL, O_HYDROXY))
    r = {rest[0]: (-1.0, 0.0)} if rest else {}
    trigonal = {C_ACID: (0.0, 0.0), **r, O_CARBONYL: _ray(60), O_HYDROXY: _ray(-60)}
    # Tetraedrisch: O2 oben, O3 unten, Alkohol-O rechts; das wandernde H sitzt unter dem Alkohol-O,
    # neben O3 — der Protonentransfer ist ein kurzer Pfeil, und das H bleibt in Schritt 5 am Ort.
    tetra_anchor = {C_ACID: (0.0, 0.0), **r, O_CARBONYL: (0.0, 1.0), O_HYDROXY: (0.0, -1.0),
                    **_tail(oxonium, O_ALCOHOL, (1.0, 0.0), 1.0, exclude=(C_ACID, H_MOVING))}
    o2 = _ray(60)
    ester_anchor = {C_ACID: (0.0, 0.0), **r, O_CARBONYL: o2, O_ALCOHOL: _ray(-60),
                    **_tail(ester, O_ALCOHOL, _ray(-60), 1.0, exclude=(C_ACID,))}
    return [
        MechanismStep(
            label="Reactants", molecules=[_smi(acid_m), _smi(alc_m), "[H+]"], arrows=[],
            anchors=[trigonal, {}, {}],
        ),
        MechanismStep(
            label="Protonation of the carbonyl group",
            molecules=[_smi(acid_m), _smi(proton)],
            arrows=[CurvedArrow(source=(O_CARBONYL, "lone_pair"), target=(H_PLUS, "atom"), style="full")],
            anchors=[trigonal, {H_PLUS: (o2[0] * 2.5, o2[1] * 2.5)}],
        ),
        MechanismStep(
            label="Nucleophilic attack of the alcohol",
            molecules=[_smi(cation), _smi(alc_m)],
            arrows=[CurvedArrow(source=(O_ALCOHOL, "lone_pair"), target=(C_ACID, "atom"), style="full")],
            anchors=[trigonal, _tail(alc_m, O_ALCOHOL, (2.4, 0.0), 1.0)],
        ),
        MechanismStep(
            label="Proton transfer to an OH group",
            molecules=[_smi(oxonium)],
            arrows=[
                CurvedArrow(source=(O_HYDROXY, "lone_pair"), target=(H_MOVING, "atom"), style="full"),
                CurvedArrow(source=(H_MOVING, "bond_to", O_ALCOHOL), target=(O_ALCOHOL, "atom"), style="full"),
            ],
            anchors=[{**tetra_anchor, H_MOVING: (1.0, -1.0)}],
        ),
        MechanismStep(
            label="Loss of water",
            molecules=[_smi(water_on)],
            arrows=[
                CurvedArrow(source=(C_ACID, "bond_to", O_HYDROXY), target=(O_HYDROXY, "atom"), style="full"),
                CurvedArrow(source=(O_CARBONYL, "lone_pair"), target=(C_ACID, "bond_to", O_CARBONYL), style="full"),
            ],
            anchors=[tetra_anchor],
        ),
        MechanismStep(
            label="Deprotonation (H⁺ regenerated)",
            molecules=[_smi(prot_ester), _smi(water)],
            arrows=[CurvedArrow(source=(H_PLUS, "bond_to", O_CARBONYL), target=(O_CARBONYL, "atom"), style="full")],
            anchors=[{**ester_anchor, H_PLUS: (o2[0] * 2.0, o2[1] * 2.0)}, {}],
        ),
        MechanismStep(
            label="Products", molecules=[_smi(ester), _smi(water), _smi(proton)],
            anchors=[ester_anchor, {}, {}], arrows=[],
        ),
    ]


# Das H, das im Protonentransfer vom Alkohol-O zum OH wandert (als Atom gezeichnet)
H_MOVING = 8


def _explicit_h(mol: Chem.Mol, heavy_map: int, h_map: int) -> Chem.Mol:
    """Ein H am Atom heavy_map als eigenes, gemapptes Atom — ein Pfeil braucht ein Ziel mit Koordinaten."""
    rw = Chem.RWMol(mol)
    heavy = rw.GetAtomWithIdx(_idx(rw, heavy_map))
    n_h = heavy.GetTotalNumHs()
    if n_h < 1:
        raise MechanismBuildError(f"atom map {heavy_map} has no hydrogen to draw")
    h = Chem.Atom(1)
    h.SetAtomMapNum(h_map)
    h_idx = rw.AddAtom(h)
    rw.AddBond(heavy.GetIdx(), h_idx, Chem.BondType.SINGLE)
    heavy.SetNumExplicitHs(n_h - 1)
    heavy.SetNoImplicit(True)
    return _sanitize(rw)


def _implicit_h(mol: Chem.Mol, h_map: int) -> Chem.Mol:
    """Gezeichnetes H-Atom wieder in die H-Zahl seines Nachbarn falten."""
    rw = Chem.RWMol(mol)
    h = rw.GetAtomWithIdx(_idx(rw, h_map))
    heavy = h.GetNeighbors()[0]
    n_h = heavy.GetTotalNumHs()
    heavy.SetNumExplicitHs(n_h + 1)
    heavy.SetNoImplicit(True)
    rw.RemoveAtom(h.GetIdx())
    return _sanitize(rw)


def _sanitize(rw: Chem.RWMol) -> Chem.Mol:
    mol = rw.GetMol()
    try:
        Chem.SanitizeMol(mol)
    except Exception as exc:  # noqa: BLE001 — jeder RDKit-Fehler heißt: Vorlage zeichnen
        raise MechanismBuildError(f"intermediate failed sanitization: {exc}") from exc
    return mol


def _set_hs(atom: Chem.Atom, n: int, charge: int) -> None:
    atom.SetFormalCharge(charge)
    atom.SetNumExplicitHs(n)
    atom.SetNoImplicit(True)


def _move_h(mol: Chem.Mol, h_map: int, from_map: int, to_map: int) -> Chem.Mol:
    """Protonentransfer: das gezeichnete H wechselt von from (wird neutral) zu to (wird +1)."""
    rw = Chem.RWMol(mol)
    h, a, b = _idx(rw, h_map), _idx(rw, from_map), _idx(rw, to_map)
    src, dst = rw.GetAtomWithIdx(a), rw.GetAtomWithIdx(b)
    # Implizite H vor dem Umbau zählen (danach ist der Valenz-Cache ungültig); das gezeichnete H
    # ist ein Atom und zählt nicht mit
    src_h, dst_h = src.GetNumExplicitHs() + src.GetNumImplicitHs(), dst.GetNumExplicitHs() + dst.GetNumImplicitHs()
    rw.RemoveBond(h, a)
    rw.AddBond(h, b, Chem.BondType.SINGLE)
    _set_hs(src, src_h, 0)
    _set_hs(dst, dst_h, +1)
    return _sanitize(rw)


def _lose_water(mol: Chem.Mol) -> tuple[Chem.Mol, Chem.Mol]:
    """C–OH₂⁺ bricht: Wasser geht neutral, O2 bildet die C=O⁺H-Doppelbindung (H als Atom H_PLUS)."""
    rw = Chem.RWMol(mol)
    c, o2, o3 = _idx(rw, C_ACID), _idx(rw, O_CARBONYL), _idx(rw, O_HYDROXY)
    rw.RemoveBond(c, o3)
    rw.GetBondBetweenAtoms(c, o2).SetBondType(Chem.BondType.DOUBLE)
    o2_atom = rw.GetAtomWithIdx(o2)
    _set_hs(o2_atom, 0, +1)
    h = Chem.Atom(1)
    h.SetAtomMapNum(H_PLUS)
    rw.AddBond(o2, rw.AddAtom(h), Chem.BondType.SINGLE)
    _set_hs(rw.GetAtomWithIdx(o3), 2, 0)
    whole = _sanitize(rw)
    frags = Chem.GetMolFrags(whole, asMols=True)
    return _frag_with(list(frags), C_ACID), _frag_with(list(frags), O_HYDROXY)


def _deprotonate(mol: Chem.Mol) -> Chem.Mol:
    """Protonierter Ester → Ester: das H-Atom an O2 geht als H⁺."""
    rw = Chem.RWMol(mol)
    rw.RemoveAtom(_idx(rw, H_PLUS))
    _set_hs(rw.GetAtomWithIdx(_idx(rw, O_CARBONYL)), 0, 0)
    return _sanitize(rw)


_BUILDERS = {"sn2": _sn2, "sn1": _sn1, "fischer_ester": _fischer}


def build_steps(reaction_type: str, smiles_list: list[str]) -> list[MechanismStep]:
    """Schritte aus den Nutzer-Substraten.

    UnsupportedSubstrates: außerhalb der Grenze (Grund im Text, kein Bild).
    MechanismBuildError: in der Grenze, aber die Ableitung scheiterte (Aufrufer zeichnet die Vorlage).
    """
    if reaction_type not in _BUILDERS:
        raise UnsupportedSubstrates(f"unknown mechanism '{reaction_type}'")
    return _BUILDERS[reaction_type](_fragments(smiles_list))
