"""Gehalt calculation from UV photometry (Beer-Lambert)."""

from __future__ import annotations

SUBSTANCE_CONSTANTS: dict[str, dict] = {
    "ascorbinsaeure": {
        "a1pct1cm": 695,
        "wavelength_nm": 245,
        "path_length_cm": 1.0,
        "solvent": "HCl 0,1 mol/L",
    },
}


def calculate_gehalt_uv(
    einwaagen: list[float],
    absorptionen: list[float],
    substance: str,
    verduennungsfaktor: float,
    kolbenvolumen_ml: float,
) -> list[dict]:
    """Calculate Gehalt% from UV absorption measurements.

    Beer-Lambert derivation:
    A1%1cm is the absorption of a 1% (= 10 mg/mL) solution at 1 cm path length.
    c [g/100mL] = A / (A1%1cm × d)
    c [mg/mL] = c × 10

    Gehalt = (c_cuvette × VF × V_kolben) / Einwaage × 100%
           = (A × VF × V_kolben) / (A1%1cm × d × m) × 1000

    The factor 1000 = 10 (g/100mL → mg/mL) × 100 (fraction → percentage).

    Returns list of dicts with keys: label, gehalt, formula,
    substitution, result, explanation.
    """
    if len(einwaagen) != len(absorptionen):
        raise ValueError(
            f"einwaagen ({len(einwaagen)} Werte) und absorptionen "
            f"({len(absorptionen)} Werte) müssen gleich lang sein."
        )
    if len(einwaagen) == 0:
        raise ValueError("einwaagen und absorptionen dürfen nicht leer sein.")
    for i, m in enumerate(einwaagen):
        if m <= 0:
            raise ValueError(f"einwaagen[{i}] = {m} — muss positiv sein.")
    for i, a in enumerate(absorptionen):
        if a < 0:
            raise ValueError(f"absorptionen[{i}] = {a} — darf nicht negativ sein.")
    for name, val in (
        ("verduennungsfaktor", verduennungsfaktor),
        ("kolbenvolumen_ml", kolbenvolumen_ml),
    ):
        if val <= 0:
            raise ValueError(f"{name} = {val} — muss positiv sein.")
    if substance not in SUBSTANCE_CONSTANTS:
        erlaubt = ", ".join(sorted(SUBSTANCE_CONSTANTS.keys()))
        raise ValueError(
            f"Unbekannte Substanz: {substance!r}. Erlaubte Werte: {erlaubt}."
        )

    consts = SUBSTANCE_CONSTANTS[substance]
    a1pct = consts["a1pct1cm"]
    d = consts["path_length_cm"]

    formula = "w = (A · VF · V_Kolben) / (A¹%₁cm · d · m) · 1000"
    explanation = (
        f"A = gemessene Absorption bei {consts['wavelength_nm']} nm. "
        f"A¹%₁cm = {a1pct} ist die spezifische Absorption "
        f"(Absorption einer 1%igen Lösung bei 1 cm Schichtdicke, "
        f"gemessen in {consts['solvent']}). "
        f"VF = {verduennungsfaktor} ist der Verdünnungsfaktor. "
        f"V_Kolben = {kolbenvolumen_ml} mL."
    )

    results = []
    for i, (m, a) in enumerate(zip(einwaagen, absorptionen), start=1):
        gehalt = a * verduennungsfaktor * kolbenvolumen_ml / (a1pct * d * m) * 1000
        substitution = (
            f"w = ({a} · {verduennungsfaktor} · {kolbenvolumen_ml}) "
            f"/ ({a1pct} · {d} · {m}) · 1000"
        )
        results.append(
            {
                "label": f"Gehalt Analyse {i}",
                "gehalt": gehalt,
                "formula": formula,
                "substitution": substitution,
                "result": f"{gehalt:.2f} %",
                "explanation": explanation if i == 1 else "",
            }
        )
    return results
