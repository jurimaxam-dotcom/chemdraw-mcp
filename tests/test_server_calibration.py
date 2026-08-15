"""`generate_calibration_curve`: Gerade zeichnen UND Proben zurückrechnen."""

from pathlib import Path

import pytest

from chemdraw_tool.image_export import PNG_MAGIC
from chemdraw_tool.payloads import PlotPayload
from chemdraw_tool.server import generate_calibration_curve

STANDARDS = [0.1, 0.2, 0.4, 0.6, 0.8]
SIGNALS = [0.105, 0.203, 0.402, 0.601, 0.798]


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.PLOT_DIR", tmp_path / "diagramme")
    return tmp_path


def test_writes_png_and_svg(_isolate):
    p = generate_calibration_curve(STANDARDS, SIGNALS, substance="Paracetamol")
    assert set(p.files) == {"png", "svg"}
    png = Path(p.files["png"])
    assert png.read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert png.parent == _isolate / "diagramme"
    assert "<svg" in Path(p.files["svg"]).read_text()


def test_returns_a_plot_payload_with_the_equation():
    p = generate_calibration_curve(STANDARDS, SIGNALS)
    assert isinstance(p, PlotPayload)
    assert p.type == "plot"
    assert "R²" in p.subtitle
    assert "y =" in p.subtitle


def test_unknown_signal_is_read_back_and_reported():
    p = generate_calibration_curve(STANDARDS, SIGNALS, unknown_signals=[0.5])
    joined = " ".join(p.notes)
    assert "0.5" in joined
    # Bei y ≈ x liegt die Konzentration nahe 0,5.
    assert "0.49" in joined or "0.50" in joined


def test_extrapolated_sample_is_flagged_not_hidden():
    p = generate_calibration_curve(STANDARDS, SIGNALS, unknown_signals=[2.5])
    joined = " ".join(p.notes).lower()
    assert "outside the calibrated range" in joined


def test_several_unknowns_all_appear():
    p = generate_calibration_curve(STANDARDS, SIGNALS, unknown_signals=[0.3, 0.5, 0.7])
    joined = " ".join(p.notes)
    assert joined.count("Signal") >= 3


def test_detection_limits_are_reported_for_real_data():
    p = generate_calibration_curve(STANDARDS, SIGNALS)
    assert any("detection" in n.lower() for n in p.notes)


def test_poor_linearity_is_called_out():
    p = generate_calibration_curve(
        [0.1, 0.2, 0.4, 0.6, 0.8], [0.10, 0.35, 0.30, 0.75, 0.60]
    )
    assert any("R²" in n for n in p.notes)


def test_through_origin_changes_the_equation():
    normal = generate_calibration_curve(STANDARDS, SIGNALS).subtitle
    forced = generate_calibration_curve(STANDARDS, SIGNALS, through_origin=True).subtitle
    assert normal != forced
    assert "+" not in forced.split("·")[0]


def test_two_standards_are_rejected():
    with pytest.raises(ValueError, match="three"):
        generate_calibration_curve([0.1, 0.2], [0.1, 0.2])


def test_empty_input_says_what_is_missing():
    with pytest.raises(ValueError, match="concentrations|signals"):
        generate_calibration_curve([], [])


def test_axis_labels_reach_the_figure():
    """Ohne Einheit an der Achse ist die Grafik im Protokoll wertlos."""
    p = generate_calibration_curve(
        STANDARDS, SIGNALS, x_label="c [µg/mL]", y_label="A (243 nm)"
    )
    assert "µg/mL" in p.svg
