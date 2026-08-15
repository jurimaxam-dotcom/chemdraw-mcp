"""Die Rechnungen, die im Praktikum vor jeder Messung stehen.

Geprüft wird nicht nur das Ergebnis, sondern der Rechenweg: Studierende
schreiben ihn ins Formblatt ab, also muss jeder Schritt Formel, eingesetzte
Zahlen und Resultat einzeln ausweisen — ein blosser Zahlenwert wäre für den
Zweck wertlos.

Einheitenkonvention (bewusst die des Laboralltags, nicht die des SI):
Masse in g, Volumen in mL, Konzentration in mol/L.
"""

import pytest

from chemdraw_tool.solution import (
    concentration_from_mass,
    dilution,
    mass_for_solution,
    mixing_cross,
    molar_mass,
)

# --- Molmasse ---------------------------------------------------------------


def test_molar_mass_of_a_plain_formula():
    r = molar_mass("NaCl")
    assert r["mass"] == pytest.approx(58.44, abs=0.01)
    assert r["formula"] == "NaCl"


def test_molar_mass_handles_hydrates():
    """Der eigentliche Grund für molmass: RDKit kann Kristallwasser nicht.

    `CuSO4 · 5 H2O` ist kein parsebares Molekül, steht aber auf jedem
    zweiten Praktikumsglas.
    """
    assert molar_mass("CuSO4.5H2O")["mass"] == pytest.approx(249.68, abs=0.01)


@pytest.mark.parametrize("written", ["CuSO4 * 5 H2O", "CuSO4·5H2O", "CuSO4 . 5H2O"])
def test_molar_mass_accepts_the_notations_students_type(written):
    """Punkt, Malzeichen, Mittelpunkt, Leerzeichen — alles meint dasselbe Salz."""
    assert molar_mass(written)["mass"] == pytest.approx(249.68, abs=0.01)


def test_molar_mass_lists_the_element_contributions():
    """Für die Kontrolle „stimmt meine Summenformel?" braucht es die Aufteilung."""
    parts = {p["symbol"]: p for p in molar_mass("H2O")["composition"]}
    assert parts["O"]["fraction"] == pytest.approx(0.888, abs=0.01)
    assert parts["H"]["count"] == 2


def test_molar_mass_rejects_nonsense_with_a_useful_message():
    with pytest.raises(ValueError, match="Xy9"):
        molar_mass("Xy9")


# --- Einwaage ---------------------------------------------------------------


def test_mass_for_solution_is_the_classic_weighing_task():
    """250 mL einer 0,1 M NaOH-Lösung: m = c · V · M."""
    r = mass_for_solution("NaOH", concentration=0.1, volume_ml=250)
    assert r["mass_g"] == pytest.approx(1.0, abs=0.01)
    assert r["molar_mass"] == pytest.approx(40.0, abs=0.01)


def test_mass_for_solution_shows_every_step():
    r = mass_for_solution("NaOH", concentration=0.1, volume_ml=250)
    labels = [s["label"] for s in r["steps"]]
    assert "Molar mass" in labels
    assert any("Amount" in label for label in labels)
    # Ein Schritt ohne eingesetzte Zahlen taugt nicht zum Abschreiben.
    for step in r["steps"]:
        assert step["formula"] and step["substitution"] and step["result"]


def test_mass_for_solution_accepts_a_molar_mass_directly():
    """Für Stoffe ohne saubere Summenformel (Extrakte, Handelsware)."""
    r = mass_for_solution("Substanz X", concentration=0.5, volume_ml=100, molar_mass_g=200.0)
    assert r["mass_g"] == pytest.approx(10.0, abs=0.001)


def test_mass_for_solution_warns_below_the_balance_resolution():
    """Unter ~10 mg ist die Analysenwaage die Fehlerquelle, nicht die Rechnung."""
    r = mass_for_solution("NaOH", concentration=0.0001, volume_ml=10)
    assert any("balance" in n.lower() or "dilut" in n.lower() for n in r["notes"])


@pytest.mark.parametrize("bad", [0, -1])
def test_mass_for_solution_rejects_nonpositive_volume(bad):
    with pytest.raises(ValueError, match="[Vv]olume"):
        mass_for_solution("NaOH", concentration=0.1, volume_ml=bad)


# --- Konzentration aus Einwaage ---------------------------------------------


def test_concentration_from_mass_is_the_reverse_direction():
    """Eingewogen ist eingewogen — was ist es geworden?"""
    r = concentration_from_mass("NaOH", mass_g=1.0, volume_ml=250)
    assert r["concentration"] == pytest.approx(0.1, abs=0.001)


def test_concentration_from_mass_reports_the_deviation_from_a_target():
    """Die Waage trifft den Sollwert nie exakt — der Istwert zählt."""
    r = concentration_from_mass("NaOH", mass_g=1.0234, volume_ml=250, target=0.1)
    assert r["concentration"] == pytest.approx(0.10234, abs=0.0001)
    assert r["deviation_percent"] == pytest.approx(2.34, abs=0.05)


# --- Verdünnung -------------------------------------------------------------


def test_dilution_solves_for_the_missing_stock_volume():
    """C1·V1 = C2·V2 — wie viel Stammlösung für 100 mL 0,1 M aus 1 M?"""
    r = dilution(c1=1.0, c2=0.1, v2_ml=100)
    assert r["v1_ml"] == pytest.approx(10.0, abs=0.01)
    assert r["solvent_ml"] == pytest.approx(90.0, abs=0.01)


def test_dilution_solves_for_the_resulting_concentration():
    """Andere Richtung: 10 mL 1 M auf 100 mL aufgefüllt — was ist drin?"""
    r = dilution(c1=1.0, v1_ml=10, v2_ml=100)
    assert r["c2"] == pytest.approx(0.1, abs=0.001)


def test_dilution_needs_enough_information():
    """Unterbestimmt ist unterbestimmt — und die Meldung sagt, was fehlt."""
    with pytest.raises(ValueError, match="exactly three"):
        dilution(c1=1.0)


def test_dilution_rejects_concentrating_by_dilution():
    """Verdünnen macht nicht konzentrierter — hier steckt ein Denkfehler."""
    with pytest.raises(ValueError, match="[Ss]tock|c1"):
        dilution(c1=0.1, c2=1.0, v2_ml=100)


def test_dilution_reports_the_factor():
    r = dilution(c1=1.0, c2=0.1, v2_ml=100)
    assert r["factor"] == pytest.approx(10.0, abs=0.01)


# --- Mischungskreuz ---------------------------------------------------------


def test_mixing_cross_gives_the_parts():
    """70 % aus 90 % und 50 %: je 20 Teile — das klassische Kreuz."""
    r = mixing_cross(high=90, low=50, target=70)
    assert r["parts_high"] == pytest.approx(20.0, abs=0.01)
    assert r["parts_low"] == pytest.approx(20.0, abs=0.01)


def test_mixing_cross_scales_to_a_wanted_amount():
    r = mixing_cross(high=90, low=50, target=70, total=200)
    assert r["amount_high"] == pytest.approx(100.0, abs=0.01)
    assert r["amount_low"] == pytest.approx(100.0, abs=0.01)


def test_mixing_cross_rejects_an_unreachable_target():
    """Zwischen 50 und 90 liegt kein 95 — das Kreuz hat keine Lösung."""
    with pytest.raises(ValueError, match="between|zwischen"):
        mixing_cross(high=90, low=50, target=95)


def test_mixing_cross_works_with_water_as_the_low_component():
    """Der häufigste Fall im Labor: verdünnen mit Wasser (0 %)."""
    r = mixing_cross(high=96, low=0, target=70, total=100)
    assert r["amount_high"] == pytest.approx(72.9, abs=0.1)
