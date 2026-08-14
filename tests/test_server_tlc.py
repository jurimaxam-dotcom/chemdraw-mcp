"""Vertragstests für das generate_tlc-Tool (DC-Platte aus Rf-Werten).

Wie generate_spectrum: PNG+SVG sind Default und werden als Dateien
geschrieben; CDXML gibt es nicht (Platte ≠ Struktur). Das Payload trägt
zusätzlich die Bahnen mit ihren Rf-Werten — das Panel listet sie als
Ableseliste fürs Protokoll.
"""

from pathlib import Path

import pytest

from chemdraw_tool.image_export import PNG_MAGIC
from chemdraw_tool.server import generate_tlc

ESTER_LANES = [
    {"name": "Edukt", "spots": [{"rf": 0.30, "label": "Säure"}]},
    {"name": "Reaktion", "spots": [{"rf": 0.65, "label": "Ester"}]},
    {"name": "Co-Spot", "spots": [{"rf": 0.30}, {"rf": 0.65}]},
]


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.TLC_DIR", tmp_path / "dc")
    yield tmp_path


def test_default_writes_png_and_svg(tmp_path):
    payload = generate_tlc(ESTER_LANES, title="Veresterung")
    assert set(payload.files) == {"png", "svg"}
    png = Path(payload.files["png"])
    assert png.read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert "<svg" in Path(payload.files["svg"]).read_text()
    assert png.parent == tmp_path / "dc"


def test_payload_fields():
    payload = generate_tlc(
        ESTER_LANES,
        title="Veresterung",
        solvent="Toluol/Ethylacetat 8:2",
        detection="UV 254 nm",
    )
    assert payload.type == "tlc"
    assert payload.name == "Veresterung"
    assert payload.solvent == "Toluol/Ethylacetat 8:2"
    assert payload.detection == "UV 254 nm"
    assert "<svg" in payload.svg


def test_payload_keeps_lanes_and_rf_values_for_the_panel():
    payload = generate_tlc(ESTER_LANES)
    assert [lane.name for lane in payload.lanes] == ["Edukt", "Reaktion", "Co-Spot"]
    assert [s.rf for s in payload.lanes[2].spots] == [0.30, 0.65]
    assert payload.lanes[0].spots[0].label == "Säure"
    assert payload.lanes[0].spots[0].intensity == 1.0


def test_svg_only_on_request(tmp_path):
    payload = generate_tlc(ESTER_LANES, formats=["svg"])
    assert set(payload.files) == {"svg"}
    assert not list((tmp_path / "dc").glob("*.png"))


def test_cdxml_not_available_for_plates():
    with pytest.raises(ValueError, match="png"):
        generate_tlc(ESTER_LANES, formats=["cdxml"])


def test_rf_above_one_raises_with_clear_message():
    with pytest.raises(ValueError, match="Rf"):
        generate_tlc([{"name": "A", "spots": [{"rf": 1.4}]}])


def test_no_lanes_raises():
    with pytest.raises(ValueError, match="[Bb]ahn"):
        generate_tlc([])


def test_filename_uses_title_slug(tmp_path):
    payload = generate_tlc(ESTER_LANES, title="Veresterung Ansatz 2")
    assert Path(payload.files["png"]).name == "veresterung-ansatz-2.png"


def test_filename_falls_back_to_plate(tmp_path):
    payload = generate_tlc(ESTER_LANES)
    assert Path(payload.files["png"]).name == "tlc-plate.png"
