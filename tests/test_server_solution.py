"""Das `calculate_solution`-Tool: Zahl UND abschreibbarer Rechenweg.

Reines Text-Tool (Markdown), also kein Panel und keine Fünf-Glieder-Kette.
Geprüft wird, was im Chat ankommt — die Mathematik selbst liegt in
`tests/test_solution_math.py`.
"""

import pytest

from chemdraw_tool.server import calculate_solution


def test_weigh_in_answers_the_question_and_shows_the_way():
    out = calculate_solution("weigh_in", substance="NaOH", concentration=0.1, volume_ml=250)
    assert "1.0" in out or "1 g" in out
    # Der Rechenweg ist der Zweck, nicht die Zugabe.
    assert "n = c · V" in out
    assert "m = n · M" in out
    assert "39.99" in out  # Molmasse NaOH, nicht auf 40 gerundet


def test_weigh_in_names_the_substance_and_the_target():
    out = calculate_solution("weigh_in", substance="NaCl", concentration=0.5, volume_ml=100)
    assert "NaCl" in out
    assert "0.5" in out
    assert "100" in out


def test_hydrate_formula_survives_the_tool_layer():
    out = calculate_solution(
        "weigh_in", substance="CuSO4·5H2O", concentration=0.1, volume_ml=1000
    )
    assert "249" in out


def test_molar_mass_topic_lists_the_elements():
    out = calculate_solution("molar_mass", substance="C9H8O4")
    assert "180" in out
    assert "C" in out and "H" in out and "O" in out
    assert "%" in out  # Massenanteile


def test_concentration_topic_reports_the_actual_value_and_deviation():
    out = calculate_solution(
        "concentration", substance="NaOH", mass_g=1.0234, volume_ml=250, target=0.1
    )
    assert "0.102" in out
    assert "+2.3" in out or "2.34" in out


def test_dilution_topic_gives_stock_portion_and_solvent():
    out = calculate_solution(
        "dilution", stock_concentration=1.0, final_concentration=0.1, final_volume_ml=100
    )
    assert "10" in out
    assert "90" in out
    assert "1 : 10" in out or "1:10" in out


def test_mixing_topic_gives_the_two_amounts():
    out = calculate_solution("mixing", high=96, low=0, target=70, total=100)
    assert "72.9" in out or "72,9" in out


def test_low_weight_warning_reaches_the_user():
    out = calculate_solution("weigh_in", substance="NaOH", concentration=0.0001, volume_ml=10)
    assert "balance" in out.lower()


def test_unknown_topic_fails_audibly():
    with pytest.raises(ValueError, match="topic"):
        calculate_solution("gibtsnicht", substance="NaOH")


def test_weigh_in_without_a_substance_says_what_is_missing():
    """Fehlende Pflichtangaben nennen, statt mit Nullen zu rechnen."""
    with pytest.raises(ValueError, match="substance|formula"):
        calculate_solution("weigh_in", concentration=0.1, volume_ml=250)


def test_dilution_denies_the_impossible_direction():
    with pytest.raises(ValueError, match="[Ss]tock|stronger|weaker"):
        calculate_solution(
            "dilution", stock_concentration=0.1, final_concentration=1.0, final_volume_ml=100
        )


def test_output_is_markdown_with_a_heading():
    out = calculate_solution("weigh_in", substance="NaOH", concentration=0.1, volume_ml=250)
    assert out.startswith("#")
