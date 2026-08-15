"""pH-Rechnungen: exakt gelöst, Näherung daneben gestellt.

Der Server zeichnet Titrationskurve und Speziesverteilung längst — die Zahl
dahinter fehlte. Gerechnet wird über dieselbe Ladungsbilanz wie in der Kurve
(`ph_plots.exact_ph`), nicht über die Lehrbuchnäherung. Die Näherung wird
trotzdem mitgeliefert, weil sie in der Klausur verlangt wird; wo beide
auseinanderlaufen, ist genau die Stelle, an der die Näherung ihre Voraussetzung
verliert.

Referenzwerte stammen aus der geschlossenen Lösung bzw. aus Lehrbuchbeispielen
und sind im Test benannt.
"""

import pytest

from chemdraw_tool.ph_calc import (
    buffer_ph,
    buffer_recipe,
    strong_acid_ph,
    strong_base_ph,
    weak_acid_ph,
    weak_base_ph,
)

# --- Schwache Säure ---------------------------------------------------------


def test_acetic_acid_matches_the_textbook_value():
    """0,1 M Essigsäure, pKs 4,76 → pH 2,88 (Standardbeispiel)."""
    r = weak_acid_ph(concentration=0.1, pka=4.76)
    assert r["ph"] == pytest.approx(2.88, abs=0.02)


def test_weak_acid_also_reports_the_approximation():
    r = weak_acid_ph(concentration=0.1, pka=4.76)
    assert r["ph_approx"] == pytest.approx(2.88, abs=0.02)
    assert "½" in r["approx_formula"] or "1/2" in r["approx_formula"]


def test_approximation_breaks_down_for_a_strong_weak_acid():
    """Chloressigsäure (pKs 2,86), stark verdünnt: die Näherung setzt voraus,
    dass kaum dissoziiert wird — hier stimmt das nicht mehr."""
    r = weak_acid_ph(concentration=0.001, pka=2.86)
    assert abs(r["ph"] - r["ph_approx"]) > 0.1
    assert r["approximation_valid"] is False


def test_approximation_is_flagged_valid_when_it_holds():
    r = weak_acid_ph(concentration=0.1, pka=4.76)
    assert r["approximation_valid"] is True


def test_polyprotic_acid_uses_all_pka_values():
    """Phosphorsäure 0,1 M: pH ≈ 1,6 — nur die erste Stufe trägt nennenswert."""
    r = weak_acid_ph(concentration=0.1, pka_values=[2.15, 7.20, 12.35])
    assert r["ph"] == pytest.approx(1.6, abs=0.1)


def test_weak_acid_needs_a_pka():
    with pytest.raises(ValueError, match="pka|pKa"):
        weak_acid_ph(concentration=0.1)


def test_weak_acid_rejects_nonpositive_concentration():
    with pytest.raises(ValueError, match="[Cc]oncentration"):
        weak_acid_ph(concentration=0, pka=4.76)


# --- Schwache Base ----------------------------------------------------------


def test_ammonia_matches_the_textbook_value():
    """0,1 M Ammoniak, pKb 4,75 → pH 11,12."""
    r = weak_base_ph(concentration=0.1, pkb=4.75)
    assert r["ph"] == pytest.approx(11.12, abs=0.03)


def test_weak_base_accepts_the_conjugate_pka_instead():
    """pKs(NH4+) = 9,25 beschreibt dasselbe System wie pKb(NH3) = 4,75."""
    from_pkb = weak_base_ph(concentration=0.1, pkb=4.75)["ph"]
    from_pka = weak_base_ph(concentration=0.1, pka=9.25)["ph"]
    assert from_pkb == pytest.approx(from_pka, abs=0.02)


def test_weak_base_needs_one_of_the_two_constants():
    with pytest.raises(ValueError, match="pkb|pka"):
        weak_base_ph(concentration=0.1)


# --- Puffer -----------------------------------------------------------------


def test_equimolar_buffer_sits_at_the_pka():
    r = buffer_ph(acid_concentration=0.1, base_concentration=0.1, pka=4.76)
    assert r["ph"] == pytest.approx(4.76, abs=0.02)


def test_buffer_shifts_with_the_ratio():
    """Zehnfacher Basenüberschuss → eine pH-Einheit über dem pKs."""
    r = buffer_ph(acid_concentration=0.1, base_concentration=1.0, pka=4.76)
    assert r["ph"] == pytest.approx(5.76, abs=0.05)


def test_buffer_warns_outside_its_working_range():
    """Mehr als 1 : 10 ist kein Puffer mehr — das gehört gesagt."""
    r = buffer_ph(acid_concentration=0.01, base_concentration=1.0, pka=4.76)
    assert any("range" in n.lower() or "ratio" in n.lower() for n in r["notes"])


def test_buffer_reports_the_capacity():
    """Die Pufferkapazität entscheidet, ob der Ansatz taugt."""
    r = buffer_ph(acid_concentration=0.1, base_concentration=0.1, pka=4.76)
    assert r["capacity"] > 0


# --- Pufferansatz -----------------------------------------------------------


def test_buffer_recipe_hits_the_target_ph():
    r = buffer_recipe(target_ph=4.76, pka=4.76, total_concentration=0.1, volume_ml=500)
    assert r["acid_concentration"] == pytest.approx(0.05, abs=0.002)
    assert r["base_concentration"] == pytest.approx(0.05, abs=0.002)


def test_buffer_recipe_gives_amounts_for_the_flask():
    r = buffer_recipe(target_ph=4.76, pka=4.76, total_concentration=0.1, volume_ml=500)
    assert r["acid_mol"] == pytest.approx(0.025, abs=0.001)
    assert r["base_mol"] == pytest.approx(0.025, abs=0.001)


def test_buffer_recipe_converts_to_masses_when_molar_masses_are_given():
    r = buffer_recipe(
        target_ph=4.76,
        pka=4.76,
        total_concentration=0.1,
        volume_ml=500,
        acid_molar_mass=60.05,
        base_molar_mass=82.03,
    )
    assert r["acid_mass_g"] == pytest.approx(1.501, abs=0.01)
    assert r["base_mass_g"] == pytest.approx(2.051, abs=0.01)


def test_buffer_recipe_refuses_an_unreachable_target():
    """Mehr als zwei pH-Einheiten vom pKs entfernt ist kein Puffer."""
    r = buffer_recipe(target_ph=8.0, pka=4.76, total_concentration=0.1, volume_ml=500)
    assert any("pKa" in n or "buffer" in n.lower() for n in r["notes"])


# --- Starke Säuren und Basen ------------------------------------------------


def test_strong_acid_is_the_negative_logarithm():
    assert strong_acid_ph(0.01)["ph"] == pytest.approx(2.0, abs=0.001)


def test_strong_base_uses_the_ion_product():
    assert strong_base_ph(0.01)["ph"] == pytest.approx(12.0, abs=0.001)


def test_very_dilute_strong_acid_does_not_go_alkaline():
    """Die klassische Fangfrage: 1e-8 M HCl ergibt NICHT pH 8.

    Bei dieser Verdünnung liefert das Wasser mehr Protonen als die Säure —
    wer stur −log c rechnet, macht aus Salzsäure eine Lauge.
    """
    r = strong_acid_ph(1e-8)
    assert 6.9 < r["ph"] < 7.0
    assert any("water" in n.lower() for n in r["notes"])


def test_very_dilute_strong_base_does_not_go_acidic():
    r = strong_base_ph(1e-8)
    assert 7.0 < r["ph"] < 7.1
