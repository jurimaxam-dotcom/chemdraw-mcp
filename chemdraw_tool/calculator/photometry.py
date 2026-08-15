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
    a1pct1cm: float | None = None,
    path_length_cm: float = 1.0,
    wavelength_nm: float | None = None,
    solvent: str = "",
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
            f"einwaagen ({len(einwaagen)} values) and absorptionen "
            f"({len(absorptionen)} values) must have the same length."
        )
    if len(einwaagen) == 0:
        raise ValueError("einwaagen and absorptionen must not be empty.")
    for i, m in enumerate(einwaagen):
        if m <= 0:
            raise ValueError(f"einwaagen[{i}] = {m} — must be positive.")
    for i, a in enumerate(absorptionen):
        if a < 0:
            raise ValueError(f"absorptionen[{i}] = {a} — must not be negative.")
    for name, val in (
        ("verduennungsfaktor", verduennungsfaktor),
        ("kolbenvolumen_ml", kolbenvolumen_ml),
    ):
        if val <= 0:
            raise ValueError(f"{name} = {val} — must be positive.")
    # A(1%,1cm) direkt übergeben schlägt die Tabelle: die Konstante steht in
    # jeder Monographie, die Tabelle kennt nur eine Handvoll Substanzen. Ohne
    # diesen Weg wäre die Funktion auf genau diese Handvoll beschränkt.
    if a1pct1cm is not None:
        if a1pct1cm <= 0:
            raise ValueError(f"a1pct1cm = {a1pct1cm} — must be positive.")
        if path_length_cm <= 0:
            raise ValueError(f"path_length_cm = {path_length_cm} — must be positive.")
        a1pct = a1pct1cm
        d = path_length_cm
        measured_at = f" at {wavelength_nm} nm" if wavelength_nm else ""
        in_solvent = f", measured in {solvent}" if solvent else ""
    else:
        if substance not in SUBSTANCE_CONSTANTS:
            erlaubt = ", ".join(sorted(SUBSTANCE_CONSTANTS.keys()))
            raise ValueError(
                f"Unknown substance: {substance!r}. Known values: {erlaubt}. "
                "Alternatively pass a1pct1cm directly — the monograph has it."
            )
        consts = SUBSTANCE_CONSTANTS[substance]
        a1pct = consts["a1pct1cm"]
        d = consts["path_length_cm"]
        measured_at = f" at {consts['wavelength_nm']} nm"
        in_solvent = f", measured in {consts['solvent']}"

    formula = "w = (A · VF · V_Kolben) / (A¹%₁cm · d · m) · 1000"
    explanation = (
        f"A = absorbance measured{measured_at}. "
        f"A¹%₁cm = {a1pct} is the specific absorbance (absorbance of a 1 % "
        f"solution at 1 cm path length{in_solvent}). "
        f"VF = {verduennungsfaktor} is the dilution factor. "
        f"V_flask = {kolbenvolumen_ml} mL."
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
                "label": f"Content, measurement {i}",
                "gehalt": gehalt,
                "formula": formula,
                "substitution": substitution,
                "result": f"{gehalt:.2f} %",
                "explanation": explanation if i == 1 else "",
            }
        )
    return results
