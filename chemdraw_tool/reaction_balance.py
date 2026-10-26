"""Stoffbilanz einer gezeichneten Reaktionsgleichung.

Zwei getrennte Schritte:

1. **Erhaltung prüfen**, wie die Gleichung dasteht (alle Koeffizienten 1 —
   die Listen von generate_reaction haben keine). Ergebnis: ausgeglichen oder
   die Elementdifferenz je Seite.
2. **Koeffizienten vorschlagen**, nur wenn der rationale Nullraum der
   Elementmatrix genau eindimensional ist und alle Einträge positiv sind.

Gerechnet wird an den vollen Molekülen (vor einer Gruppenabkürzung), Isotope
zählen als ihr Element, die Ladung ist eine eigene Zeile. Reagenzien im
Pfeiltext sind keine Stoffe der Gleichung und kommen hier nie an.

Texte sprechen von links/rechts, nie von Edukten/Produkten — beim
Retropfeil liest man die Gleichung andersherum, die Bilanz bleibt dieselbe.
Keine Abhängigkeit außer RDKit und der Standardbibliothek.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, lcm

from rdkit import Chem

from chemdraw_tool.payloads import ReactionBalance

Counts = tuple[dict[str, int], int]  # (Element → Anzahl, Gesamtladung)

_ARROWS = {"forward": "→", "equilibrium": "⇌", "retro": "⇒"}
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_SUP = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")

# Kleine Moleküle/Ionen, die als „fehlt“ benannt werden dürfen. Alles andere
# bleibt eine Elementliste — kein Raten, welcher Stoff gemeint sein könnte.
# Formel in der üblichen Schreibweise (HCl, NH3), nicht in Hill-Ordnung.
_SIMPLE = {
    "O": "H2O", "[H][H]": "H2", "O=O": "O2", "N#N": "N2", "ClCl": "Cl2",
    "BrBr": "Br2", "II": "I2", "[C-]#[O+]": "CO", "O=C=O": "CO2", "N": "NH3",
    "Cl": "HCl", "Br": "HBr", "I": "HI", "F": "HF", "S": "H2S", "O=S=O": "SO2",
    "O=S(=O)=O": "SO3", "C": "CH4", "CO": "CH3OH", "[OH-]": "OH-",
}


def element_counts(mol: Chem.Mol) -> Counts:
    """Elemente inkl. impliziter H und Gesamtladung eines Moleküls.

    Explizite H-Atome im Graphen zählen als Atome; `GetTotalNumHs()` ohne
    Nachbarn ergänzt nur die angehängten H — so zählt nichts doppelt.
    """
    counts: dict[str, int] = {}
    charge = 0
    for atom in mol.GetAtoms():
        sym = atom.GetSymbol()
        counts[sym] = counts.get(sym, 0) + 1
        hs = atom.GetTotalNumHs()
        if hs:
            counts["H"] = counts.get("H", 0) + hs
        charge += atom.GetFormalCharge()
    return counts, charge


def _hill_order(elements) -> list[str]:
    els = set(elements)
    if "C" in els:
        return ["C"] + (["H"] if "H" in els else []) + sorted(els - {"C", "H"})
    return sorted(els)


def formula(counts: Counts) -> str:
    """Summenformel in Hill-Ordnung mit Ladung, z. B. 'H2O', 'H4N+'."""
    elements, charge = counts
    text = "".join(
        f"{el}{n if n != 1 else ''}" for el in _hill_order(elements) if (n := elements[el])
    )
    if charge:
        mag = abs(charge)
        text += f"{mag if mag != 1 else ''}{'+' if charge > 0 else '-'}"
    return text


def _display(counts: Counts) -> str:
    """Unicode-Formel fürs Panel; Ladungsziffern hochgestellt, nicht tief."""
    elements, charge = counts
    plain = formula((elements, 0))
    text = plain.translate(_SUB)
    if charge:
        mag = abs(charge)
        text += (f"{mag if mag != 1 else ''}{'+' if charge > 0 else '-'}").translate(_SUP)
    return text


def _simple_table() -> dict[tuple, str]:
    table = {}
    for smi, name in _SIMPLE.items():
        elements, charge = element_counts(Chem.MolFromSmiles(smi))
        table[(tuple(sorted(elements.items())), charge)] = name
    # H⁺ direkt: RDKit warnt beim Parsen eines nackten Protons.
    table[((("H", 1),), 1)] = "H+"
    return table


_SIMPLE_TABLE: dict[tuple, str] | None = None


def _match_simple(elements: dict[str, int], charge: int) -> str | None:
    global _SIMPLE_TABLE
    if _SIMPLE_TABLE is None:
        _SIMPLE_TABLE = _simple_table()
    return _SIMPLE_TABLE.get((tuple(sorted(elements.items())), charge))


def _display_name(plain: str) -> str:
    """'H2O' → 'H₂O', 'OH-' → 'OH⁻' (Ladung hoch, Ziffern tief)."""
    body = plain.rstrip("+-")
    return body.translate(_SUB) + plain[len(body):].translate(_SUP)


def _sum(species: list[Counts]) -> Counts:
    total: dict[str, int] = {}
    charge = 0
    for elements, q in species:
        for el, n in elements.items():
            total[el] = total.get(el, 0) + n
        charge += q
    return total, charge


# --- Schritt 2: rationaler Nullraum ----------------------------------------


def _nullspace(matrix: list[list[Fraction]], ncols: int) -> list[list[Fraction]]:
    """Basis des Nullraums per Gauß-Jordan über den rationalen Zahlen."""
    rows = [row[:] for row in matrix]
    pivots: list[int] = []
    r = 0
    for c in range(ncols):
        pivot = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        p = rows[r][c]
        rows[r] = [v / p for v in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == len(rows):
            break
    free = [c for c in range(ncols) if c not in pivots]
    basis = []
    for fc in free:
        vec = [Fraction(0)] * ncols
        vec[fc] = Fraction(1)
        for i, pc in enumerate(pivots):
            vec[pc] = -rows[i][fc]
        basis.append(vec)
    return basis


def suggest_coefficients(
    left: list[Counts], right: list[Counts]
) -> tuple[list[int] | None, str]:
    """Kleinste ganzzahlige Koeffizienten (links, dann rechts) oder Grund.

    Spalten = Stoffe (rechts mit negativem Vorzeichen), Zeilen = Elemente
    plus Ladung. Vorschlag nur bei genau eindimensionalem Nullraum mit
    durchweg positiven Einträgen.
    """
    species = left + right
    signs = [1] * len(left) + [-1] * len(right)
    elements = sorted({el for counts, _ in species for el in counts})
    matrix = [
        [Fraction(s * counts.get(el, 0)) for (counts, _), s in zip(species, signs)]
        for el in elements
    ]
    matrix.append([Fraction(s * q) for (_, q), s in zip(species, signs)])
    basis = _nullspace(matrix, len(species))
    if not basis:
        return None, "no coefficients balance these species"
    if len(basis) > 1:
        return None, "more than one independent set of coefficients fits, so none is suggested"
    vec = basis[0]
    if any(v == 0 for v in vec):
        return None, "a species does not take part in any balanced form"
    if vec[0] < 0:
        vec = [-v for v in vec]
    if any(v < 0 for v in vec):
        return None, "balancing would need a species on the other side"
    scale = lcm(*(v.denominator for v in vec))
    ints = [int(v * scale) for v in vec]
    g = 0
    for n in ints:
        g = gcd(g, n)
    return [n // g for n in ints], ""


# --- Schritt 1 + Zusammenbau -----------------------------------------------


def _side_text(surplus: dict[str, int], charge: int) -> str:
    parts = [f"+{surplus[el]} {el}" for el in _hill_order(surplus)]
    if charge:
        parts.append(f"+{charge} charge")
    return ", ".join(parts)


def _equation(coeffs: list[int], displays: list[str], n_left: int, arrow: str) -> str:
    terms = [f"{c} {d}" if c != 1 else d for c, d in zip(coeffs, displays)]
    return f"{' + '.join(terms[:n_left])} {_ARROWS.get(arrow, '→')} {' + '.join(terms[n_left:])}"


def check_balance(
    left_mols: list[Chem.Mol], right_mols: list[Chem.Mol], arrow: str = "forward"
) -> ReactionBalance | None:
    """Bilanz links gegen rechts; None, wenn sie sich nicht prüfen lässt
    (eine Seite leer, Platzhalteratome wie R/*)."""
    if not left_mols or not right_mols:
        return None
    mols = list(left_mols) + list(right_mols)
    if any(a.GetAtomicNum() == 0 for m in mols for a in m.GetAtoms()):
        return None

    left = [element_counts(m) for m in left_mols]
    right = [element_counts(m) for m in right_mols]
    formulas = [formula(c) for c in left + right]
    displays = [_display(c) for c in left + right]

    (l_el, l_q), (r_el, r_q) = _sum(left), _sum(right)
    difference = {
        el: r_el.get(el, 0) - l_el.get(el, 0)
        for el in _hill_order(set(l_el) | set(r_el))
        if r_el.get(el, 0) != l_el.get(el, 0)
    }
    charge_diff = r_q - l_q

    if not difference and charge_diff == 0:
        return ReactionBalance(
            balanced=True,
            difference={},
            chargeDifference=0,
            formulas=formulas,
            note="Balanced as drawn: atoms and charge agree on both sides.",
        )

    # Überschuss je Seite: was links mehr steht, fehlt rechts (und umgekehrt).
    left_more = {el: -d for el, d in difference.items() if d < 0}
    right_more = {el: d for el, d in difference.items() if d > 0}
    simple = None
    if left_more and not right_more:
        simple = ("right", _match_simple(left_more, -charge_diff))
    elif right_more and not left_more:
        simple = ("left", _match_simple(right_more, charge_diff))

    if simple and simple[1]:
        side, name = simple
        summary = f"{side} side lacks {_display_name(name)}"
        plain_diff = f"{side} side lacks {name}"
    else:
        pieces = []
        lt = _side_text(left_more, max(-charge_diff, 0))
        rt = _side_text(right_more, max(charge_diff, 0))
        if lt:
            pieces.append(f"left: {lt}")
        if rt:
            pieces.append(f"right: {rt}")
        summary = plain_diff = "; ".join(pieces)

    coeffs, reason = suggest_coefficients(left, right)
    if coeffs:
        suggested = _equation(coeffs, displays, len(left), arrow)
        plain_eq = _equation(coeffs, formulas, len(left), arrow)
        note = (
            f"Not balanced as drawn ({plain_diff}). Suggested coefficients, "
            f"not drawn: {plain_eq}."
        )
    else:
        suggested = ""
        note = f"Not balanced as drawn ({plain_diff}); {reason}."

    return ReactionBalance(
        balanced=False,
        difference=difference,
        chargeDifference=charge_diff,
        suggestedCoefficients=coeffs,
        formulas=formulas,
        summary=summary,
        suggestedEquation=suggested,
        note=note,
    )
