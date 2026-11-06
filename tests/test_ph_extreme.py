"""Regressionen: Die Ladungsbilanz darf die pH-Achse nicht als Suchgrenze nutzen."""

import math

import pytest

from chemdraw_tool import ph_calc
from chemdraw_tool.ph_core import exact_ph
from chemdraw_tool.ph_plots import titration_curve
from chemdraw_tool.server import calculate_ph


@pytest.mark.parametrize("concentration,pka", [(5.0, 0.5), (10.0, -1.0)])
def test_concentrated_acid_matches_independent_quadratic(concentration, pka):
    # Ohne Wasser: h² + Ka·h − Ka·c = 0. Bei h > 1 M ist Kw/h
    # weit unter der Testtoleranz; keine zweite Kopie der Bisektion.
    ka = 10 ** -pka
    h = 2 * ka * concentration / (ka + math.sqrt(ka * ka + 4 * ka * concentration))
    expected = -math.log10(h)
    assert exact_ph([pka], concentration, 0) == pytest.approx(expected, abs=1e-10)
    assert ph_calc.weak_acid_ph(concentration, pka=pka)["ph"] == pytest.approx(expected)
    assert f"**pH = {expected:.2f}**" in calculate_ph(
        topic="weak_acid", concentration=concentration, pka=pka
    )


def test_concentrated_base_and_curve_share_unclipped_balance():
    acid = ph_calc.weak_acid_ph(5.0, pka=0.5)["ph"]
    base = ph_calc.weak_base_ph(5.0, pkb=0.5)["ph"]
    assert base > 14
    assert base == pytest.approx(14 - acid, abs=1e-10)
    assert "**pH = 14.05**" in calculate_ph(topic="weak_base", concentration=5.0, pkb=0.5)
    curve = titration_curve(
        pka_values=[0.5], c_acid=5.0, v_acid_ml=25.0,
        c_titrant=5.0,
    )
    assert curve.ph[0] == pytest.approx(acid)
    assert curve.ph[0] < 0


@pytest.mark.parametrize("topic,kwargs", [
    ("weak_acid", {"concentration": 5.0, "pka": 0.5}),
    ("weak_base", {"concentration": 5.0, "pkb": 0.5}),
    ("strong_acid", {"concentration": 2.0}),
    ("strong_base", {"concentration": 2.0}),
    ("buffer", {"acid_concentration": 5.0, "base_concentration": 5.0, "pka": -1.0}),
])
def test_outside_usual_range_is_explained_in_tool_text(topic, kwargs):
    text = calculate_ph(topic=topic, **kwargs)
    assert "outside 0–14" in text
    assert "activities" in text
