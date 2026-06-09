"""Vertragstests für den formats-Parameter der generate_*-Tools.

Neue Spec (2026-06-09, ChemDraw-Entkopplung): PNG+SVG sind die primären
Artefakte und Default; CDXML wird NUR auf explizite Anforderung geschrieben.
SMILES-Inputs → resolve() geht nie ins Netz; PubChem-Enrichment ist gemockt.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from chemdraw_tool.image_export import PNG_MAGIC
from chemdraw_tool.server import batch_generate, generate_molecule, generate_reaction

ASPIRIN = "CC(=O)OC1=CC=CC=C1C(=O)O"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    monkeypatch.setattr("chemdraw_tool.server.REACTION_DIR", tmp_path / "rxn")
    with patch("chemdraw_tool.server._enrich_properties", return_value={}):
        yield tmp_path


def test_molecule_default_writes_png_and_svg_no_cdxml(tmp_path):
    payload = generate_molecule(ASPIRIN, label="Aspirin")
    assert set(payload.files) == {"png", "svg"}
    png = Path(payload.files["png"])
    assert png.read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert "<svg" in Path(payload.files["svg"]).read_text()
    assert payload.cdxml_path == ""
    assert not list((tmp_path / "mol").glob("*.cdxml")), (
        "CDXML darf ohne explizite Anforderung nicht geschrieben werden"
    )


def test_molecule_cdxml_only_on_request(tmp_path):
    payload = generate_molecule(ASPIRIN, label="Aspirin", formats=["cdxml"])
    assert set(payload.files) == {"cdxml"}
    cdxml = Path(payload.files["cdxml"])
    assert cdxml.exists()
    assert "CDXML" in cdxml.read_text()
    assert payload.cdxml_path == str(cdxml)
    assert not list((tmp_path / "mol").glob("*.png"))


def test_molecule_invalid_format_raises():
    with pytest.raises(ValueError, match="[Ff]ormat"):
        generate_molecule(ASPIRIN, formats=["pdf"])


def test_reaction_default_writes_png_and_svg_no_cdxml(tmp_path):
    payload = generate_reaction(
        ["C(C)O", "CC(=O)O"], ["CC(=O)OCC"], conditions="H2SO4", name="Veresterung"
    )
    assert set(payload.files) == {"png", "svg"}
    assert Path(payload.files["png"]).read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert payload.cdxml_path == ""
    assert not list((tmp_path / "rxn").rglob("*.cdxml"))


def test_reaction_cdxml_on_request(tmp_path):
    payload = generate_reaction(
        ["C(C)O", "CC(=O)O"], ["CC(=O)OCC"], name="Ester", formats=["png", "cdxml"]
    )
    assert set(payload.files) == {"png", "cdxml"}
    assert Path(payload.cdxml_path).exists()
    assert payload.cdxml_path == payload.files["cdxml"]


def test_batch_passes_formats_through(tmp_path):
    payload = batch_generate([ASPIRIN, "CC(C)O"], formats=["svg"])
    assert payload.failed == []
    assert len(payload.molecules) == 2
    for mol_payload in payload.molecules:
        assert set(mol_payload.files) == {"svg"}
        assert mol_payload.cdxml_path == ""
    assert payload.cdxml_paths == []
    assert not list((tmp_path / "mol").glob("*.cdxml"))


def test_batch_default_no_cdxml_but_paths_for_requested(tmp_path):
    payload = batch_generate([ASPIRIN], formats=["cdxml"])
    assert len(payload.cdxml_paths) == 1
    assert Path(payload.cdxml_paths[0]).exists()
