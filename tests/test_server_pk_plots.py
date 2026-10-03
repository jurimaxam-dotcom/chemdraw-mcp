"""generate_pk_curve + generate_dose_response: PlotPayload (type='plot'), Panel unverändert."""

from pathlib import Path

import pytest

from chemdraw_tool import pk, pk_plots
from chemdraw_tool.server import generate_dose_response, generate_pk_curve


def test_pk_curve_schreibt_dateien_und_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    p = generate_pk_curve(dose_mg=500, vd_l=70, ke_per_h=0.15, ka_per_h=1.2, bioavailability=0.8, drug="Ibuprofen")
    assert p.type == "plot"
    assert p.name == "Ibuprofen"
    assert "<svg" in p.svg
    assert Path(p.files["png"]).exists() and Path(p.files["svg"]).exists()
    assert any("Cmax" in n for n in p.notes)


def test_pk_curve_mehrfachgabe_nennt_steady_state_in_den_notizen(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    p = generate_pk_curve(dose_mg=500, vd_l=70, half_life_h=4.62, tau_h=8)
    joined = " ".join(p.notes)
    assert "Css,av" in joined and "R = 1.43" in joined


def test_pk_curve_widerspruch_wird_benannt(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    with pytest.raises(ValueError, match="widersprechen"):
        generate_pk_curve(dose_mg=500, vd_l=70, ke_per_h=0.15, clearance_l_per_h=20)


def test_pk_figure_hoechster_punkt_stimmt_mit_cmax_der_formel():
    """Bild und Zahl: die gezeichnete Kurve erreicht genau Cmax aus pk.cmax."""
    fig = pk_plots.build_pk_figure(500, 70, 0.15, f=0.8, ka=1.2)
    line = fig.axes[0].lines[0]
    assert max(line.get_ydata()) == pytest.approx(pk.cmax(500, 0.8, 70, 0.15, 1.2), rel=2e-3)


def test_pk_figure_legende_ausserhalb_der_achse():
    fig = pk_plots.build_pk_figure(500, 70, 0.15, ka=1.2, tau=8, mec=2, mtc=6)
    fig.canvas.draw()
    ax = fig.axes[0]
    assert ax.get_legend().get_window_extent().x0 >= ax.get_window_extent().x1 - 1


def test_dose_response_schreibt_dateien_und_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    p = generate_dose_response(ec50=10, unit="nM", antagonist_concentration=20, antagonist_kb=10, drug="Agonist A")
    assert p.type == "plot"
    assert "<svg" in p.svg
    assert Path(p.files["png"]).exists()
    joined = " ".join(p.notes)
    assert "EC50 = 10 nM" in joined and "r = 3" in joined and "30 nM" in joined


def test_dose_response_antagonist_braucht_beide_angaben(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    with pytest.raises(ValueError, match="antagonist_kb"):
        generate_dose_response(ec50=10, antagonist_concentration=20)


def test_dose_response_figure_kurve_geht_bei_ec50_durch_die_haelfte():
    fig = pk_plots.build_dose_response_figure(ec50=10, emax=100, hill=1.5)
    xs, ys = fig.axes[0].lines[0].get_xdata(), fig.axes[0].lines[0].get_ydata()
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - 10))
    assert ys[i] == pytest.approx(50, abs=1.0)
