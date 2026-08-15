"""`calculate_ph`: die Zahl zu den pH-Diagrammen, die der Server längst zeichnet."""

import pytest

from chemdraw_tool.server import calculate_ph


def test_weak_acid_gives_the_ph_and_both_routes():
    out = calculate_ph("weak_acid", concentration=0.1, pka=4.76)
    assert "2.88" in out
    assert "pKa" in out
    # Näherung und exakter Wert nebeneinander — das ist der Lerninhalt.
    assert "approx" in out.lower() or "½" in out


def test_weak_acid_flags_a_broken_approximation():
    out = calculate_ph("weak_acid", concentration=0.001, pka=2.86)
    assert "no longer holds" in out or "approximation" in out.lower()


def test_polyprotic_acid_takes_a_list():
    out = calculate_ph("weak_acid", concentration=0.1, pka_values=[2.15, 7.20, 12.35])
    assert "1.6" in out


def test_weak_base_from_pkb():
    out = calculate_ph("weak_base", concentration=0.1, pkb=4.75)
    assert "11.1" in out


def test_buffer_reports_ph_ratio_and_capacity():
    out = calculate_ph(
        "buffer", acid_concentration=0.1, base_concentration=0.1, pka=4.76
    )
    assert "4.76" in out
    assert "capacity" in out.lower()


def test_buffer_recipe_gives_something_you_can_weigh():
    out = calculate_ph(
        "buffer_recipe",
        target_ph=4.76,
        pka=4.76,
        total_concentration=0.1,
        volume_ml=500,
        acid_molar_mass=60.05,
        base_molar_mass=82.03,
    )
    assert "1.50" in out
    assert "2.05" in out
    assert "g" in out


def test_buffer_recipe_without_molar_masses_still_gives_moles():
    out = calculate_ph(
        "buffer_recipe", target_ph=7.2, pka=7.2, total_concentration=0.1, volume_ml=1000
    )
    assert "mol" in out


def test_strong_acid_dilute_case_carries_the_warning():
    out = calculate_ph("strong_acid", concentration=1e-8)
    assert "6.9" in out
    assert "water" in out.lower()


def test_strong_base_works():
    out = calculate_ph("strong_base", concentration=0.01)
    assert "12" in out


def test_missing_pka_says_so():
    with pytest.raises(ValueError, match="pka|pKa"):
        calculate_ph("weak_acid", concentration=0.1)


def test_unknown_topic_fails_audibly():
    with pytest.raises(ValueError, match="topic"):
        calculate_ph("saurewerden", concentration=0.1)


def test_output_is_markdown_with_a_heading():
    out = calculate_ph("weak_acid", concentration=0.1, pka=4.76)
    assert out.startswith("#")
