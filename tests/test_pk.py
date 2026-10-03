"""Pharmakokinetik, Einkompartiment-Modell: reine Formeln.

Zahlen von Hand gegengerechnet (D=500 mg, F=0,8, Vd=70 L, ke=0,15/h, ka=1,2/h):
t½ = ln2/0,15 = 4,62 h · C0 = 500/70 = 7,143 mg/L · AUC(i.v.) = 500/(0,15·70) = 47,62 mg·h/L
tmax = ln(1,2/0,15)/(1,2−0,15) = 1,98 h · Cmax = 4,25 mg/L · R(τ=8 h) = 1/(1−e^−1,2) = 1,431
"""

import math

import pytest

from chemdraw_tool import pk

D, F, VD, KE, KA = 500.0, 0.8, 70.0, 0.15, 1.2


def test_halbwertszeit_und_umkehrung():
    assert pk.half_life(KE) == pytest.approx(4.621, abs=1e-3)
    assert pk.ke_from_half_life(4.621) == pytest.approx(KE, abs=1e-4)


def test_iv_bolus_anfangskonzentration_und_abfall():
    assert pk.c_iv(D, VD, KE, 0) == pytest.approx(7.1429, abs=1e-4)
    assert pk.c_iv(D, VD, KE, pk.half_life(KE)) == pytest.approx(7.1429 / 2, abs=1e-3)


def test_resolve_aus_clearance_und_vd():
    r = pk.resolve(vd=70, cl=10.5)
    assert r["ke"] == pytest.approx(0.15)
    assert r["t_half"] == pytest.approx(4.621, abs=1e-3)


def test_resolve_aus_halbwertszeit_und_vd_liefert_clearance():
    r = pk.resolve(vd=70, t_half=4.621)
    assert r["cl"] == pytest.approx(10.5, abs=1e-2)


def test_resolve_widerspruch_wird_benannt():
    with pytest.raises(ValueError, match="widersprechen"):
        pk.resolve(vd=70, ke=0.15, cl=20)


def test_resolve_zu_wenig_angaben():
    with pytest.raises(ValueError, match="Halbwertszeit"):
        pk.resolve(vd=70)


def test_auc_iv_und_oral():
    assert pk.auc_inf(D, 1.0, VD * KE) == pytest.approx(47.619, abs=1e-3)
    assert pk.auc_inf(D, F, VD * KE) == pytest.approx(38.095, abs=1e-3)


def test_oral_tmax_cmax():
    assert pk.tmax(KA, KE) == pytest.approx(1.98, abs=0.01)
    assert pk.cmax(D, F, VD, KE, KA) == pytest.approx(4.25, abs=0.01)


def test_oral_ist_bei_t0_null_und_laeuft_gegen_null():
    assert pk.c_oral(D, F, VD, KE, KA, 0) == pytest.approx(0.0, abs=1e-12)
    assert pk.c_oral(D, F, VD, KE, KA, 200) == pytest.approx(0.0, abs=1e-9)


def test_oral_flip_flop_grenzfall_ka_gleich_ke_ist_stetig():
    gleich = pk.c_oral(D, F, VD, KE, KE, 3.0)
    knapp = pk.c_oral(D, F, VD, KE, KE + 1e-7, 3.0)
    assert gleich == pytest.approx(knapp, rel=1e-4)
    assert pk.tmax(KE, KE) == pytest.approx(1 / KE)


def test_auc_numerisch_stimmt_mit_formel_ueberein():
    """Figur und Zahl müssen übereinstimmen (wie ph_plots.exact_ph und ph_calc)."""
    n, t_max = 40000, 400.0
    h = t_max / n
    num = sum(pk.c_oral(D, F, VD, KE, KA, (i + 0.5) * h) for i in range(n)) * h
    assert num == pytest.approx(pk.auc_inf(D, F, VD * KE), rel=1e-3)


def test_akkumulation_und_steady_state():
    assert pk.accumulation(KE, 8) == pytest.approx(1.431, abs=1e-3)
    assert pk.css_avg(D, F, VD * KE, 8) == pytest.approx(4.762, abs=1e-3)
    hi = pk.css_max_iv(D, VD, KE, 8)
    lo = pk.css_min_iv(D, VD, KE, 8)
    assert hi == pytest.approx(7.1429 * 1.431, abs=1e-2)
    assert lo == pytest.approx(hi * math.exp(-KE * 8), rel=1e-9)


def test_zeit_bis_steady_state():
    assert pk.time_to_fraction_ss(KE, 0.9) == pytest.approx(math.log(10) / KE, abs=1e-9)
    assert pk.time_to_fraction_ss(KE, 0.9) == pytest.approx(3.32 * pk.half_life(KE), abs=0.05)


def test_aufsaettigungs_und_erhaltungsdosis():
    assert pk.loading_dose(4.0, VD, F) == pytest.approx(350.0)
    assert pk.maintenance_rate(4.0, VD * KE, F) == pytest.approx(52.5)


@pytest.mark.parametrize("args", [(0, 70, 0.15, 1), (500, -1, 0.15, 1), (500, 70, 0, 1)])
def test_unsinnige_werte_werden_abgelehnt(args):
    with pytest.raises(ValueError):
        pk.c_iv(*args)
