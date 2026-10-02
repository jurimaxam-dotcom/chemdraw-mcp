"""Lösungsrechnen (Allgemeine Chemie, 1. Semester; Praktikumsrechner 02.10.2026).

Stufe 2 der Hebelkarte: Stöchiometrie trifft alle Fächer im 1. Semester. Jede
Lösung wird gegen solution.py (den Rechenkern hinter calculate_solution)
geprüft, jede Molmasse gegen die Summenformel (molmass).
"""

import pytest
from molmass import Formula

from chemdraw_tool import solution
from chemdraw_tool.aufgaben import loesungen as lo

SCHRITT = {"label", "formula", "substitution", "result", "explanation"}


@pytest.mark.parametrize("stoff", lo.EINWAAGE_STOFFE, ids=lambda s: s[0])
def test_molmasse_passt_zur_formel(stoff):
    name, formel, m = stoff
    assert Formula(formel).mass == pytest.approx(m, abs=0.02)


@pytest.mark.parametrize("seed", range(150))
def test_einwaage_wie_der_rechenkern(seed):
    a = lo.einwaage_aufgabe(seed)
    g = a["werte"]
    kern = solution.mass_for_solution("x", g["c"], g["v_ml"], molar_mass_g=g["M"])["mass_g"]
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)


@pytest.mark.parametrize("seed", range(150))
def test_verduennung_wie_der_rechenkern(seed):
    a = lo.verduennung_aufgabe(seed)
    g = a["werte"]
    kern = solution.dilution(c1=g["c1"], c2=g["c2"], v2_ml=g["v2_ml"])["v1_ml"]
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)
    assert g["c1"] > g["c2"]


@pytest.mark.parametrize("seed", range(150))
def test_mischungskreuz_wie_der_rechenkern(seed):
    a = lo.mischkreuz_aufgabe(seed)
    g = a["werte"]
    kern = solution.mixing_cross(g["hoch"], g["tief"], g["ziel"], total=g["gesamt"])["amount_high"]
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)


@pytest.mark.parametrize("seed", range(100))
def test_konzentrierte_saeure_c_aus_w_rho_m(seed):
    a = lo.konz_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(g["w"] / 100 * g["rho"] * 1000 / g["M"], rel=1e-9)


@pytest.mark.parametrize("bauer", [lo.einwaage_aufgabe, lo.verduennung_aufgabe, lo.mischkreuz_aufgabe, lo.konz_aufgabe])
def test_aufgabe_vollstaendig(bauer):
    a = bauer(4)
    assert a["text"] and a["rechenweg"] and a["toleranz"] > 0
    for s in a["rechenweg"]:
        assert set(s) == SCHRITT


def test_neue_aufgabe_mischt_vier_typen():
    assert {lo.neue_aufgabe(s)["typ"] for s in range(80)} == {"einwaage", "verduennung", "mischkreuz", "konz"}
