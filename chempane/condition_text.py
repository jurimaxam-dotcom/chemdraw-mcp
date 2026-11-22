"""Reaktionsbedingungen: Ziffern in Summenformeln tiefstellen.

Eine Ziffer wird nur tiefgestellt, wenn ihr Token (leerzeichenfrei, getrennt
auch an `,` `;` `:` `/`) als Ganzes wie eine Formel gebaut ist: Elementsymbole
bzw. gängige Gruppenkürzel (Me, Et, Ph …), Klammern, Ziffern nur direkt nach
einem Symbol oder einer schließenden Klammer, optional eine Ladung am Ende.
Alles andere ("80 °C", "2 h", "12h", "2 eq", "THF") bleibt, wie es ist.

Zwei Ausgaben aus einer Zerlegung: `formula_runs` für CDXML (ChemDraw stellt
per `face="32"` tief), `subscript_formulas` mit Unicode-Ziffern für PNG, SVG
und Panel.
"""

from __future__ import annotations

import re

_ELEMENTS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni "
    "Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I "
    "Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt "
    "Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr"
).split()
# Gruppenkürzel, die in Bedingungen wie Elemente stehen (Et3N, Pd(PPh3)4).
# i/n/s/t-Präfix nur vor Pr/Bu (OiPr, tBu).
_GROUPS = ["Me", "Et", "Ph", "Bn", "Bz", "Ts", "Ms", "Tf", "Boc"]
_SYMBOL = (
    "(?:[inst]?(?:Pr|Bu)|"
    + "|".join(sorted(_ELEMENTS + _GROUPS, key=len, reverse=True))
    + ")"
)
_FORMULA = re.compile(
    rf"(?:(?:{_SYMBOL}|[)\]])\d*|[(\[])+(?:\d*[+\-−])?"
)
_DIGIT_AFTER = re.compile(r"(?<=[A-Za-z)\]])(\d+)")
# Mechanismus-Kürzel sehen aus wie Formeln (S + N + 2), sind aber keine.
_NOT_FORMULA = re.compile(r"S[NE]\d'?")
_SEPARATORS = re.compile(r"(\s+|[,;:/])")
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _is_formula(token: str) -> bool:
    return (
        any(c.isdigit() for c in token)
        and (token[0].isupper() or token[0] in "([")
        and _FORMULA.fullmatch(token) is not None
        and _NOT_FORMULA.fullmatch(token) is None
    )


def _token_runs(token: str) -> list[tuple[str, bool]]:
    if not token or not _is_formula(token):
        return [(token, False)]
    charge = re.search(r"\d*[+\-−]$", token)
    body, tail = (token[: charge.start()], charge.group()) if charge else (token, "")
    runs: list[tuple[str, bool]] = []
    pos = 0
    for m in _DIGIT_AFTER.finditer(body):
        runs.append((body[pos : m.start()], False))
        runs.append((m.group(), True))
        pos = m.end()
    runs.append((body[pos:] + tail, False))
    return runs


def formula_runs(text: str) -> list[tuple[str, bool]]:
    """Zerlegt `text` in (Teiltext, tiefgestellt?)-Läufe, benachbarte
    gleichartige Läufe zusammengefasst. Ohne Formel: genau ein Lauf."""
    runs: list[tuple[str, bool]] = []
    for part in _SEPARATORS.split(text):
        for chunk, sub in _token_runs(part):
            if not chunk:
                continue
            if runs and runs[-1][1] == sub:
                runs[-1] = (runs[-1][0] + chunk, sub)
            else:
                runs.append((chunk, sub))
    return runs


def subscript_formulas(text: str) -> str:
    """Wie `formula_runs`, aber als Text mit Unicode-Tiefziffern (H₂SO₄)."""
    return "".join(
        chunk.translate(_SUB) if sub else chunk for chunk, sub in formula_runs(text)
    )
