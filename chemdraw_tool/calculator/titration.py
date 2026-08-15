"""Gehalt calculation from titration (acidimetry)."""

from __future__ import annotations

SUBSTANCE_FACTORS: dict[str, float] = {
    "ascorbinsaeure": 8.806,
    "ibuprofen": 20.63,
}


def _validate_paired(name_a: str, a: list, name_b: str, b: list) -> None:
    if len(a) != len(b):
        raise ValueError(
            f"{name_a} ({len(a)} values) and {name_b} ({len(b)} values) "
            f"must have the same length."
        )
    if len(a) == 0:
        raise ValueError(f"{name_a} and {name_b} must not be empty.")


def _validate_positive(name: str, values: list[float]) -> None:
    for i, v in enumerate(values):
        if v <= 0:
            raise ValueError(f"{name}[{i}] = {v} — must be positive.")


def _validate_positive_scalar(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} = {value} — must be positive.")


def calculate_titer(
    ref_einwaagen: list[float],
    ref_volumina: list[float],
    blindwert: float,
    faktor: float,
    soll_gehalt: float = 100.0,
) -> float:
    """Calculate titer from reference titrations.

    Titer = mean(Gehalt_ref) / soll_gehalt.
    """
    _validate_paired("ref_einwaagen", ref_einwaagen, "ref_volumina", ref_volumina)
    _validate_positive("ref_einwaagen", ref_einwaagen)
    _validate_positive("ref_volumina", ref_volumina)
    _validate_positive_scalar("faktor", faktor)
    _validate_positive_scalar("soll_gehalt", soll_gehalt)
    gehalte = []
    for m, v in zip(ref_einwaagen, ref_volumina):
        gehalt = (faktor * (v - blindwert)) / m * 100
        gehalte.append(gehalt)
    mean_gehalt = sum(gehalte) / len(gehalte)
    return mean_gehalt / soll_gehalt


def calculate_gehalt_titration(
    einwaagen: list[float],
    volumina: list[float],
    blindwert: float,
    faktor: float,
    titer: float = 1.0,
) -> list[dict]:
    """Calculate Gehalt% for each titration measurement.

    Returns list of dicts with keys: label, gehalt, formula,
    substitution, result, explanation.
    """
    _validate_paired("einwaagen", einwaagen, "volumina", volumina)
    _validate_positive("einwaagen", einwaagen)
    _validate_positive("volumina", volumina)
    _validate_positive_scalar("faktor", faktor)
    _validate_positive_scalar("titer", titer)
    results = []
    formula = "w = (F · T · (V − V_blind)) / m · 100%"
    explanation = (
        f"F = {faktor} mg/mL is the equivalence factor from the Ph. Eur.: the mg "
        f"of substance that 1 mL of volumetric solution corresponds to. "
        f"T = {titer:.4f} is the titer, the correction factor of that solution. "
        f"V_blank = {blindwert} mL is subtracted from every reading."
    )

    for i, (m, v) in enumerate(zip(einwaagen, volumina), start=1):
        gehalt = (faktor * titer * (v - blindwert)) / m * 100
        substitution = (
            f"w = ({faktor} · {titer:.4f} · ({v} − {blindwert})) / {m} · 100%"
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
