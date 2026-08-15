"""Fettkennzahlen und Karl-Fischer — Ph.-Eur.-Arithmetik nach dem Muster von
`titration.py`.

Die Zahlenwerte sind gegen die Kurzformeln des Arzneibuchs geprüft, die für
die jeweilige Standardmaßlösung gelten (z. B. IZ = 1,269 · ΔV / m für 0,1 M
Thiosulfat). Gerechnet wird hier aber allgemein mit der tatsächlichen
Konzentration, damit auch eine 0,05 M Lösung richtig gerechnet wird — die
Kurzformel ist nur der Sonderfall.
"""

import pytest

from chemdraw_tool.calculator.fat_values import (
    acid_value,
    ester_value,
    iodine_value,
    saponification_value,
    water_content_kf,
)

# --- Säurezahl --------------------------------------------------------------


def test_acid_value_matches_the_pharmacopoeia_short_formula():
    """SZ = 5,610 · V / m für 0,1 M KOH (V in mL, m in g)."""
    r = acid_value(sample_g=2.0, volume_ml=1.5, concentration=0.1)
    assert r["value"] == pytest.approx(5.610 * 1.5 / 2.0, abs=0.01)


def test_acid_value_scales_with_the_actual_concentration():
    """Halbe Konzentration, halber Wert — die Kurzformel gilt nur für 0,1 M."""
    weak = acid_value(sample_g=2.0, volume_ml=1.5, concentration=0.05)
    strong = acid_value(sample_g=2.0, volume_ml=1.5, concentration=0.1)
    assert weak["value"] == pytest.approx(strong["value"] / 2, abs=0.001)


def test_acid_value_carries_its_unit_and_working():
    r = acid_value(sample_g=2.0, volume_ml=1.5, concentration=0.1)
    assert "mg KOH/g" in r["unit"]
    assert r["formula"] and r["substitution"]


# --- Verseifungszahl --------------------------------------------------------


def test_saponification_value_uses_the_blank_difference():
    """VZ = 28,05 · (V_blind − V_probe) / m für 0,5 M HCl."""
    r = saponification_value(
        sample_g=2.0, blank_ml=25.0, sample_ml=18.0, concentration=0.5
    )
    assert r["value"] == pytest.approx(28.05 * (25.0 - 18.0) / 2.0, abs=0.05)


def test_saponification_rejects_a_sample_above_the_blank():
    """Die Probe kann nicht weniger verbrauchen als der Blindwert freilässt —
    das ist ein vertauschtes Wertepaar, kein Messergebnis."""
    with pytest.raises(ValueError, match="blank"):
        saponification_value(
            sample_g=2.0, blank_ml=18.0, sample_ml=25.0, concentration=0.5
        )


# --- Esterzahl --------------------------------------------------------------


def test_ester_value_is_the_difference():
    r = ester_value(saponification=190.0, acid=1.5)
    assert r["value"] == pytest.approx(188.5, abs=0.01)


def test_ester_value_rejects_an_acid_above_the_saponification_value():
    with pytest.raises(ValueError, match="acid|saponification"):
        ester_value(saponification=1.0, acid=5.0)


# --- Iodzahl ----------------------------------------------------------------


def test_iodine_value_matches_the_short_formula():
    """IZ = 1,269 · (V_blind − V_probe) / m für 0,1 M Thiosulfat."""
    r = iodine_value(sample_g=0.3, blank_ml=25.0, sample_ml=12.0, concentration=0.1)
    assert r["value"] == pytest.approx(1.269 * (25.0 - 12.0) / 0.3, abs=0.1)


def test_iodine_value_reports_grams_of_iodine_per_hundred_grams():
    r = iodine_value(sample_g=0.3, blank_ml=25.0, sample_ml=12.0, concentration=0.1)
    assert "100" in r["unit"]


# --- Karl Fischer -----------------------------------------------------------


def test_water_content_from_titer_and_volume():
    """1,5 mL einer Lösung mit T = 5,0 mg/mL in 500 mg Probe → 1,5 %."""
    r = water_content_kf(sample_mg=500.0, volume_ml=1.5, titer_mg_per_ml=5.0)
    assert r["value"] == pytest.approx(1.5, abs=0.01)
    assert r["water_mg"] == pytest.approx(7.5, abs=0.01)


def test_water_content_subtracts_the_drift():
    """Die Drift des Titrators zaehlt nicht als Probenwasser."""
    plain = water_content_kf(sample_mg=500.0, volume_ml=1.5, titer_mg_per_ml=5.0)
    drifted = water_content_kf(
        sample_mg=500.0, volume_ml=1.5, titer_mg_per_ml=5.0, blank_ml=0.1
    )
    assert drifted["value"] < plain["value"]


def test_water_content_rejects_a_blank_above_the_reading():
    with pytest.raises(ValueError, match="blank"):
        water_content_kf(
            sample_mg=500.0, volume_ml=0.05, titer_mg_per_ml=5.0, blank_ml=0.1
        )


# --- Gemeinsame Zusagen -----------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda: acid_value(sample_g=0, volume_ml=1.5, concentration=0.1),
        lambda: iodine_value(
            sample_g=0, blank_ml=25.0, sample_ml=12.0, concentration=0.1
        ),
        lambda: water_content_kf(sample_mg=0, volume_ml=1.5, titer_mg_per_ml=5.0),
    ],
)
def test_zero_sample_is_rejected_everywhere(call):
    """Division durch die Einwaage — null ist kein Messwert, sondern ein Tippfehler."""
    with pytest.raises(ValueError):
        call()
