"""`calculate_content`: der komplette Rechenweg einer Gehaltsbestimmung.

Das ist der Weg, den das Praktikumsformblatt vorschreibt, in der Reihenfolge,
in der er dort steht: Einzelgehalt pro Messung → Ausreißer identifizieren →
mitteln → streuen → gegen den Sollwert prüfen. Ein Tool, das nur den
Mittelwert liefert, wäre für den Zweck wertlos.

Die Mathematik selbst liegt in `chemdraw_tool/calculator/` und ist dort
getestet; hier wird geprüft, was im Chat ankommt.
"""

import pytest

from chemdraw_tool.server import calculate_content

# Ascorbinsäure-Titration, wie sie im Praktikum anfällt:
# Faktor 8,806 mg/mL, drei Einwaagen um 250 mg.
WEIGHTS = [251.3, 249.8, 250.6]
VOLUMES = [28.5, 28.3, 28.4]


def test_titration_reports_one_content_per_measurement():
    """Einzelgehalte sind Pflicht — der Mittelwert allein ist nicht prüfbar."""
    out = calculate_content(
        "titration", weights_mg=WEIGHTS, measurements=VOLUMES, factor_mg_per_ml=8.806
    )
    assert out.count("Measurement") >= 3


def test_titration_gives_mean_and_spread():
    out = calculate_content(
        "titration", weights_mg=WEIGHTS, measurements=VOLUMES, factor_mg_per_ml=8.806
    )
    assert "Mean" in out
    assert "RSD" in out or "relative standard deviation" in out.lower()


def test_titration_runs_the_outlier_check():
    """Der Schritt, den das Formblatt ausdrücklich verlangt."""
    out = calculate_content(
        "titration", weights_mg=WEIGHTS, measurements=VOLUMES, factor_mg_per_ml=8.806
    )
    assert "Grubbs" in out or "utlier" in out


def test_an_actual_outlier_is_named_and_flagged():
    out = calculate_content(
        "titration",
        weights_mg=[250.0, 250.0, 250.0, 250.0, 250.0],
        measurements=[28.4, 28.5, 28.3, 28.4, 34.0],
        factor_mg_per_ml=8.806,
    )
    assert "outlier" in out.lower()
    # Der verdächtige Wert muss im Text stehen, sonst ist die Meldung nutzlos.
    assert "34" in out or "119" in out


def test_titer_is_derived_from_reference_measurements():
    """Titerbestimmung gehört zur selben Rechnung, nicht in ein zweites Tool."""
    out = calculate_content(
        "titration",
        weights_mg=WEIGHTS,
        measurements=VOLUMES,
        factor_mg_per_ml=8.806,
        reference_weights_mg=[250.0, 250.2],
        reference_volumes_ml=[28.4, 28.42],
    )
    assert "Titer" in out or "titer" in out


def test_blank_is_subtracted_and_visible():
    plain = calculate_content(
        "titration", weights_mg=WEIGHTS, measurements=VOLUMES, factor_mg_per_ml=8.806
    )
    blanked = calculate_content(
        "titration",
        weights_mg=WEIGHTS,
        measurements=VOLUMES,
        factor_mg_per_ml=8.806,
        blank_ml=0.2,
    )
    assert plain != blanked


def test_photometry_takes_the_absorption_constant_directly():
    """Ohne diesen Parameter waere das Tool auf die eine hinterlegte Substanz
    beschraenkt — A(1%,1cm) steht in jeder Monographie."""
    out = calculate_content(
        "photometry",
        weights_mg=[100.0, 100.5],
        measurements=[0.695, 0.698],
        a1_1cm=695,
        flask_volume_ml=100.0,
        dilution_factor=100.0,
    )
    assert "Mean" in out


def test_content_is_compared_against_the_declared_value():
    out = calculate_content(
        "titration",
        weights_mg=WEIGHTS,
        measurements=VOLUMES,
        factor_mg_per_ml=8.806,
        declared_content=99.0,
    )
    assert "99" in out


def test_titration_without_a_factor_says_what_is_missing():
    with pytest.raises(ValueError, match="factor"):
        calculate_content("titration", weights_mg=WEIGHTS, measurements=VOLUMES)


def test_photometry_without_the_constant_says_what_is_missing():
    with pytest.raises(ValueError, match="a1_1cm|absorption"):
        calculate_content(
            "photometry",
            weights_mg=[100.0],
            measurements=[0.695],
            flask_volume_ml=100.0,
        )


def test_mismatched_list_lengths_are_rejected():
    with pytest.raises(ValueError, match="length|same"):
        calculate_content(
            "titration",
            weights_mg=[250.0, 250.0],
            measurements=[28.4],
            factor_mg_per_ml=8.806,
        )


def test_unknown_method_fails_audibly():
    with pytest.raises(ValueError, match="method"):
        calculate_content("hellsehen", weights_mg=WEIGHTS, measurements=VOLUMES)


def test_output_is_markdown_with_a_heading():
    out = calculate_content(
        "titration", weights_mg=WEIGHTS, measurements=VOLUMES, factor_mg_per_ml=8.806
    )
    assert out.startswith("#")


def test_single_measurement_still_works_but_says_what_is_missing():
    """Eine Messung ist keine Messreihe — Streuung und Tests entfallen."""
    out = calculate_content(
        "titration", weights_mg=[250.0], measurements=[28.4], factor_mg_per_ml=8.806
    )
    assert "%" in out
    assert "one measurement" in out.lower() or "single" in out.lower()


# --- Fettkennzahlen und Karl-Fischer ----------------------------------------
# Eigene Methoden desselben Tools statt eigener Tools: gleiche Eingabeform
# (Einwaage + Ablesung + Blindwert), gleiche Ausgabe (Wert + Statistik).


def test_acid_value_series_gives_value_and_spread():
    out = calculate_content(
        "acid_value",
        weights_mg=[2000.0, 2010.0, 1995.0],
        measurements=[1.5, 1.52, 1.48],
        titrant_concentration=0.1,
    )
    assert "mg KOH/g" in out
    assert "Mean" in out


def test_saponification_uses_the_blank_as_the_reference():
    out = calculate_content(
        "saponification_value",
        weights_mg=[2000.0],
        measurements=[18.0],
        blank_ml=25.0,
        titrant_concentration=0.5,
    )
    assert "98" in out  # 28.05 * 7 / 2 = 98.2


def test_saponification_also_reports_the_ester_value_when_the_acid_value_is_known():
    out = calculate_content(
        "saponification_value",
        weights_mg=[2000.0],
        measurements=[18.0],
        blank_ml=25.0,
        titrant_concentration=0.5,
        known_acid_value=4.2,
    )
    assert "Ester value" in out


def test_iodine_value_names_its_unit():
    out = calculate_content(
        "iodine_value",
        weights_mg=[300.0],
        measurements=[12.0],
        blank_ml=25.0,
        titrant_concentration=0.1,
    )
    assert "I₂/100" in out or "I2/100" in out


def test_karl_fischer_needs_the_titer():
    with pytest.raises(ValueError, match="titer"):
        calculate_content("water_kf", weights_mg=[500.0], measurements=[1.5])


def test_karl_fischer_reports_percent_water():
    out = calculate_content(
        "water_kf",
        weights_mg=[500.0],
        measurements=[1.5],
        titer_mg_per_ml=5.0,
    )
    assert "1.50" in out


def test_back_titration_methods_need_a_blank():
    with pytest.raises(ValueError, match="blank"):
        calculate_content(
            "saponification_value",
            weights_mg=[2000.0],
            measurements=[18.0],
            titrant_concentration=0.5,
        )


def test_fat_value_methods_need_the_titrant_concentration():
    with pytest.raises(ValueError, match="titrant_concentration"):
        calculate_content(
            "acid_value", weights_mg=[2000.0], measurements=[1.5]
        )
