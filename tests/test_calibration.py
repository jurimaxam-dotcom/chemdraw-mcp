"""Kalibriergerade: Regression, Güte, Rückrechnung unbekannter Proben.

Die Regression allein beantwortet keine Frage, die jemand stellt. Gefragt wird
„ich habe Absorption 0,42 gemessen — wie viel ist das?" Deshalb steht die
Rückrechnung hier gleichberechtigt neben Steigung und Bestimmtheitsmaß.

Referenzwerte: exakt konstruierte Datensätze (y = 2x + 1 usw.), damit ein
Fehler in der Formel sofort auffällt statt sich in Rundung zu verstecken.
"""

import pytest

from chemdraw_tool.calibration import (
    detection_limits,
    interpolate,
    linear_regression,
)

# y = 2x + 1, exakt
X = [1.0, 2.0, 3.0, 4.0, 5.0]
Y = [3.0, 5.0, 7.0, 9.0, 11.0]


def test_regression_finds_the_exact_line():
    r = linear_regression(X, Y)
    assert r["slope"] == pytest.approx(2.0, abs=1e-9)
    assert r["intercept"] == pytest.approx(1.0, abs=1e-9)


def test_perfect_data_has_r_squared_one():
    assert linear_regression(X, Y)["r_squared"] == pytest.approx(1.0, abs=1e-9)


def test_scatter_lowers_r_squared():
    noisy = [3.1, 4.8, 7.2, 8.9, 11.1]
    assert linear_regression(X, noisy)["r_squared"] < 1.0


def test_regression_reports_residuals_per_point():
    """Ein einzelner Ausreißer ist in den Residuen sichtbar, in R² kaum."""
    r = linear_regression(X, [3.0, 5.0, 7.0, 9.0, 12.0])
    assert len(r["residuals"]) == 5
    assert abs(r["residuals"][-1]) > abs(r["residuals"][0])


def test_regression_reports_standard_errors():
    r = linear_regression(X, [3.1, 4.8, 7.2, 8.9, 11.1])
    assert r["se_slope"] > 0
    assert r["se_intercept"] > 0


def test_regression_through_origin_forces_the_intercept():
    r = linear_regression(X, Y, through_origin=True)
    assert r["intercept"] == 0.0
    assert r["slope"] > 0


def test_regression_needs_at_least_three_points():
    """Durch zwei Punkte geht immer eine Gerade — das ist keine Kalibrierung."""
    with pytest.raises(ValueError, match="three"):
        linear_regression([1.0, 2.0], [3.0, 5.0])


def test_regression_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        linear_regression([1.0, 2.0, 3.0], [3.0, 5.0])


def test_regression_rejects_a_constant_x():
    """Alle Standards gleich konzentriert: keine Steigung bestimmbar."""
    with pytest.raises(ValueError, match="differ|constant"):
        linear_regression([1.0, 1.0, 1.0], [3.0, 5.0, 7.0])


# --- Rückrechnung -----------------------------------------------------------


def test_interpolate_inverts_the_line():
    r = linear_regression(X, Y)
    assert interpolate(7.0, r)["concentration"] == pytest.approx(3.0, abs=1e-9)


def test_interpolate_warns_outside_the_calibrated_range():
    """Extrapolation ist der häufigste stille Fehler der Analytik."""
    r = linear_regression(X, Y)
    high = interpolate(25.0, r)
    assert high["extrapolated"] is True
    assert any("range" in n.lower() for n in high["notes"])


def test_interpolate_inside_the_range_is_not_flagged():
    r = linear_regression(X, Y)
    assert interpolate(7.0, r)["extrapolated"] is False


def test_interpolate_refuses_a_zero_slope():
    r = linear_regression([1.0, 2.0, 3.0], [5.0, 5.0, 5.0])
    with pytest.raises(ValueError, match="slope"):
        interpolate(5.0, r)


# --- Nachweis- und Bestimmungsgrenze ----------------------------------------


def test_detection_limits_follow_from_the_residual_scatter():
    """NWG = 3,3 · s(y) / Steigung, BG = 10 · s(y) / Steigung."""
    r = linear_regression(X, [3.1, 4.8, 7.2, 8.9, 11.1])
    limits = detection_limits(r)
    assert limits["lod"] > 0
    assert limits["loq"] == pytest.approx(limits["lod"] * 10 / 3.3, rel=0.01)


def test_detection_limits_are_undefined_for_perfect_data():
    """Ohne Streuung gibt es keine Grenze — das zu sagen ist ehrlicher als 0."""
    limits = detection_limits(linear_regression(X, Y))
    assert limits["lod"] == 0.0
    assert any("scatter" in n.lower() or "residual" in n.lower() for n in limits["notes"])
