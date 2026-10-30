"""Tests für generate_titration_curve + generate_species_distribution.

Beide Tools teilen den PlotPayload (type='plot') und die PlotView im Panel.
"""

from pathlib import Path

import pytest

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


def test_compare_molecules_returns_plot_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    from chemdraw_tool.server import compare_molecules

    payload = compare_molecules(
        structures=["Cc1ccccc1", "Clc1ccccc1"],
        labels=["Toluene", "Chlorobenzene"],
        title="Benzene derivatives",
    )
    assert payload.type == "plot"
    assert payload.name == "Benzene derivatives"
    assert "<svg" in payload.svg
    assert Path(payload.files["png"]).exists()


def test_compare_molecules_needs_two_to_four(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    import pytest

    from chemdraw_tool.server import compare_molecules

    with pytest.raises(ValueError):
        compare_molecules(structures=["CCO"])
    with pytest.raises(ValueError):
        compare_molecules(structures=["C", "CC", "CCC", "CCCC", "CCCCC"])


# --- Befunde aus dem echten Aufruf (Welle 2, 30.10.2026) ------------------

_GERMAN = ("Mindestens", "benötigt", "müssen", "Werte", "ergeben", "übergeben")
_TITRATION = dict(c_acid=0.1, v_acid_ml=20, c_titrant=0.1)


@pytest.mark.parametrize("call", [
    lambda: generate_titration_curve("x", [], **_TITRATION),
    lambda: generate_titration_curve("x", [4.76], c_acid=-0.1, v_acid_ml=20, c_titrant=0.1),
    lambda: generate_species_distribution("x", []),
    lambda: generate_species_distribution("x", [4.4], labels=["HA"]),
])
def test_plot_errors_are_english(call, tmp_path, monkeypatch):
    """Nutzertexte sind englisch (Projektkonvention); alle vier kamen deutsch an."""
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    with pytest.raises(ValueError) as error:
        call()
    assert not [w for w in _GERMAN if w in str(error.value)], str(error.value)


@pytest.mark.parametrize("call", [
    lambda: generate_titration_curve("x", [7.2, 2.1], **_TITRATION),
    lambda: generate_species_distribution("x", [7.2, 2.1]),
    lambda: generate_species_distribution("x", [2.15, 12.35, 7.2]),
])
def test_descending_pka_values_are_rejected(call, tmp_path, monkeypatch):
    """Befund 30.10.2026: [7.2, 2.1] wurde still gezeichnet — Pufferpunkte
    schwebten neben der Kurve, die Zwischenspezies HA⁻ verschwand. pKa₁ < pKa₂
    gilt immer; vertauschte Werte sind ein Eingabefehler, kein Diagramm."""
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path)
    with pytest.raises(ValueError, match="ascending"):
        call()
    assert not list(tmp_path.iterdir())
