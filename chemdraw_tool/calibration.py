"""Kalibriergerade: lineare Regression, Güte, Rückrechnung, Nachweisgrenzen.

Reine Mathematik ohne matplotlib und ohne MCP — der Plot liegt daneben in
`calibration_plot`, damit beides einzeln prüfbar bleibt.

Die Rückrechnung ist kein Anhängsel: Eine Kalibriergerade wird gemessen, um
unbekannte Proben zu bestimmen. Steigung und R² allein beantworten keine
Frage, die jemand stellt.
"""

from __future__ import annotations

import math

# DIN 32645, Schnellschätzung über die Reststreuung der Kalibriergeraden.
LOD_FACTOR = 3.3
LOQ_FACTOR = 10.0


def linear_regression(
    x: list[float], y: list[float], through_origin: bool = False
) -> dict:
    """Kleinste Quadrate: y = a·x + b (oder y = a·x durch den Ursprung)."""
    if len(x) != len(y):
        raise ValueError(
            f"x ({len(x)} values) and y ({len(y)} values) must have the same "
            "length — every standard needs exactly one signal."
        )
    if len(x) < 3:
        raise ValueError(
            f"A calibration needs at least three standards, got {len(x)}. "
            "A line always fits two points, so two prove nothing about linearity."
        )
    if max(x) - min(x) == 0:
        raise ValueError(
            "All standards have the same concentration, so the x values do not "
            "differ and no slope can be determined. Vary the concentration."
        )

    n = len(x)
    if through_origin:
        # Ursprungsgerade: a = Σxy / Σx²; sinnvoll, wenn das Verfahren
        # nachweislich keinen Blindwert hat.
        sxx = sum(xi * xi for xi in x)
        sxy = sum(xi * yi for xi, yi in zip(x, y))
        slope = sxy / sxx
        intercept = 0.0
    else:
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        sxx = sum((xi - mean_x) ** 2 for xi in x)
        sxy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        slope = sxy / sxx
        intercept = mean_y - slope * mean_x

    predicted = [slope * xi + intercept for xi in x]
    residuals = [yi - pi for yi, pi in zip(y, predicted)]

    mean_y = sum(y) / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum(r * r for r in residuals)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    # Reststandardabweichung s(y) und daraus die Standardfehler.
    df = n - (1 if through_origin else 2)
    s_y = math.sqrt(ss_res / df) if df > 0 and ss_res > 0 else 0.0

    mean_x = sum(x) / n
    sxx_centered = sum((xi - mean_x) ** 2 for xi in x)
    se_slope = s_y / math.sqrt(sxx_centered) if sxx_centered > 0 else 0.0
    se_intercept = (
        s_y * math.sqrt(1.0 / n + mean_x**2 / sxx_centered)
        if sxx_centered > 0
        else 0.0
    )

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "residuals": residuals,
        "predicted": predicted,
        "s_y": s_y,
        "se_slope": se_slope,
        "se_intercept": se_intercept,
        "n": n,
        "x": list(x),
        "y": list(y),
        "x_min": min(x),
        "x_max": max(x),
        "through_origin": through_origin,
        "equation": (
            f"y = {slope:.6g} · x" + ("" if through_origin else f" + {intercept:.6g}")
        ),
    }


def interpolate(signal: float, regression: dict) -> dict:
    """Signal → Konzentration, mit Warnung bei Extrapolation."""
    slope = regression["slope"]
    if slope == 0:
        raise ValueError(
            "The slope is zero — the signal does not depend on concentration, "
            "so nothing can be read back from it."
        )

    concentration = (signal - regression["intercept"]) / slope

    notes = []
    extrapolated = not (
        regression["x_min"] <= concentration <= regression["x_max"]
    )
    if extrapolated:
        notes.append(
            f"{concentration:.4g} lies outside the calibrated range "
            f"{regression['x_min']:.4g} … {regression['x_max']:.4g}. The line was "
            "never verified there — dilute the sample into the range or extend "
            "the calibration instead of trusting this number."
        )

    # Vertrauensbereich der Rückrechnung, Näherung über den Standardfehler
    # der Steigung. Reicht für die Frage „wie genau ist das?".
    uncertainty = 0.0
    if regression["s_y"] > 0 and slope != 0:
        uncertainty = regression["s_y"] / abs(slope)

    return {
        "signal": signal,
        "concentration": concentration,
        "extrapolated": extrapolated,
        "uncertainty": uncertainty,
        "formula": "x = (y − b) / a",
        "substitution": (
            f"x = ({signal:.6g} − {regression['intercept']:.6g}) "
            f"/ {slope:.6g}"
        ),
        "notes": notes,
    }


def detection_limits(regression: dict) -> dict:
    """Nachweis- und Bestimmungsgrenze aus der Reststreuung (DIN 32645)."""
    slope = regression["slope"]
    s_y = regression["s_y"]

    notes = []
    if s_y == 0 or slope == 0:
        notes.append(
            "The points sit exactly on the line, so there is no residual "
            "scatter to derive a limit from. Real measurements always scatter — "
            "with constructed data these limits have no meaning."
        )
        return {"lod": 0.0, "loq": 0.0, "s_y": s_y, "notes": notes}

    lod = LOD_FACTOR * s_y / abs(slope)
    loq = LOQ_FACTOR * s_y / abs(slope)

    if lod > regression["x_min"]:
        notes.append(
            f"The limit of detection ({lod:.4g}) is above the lowest standard "
            f"({regression['x_min']:.4g}) — that standard is below what the "
            "method can detect and should not anchor the line."
        )

    return {
        "lod": lod,
        "loq": loq,
        "s_y": s_y,
        "formula": "LOD = 3.3 · s(y) / a,  LOQ = 10 · s(y) / a",
        "substitution": f"s(y) = {s_y:.6g}, a = {slope:.6g}",
        "notes": notes,
    }
