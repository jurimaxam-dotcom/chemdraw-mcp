"""Vertragstests für das generate_spectrum-Tool.

Wie die anderen generate_*-Tools: PNG+SVG sind Default und werden als Dateien
geschrieben; CDXML gibt es für Spektren nicht (Spektrum ≠ Struktur).
"""

from pathlib import Path

import pytest

from chemdraw_tool.image_export import PNG_MAGIC
from chemdraw_tool.server import generate_spectrum

IR_PEAKS = [
    {"position": 1750, "intensity": 1, "label": "C=O"},
    {"position": 3000, "intensity": 0.4},
]


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.SPECTRUM_DIR", tmp_path / "spektren")
    yield tmp_path


def test_default_writes_png_and_svg(tmp_path):
    payload = generate_spectrum("ir", IR_PEAKS, title="Aspirin")
    assert set(payload.files) == {"png", "svg"}
    png = Path(payload.files["png"])
    assert png.read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert "<svg" in Path(payload.files["svg"]).read_text()
    assert png.parent == tmp_path / "spektren"


def test_payload_fields():
    payload = generate_spectrum("ir", IR_PEAKS, title="Aspirin")
    assert payload.type == "spectrum"
    assert payload.spectrum_type == "ir"
    assert payload.name == "Aspirin"
    assert "<svg" in payload.svg


def test_svg_only_on_request(tmp_path):
    payload = generate_spectrum("uv_vis", [{"position": 260}], formats=["svg"])
    assert set(payload.files) == {"svg"}
    assert not list((tmp_path / "spektren").glob("*.png"))


def test_cdxml_not_available_for_spectra():
    with pytest.raises(ValueError, match="png"):
        generate_spectrum("ir", IR_PEAKS, formats=["cdxml"])


def test_unknown_spectrum_type_raises():
    with pytest.raises(ValueError, match="[Ss]pektrentyp"):
        generate_spectrum("xrd", IR_PEAKS)


def test_filename_uses_title_slug(tmp_path):
    payload = generate_spectrum("nmr_1h", [{"position": 7.3}], title="Aspirin 1H")
    assert Path(payload.files["png"]).name == "aspirin-1h.png"


def test_filename_falls_back_to_type(tmp_path):
    payload = generate_spectrum("cd", [{"position": 280, "intensity": -1}])
    assert Path(payload.files["png"]).name == "cd-spectrum.png"
