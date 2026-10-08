"""Pharmakokinetik-Aufgaben (Pharmakologie, Praktikumsrechner 03.10.2026).

Jede Lösung wird gegen `chemdraw_tool.pk` geprüft — dieselben Formeln wie in
`calculate_pharmacokinetics` und in den Kurven. Wirkstoff X ist fiktiv: die Werte sind
Übungszahlen, keine Wirkstoffdaten.
"""


import pytest

from chemdraw_tool import ph_calc, pk
from chemdraw_tool.aufgaben import pharmakokinetik as pa
from chemdraw_tool.aufgaben.basis import de, pruefe

SCHRITT = {"label", "formula", "substitution", "result", "explanation"}
TR = "taschenrechner"  # Hilfsmittel TI-84 Plus CE-T: optionaler Tastenweg je Schritt
TYPEN = {
    "halbwertszeit": pa.halbwertszeit_aufgabe,
    "iv_c": pa.konzentration_aufgabe,
    "css": pa.steady_state_aufgabe,
    "aufsaettigung": pa.aufsaettigung_aufgabe,
    "akkumulation": pa.akkumulation_aufgabe,
    "ionisation": pa.ionisation_aufgabe,
    "tangente": pa.tangente_aufgabe,
}


@pytest.mark.parametrize("typ,bauer", sorted(TYPEN.items()))
@pytest.mark.parametrize("seed", range(120))
def test_grundform_jeder_aufgabe(typ, bauer, seed):
    a = bauer(seed)
    assert a["typ"] == typ
    for feld in ("text", "gesucht", "einheit", "loesung", "toleranz", "werte", "rechenweg"):
        assert feld in a, f"{typ}: Feld {feld} fehlt"
    assert a["toleranz"] > 0
    assert a["rechenweg"] and all(set(s) - {TR} == SCHRITT for s in a["rechenweg"])
    # die richtige Antwort wird in deutscher und englischer Schreibweise angenommen
    assert pruefe(a, de(a["loesung"], 4))
    assert pruefe(a, f"{a['loesung']:.4f}")
    # deutlich daneben — vom Betrag weg, sonst trifft x·1,2 + 1 bei negativen Lösungen fast wieder x
    assert not pruefe(a, de(a["loesung"] * 1.2 + (1 if a["loesung"] >= 0 else -1), 4))
    assert "Wirkstoff X" in a["text"] or typ == "ionisation"
    assert bauer(seed)["text"] == a["text"], "gleicher Seed muss dieselbe Aufgabe geben"


@pytest.mark.parametrize("seed", range(120))
def test_halbwertszeit_wie_der_rechenkern(seed):
    a = pa.halbwertszeit_aufgabe(seed)
    g = a["werte"]
    kern = pk.resolve(vd=g["vd"], cl=g["cl"])["t_half"]
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)
    assert 0.5 <= a["loesung"] <= 80, "unsinnige Halbwertszeit für eine Übungsaufgabe"


@pytest.mark.parametrize("seed", range(120))
def test_konzentration_nach_i_v_gabe(seed):
    a = pa.konzentration_aufgabe(seed)
    g = a["werte"]
    kern = pk.c_iv(g["dose"], g["vd"], pk.ke_from_half_life(g["t_half"]), g["t"])
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)
    assert a["loesung"] >= 0.05, "Konzentration zu klein, um sinnvoll abgefragt zu werden"


@pytest.mark.parametrize("seed", range(120))
def test_steady_state_wie_der_rechenkern(seed):
    a = pa.steady_state_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(pk.css_avg(g["dose"], g["f"], g["cl"], g["tau"]), rel=1e-9)


@pytest.mark.parametrize("seed", range(120))
def test_aufsaettigungsdosis_wie_der_rechenkern(seed):
    a = pa.aufsaettigung_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(pk.loading_dose(g["target"], g["vd"], g["f"]), rel=1e-9)


@pytest.mark.parametrize("seed", range(120))
def test_akkumulation_wie_der_rechenkern(seed):
    a = pa.akkumulation_aufgabe(seed)
    g = a["werte"]
    assert a["loesung"] == pytest.approx(pk.accumulation(pk.ke_from_half_life(g["t_half"]), g["tau"]), rel=1e-9)
    assert a["loesung"] > 1


@pytest.mark.parametrize("seed", range(120))
def test_ionisation_wie_der_rechenkern(seed):
    a = pa.ionisation_aufgabe(seed)
    g = a["werte"]
    kern = ph_calc.ionisation(pka=g["pka"], ph=g["ph"], kind=g["art"])["fraction_unionised"] * 100
    assert a["loesung"] == pytest.approx(kern, rel=1e-9)
    assert 2 <= a["loesung"] <= 98, "Extremwerte sind als Rechenaufgabe sinnlos"
    assert abs(g["pka"] - g["ph"]) <= 2.5


def test_gemischte_aufgabe_deckt_alle_typen_ab_und_ist_reproduzierbar():
    typen = {pa.neue_aufgabe(s)["typ"] for s in range(200)}
    assert typen == set(TYPEN)
    assert pa.neue_aufgabe(7)["text"] == pa.neue_aufgabe(7)["text"]


@pytest.mark.parametrize("typ,bauer", sorted(TYPEN.items()))
def test_aufgaben_sind_abwechslungsreich(typ, bauer):
    assert len({bauer(s)["text"] for s in range(120)}) >= 25, f"{typ}: zu wenig Varianten"


def test_rechenweg_nennt_das_ergebnis_der_aufgabe():
    """Der letzte Schritt trägt die Lösung als Zahl (deutsches Komma) — sonst widerspricht der Weg der Antwort."""
    for bauer in TYPEN.values():
        for seed in range(30):
            a = bauer(seed)
            ende = a["rechenweg"][-1]["result"]
            assert any(ch.isdigit() for ch in ende)
            gerundet = de(a["loesung"], 2)
            assert gerundet in ende or de(a["loesung"], 3) in ende or de(a["loesung"], 1) in ende or de(a["loesung"], 4) in ende, (
                f"{bauer.__name__} Seed {seed}: Ergebnis {gerundet} steht nicht im letzten Schritt: {ende}"
            )


@pytest.mark.parametrize("typ,bauer", sorted(TYPEN.items()))
def test_jeder_schritt_hat_den_tastenweg_fuer_den_ti84(typ, bauer):
    """Hilfsmittel (Biopharmazie-Klausur: TI-84 Plus CE-T zugelassen): jeder Schritt sagt, was man tippt."""
    for seed in range(30):
        for s in bauer(seed)["rechenweg"]:
            assert s.get(TR), f"{typ} Seed {seed}: Schritt „{s['label']}“ ohne Tastenweg"
            assert all(isinstance(z, str) and z.strip() for z in s[TR])


@pytest.mark.parametrize("seed", range(30))
def test_tastenweg_tippt_zahlen_mit_punkt(seed):
    """Der TI kennt kein Dezimalkomma — eine getippte 0,0714 wäre ein Syntaxfehler."""
    import re

    for bauer in TYPEN.values():
        for s in bauer(seed)["rechenweg"]:
            for zeile in s[TR]:
                getippt = zeile.split("→")[0]  # rechts vom Pfeil steht die Anzeige/Erklärung
                assert not re.search(r"\d,\d", getippt), f"Komma im Tastenweg: {zeile}"


@pytest.mark.parametrize("seed", range(120))
def test_tangente_ist_die_ableitung_der_konzentrationskurve(seed):
    a = pa.tangente_aufgabe(seed)
    g = a["werte"]
    ke = pk.ke_from_half_life(g["t_half"])
    c = pk.c_iv(g["dose"], g["vd"], ke, g["t"])
    assert a["loesung"] == pytest.approx(-ke * c, rel=1e-9)
    assert a["loesung"] < 0, "Konzentration fällt — die Tangente muss negativ steigen"
    # numerische Gegenprobe: Differenzenquotient wie nDeriv( auf dem TI
    h = 1e-4
    num = (pk.c_iv(g["dose"], g["vd"], ke, g["t"] + h) - pk.c_iv(g["dose"], g["vd"], ke, g["t"] - h)) / (2 * h)
    assert a["loesung"] == pytest.approx(num, rel=1e-6)


def test_tangente_zeigt_den_zeichnen_weg_mit_geradengleichung():
    tasten = " ".join(z for s in pa.tangente_aufgabe(3)["rechenweg"] for z in s[TR])
    for muss in ("[2nd] [prgm]", "5:Tangente(", "[graph]", "6:dy/dx", "y ="):
        assert muss in tasten, f"Tastenweg ohne {muss}"
