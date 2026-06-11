"""Tests für generate_titration_curve + generate_species_distribution.

Beide Tools teilen den PlotPayload (type='plot') und die PlotView im Panel.
"""

from pathlib import Path

from chemdraw_tool.server import (
    generate_species_distribution,
    generate_titration_curve,
)


def test_titration_tool_writes_files_and_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    payload = generate_titration_curve(
        substance="Acetic acid with NaOH",
        pka_values=[4.76],
        c_acid=0.1,
        v_acid_ml=25.0,
        c_titrant=0.1,
        indicator={"name": "Phenolphthalein", "ph_range": [8.2, 10.0]},
    )
    assert payload.type == "plot"
    assert payload.name == "Acetic acid with NaOH"
    assert "Titration" in payload.subtitle
    assert "<svg" in payload.svg
    assert Path(payload.files["png"]).exists()
    assert Path(payload.files["svg"]).exists()


def test_species_tool_writes_files_and_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    payload = generate_species_distribution(
        substance="Phosphoric acid",
        pka_values=[2.15, 7.2, 12.35],
        labels=["H₃PO₄", "H₂PO₄⁻", "HPO₄²⁻", "PO₄³⁻"],
    )
    assert payload.type == "plot"
    assert "Species" in payload.subtitle
    assert Path(payload.files["png"]).exists()


def test_titration_requires_positive_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError):
        generate_titration_curve(
            substance="x", pka_values=[], c_acid=0.1, v_acid_ml=25.0, c_titrant=0.1
        )
    with pytest.raises(ValueError):
        generate_titration_curve(
            substance="x", pka_values=[4.76], c_acid=-1, v_acid_ml=25.0, c_titrant=0.1
        )
