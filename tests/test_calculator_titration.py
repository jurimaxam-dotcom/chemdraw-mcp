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
