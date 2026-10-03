"""calculate_pharmacokinetics: Zahl UND Rechenweg, Einkompartiment-Modell.

Referenz (D=500 mg, F=0,8, Vd=70 L, ke=0,15/h, ka=1,2/h) siehe tests/test_pk.py.
"""

import pytest

from chemdraw_tool.server import calculate_pharmacokinetics as pk_tool


def test_half_life_aus_ke_nennt_halbwertszeit_und_clearance():
    out = pk_tool("half_life", vd_l=70, ke_per_h=0.15)
    assert "4.62 h" in out  # t½
    assert "10.5 L/h" in out  # CL = ke · Vd


def test_half_life_aus_clearance_und_vd():
    out = pk_tool("half_life", vd_l=70, clearance_l_per_h=10.5)
    assert "ke = 0.15" in out


def test_iv_bolus_anfang_zeitpunkt_und_auc():
    out = pk_tool("iv_bolus", dose_mg=500, vd_l=70, ke_per_h=0.15, time_h=4.621)
    assert "7.14 mg/L" in out  # C0
    assert "3.57 mg/L" in out  # nach einer Halbwertszeit
    assert "47.6 mg·h/L" in out  # AUC


def test_oral_tmax_cmax_auc():
    out = pk_tool("oral", dose_mg=500, bioavailability=0.8, vd_l=70, ke_per_h=0.15, ka_per_h=1.2)
    assert "1.98 h" in out
    assert "4.25 mg/L" in out
    assert "38.1 mg·h/L" in out


def test_steady_state():
    out = pk_tool("steady_state", dose_mg=500, bioavailability=0.8, vd_l=70, ke_per_h=0.15, tau_h=8)
    assert "R = 1.43" in out
    assert "4.76 mg/L" in out  # Css,av
    assert "90 %" in out  # Zeit bis Steady State


def test_loading_dose_und_erhaltungsrate():
    out = pk_tool("loading_dose", target_mg_per_l=4, bioavailability=0.8, vd_l=70, ke_per_h=0.15)
    assert "350 mg" in out
    assert "52.5 mg/h" in out


def test_fehlende_angabe_nennt_was_fehlt():
    with pytest.raises(ValueError, match="dose_mg"):
        pk_tool("iv_bolus", vd_l=70, ke_per_h=0.15)
    with pytest.raises(ValueError, match="Halbwertszeit"):
        pk_tool("half_life", vd_l=70)


def test_widerspruch_wird_nicht_still_aufgeloest():
    with pytest.raises(ValueError, match="widersprechen"):
        pk_tool("half_life", vd_l=70, ke_per_h=0.15, clearance_l_per_h=20)
