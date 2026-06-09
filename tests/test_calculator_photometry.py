"""Tests for UV photometry Gehalt calculations."""

import pytest

from chemdraw_tool.calculator.photometry import (
    SUBSTANCE_CONSTANTS,
    calculate_gehalt_uv,
)


def test_substance_constants_ascorbinsaeure():
    c = SUBSTANCE_CONSTANTS["ascorbinsaeure"]
    assert c["a1pct1cm"] == pytest.approx(695)
    assert c["wavelength_nm"] == 245
    assert c["solvent"] == "HCl 0,1 mol/L"


def test_calculate_gehalt_uv_basic():
    result = calculate_gehalt_uv(
        einwaagen=[50.0, 51.0, 49.5, 50.5, 50.2, 49.8],
        absorptionen=[0.348, 0.355, 0.345, 0.351, 0.349, 0.347],
        substance="ascorbinsaeure",
        verduennungsfaktor=100.0,
        kolbenvolumen_ml=100.0,
    )
    assert len(result) == 6
    for step in result:
        assert "gehalt" in step
        assert 90.0 < step["gehalt"] < 110.0
        assert "label" in step
        assert "formula" in step


def test_calculate_gehalt_uv_explanation_only_first():
    result = calculate_gehalt_uv(
        einwaagen=[50.0, 51.0],
        absorptionen=[0.348, 0.355],
        substance="ascorbinsaeure",
        verduennungsfaktor=100.0,
        kolbenvolumen_ml=100.0,
    )
    assert result[0]["explanation"] != ""
    assert result[1]["explanation"] == ""


def test_uv_mismatched_lengths_raises():
    with pytest.raises(ValueError, match="gleich lang"):
        calculate_gehalt_uv(
            einwaagen=[50.0, 51.0, 49.5],
            absorptionen=[0.348, 0.355],
            substance="ascorbinsaeure",
            verduennungsfaktor=100.0,
            kolbenvolumen_ml=100.0,
        )


def test_uv_empty_raises():
    with pytest.raises(ValueError, match="nicht leer"):
        calculate_gehalt_uv(
            einwaagen=[],
            absorptionen=[],
            substance="ascorbinsaeure",
            verduennungsfaktor=100.0,
            kolbenvolumen_ml=100.0,
        )


def test_uv_negative_mass_raises():
    with pytest.raises(ValueError, match="positiv"):
        calculate_gehalt_uv(
            einwaagen=[-50.0],
            absorptionen=[0.348],
            substance="ascorbinsaeure",
            verduennungsfaktor=100.0,
            kolbenvolumen_ml=100.0,
        )


def test_uv_zero_verduennungsfaktor_raises():
    with pytest.raises(ValueError, match="positiv"):
        calculate_gehalt_uv(
            einwaagen=[50.0],
            absorptionen=[0.348],
            substance="ascorbinsaeure",
            verduennungsfaktor=0.0,
            kolbenvolumen_ml=100.0,
        )


def test_uv_zero_kolbenvolumen_raises():
    with pytest.raises(ValueError, match="positiv"):
        calculate_gehalt_uv(
            einwaagen=[50.0],
            absorptionen=[0.348],
            substance="ascorbinsaeure",
            verduennungsfaktor=100.0,
            kolbenvolumen_ml=0.0,
        )


def test_uv_unknown_substance_raises():
    with pytest.raises(ValueError, match="[Uu]nbekannte Substanz"):
        calculate_gehalt_uv(
            einwaagen=[50.0],
            absorptionen=[0.348],
            substance="koffein",
            verduennungsfaktor=100.0,
            kolbenvolumen_ml=100.0,
        )
