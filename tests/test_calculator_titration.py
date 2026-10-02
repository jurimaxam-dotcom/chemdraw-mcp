"""Tests for titration Gehalt calculations."""

import pytest

from chemdraw_tool.calculator.titration import (
    SUBSTANCE_FACTORS,
    calculate_gehalt_titration,
    calculate_titer,
)


def test_substance_factors_ascorbinsaeure():
    assert "ascorbinsaeure" in SUBSTANCE_FACTORS
    assert SUBSTANCE_FACTORS["ascorbinsaeure"] == pytest.approx(8.806)


def test_substance_factors_ibuprofen():
    assert "ibuprofen" in SUBSTANCE_FACTORS
    assert SUBSTANCE_FACTORS["ibuprofen"] == pytest.approx(20.63)


def test_calculate_titer():
    ref_einwaagen = [370.0, 372.0]
    ref_volumina = [18.0, 18.1]
    blindwert = 0.15
    faktor = 20.63
    titer = calculate_titer(ref_einwaagen, ref_volumina, blindwert, faktor)
    assert 0.95 < titer < 1.05


def test_calculate_gehalt_titration_basic():
    result = calculate_gehalt_titration(
        einwaagen=[419.3, 452.7, 487.0, 445.5],
        volumina=[16.75, 18.10, 19.45, 17.80],
        blindwert=0.15,
        faktor=20.63,
        titer=1.0,
    )
    assert len(result) == 4
    for step in result:
        assert "gehalt" in step
        assert 70.0 < step["gehalt"] < 100.0
        assert "label" in step
        assert "formula" in step
        assert "substitution" in step


def test_calculate_gehalt_titration_ibuprofen_example():
    """Verify against Folie 15 example: w(Ibu) = 82.5%"""
    result = calculate_gehalt_titration(
        einwaagen=[419.3, 452.7, 487.0, 445.5],
        volumina=[16.75, 18.10, 19.45, 17.80],
        blindwert=0.0,
        faktor=20.63,
        titer=1.0,
    )
    gehalte = [r["gehalt"] for r in result]
    mean = sum(gehalte) / len(gehalte)
    assert mean == pytest.approx(82.4, abs=0.5)


def test_titer_mismatched_lengths_raises():
    with pytest.raises(ValueError, match="same length"):
        calculate_titer([370.0, 372.0], [18.0], 0.15, 20.63)


def test_titer_empty_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_titer([], [], 0.15, 20.63)


def test_gehalt_mismatched_lengths_raises():
    with pytest.raises(ValueError, match="same length"):
        calculate_gehalt_titration(
            einwaagen=[419.3, 452.7],
            volumina=[16.75],
            blindwert=0.15,
            faktor=20.63,
        )


def test_gehalt_negative_mass_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_gehalt_titration(
            einwaagen=[-1.0, 452.7],
            volumina=[16.75, 18.10],
            blindwert=0.15,
            faktor=20.63,
        )


def test_titer_negative_volumen_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_titer([370.0, 372.0], [-18.0, 18.1], 0.15, 20.63)


def test_titer_zero_faktor_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_titer([370.0, 372.0], [18.0, 18.1], 0.15, 0.0)


def test_titer_zero_soll_gehalt_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_titer([370.0, 372.0], [18.0, 18.1], 0.15, 20.63, soll_gehalt=0.0)


def test_gehalt_negative_volumen_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_gehalt_titration(
            einwaagen=[419.3, 452.7],
            volumina=[-16.75, 18.10],
            blindwert=0.15,
            faktor=20.63,
        )


def test_gehalt_zero_faktor_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_gehalt_titration(
            einwaagen=[419.3, 452.7],
            volumina=[16.75, 18.10],
            blindwert=0.15,
            faktor=0.0,
        )


def test_gehalt_zero_titer_raises():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_gehalt_titration(
            einwaagen=[419.3, 452.7],
            volumina=[16.75, 18.10],
            blindwert=0.15,
            faktor=20.63,
            titer=0.0,
        )


# --- Richtung des Titers (02.10.2026) ---------------------------------------
# Ist die Maßlösung stärker als nominal (t > 1), verbraucht die Referenz WENIGER
# Volumen; ihr scheinbarer Gehalt liegt unter dem Sollwert. Der Titer ist also
# Soll / scheinbar — nicht umgekehrt. Der alte Test (0,95 < t < 1,05) sah die
# Richtung nicht; mit t = 1/1,02 lag jede Probe rund 4 % zu niedrig.


@pytest.mark.parametrize("t_wahr", [0.97, 1.0, 1.02])
def test_titer_aus_referenz_hat_die_richtige_richtung(t_wahr):
    faktor, m = 20.63, 400.0
    v = m / (faktor * t_wahr)  # Referenz mit 100 % Gehalt, Blindwert 0
    assert calculate_titer([m], [v], 0.0, faktor) == pytest.approx(t_wahr, rel=1e-9)


def test_probe_mit_derselben_massloesung_ergibt_ihren_wahren_gehalt():
    faktor, t_wahr = 20.63, 1.02
    ref_m = [400.0, 410.0]
    ref_v = [m / (faktor * t_wahr) for m in ref_m]
    titer = calculate_titer(ref_m, ref_v, 0.0, faktor)
    m_probe, gehalt_wahr = 450.0, 99.3
    v_probe = m_probe * gehalt_wahr / 100 / (faktor * t_wahr)
    gehalt = calculate_gehalt_titration([m_probe], [v_probe], 0.0, faktor, titer)[0]["gehalt"]
    assert gehalt == pytest.approx(gehalt_wahr, rel=1e-9)
