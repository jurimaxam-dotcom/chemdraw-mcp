"""SN1/SN2/E1/E2-Entscheider (Praktikumsrechner, Stufe 2, 02.10.2026).

Nur Fälle, die jedes Lehrbuch gleich beantwortet. Die Erwartung steht hier als
eigene Tabelle — eine zweite Formulierung der Regeln, damit ein Fehler in der
Generator-Tabelle nicht unbemerkt durchrutscht.
"""

import pytest

from chemdraw_tool.aufgaben import mechanismus as m

ERWARTET = {
    ("methyl", "nuc"): "SN2",
    ("methyl", "base"): "SN2",
    ("methyl", "sperrig"): "SN2",
    ("primaer", "nuc"): "SN2",
    ("primaer", "base"): "SN2",
    ("primaer", "sperrig"): "E2",
    ("sekundaer", "nuc"): "SN2",
    ("sekundaer", "base"): "E2",
    ("sekundaer", "sperrig"): "E2",
    ("tertiaer", "base"): "E2",
    ("tertiaer", "sperrig"): "E2",
    ("tertiaer", "solvolyse_kalt"): "SN1",
    ("tertiaer", "solvolyse_warm"): "E1",
}


@pytest.mark.parametrize("seed", range(300))
def test_antwort_folgt_den_lehrbuchregeln(seed):
    a = m.weg_aufgabe(seed)
    assert (a["werte"]["klasse"], a["werte"]["reagenz"]) in ERWARTET, "unklarer Fall erzeugt"
    assert a["loesung"] == ERWARTET[(a["werte"]["klasse"], a["werte"]["reagenz"])]


def test_alle_eindeutigen_faelle_kommen_vor():
    gesehen = {(m.weg_aufgabe(s)["werte"]["klasse"], m.weg_aufgabe(s)["werte"]["reagenz"]) for s in range(600)}
    assert gesehen == set(ERWARTET)


def test_aufgabe_hat_auswahl_und_begruendung():
    a = m.weg_aufgabe(3)
    assert a["auswahl"] == ["SN1", "SN2", "E1", "E2"]
    assert a["loesung"] in a["auswahl"]
    assert len(a["rechenweg"]) >= 3
    for s in a["rechenweg"]:
        assert set(s) == {"label", "formula", "substitution", "result", "explanation"}


def test_pruefe_auswahl_ohne_ruecksicht_auf_schreibweise():
    from chemdraw_tool.aufgaben.basis import pruefe

    a = m.weg_aufgabe(5)
    assert pruefe(a, a["loesung"])
    assert pruefe(a, a["loesung"].lower().replace("n", "N ", 1))
    falsch = next(x for x in a["auswahl"] if x != a["loesung"])
    assert not pruefe(a, falsch)


def test_sperrige_base_nennt_hofmann():
    for s in range(300):
        a = m.weg_aufgabe(s)
        if (a["werte"]["reagenz_name"] == "Kalium-tert-butanolat" and a["loesung"] == "E2"
                and a["werte"]["klasse"] != "primaer" and a["werte"]["substrat"] not in m.SYMMETRISCH):
            assert "Hofmann" in " ".join(x["explanation"] for x in a["rechenweg"])
            return
    pytest.fail("kein Fall sperrige Base + E2 an sek./tert. Substrat gezogen")


def test_symmetrisches_substrat_behauptet_keine_regioselektivitaet():
    for s in range(400):
        a = m.weg_aufgabe(s)
        if a["werte"]["substrat"] in m.SYMMETRISCH:
            text = " ".join(x["explanation"] for x in a["rechenweg"])
            assert "Hofmann" not in text and "Saytzeff" not in text


def test_kein_cyanid_bei_den_eindeutigen_faellen():
    assert all("cyanid" not in m.weg_aufgabe(s)["werte"]["reagenz_name"].lower() for s in range(300))


def test_dbu_behauptet_kein_hofmann_produkt():
    for s in range(400):
        a = m.weg_aufgabe(s)
        if a["werte"]["reagenz_name"] == "DBU":
            assert "Hofmann" not in " ".join(x["explanation"] for x in a["rechenweg"])


def test_kein_iodid_an_iodalkan():
    """1-Iodbutan + NaI tauscht Iod gegen Iod — keine Aufgabe (Screenshot 02.10.)."""
    for s in range(600):
        w = m.weg_aufgabe(s)["werte"]
        assert not ("Iod" in w["substrat"] and w["reagenz_name"] == "Natriumiodid"), s
