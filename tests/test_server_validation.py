"""Integration tests for calculate_validation MCP tool."""

import pytest

from chemdraw_tool.payloads import ValidationPayload
from chemdraw_tool.server import calculate_validation

_ACID_KWARGS = dict(
    acid_einwaagen=[150.0, 148.0, 153.0, 149.0, 151.0, 150.5],
    acid_volumina=[17.10, 16.88, 17.43, 16.99, 17.21, 17.16],
    acid_referenz_einwaagen=[150.0, 152.0],
    acid_referenz_volumina=[17.18, 17.41],
    acid_blindwert=0.15,
)
_UV_KWARGS = dict(
    uv_einwaagen=[50.0, 51.0, 49.5, 50.5, 50.2, 49.8],
    uv_absorptionen=[0.348, 0.355, 0.345, 0.351, 0.349, 0.347],
)


def test_validation_variante_b_basic():
    result = calculate_validation(
        variante="B",
        wahrer_wert=99.5,
        **_ACID_KWARGS,
        **_UV_KWARGS,
    )
    assert isinstance(result, ValidationPayload)
    assert result.type == "validation"
    assert result.variante == "B"
    assert result.substance == "Ascorbinsäure"


def test_validation_has_two_methods():
    result = calculate_validation(
        variante="B",
        wahrer_wert=99.5,
        **_ACID_KWARGS,
        **_UV_KWARGS,
    )
    assert result.method_a.name == "UV-Photometrie"
    assert result.method_b.name == "Acidimetrie"
    assert len(result.method_a.gehalt_steps) == 6
    assert len(result.method_b.gehalt_steps) == 6


def test_validation_has_comparison():
    result = calculate_validation(
        variante="B",
        wahrer_wert=99.5,
        **_ACID_KWARGS,
        **_UV_KWARGS,
    )
    assert hasattr(result.comparison, "f_test_value")
    assert hasattr(result.comparison, "t_test_value")
    assert result.comparison.result_text != ""


def test_validation_has_summary():
    result = calculate_validation(
        variante="B",
        wahrer_wert=99.5,
        **_ACID_KWARGS,
        **_UV_KWARGS,
    )
    assert result.summary != ""
    assert "Ascorbinsäure" in result.summary


def test_validation_missing_uv_data():
    with pytest.raises(ValueError, match="UV"):
        calculate_validation(
            variante="B",
            wahrer_wert=99.5,
            acid_einwaagen=[150.0],
            acid_volumina=[17.10],
            acid_referenz_einwaagen=[150.0],
            acid_referenz_volumina=[17.18],
            acid_blindwert=0.15,
        )
