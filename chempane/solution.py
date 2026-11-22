"""Lösungsrechnen: Einwaage, Konzentration, Verdünnung, Mischungskreuz.

Reine Funktionen ohne MCP-Bezug, damit sie einzeln testbar bleiben — dasselbe
Muster wie bei den Renderern.

Jede Funktion liefert neben der Zahl einen **Rechenweg**: eine Liste von
Schritten mit Formel, eingesetzten Zahlen und Ergebnis. Das ist kein Beiwerk,
sondern der eigentliche Zweck — im Praktikumsformblatt steht der Rechenweg,
nicht das Resultat. Das Schema `{label, formula, substitution, result,
explanation}` ist dasselbe wie in `calculator/`, damit beide Familien im Chat
gleich aussehen.

Einheiten sind die des Laboralltags, nicht die des SI: Masse in g, Volumen in
mL, Konzentration in mol/L. Umgerechnet wird intern und sichtbar im Rechenweg.
"""

from __future__ import annotations

import re

from molmass import Formula

# Unter dieser Einwaage wird die Analysenwaage zur dominierenden Fehlerquelle
# (Ablesegenauigkeit 0,1 mg, dazu Wägefehler) — dann ist Verdünnen einer
# grösseren Einwaage der richtige Weg, nicht genaueres Wiegen.
MIN_PRACTICAL_WEIGHT_G = 0.01

# Schreibweisen für Kristallwasser, wie sie auf Gläsern und in Skripten stehen.
# molmass versteht nur den Punkt.
_HYDRATE_SEPARATORS = ("·", "•", "*", "×", "x·", " . ", " · ")


def _step(label: str, formula: str, substitution: str, result: str, explanation: str = "") -> dict:
    return {
        "label": label,
        "formula": formula,
        "substitution": substitution,
        "result": result,
        "explanation": explanation,
    }


def _normalize_formula(raw: str) -> str:
    """Bringt die üblichen Hydrat-Schreibweisen auf die Form, die molmass kennt."""
    text = raw.strip()
    for sep in _HYDRATE_SEPARATORS:
        text = text.replace(sep, ".")
    # "CuSO4 . 5 H2O" → "CuSO4.5H2O": Leerzeichen sind hier reine Typografie.
    text = re.sub(r"\s*\.\s*", ".", text)
    return text.replace(" ", "")


def molar_mass(formula: str) -> dict:
    """Molmasse einer Summenformel samt Elementbeitrag.

    Nimmt auch Hydrate (`CuSO4·5H2O`) — der Grund, warum hier molmass statt
    RDKit rechnet: Kristallwasser ist kein Molekül, das sich parsen liesse.
    """
    if not formula or not formula.strip():
        raise ValueError("Please give a chemical formula, e.g. 'NaCl' or 'CuSO4·5H2O'.")

    normalized = _normalize_formula(formula)
    try:
        f = Formula(normalized)
        mass = f.mass
        # composition() verhält sich wie ein Mapping Symbol → CompositionItem;
        # das direkte Iterieren liefert nur die Symbole.
        composition = [
            {
                "symbol": item.symbol,
                "count": int(item.count),
                "mass": float(item.mass),
                "fraction": float(item.fraction),
            }
            for item in f.composition().values()
        ]
    except Exception as exc:  # molmass wirft je nach Fehler verschiedene Typen
        raise ValueError(
            f"'{formula}' is not a formula I can read. Write it as element symbols "
            "with counts, e.g. 'C9H8O4', 'NaCl' or 'CuSO4·5H2O'."
        ) from exc

    return {
        "formula": formula.strip(),
        "normalized": normalized,
        "mass": mass,
        "composition": composition,
    }


def _resolve_molar_mass(substance: str, molar_mass_g: float | None) -> tuple[float, list[dict]]:
    """Molmasse entweder aus der Formel oder direkt übernommen."""
    if molar_mass_g is not None:
        if molar_mass_g <= 0:
            raise ValueError("The molar mass must be greater than zero.")
        return molar_mass_g, [
            _step(
                "Molar mass",
                "M (given)",
                f"M = {molar_mass_g:.4g} g/mol",
                f"{molar_mass_g:.4g} g/mol",
                "Taken from the input, not from a formula.",
            )
        ]

    data = molar_mass(substance)
    parts = " + ".join(
        f"{p['count']}×{p['symbol']}" for p in data["composition"] if p["count"]
    )
    return data["mass"], [
        _step(
            "Molar mass",
            "M = Σ (count × atomic mass)",
            parts,
            f"{data['mass']:.4f} g/mol",
            f"From the formula {data['formula']}.",
        )
    ]


def mass_for_solution(
    substance: str,
    concentration: float,
    volume_ml: float,
    molar_mass_g: float | None = None,
) -> dict:
    """Wie viel wiege ich ein? m = c · V · M — die häufigste Laborrechnung."""
    if volume_ml <= 0:
        raise ValueError("The volume must be greater than zero.")
    if concentration <= 0:
        raise ValueError("The concentration must be greater than zero.")

    m_molar, steps = _resolve_molar_mass(substance, molar_mass_g)
    volume_l = volume_ml / 1000.0
    amount_mol = concentration * volume_l
    mass_g = amount_mol * m_molar

    steps.append(
        _step(
            "Amount of substance",
            "n = c · V",
            f"n = {concentration:.4g} mol/L · {volume_l:.4g} L",
            f"{amount_mol:.6g} mol",
            f"{volume_ml:.4g} mL = {volume_l:.4g} L.",
        )
    )
    steps.append(
        _step(
            "Weighed portion",
            "m = n · M",
            f"m = {amount_mol:.6g} mol · {m_molar:.4f} g/mol",
            f"{mass_g:.4g} g",
        )
    )

    notes = []
    if mass_g < MIN_PRACTICAL_WEIGHT_G:
        notes.append(
            f"{mass_g * 1000:.2f} mg is at or below what an analytical balance "
            "resolves reliably. Weigh a larger portion and dilute instead."
        )

    return {
        "substance": substance,
        "molar_mass": m_molar,
        "concentration": concentration,
        "volume_ml": volume_ml,
        "amount_mol": amount_mol,
        "mass_g": mass_g,
        "steps": steps,
        "notes": notes,
    }


def concentration_from_mass(
    substance: str,
    mass_g: float,
    volume_ml: float,
    molar_mass_g: float | None = None,
    target: float | None = None,
) -> dict:
    """Die Gegenrichtung: eingewogen ist eingewogen — was ist es geworden?

    Die Waage trifft den Sollwert nie exakt; gerechnet wird mit dem Istwert.
    """
    if volume_ml <= 0:
        raise ValueError("The volume must be greater than zero.")
    if mass_g <= 0:
        raise ValueError("The weighed portion must be greater than zero.")

    m_molar, steps = _resolve_molar_mass(substance, molar_mass_g)
    volume_l = volume_ml / 1000.0
    amount_mol = mass_g / m_molar
    concentration = amount_mol / volume_l

    steps.append(
        _step(
            "Amount of substance",
            "n = m / M",
            f"n = {mass_g:.4g} g / {m_molar:.4f} g/mol",
            f"{amount_mol:.6g} mol",
        )
    )
    steps.append(
        _step(
            "Concentration",
            "c = n / V",
            f"c = {amount_mol:.6g} mol / {volume_l:.4g} L",
            f"{concentration:.6g} mol/L",
            f"{volume_ml:.4g} mL = {volume_l:.4g} L.",
        )
    )

    result = {
        "substance": substance,
        "molar_mass": m_molar,
        "mass_g": mass_g,
        "volume_ml": volume_ml,
        "amount_mol": amount_mol,
        "concentration": concentration,
        "steps": steps,
        "notes": [],
    }

    if target is not None:
        if target <= 0:
            raise ValueError("The target concentration must be greater than zero.")
        deviation = (concentration - target) / target * 100.0
        result["target"] = target
        result["deviation_percent"] = deviation
        steps.append(
            _step(
                "Deviation from target",
                "Δ = (c − c_target) / c_target · 100 %",
                f"Δ = ({concentration:.6g} − {target:.6g}) / {target:.6g} · 100 %",
                f"{deviation:+.2f} %",
                "Report the actual concentration, do not round it to the target.",
            )
        )

    return result


def dilution(
    c1: float | None = None,
    v1_ml: float | None = None,
    c2: float | None = None,
    v2_ml: float | None = None,
) -> dict:
    """C1·V1 = C2·V2 — die fehlende der vier Grössen wird berechnet.

    Genau eine darf fehlen; alles andere wäre unterbestimmt.
    """
    given = {"c1": c1, "v1_ml": v1_ml, "c2": c2, "v2_ml": v2_ml}
    missing = [k for k, v in given.items() if v is None]
    if len(missing) != 1:
        raise ValueError(
            "Give exactly three of c1, v1_ml, c2, v2_ml — the fourth is what "
            f"gets calculated. Missing right now: {len(missing)}."
        )
    for key, value in given.items():
        if value is not None and value <= 0:
            raise ValueError(f"{key} must be greater than zero.")

    unknown = missing[0]
    if unknown == "v1_ml":
        v1_ml = c2 * v2_ml / c1
    elif unknown == "c2":
        c2 = c1 * v1_ml / v2_ml
    elif unknown == "v2_ml":
        v2_ml = c1 * v1_ml / c2
    else:
        c1 = c2 * v2_ml / v1_ml

    # Verdünnen heisst dünner werden. Ein umgekehrtes Verhältnis ist kein
    # Rechenfehler, sondern ein Denkfehler — und der gehört benannt.
    if c2 > c1:
        raise ValueError(
            f"The stock solution (c1 = {c1:.4g} mol/L) is weaker than the target "
            f"(c2 = {c2:.4g} mol/L). Diluting cannot make a solution stronger — "
            "check which one is the stock."
        )
    if v1_ml > v2_ml:
        raise ValueError(
            f"The stock portion (v1 = {v1_ml:.4g} mL) is larger than the final "
            f"volume (v2 = {v2_ml:.4g} mL). Check the two volumes."
        )

    solvent_ml = v2_ml - v1_ml
    factor = c1 / c2

    steps = [
        _step(
            "Dilution law",
            "c₁ · V₁ = c₂ · V₂",
            f"{c1:.4g} mol/L · {v1_ml:.4g} mL = {c2:.4g} mol/L · {v2_ml:.4g} mL",
            f"solved for {unknown.replace('_ml', '')}",
            "The amount of substance does not change on dilution.",
        ),
        _step(
            "Solvent to add",
            "V_solvent = V₂ − V₁",
            f"V_solvent = {v2_ml:.4g} mL − {v1_ml:.4g} mL",
            f"{solvent_ml:.4g} mL",
            "Make up to the mark, do not add this volume to a full flask.",
        ),
        _step(
            "Dilution factor",
            "f = c₁ / c₂",
            f"f = {c1:.4g} / {c2:.4g}",
            f"1 : {factor:.4g}",
        ),
    ]

    return {
        "c1": c1,
        "v1_ml": v1_ml,
        "c2": c2,
        "v2_ml": v2_ml,
        "solvent_ml": solvent_ml,
        "factor": factor,
        "solved_for": unknown,
        "steps": steps,
        "notes": [],
    }


def mixing_cross(high: float, low: float, target: float, total: float | None = None) -> dict:
    """Mischungskreuz: zwei Gehalte zu einem Zielgehalt mischen.

    Die Anteile sind Differenzen über Kreuz — welche Einheit die Gehalte haben
    (%, mol/L), ist der Rechnung egal, solange alle drei dieselbe benutzen.
    """
    if high <= low:
        raise ValueError(
            f"The stronger component must be stronger: high = {high:.4g}, "
            f"low = {low:.4g}."
        )
    if not (low <= target <= high):
        raise ValueError(
            f"The target {target:.4g} lies outside {low:.4g} … {high:.4g}. "
            "Mixing two components can only reach values between them."
        )

    parts_high = target - low
    parts_low = high - target
    parts_total = parts_high + parts_low
    if parts_total == 0:
        raise ValueError("high and low are identical — there is nothing to mix.")

    steps = [
        _step(
            "Parts of the strong component",
            "parts_high = target − low",
            f"parts_high = {target:.4g} − {low:.4g}",
            f"{parts_high:.4g} parts",
        ),
        _step(
            "Parts of the weak component",
            "parts_low = high − target",
            f"parts_low = {high:.4g} − {target:.4g}",
            f"{parts_low:.4g} parts",
        ),
        _step(
            "Ratio",
            "high : low",
            f"{parts_high:.4g} : {parts_low:.4g}",
            f"{parts_high:.4g} : {parts_low:.4g}",
            "Cross-wise differences — that is the whole trick.",
        ),
    ]

    result = {
        "high": high,
        "low": low,
        "target": target,
        "parts_high": parts_high,
        "parts_low": parts_low,
        "steps": steps,
        "notes": [],
    }

    if total is not None:
        if total <= 0:
            raise ValueError("The total amount must be greater than zero.")
        amount_high = total * parts_high / parts_total
        amount_low = total * parts_low / parts_total
        result["total"] = total
        result["amount_high"] = amount_high
        result["amount_low"] = amount_low
        steps.append(
            _step(
                "Scaled to the wanted amount",
                "amount = total · parts / (parts_high + parts_low)",
                f"{total:.4g} · {parts_high:.4g} / {parts_total:.4g}",
                f"{amount_high:.4g} of the strong, {amount_low:.4g} of the weak",
            )
        )

    return result
