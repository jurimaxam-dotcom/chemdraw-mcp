"""pH- und Pufferaufgaben (Praktikumsrechner, 02.10.2026).

Verlangt wird, was die Klausur verlangt: die Näherungsformel. Damit sie nicht
falsch unterrichtet, zieht der Generator nur Fälle, in denen die Näherung
gilt — geprüft gegen die exakte Ladungsbilanz aus `ph_calc` (zweite, unabhängige
Rechnung).
"""

import pytest

from chemdraw_tool import ph_calc
from chemdraw_tool.aufgaben import ph

SCHRITT_KEYS = {"label", "formula", "substitution", "result", "explanation"}
N = range(150)


@pytest.mark.parametrize("seed", N)
def test_schwache_saeure_naeherung_stimmt_mit_ladungsbilanz(seed):
    a = ph.saeure_aufgabe(seed)
    g = a["werte"]
    exakt = ph_calc.weak_acid_ph(g["c"], pka=g["pks"])["ph"]
    assert a["loesung"] == pytest.approx(exakt, abs=0.05)


@pytest.mark.parametrize("seed", N)
def test_schwache_base_naeherung_stimmt_mit_ladungsbilanz(seed):
    a = ph.base_aufgabe(seed)
    g = a["werte"]
    exakt = ph_calc.weak_base_ph(g["c"], pkb=g["pkb"])["ph"]
    assert a["loesung"] == pytest.approx(exakt, abs=0.05)


@pytest.mark.parametrize("seed", N)
def test_starke_saeure_oder_base(seed):
    a = ph.stark_aufgabe(seed)
    g = a["werte"]
    fn = ph_calc.strong_acid_ph if g["saeure"] else ph_calc.strong_base_ph
    assert a["loesung"] == pytest.approx(fn(g["c"])["ph"], abs=0.02)


@pytest.mark.parametrize("seed", N)
def test_puffer_henderson_hasselbalch_stimmt_mit_ladungsbilanz(seed):
    a = ph.puffer_aufgabe(seed)
    g = a["werte"]
    exakt = ph_calc.buffer_ph(g["c_saeure"], g["c_base"], g["pks"])["ph"]
    assert a["loesung"] == pytest.approx(exakt, abs=0.05)
    assert abs(a["loesung"] - g["pks"]) <= 1.0, "nur im Pufferbereich"


@pytest.mark.parametrize("seed", N)
def test_pufferverhaeltnis_eingesetzt_ergibt_ziel_ph(seed):
    a = ph.verhaeltnis_aufgabe(seed)
    g = a["werte"]
    import math

    assert g["pks"] + math.log10(a["loesung"]) == pytest.approx(g["ziel_ph"], abs=1e-9)


@pytest.mark.parametrize(
    "bauer",
    [ph.saeure_aufgabe, ph.base_aufgabe, ph.stark_aufgabe, ph.puffer_aufgabe, ph.verhaeltnis_aufgabe],
)
def test_jede_ph_aufgabe_hat_text_rechenweg_und_toleranz(bauer):
    a = bauer(5)
    assert a["text"] and a["toleranz"] > 0 and a["rechenweg"]
    for s in a["rechenweg"]:
        assert set(s) == SCHRITT_KEYS


def test_neue_ph_aufgabe_mischt_alle_typen():
    assert {ph.neue_aufgabe(s)["typ"] for s in range(100)} == {
        "saeure", "base", "stark", "puffer", "verhaeltnis"
    }


def test_pruefe_akzeptiert_komma():
    a = ph.puffer_aufgabe(1)
    assert ph.pruefe(a, f"{a['loesung']:.2f}".replace(".", ","))


# --- Chemie-Gutachten 02.10.2026 --------------------------------------------


@pytest.mark.parametrize("seed", range(300))
def test_benzoesaeure_nur_unter_ihrer_loeslichkeit(seed):
    a = ph.saeure_aufgabe(seed)
    if a["stoff"] == "Benzoesäure":
        assert a["werte"]["c"] <= 0.02, "Benzoesäure löst sich nur zu ~0,025 mol/L"


def test_salzloesungen_nennen_das_teilchen_im_pk():
    texte = [ph.neue_aufgabe(s)["text"] for s in range(300)]
    assert any("pKs(NH₄⁺)" in x for x in texte)
    assert not any("(NH₄⁺)-Lösung" in x or "(CH₃COO⁻)-Lösung" in x for x in texte)
