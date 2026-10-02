"""Aufgabengenerator Gehaltsbestimmung (Produkt „Praktikumsrechner“, 02.10.2026).

Der Wert des Produkts ist, dass jede erzeugte Aufgabe stimmt. Deshalb prüfen
die Tests nicht nur das Format, sondern gegen zwei unabhängige Quellen:
- jeder Äquivalenzfaktor F muss aus M · c / z folgen (und M aus der Summenformel
  per molmass),
- jede Lösung muss mit dem bestehenden Rechenkern
  (`calculator.titration.calculate_gehalt_titration`) übereinstimmen.
"""

import pytest
from molmass import Formula

from chemdraw_tool.aufgaben import titration as t
from chemdraw_tool.calculator.titration import calculate_gehalt_titration

SCHRITT_KEYS = {"label", "formula", "substitution", "result", "explanation"}


@pytest.mark.parametrize("stoff", t.STOFFE, ids=lambda s: s.name)
def test_faktor_folgt_aus_molmasse_konzentration_und_stoechiometrie(stoff):
    assert stoff.faktor == pytest.approx(stoff.molmasse * stoff.c / stoff.z, abs=0.011)


@pytest.mark.parametrize("stoff", t.STOFFE, ids=lambda s: s.name)
def test_molmasse_passt_zur_summenformel(stoff):
    assert Formula(stoff.formel).mass == pytest.approx(stoff.molmasse, abs=0.02)


@pytest.mark.parametrize("seed", range(200))
def test_gehaltsaufgabe_stimmt_mit_dem_rechenkern(seed):
    a = t.gehalt_aufgabe(seed)
    g = a["werte"]
    kern = calculate_gehalt_titration(
        [g["m_mg"]], [g["v_ml"]], g["v_blind_ml"], g["faktor"], g["titer"]
    )[0]["gehalt"]
    assert a["loesung"] == pytest.approx(kern, abs=1e-9)


@pytest.mark.parametrize("seed", range(200))
def test_gehaltsaufgabe_ist_laborplausibel(seed):
    g = t.gehalt_aufgabe(seed)["werte"]
    assert 5.0 <= g["v_ml"] <= 25.0, "Bürette hat 25 mL"
    assert round(g["v_ml"] / 0.05, 6) == round(g["v_ml"] / 0.05), "Ablesung auf 0,05 mL"
    assert 0.97 <= g["titer"] <= 1.03
    assert 96.0 <= t.gehalt_aufgabe(seed)["loesung"] <= 103.0


@pytest.mark.parametrize("seed", range(50))
def test_sollverbrauch_umgekehrt_eingesetzt_ergibt_100_prozent(seed):
    a = t.sollverbrauch_aufgabe(seed)
    g = a["werte"]
    gehalt = g["faktor"] * g["titer"] * a["loesung"] / g["m_mg"] * 100
    assert gehalt == pytest.approx(100.0, abs=1e-9)


@pytest.mark.parametrize("seed", range(50))
def test_faktoraufgabe_loest_nach_m_c_durch_z(seed):
    a = t.faktor_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(g["molmasse"] * g["c"] / g["z"], abs=1e-9)


@pytest.mark.parametrize("bauer", [t.gehalt_aufgabe, t.sollverbrauch_aufgabe, t.faktor_aufgabe])
def test_jede_aufgabe_hat_text_rechenweg_und_toleranz(bauer):
    a = bauer(7)
    assert a["text"] and a["einheit"] and a["toleranz"] > 0
    assert a["rechenweg"], "ohne Rechenweg kein Produkt"
    for schritt in a["rechenweg"]:
        assert set(schritt) == SCHRITT_KEYS


def test_gleicher_seed_gleiche_aufgabe():
    assert t.gehalt_aufgabe(42) == t.gehalt_aufgabe(42)


def test_verschiedene_seeds_verschiedene_aufgaben():
    texte = {t.gehalt_aufgabe(s)["text"] for s in range(30)}
    assert len(texte) > 25


def test_neue_aufgabe_waehlt_typ_nach_seed():
    typen = {t.neue_aufgabe(s)["typ"] for s in range(60)}
    assert typen == {"gehalt", "sollverbrauch", "faktor"}


def test_pruefe_antwort_toleriert_rundung():
    a = t.gehalt_aufgabe(3)
    assert t.pruefe(a, round(a["loesung"], 2))
    assert t.pruefe(a, f"{a['loesung']:.2f}".replace(".", ","))
    assert not t.pruefe(a, a["loesung"] + 1.0)
    assert not t.pruefe(a, "abc")


def test_zahl_und_einheit_brechen_nicht_auseinander():
    texte = " ".join(t.neue_aufgabe(s)["text"] for s in range(60))
    for einheit in ("mL", "mg", "%"):
        assert f"0 {einheit}" not in texte and f"5 {einheit}" not in texte
    assert " %" in texte
