"""Pure statistics functions — no chemistry knowledge."""

from __future__ import annotations

import math


def descriptive_stats(
    values: list[float],
    true_value: float | None = None,
) -> dict[str, float]:
    """Calculate descriptive statistics for a set of measurements.

    Returns dict with: mean, std_abs, std_rel, variance,
    and optionally recovery and rel_deviation if true_value is given.
    """
    if not values:
        raise ValueError("values must not be empty.")
    n = len(values)
    mean = sum(values) / n

    if n > 1:
        ss = sum((x - mean) ** 2 for x in values)
        variance = ss / (n - 1)
        std_abs = math.sqrt(variance)
    else:
        variance = 0.0
        std_abs = 0.0

    std_rel = (std_abs / mean * 100) if mean != 0 else 0.0

    result = {
        "mean": mean,
        "std_abs": std_abs,
        "std_rel": std_rel,
        "variance": variance,
    }

    if true_value is not None and true_value != 0:
        result["recovery"] = mean / true_value * 100
        result["rel_deviation"] = abs(mean - true_value) / true_value * 100

    return result


# Two-tailed t-distribution critical values at alpha=0.05
# Key: degrees of freedom, Value: t_critical
_T_CRITICAL = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    25: 2.060,
    30: 2.042,
}

# F-distribution critical values at alpha=0.05
# Key: (df_numerator, df_denominator), Value: F_critical
_F_CRITICAL = {
    (1, 1): 161.4,
    (1, 2): 18.51,
    (1, 3): 10.13,
    (1, 4): 7.709,
    (1, 5): 6.608,
    (2, 1): 199.5,
    (2, 2): 19.00,
    (2, 3): 9.552,
    (2, 4): 6.944,
    (2, 5): 5.786,
    (3, 1): 215.7,
    (3, 2): 19.16,
    (3, 3): 9.277,
    (3, 4): 6.591,
    (3, 5): 5.409,
    (4, 1): 224.6,
    (4, 2): 19.25,
    (4, 3): 9.117,
    (4, 4): 6.388,
    (4, 5): 5.192,
    (5, 1): 230.2,
    (5, 2): 19.30,
    (5, 3): 9.013,
    (5, 4): 6.256,
    (5, 5): 5.050,
    (5, 6): 4.387,
    (5, 7): 3.972,
    (5, 8): 3.687,
    (5, 9): 3.482,
    (5, 10): 3.326,
    (6, 5): 4.950,
    (6, 6): 4.284,
    (7, 5): 4.876,
    (7, 7): 3.787,
}


def _lookup_t_critical(df: int) -> float:
    if df in _T_CRITICAL:
        return _T_CRITICAL[df]
    # Conservative: use next-lower df (higher t_critical)
    for d in sorted(_T_CRITICAL.keys(), reverse=True):
        if d <= df:
            return _T_CRITICAL[d]
    return _T_CRITICAL[1]


def _lookup_f_critical(df1: int, df2: int) -> float:
    if (df1, df2) in _F_CRITICAL:
        return _F_CRITICAL[(df1, df2)]
    best_key = min(
        _F_CRITICAL.keys(),
        key=lambda k: abs(k[0] - df1) + abs(k[1] - df2),
    )
    return _F_CRITICAL[best_key]


def one_sample_t_test(values: list[float], mu: float) -> dict[str, float | bool]:
    """One-sample t-test: is the mean significantly different from mu?"""
    if not values:
        raise ValueError("values must not be empty.")
    n = len(values)
    stats = descriptive_stats(values)
    mean = stats["mean"]
    s = stats["std_abs"]

    if s == 0 or n < 2:
        return {"t_value": 0.0, "t_critical": 0.0, "df": n - 1, "passed": mean == mu}

    t_value = abs(mean - mu) / (s / math.sqrt(n))
    df = n - 1
    t_critical = _lookup_t_critical(df)

    return {
        "t_value": t_value,
        "t_critical": t_critical,
        "df": df,
        "passed": t_value < t_critical,
    }


def f_test(values1: list[float], values2: list[float]) -> dict[str, float | bool]:
    """F-test: are the variances of two samples equal?"""
    if not values1 or not values2:
        raise ValueError("Both value lists must contain at least one value.")
    s1 = descriptive_stats(values1)
    s2 = descriptive_stats(values2)

    var1 = s1["variance"]
    var2 = s2["variance"]

    if var2 == 0 and var1 == 0:
        return {"f_value": 1.0, "f_critical": 1.0, "passed": True}

    if var1 >= var2:
        f_value = var1 / var2 if var2 > 0 else float("inf")
        df1, df2 = len(values1) - 1, len(values2) - 1
    else:
        f_value = var2 / var1 if var1 > 0 else float("inf")
        df1, df2 = len(values2) - 1, len(values1) - 1

    f_critical = _lookup_f_critical(df1, df2)

    return {
        "f_value": f_value,
        "f_critical": f_critical,
        "df1": df1,
        "df2": df2,
        "passed": f_value < f_critical,
    }


def welch_t_test(values1: list[float], values2: list[float]) -> dict[str, float | bool]:
    """Welch's t-test: are the means of two samples equal?"""
    if not values1 or not values2:
        raise ValueError("Both value lists must contain at least one value.")
    s1 = descriptive_stats(values1)
    s2 = descriptive_stats(values2)
    n1, n2 = len(values1), len(values2)

    var1, var2 = s1["variance"], s2["variance"]
    se = math.sqrt(var1 / n1 + var2 / n2) if (var1 + var2) > 0 else 0.0

    if se == 0:
        return {"t_value": 0.0, "t_critical": 0.0, "df": 1, "passed": True}

    t_value = abs(s1["mean"] - s2["mean"]) / se

    numerator = (var1 / n1 + var2 / n2) ** 2
    denominator = (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
    df = int(numerator / denominator) if denominator > 0 else 1

    t_critical = _lookup_t_critical(df)

    return {
        "t_value": t_value,
        "t_critical": t_critical,
        "df": df,
        "passed": t_value < t_critical,
    }


# Kritische Werte des Grubbs-Tests (zweiseitig, alpha = 0,05).
# Schlüssel: Stichprobenumfang n. Quelle: ISO 5725-2 / Grubbs (1969).
_GRUBBS_CRITICAL = {
    3: 1.155,
    4: 1.481,
    5: 1.715,
    6: 1.887,
    7: 2.020,
    8: 2.126,
    9: 2.215,
    10: 2.290,
    11: 2.355,
    12: 2.412,
    13: 2.462,
    14: 2.507,
    15: 2.549,
    16: 2.585,
    17: 2.620,
    18: 2.651,
    19: 2.681,
    20: 2.709,
}


def _lookup_grubbs_critical(n: int) -> float:
    if n in _GRUBBS_CRITICAL:
        return _GRUBBS_CRITICAL[n]
    # Über der Tabelle: den grössten bekannten Wert nehmen. Konservativ in die
    # sichere Richtung — der Test wird strenger, verwirft also seltener einen
    # echten Messwert.
    largest = max(_GRUBBS_CRITICAL)
    return _GRUBBS_CRITICAL[largest] if n > largest else _GRUBBS_CRITICAL[3]


def grubbs_test(values: list[float], alpha: float = 0.05) -> dict:
    """Grubbs test for a single outlier: G = |x_suspect − mean| / s.

    Checks the one value farthest from the mean — the only value the test is
    defined for. Repeating it on the same series after removing a hit is
    statistically unsound, so this returns one verdict, not a cleaned list.

    Returns the verdict plus formula, substitution and explanation, so the
    decision can be written into a lab report and checked by someone else.
    """
    if len(values) < 3:
        raise ValueError(
            f"The Grubbs test needs at least three values, got {len(values)}. "
            "With fewer measurements an outlier cannot be told apart from spread."
        )
    if alpha != 0.05:
        raise ValueError(
            "Only alpha = 0.05 is tabulated here; pass 0.05 or extend "
            "_GRUBBS_CRITICAL with the values you need."
        )

    n = len(values)
    stats = descriptive_stats(values)
    mean = stats["mean"]
    s = stats["std_abs"]

    # Grösster Abstand zum Mittelwert — index() würde bei doppelten Werten den
    # falschen Treffer liefern, deshalb über die Position suchen.
    index = max(range(n), key=lambda i: abs(values[i] - mean))
    suspect = values[index]
    deviation = abs(suspect - mean)

    if s == 0:
        # Alle Werte gleich: kein Ausreisser, und keine Division durch null.
        return {
            "value": suspect,
            "index": index,
            "n": n,
            "mean": mean,
            "std_abs": s,
            "g_value": 0.0,
            "g_critical": _lookup_grubbs_critical(n),
            "is_outlier": False,
            "formula": "G = |x − x̄| / s",
            "substitution": "s = 0 — all values are identical",
            "explanation": (
                "All measurements are identical, so there is no spread and no "
                "outlier."
            ),
        }

    g_value = deviation / s
    g_critical = _lookup_grubbs_critical(n)
    is_outlier = g_value > g_critical

    if is_outlier:
        explanation = (
            f"G = {g_value:.3f} > G_crit = {g_critical:.3f} (n = {n}, α = 0.05): "
            f"{suspect:.4g} is an outlier. Exclude it, then recalculate mean and "
            "standard deviation from the remaining values — and say so in the report."
        )
    else:
        explanation = (
            f"G = {g_value:.3f} ≤ G_crit = {g_critical:.3f} (n = {n}, α = 0.05): "
            f"{suspect:.4g} is the most deviating value but not an outlier. "
            "Keep all measurements."
        )

    return {
        "value": suspect,
        "index": index,
        "n": n,
        "mean": mean,
        "std_abs": s,
        "g_value": g_value,
        "g_critical": g_critical,
        "is_outlier": is_outlier,
        "formula": "G = |x − x̄| / s",
        "substitution": f"G = |{suspect:.4g} − {mean:.4g}| / {s:.4g}",
        "explanation": explanation,
    }
