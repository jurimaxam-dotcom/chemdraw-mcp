"""Erwartete Spektrenmerkmale aus der Struktur — IR-Banden und ¹H-Signale.

Bewusst deterministisch und damit ehrlich begrenzt:

* **IR-Banden** kommen aus einer kuratierten Tabelle, die über SMARTS an die
  Struktur gebunden wird. Es gibt dafür keine Bibliothek (Stand 08/2026), und
  eine Vorhersage aus erster Hand wäre Quantenchemie, nicht ein Tool.
* **¹H-Signale** zählt RDKit über die topologische Äquivalenz der Protonen.
  Das liefert Signalzahl und Integralverhältnis — genau das, was Klausuren
  fragen. Verschiebungen in ppm liefert es NICHT; die kämen nur aus einem
  ML-Modell und wären geraten.

Die Grenze der Äquivalenzzählung (diastereotope Protonen) steht in der
Rückgabe, nicht nur hier — ein Ergebnis, das genauer wirkt als es ist, ist
schlimmer als eines mit Fussnote.
"""

from __future__ import annotations

from rdkit import Chem

# Wellenzahlbereich, in dem IR-Spektren aufgenommen werden.
IR_MIN = 400
IR_MAX = 4000

# Kuratierte Bandentabelle. Reihenfolge egal — sortiert wird nach Lage.
# Jede Zeile: SMARTS, Gruppenname, Bereich, Intensität, Bandenform, Hinweis.
# Die Bereiche folgen den gängigen Lehrbuchtabellen (Hesse/Meier/Zeeh).
_IR_TABLE: list[dict] = [
    {
        "smarts": "[CX3](=O)[OX2H1]",
        "group": "O–H (carboxylic acid)",
        "low": 2500,
        "high": 3300,
        "intensity": "medium",
        "shape": "very broad",
        "hint": "The broadest band in the spectrum — it swallows the C–H region.",
    },
    {
        "smarts": "[CX3](=O)[OX2H1]",
        "group": "C=O (carboxylic acid)",
        "low": 1700,
        "high": 1725,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Together with the broad O–H this pair identifies the acid.",
    },
    {
        "smarts": "[OX2H][CX4]",
        "group": "O–H (alcohol)",
        "low": 3200,
        "high": 3600,
        "intensity": "strong",
        "shape": "broad",
        "hint": "Broad because of hydrogen bonding; sharp when measured dilute.",
    },
    {
        "smarts": "[OX2H]c",
        "group": "O–H (phenol)",
        "low": 3200,
        "high": 3600,
        "intensity": "strong",
        "shape": "broad",
        "hint": "",
    },
    {
        "smarts": "[NX3;H2][CX4,c]",
        "group": "N–H (primary amine)",
        "low": 3300,
        "high": 3500,
        "intensity": "medium",
        "shape": "two bands",
        "hint": "Two bands — symmetric and antisymmetric. One band means secondary.",
    },
    {
        "smarts": "[NX3;H1]([CX4,c])[CX4,c]",
        "group": "N–H (secondary amine)",
        "low": 3300,
        "high": 3500,
        "intensity": "weak",
        "shape": "single band",
        "hint": "",
    },
    {
        "smarts": "[CX3](=[OX1])[NX3]",
        "group": "C=O (amide, band I)",
        "low": 1630,
        "high": 1690,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Lowest of all carbonyls — the nitrogen lone pair weakens the C=O.",
    },
    {
        "smarts": "[NX3;H1,H2][CX3]=[OX1]",
        "group": "N–H (amide)",
        "low": 3100,
        "high": 3500,
        "intensity": "medium",
        "shape": "broad",
        "hint": "",
    },
    {
        "smarts": "[CX3H1](=O)[#6]",
        "group": "C=O (aldehyde)",
        "low": 1720,
        "high": 1740,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Look for the two weak C–H bands near 2720 and 2820 to confirm.",
    },
    {
        "smarts": "[CX3H1](=O)[#6]",
        "group": "C–H (aldehyde)",
        "low": 2700,
        "high": 2850,
        "intensity": "weak",
        "shape": "two bands",
        "hint": "The Fermi doublet — the only proof of an aldehyde vs. a ketone.",
    },
    {
        "smarts": "[#6][CX3](=O)[#6]",
        "group": "C=O (ketone)",
        "low": 1705,
        "high": 1725,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "",
    },
    {
        "smarts": "[CX3](=O)[OX2][#6]",
        "group": "C=O (ester)",
        "low": 1735,
        "high": 1750,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Higher than a ketone — the ester oxygen pulls electron density.",
    },
    {
        "smarts": "[CX3](=O)[OX2][#6]",
        "group": "C–O (ester)",
        "low": 1000,
        "high": 1300,
        "intensity": "strong",
        "shape": "two bands",
        "hint": "",
    },
    {
        "smarts": "[CX3](=O)[Cl,Br,I,F]",
        "group": "C=O (acid halide)",
        "low": 1785,
        "high": 1815,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "The highest carbonyl there is.",
    },
    {
        "smarts": "[CX3](=O)[OX2][CX3]=O",
        "group": "C=O (anhydride)",
        "low": 1740,
        "high": 1830,
        "intensity": "strong",
        "shape": "two bands",
        "hint": "Two carbonyl bands — coupling of the two C=O groups.",
    },
    {
        "smarts": "[NX1]#[CX2]",
        "group": "C≡N (nitrile)",
        "low": 2220,
        "high": 2260,
        "intensity": "medium",
        "shape": "sharp",
        "hint": "Almost nothing else absorbs here — a lonely, telling band.",
    },
    {
        "smarts": "[CX2]#[CX2]",
        "group": "C≡C (alkyne)",
        "low": 2100,
        "high": 2260,
        "intensity": "weak",
        "shape": "sharp",
        "hint": "Weak, and absent in a symmetric alkyne.",
    },
    {
        "smarts": "[CX2;H1]#[CX2]",
        "group": "C–H (terminal alkyne)",
        "low": 3260,
        "high": 3330,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Sharp — that is what separates it from a broad O–H.",
    },
    {
        "smarts": "[CX3]=[CX3]",
        "group": "C=C (alkene)",
        "low": 1620,
        "high": 1680,
        "intensity": "weak",
        "shape": "sharp",
        "hint": "",
    },
    {
        "smarts": "[CX3;H1,H2]=[CX3]",
        "group": "C–H (alkene)",
        "low": 3000,
        "high": 3100,
        "intensity": "medium",
        "shape": "sharp",
        "hint": "Above 3000 — that is the line between sp² and sp³ C–H.",
    },
    {
        "smarts": "c1ccccc1",
        "group": "C=C (aromatic ring)",
        "low": 1450,
        "high": 1600,
        "intensity": "medium",
        "shape": "several bands",
        "hint": "Usually two to four bands between 1450 and 1600.",
    },
    {
        "smarts": "c[H]",
        "group": "C–H (aromatic)",
        "low": 3000,
        "high": 3100,
        "intensity": "medium",
        "shape": "sharp",
        "hint": "",
    },
    {
        "smarts": "[NX3](=O)=O",
        "group": "N=O (nitro, antisymmetric)",
        "low": 1500,
        "high": 1560,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Nitro always shows a pair — this one and the band near 1350.",
    },
    {
        "smarts": "[NX3](=O)=O",
        "group": "N=O (nitro, symmetric)",
        "low": 1345,
        "high": 1385,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "",
    },
    {
        "smarts": "[CX4;H1,H2,H3]",
        "group": "C–H (alkane, sp³)",
        "low": 2850,
        "high": 3000,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "Below 3000 — present in almost every organic compound.",
    },
    {
        # Beide Nachbarn ausdrücklich keine Carbonyl-Kohlenstoffe: Ein Ester
        # enthält formal ein C–O–C, ist aber kein Ether — die Bande separat zu
        # melden würde eine Gruppe vortäuschen, die nicht da ist.
        "smarts": "[#6;!$([CX3]=[OX1])][OX2][#6;!$([CX3]=[OX1])]",
        "group": "C–O (ether)",
        "low": 1050,
        "high": 1150,
        "intensity": "strong",
        "shape": "sharp",
        "hint": "",
    },
    {
        "smarts": "[SX2H]",
        "group": "S–H (thiol)",
        "low": 2550,
        "high": 2600,
        "intensity": "weak",
        "shape": "sharp",
        "hint": "Weak, but nothing else sits there.",
    },
]


def _parse(structure: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(structure)
    if mol is None:
        raise ValueError(
            f"'{structure}' could not be parsed as a structure. Pass a SMILES "
            "string; a compound name has to be resolved before it gets here."
        )
    return mol


def expected_ir_bands(structure: str) -> list[dict]:
    """IR-Banden, die diese Struktur zeigen sollte — hohe Wellenzahl zuerst."""
    mol = _parse(structure)
    mol_h = Chem.AddHs(mol)

    seen: set[str] = set()
    bands: list[dict] = []
    for entry in _IR_TABLE:
        pattern = Chem.MolFromSmarts(entry["smarts"])
        if pattern is None:
            continue
        # Aromatische C–H brauchen explizite Wasserstoffe, alles andere nicht.
        target = mol_h if "[H]" in entry["smarts"] else mol
        if not target.HasSubstructMatch(pattern):
            continue
        if entry["group"] in seen:
            continue
        seen.add(entry["group"])
        bands.append({k: v for k, v in entry.items() if k != "smarts"})

    bands.sort(key=lambda b: b["high"], reverse=True)
    return bands


def assign_wavenumber(wavenumber: float, tolerance: float = 0.0) -> list[dict]:
    """Gemessene Wellenzahl → Gruppen, die dort absorbieren.

    Sortiert danach, wie mittig die Zahl im jeweiligen Bereich liegt: Ein
    Treffer im Zentrum eines Bereichs ist wahrscheinlicher als einer am Rand.
    """
    if not (IR_MIN <= wavenumber <= IR_MAX):
        return []

    hits = []
    for entry in _IR_TABLE:
        low = entry["low"] - tolerance
        high = entry["high"] + tolerance
        if not (low <= wavenumber <= high):
            continue
        centre = (entry["low"] + entry["high"]) / 2.0
        half_width = max((entry["high"] - entry["low"]) / 2.0, 1.0)
        # 0 = genau in der Mitte, 1 = am Rand des Bereichs.
        offset = abs(wavenumber - centre) / half_width
        hit = {k: v for k, v in entry.items() if k != "smarts"}
        hit["offset"] = offset
        hits.append(hit)

    # Doppelte Gruppennamen (mehrere SMARTS je Gruppe) zusammenfassen.
    best: dict[str, dict] = {}
    for hit in hits:
        current = best.get(hit["group"])
        if current is None or hit["offset"] < current["offset"]:
            best[hit["group"]] = hit

    return sorted(best.values(), key=lambda h: h["offset"])


def proton_signals(structure: str) -> dict:
    """Anzahl der ¹H-Signale und ihr Integralverhältnis.

    Zählt topologisch äquivalente Protonen zusammen — das ist die Zählweise,
    die Klausuren meinen.
    """
    mol = _parse(structure)
    mol_h = Chem.AddHs(mol)

    # breakTies=False: symmetrieäquivalente Atome behalten denselben Rang.
    ranks = list(Chem.CanonicalRankAtoms(mol_h, breakTies=False))

    groups: dict[int, int] = {}
    for atom in mol_h.GetAtoms():
        if atom.GetAtomicNum() != 1:
            continue
        rank = ranks[atom.GetIdx()]
        groups[rank] = groups.get(rank, 0) + 1

    integrals = sorted(groups.values(), reverse=True)
    total = sum(integrals)

    if not integrals:
        explanation = (
            "This molecule has no hydrogen atoms, so there is no ¹H spectrum "
            "to expect."
        )
    else:
        ratio = ":".join(str(i) for i in integrals)
        explanation = (
            f"{len(integrals)} signal(s) for {total} hydrogens, integral ratio "
            f"{ratio}. Equivalent protons — same chemical environment by "
            "symmetry — give one signal together."
        )

    return {
        "count": len(integrals),
        "integrals": integrals,
        "total_hydrogens": total,
        "explanation": explanation,
        "limitation": (
            "Counted by topological equivalence. Diastereotope protons — for "
            "example the two hydrogens of a CH₂ next to a stereocentre — are "
            "counted as one signal here, although they do split in reality. "
            "For exam-level molecules the count is right; check it by hand "
            "whenever a stereocentre sits next to a CH₂."
        ),
    }
