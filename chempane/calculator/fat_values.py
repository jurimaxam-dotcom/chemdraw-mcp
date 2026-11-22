"""Fettkennzahlen (SZ, VZ, EZ, IZ) und Karl-Fischer-Wassergehalt.

Reine Arithmetik nach dem Muster von `titration.py`: Jede Funktion liefert
Wert, Einheit und den Rechenweg mit eingesetzten Zahlen.

Bewusst allgemein gerechnet — mit der tatsächlichen Konzentration der
Maßlösung, nicht mit den Kurzformeln des Arzneibuchs. Die Kurzformeln
(SZ = 5,610·V/m, VZ = 28,05·ΔV/m, IZ = 1,269·ΔV/m) sind darin als Sonderfall
für die jeweilige Standardlösung enthalten; wer mit einer 0,05 M Lösung
arbeitet, bekommt hier trotzdem den richtigen Wert.
"""

from __future__ import annotations

# Molmasse KOH: die Kennzahlen sind als mg KOH pro g Fett definiert.
M_KOH = 56.106
# Molmasse Iod (I2) — die Iodzahl zählt g Iod pro 100 g Fett.
M_I2 = 253.809


def _positive(value: float, name: str) -> float:
    if value is None or value <= 0:
        raise ValueError(f"{name} = {value!r} — must be greater than zero.")
    return value


def _result(value: float, unit: str, formula: str, substitution: str, explanation: str) -> dict:
    return {
        "value": value,
        "unit": unit,
        "formula": formula,
        "substitution": substitution,
        "result": f"{value:.2f} {unit}",
        "explanation": explanation,
    }


def acid_value(sample_g: float, volume_ml: float, concentration: float = 0.1) -> dict:
    """Säurezahl: mg KOH, die die freien Säuren in 1 g Fett neutralisieren."""
    _positive(sample_g, "sample_g")
    _positive(concentration, "concentration")
    if volume_ml < 0:
        raise ValueError(f"volume_ml = {volume_ml} — must not be negative.")

    value = volume_ml * concentration * M_KOH / sample_g
    return _result(
        value,
        "mg KOH/g",
        "AV = V · c · M(KOH) / m",
        f"AV = {volume_ml:g} mL · {concentration:g} mol/L · {M_KOH:g} g/mol "
        f"/ {sample_g:g} g",
        "The free fatty acids present. A rising acid value means the fat is "
        "going rancid — it is the freshness measure of the monograph.",
    )


def saponification_value(
    sample_g: float,
    blank_ml: float,
    sample_ml: float,
    concentration: float = 0.5,
) -> dict:
    """Verseifungszahl: mg KOH, die 1 g Fett vollständig verseifen."""
    _positive(sample_g, "sample_g")
    _positive(concentration, "concentration")
    if sample_ml > blank_ml:
        raise ValueError(
            f"The sample consumed more titrant ({sample_ml:g} mL) than the blank "
            f"({blank_ml:g} mL). Back titration works the other way round — the "
            "sample uses up alkali, so it needs LESS acid than the blank. Check "
            "whether the two readings were swapped."
        )

    delta = blank_ml - sample_ml
    value = delta * concentration * M_KOH / sample_g
    return _result(
        value,
        "mg KOH/g",
        "SV = (V_blank − V_sample) · c · M(KOH) / m",
        f"SV = ({blank_ml:g} − {sample_ml:g}) mL · {concentration:g} mol/L · "
        f"{M_KOH:g} g/mol / {sample_g:g} g",
        "Back titration: the blank shows how much alkali was offered, the "
        "sample how much is left. The difference was consumed by the fat.",
    )


def ester_value(saponification: float, acid: float) -> dict:
    """Esterzahl: der Anteil der Verseifungszahl, der auf Ester entfällt."""
    if acid > saponification:
        raise ValueError(
            f"The acid value ({acid:g}) is larger than the saponification value "
            f"({saponification:g}). The saponification value covers free acids "
            "AND esters, so it can never be the smaller of the two — one of the "
            "two determinations is off."
        )
    value = saponification - acid
    return _result(
        value,
        "mg KOH/g",
        "EV = SV − AV",
        f"EV = {saponification:g} − {acid:g}",
        "Saponification consumes alkali for free acids and for esters; "
        "subtracting the free acids leaves the ester share.",
    )


def iodine_value(
    sample_g: float,
    blank_ml: float,
    sample_ml: float,
    concentration: float = 0.1,
) -> dict:
    """Iodzahl: g Iod, die sich an 100 g Fett addieren — das Maß für
    Doppelbindungen."""
    _positive(sample_g, "sample_g")
    _positive(concentration, "concentration")
    if sample_ml > blank_ml:
        raise ValueError(
            f"The sample consumed more thiosulfate ({sample_ml:g} mL) than the "
            f"blank ({blank_ml:g} mL). The sample binds iodine, so less is left "
            "to titrate — check whether the readings were swapped."
        )

    delta = blank_ml - sample_ml
    # Thiosulfat reagiert 2 : 1 mit Iod: 2 S2O3^2- + I2 -> S4O6^2- + 2 I-.
    mol_i2 = delta / 1000.0 * concentration / 2.0
    value = mol_i2 * M_I2 / sample_g * 100.0
    return _result(
        value,
        "g I₂/100 g",
        "IV = (V_blank − V_sample) · c / 2 · M(I₂) / m · 100",
        f"IV = ({blank_ml:g} − {sample_ml:g}) mL · {concentration:g} mol/L / 2 · "
        f"{M_I2:g} g/mol / {sample_g:g} g · 100",
        "Two thiosulfate ions per iodine molecule — that factor 2 is the step "
        "most often forgotten. A high iodine value means many double bonds, "
        "hence a drying oil rather than a solid fat.",
    )


def water_content_kf(
    sample_mg: float,
    volume_ml: float,
    titer_mg_per_ml: float,
    blank_ml: float = 0.0,
) -> dict:
    """Karl-Fischer-Wassergehalt in Prozent."""
    _positive(sample_mg, "sample_mg")
    _positive(titer_mg_per_ml, "titer_mg_per_ml")
    if blank_ml > volume_ml:
        raise ValueError(
            f"The blank ({blank_ml:g} mL) is larger than the reading "
            f"({volume_ml:g} mL). Then the drift alone would account for more "
            "water than was found — the sample was probably too small."
        )

    net_ml = volume_ml - blank_ml
    water_mg = net_ml * titer_mg_per_ml
    value = water_mg / sample_mg * 100.0
    return {
        **_result(
            value,
            "% (m/m)",
            "w(H₂O) = (V − V_blank) · T / m · 100 %",
            f"w = ({volume_ml:g} − {blank_ml:g}) mL · {titer_mg_per_ml:g} mg/mL "
            f"/ {sample_mg:g} mg · 100 %",
            "T is the titer of the KF reagent in mg water per mL — it drifts, "
            "so it is redetermined before the run, and the blank covers the "
            "moisture the apparatus itself pulls in.",
        ),
        "water_mg": water_mg,
    }
