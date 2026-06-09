import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from chemdraw_tool.server import open_chemdraw_file


@pytest.fixture(autouse=True)
def _isolate_output(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")


def test_open_chemdraw_file_rejects_non_cdxml_extension():
    """An existing file that isn't a ChemDraw document must be refused before
    any AppleScript runs — open_chemdraw_file is not a generic file-open vector."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not a chemdraw file")
        bad = f.name
    try:
        with (
            patch(
                "chemdraw_tool.server.find_chemdraw",
                return_value=Path("/Applications/ChemDraw.app"),
            ),
            patch("chemdraw_tool.server.open_in_chemdraw") as mock_open,
        ):
            result = open_chemdraw_file(bad)
        mock_open.assert_not_called()
        assert "cdxml" in result.lower()
    finally:
        Path(bad).unlink()


def test_open_chemdraw_file_generates_cdxml_on_demand(tmp_path):
    """Seit der ChemDraw-Entkopplung schreibt generate_molecule per Default kein
    CDXML mehr — open_chemdraw_file muss die Struktur deshalb selbst als CDXML
    erzeugen können (name_or_smiles), statt auf einen vorhandenen Pfad zu bauen."""
    with (
        patch(
            "chemdraw_tool.server.find_chemdraw",
            return_value=Path("/Applications/ChemDraw.app"),
        ),
        patch("chemdraw_tool.server.open_in_chemdraw", return_value=True) as mock_open,
    ):
        result = open_chemdraw_file(name_or_smiles="CC(=O)OC1=CC=CC=C1C(=O)O")
    mock_open.assert_called_once()
    opened_path = Path(mock_open.call_args[0][0])
    assert opened_path.suffix == ".cdxml"
    assert opened_path.exists(), "CDXML muss on-demand erzeugt worden sein"
    assert "Geöffnet" in result


def test_open_chemdraw_file_requires_path_or_structure():
    """Ohne file_path UND ohne name_or_smiles: klare Meldung, kein AppleScript."""
    with patch("chemdraw_tool.server.open_in_chemdraw") as mock_open:
        result = open_chemdraw_file()
    mock_open.assert_not_called()
    assert "name_or_smiles" in result


def test_open_chemdraw_file_accepts_cdxml_extension():
    """A .cdxml file passes the extension gate and reaches ChemDraw."""
    with tempfile.NamedTemporaryFile(suffix=".cdxml", delete=False) as f:
        f.write(b"<CDXML></CDXML>")
        good = f.name
    try:
        with (
            patch(
                "chemdraw_tool.server.find_chemdraw",
                return_value=Path("/Applications/ChemDraw.app"),
            ),
            patch(
                "chemdraw_tool.server.open_in_chemdraw", return_value=True
            ) as mock_open,
        ):
            result = open_chemdraw_file(good, cleanup=False)
        mock_open.assert_called_once()
        assert "Geöffnet" in result
    finally:
        Path(good).unlink()
