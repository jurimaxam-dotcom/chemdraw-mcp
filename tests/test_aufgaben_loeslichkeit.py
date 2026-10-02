"""Löslichkeitsprodukt (Quali-Klausur, 1. Semester; Praktikumsrechner 02.10.2026).

Der KL-Wert steht in jeder Aufgabe — die Lösung hängt also nicht an einem
Tabellenwert, sondern nur an der Stöchiometrie. Geprüft wird gegen eine
unabhängige numerische Lösung (Bisektion von KL = (x·L + c_x)^x · (y·L + c_y)^y).
"""

import pytest

from chemdraw_tool.aufgaben import loeslichkeit as l


def _numerisch(kl, x, y, c_kat=0.0, c_an=0.0):
    lo, hi = 0.0, 10.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if (x * mid + c_kat) ** x * (y * mid + c_an) ** y > kl:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


@pytest.mark.parametrize("seed", range(150))
def test_loeslichkeit_aus_kl_stimmt_numerisch(seed):
    a = l.loeslichkeit_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(_numerisch(g["kl"], g["x"], g["y"]), rel=1e-6)


@pytest.mark.parametrize("seed", range(150))
def test_kl_aus_loeslichkeit_rueckwaerts(seed):
    a = l.kl_aufgabe(seed)
    g = a["werte"]
    assert _numerisch(a["loesung"], g["x"], g["y"]) == pytest.approx(g["L"], rel=1e-6)


@pytest.mark.parametrize("seed", range(150))
def test_gleichioniger_zusatz_naeherung_haelt(seed):
    a = l.zusatz_aufgabe(seed)
    g = a["werte"]
    exakt = _numerisch(g["kl"], g["x"], g["y"], g.get("c_kat", 0.0), g.get("c_an", 0.0))
    assert a["loesung"] == pytest.approx(exakt, rel=0.02), "Näherung c_zusatz ≫ x·L muss halten"


@pytest.mark.parametrize("bauer", [l.loeslichkeit_aufgabe, l.kl_aufgabe, l.zusatz_aufgabe])
def test_aufgabe_hat_text_rechenweg_und_relative_toleranz(bauer):
    a = bauer(2)
    assert a["text"] and a["rechenweg"] and 0 < a["toleranz"] <= 0.03 * a["loesung"]
    for s in a["rechenweg"]:
        assert set(s) == {"label", "formula", "substitution", "result", "explanation"}


def test_pruefe_nimmt_wissenschaftliche_schreibweise():
    from chemdraw_tool.aufgaben.basis import pruefe

    a = l.loeslichkeit_aufgabe(1)
    assert pruefe(a, f"{a['loesung']:.3e}")
    assert pruefe(a, f"{a['loesung']:.3e}".replace(".", ",").replace("e", "E"))
    assert pruefe(a, f"{a['loesung']:.2e}".replace("e", " · 10^").replace(".", ","))


def test_neue_aufgabe_mischt():
    assert {l.neue_aufgabe(s)["typ"] for s in range(60)} == {"loeslichkeit", "kl", "zusatz"}


@pytest.mark.parametrize("seed", range(100))
def test_angezeigte_loeslichkeit_ist_die_gerechnete(seed):
    """Text zeigte 1,5 · 10⁻⁵, gerechnet wurde mit 1,47 · 10⁻⁵ (Befund 02.10.)."""
    a = l.kl_aufgabe(seed)
    L = a["werte"]["L"]
    gezeigt = l.sci(L, 3)
    assert gezeigt in a["text"]
    from chemdraw_tool.aufgaben.basis import zahl

    assert zahl(gezeigt.replace("⁻", "-").translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")).replace(" · 10", "e")) == pytest.approx(L)
