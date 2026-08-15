"""Grubbs-Ausreißertest — die Lücke im Rechenweg des Praktikumsformblatts.

Das Formblatt verlangt ausdrücklich: „Einzelgehalt pro Messung, Ausreißer
identifizieren, dann mitteln." `stats.py` konnte bisher t- und F-Test, aber
den Schritt davor nicht — also den, der über die Datenbasis aller folgenden
Zahlen entscheidet.

Grubbs prüft genau einen Wert: den am weitesten vom Mittel entfernten.
Mehrfachanwendung auf dieselbe Reihe ist statistisch unsauber und wird hier
bewusst nicht angeboten.
"""

import pytest

from chemdraw_tool.calculator.stats import grubbs_test


def test_clean_series_has_no_outlier():
    r = grubbs_test([99.8, 100.1, 99.9, 100.2, 100.0])
    assert r["is_outlier"] is False
    assert r["value"] == pytest.approx(100.2, abs=0.01) or r["value"] == pytest.approx(
        99.8, abs=0.01
    )


def test_obvious_outlier_is_found_and_named():
    """Ein Wert weit ausserhalb: der Test muss ihn benennen, nicht nur melden."""
    r = grubbs_test([99.8, 100.1, 99.9, 100.2, 108.5])
    assert r["is_outlier"] is True
    assert r["value"] == pytest.approx(108.5, abs=0.01)
    assert r["index"] == 4


def test_outlier_can_be_the_low_end():
    r = grubbs_test([100.0, 100.1, 99.9, 100.2, 91.0])
    assert r["is_outlier"] is True
    assert r["value"] == pytest.approx(91.0, abs=0.01)


def test_reports_g_and_the_critical_value():
    """Beides gehört ins Protokoll, sonst ist die Entscheidung nicht prüfbar."""
    r = grubbs_test([99.8, 100.1, 99.9, 100.2, 108.5])
    assert r["g_value"] > r["g_critical"]
    assert r["n"] == 5


def test_three_values_is_the_minimum():
    """Unter n=3 ist der Test nicht definiert — das muss er sagen."""
    with pytest.raises(ValueError, match="three|3"):
        grubbs_test([100.0, 101.0])


def test_identical_values_are_not_outliers():
    """Streuung null: kein Ausreisser, und keine Division durch null."""
    r = grubbs_test([100.0, 100.0, 100.0, 100.0])
    assert r["is_outlier"] is False
    assert r["g_value"] == 0.0


def test_borderline_case_stays_below_the_critical_value():
    """Ein leicht abweichender Wert ist noch kein Ausreisser.

    Wichtig, weil ein zu scharfer Test echte Messwerte aussortiert — und
    genau das verfälscht den Gehalt, den er schützen soll.
    """
    r = grubbs_test([99.5, 100.0, 100.2, 100.3, 101.0])
    assert r["is_outlier"] is False


def test_explanation_is_written_for_the_report():
    r = grubbs_test([99.8, 100.1, 99.9, 100.2, 108.5])
    assert "G" in r["explanation"]
    assert r["formula"] and r["substitution"]
