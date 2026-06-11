"""Tests für das export_anki_deck-Server-Tool.

Schreibt das .apkg nach ANKI_DIR und liefert einen AnkiDeckPayload fürs
UI-Panel. Offline: Strukturen als SMILES.
"""

from pathlib import Path

from chemdraw_tool.payloads import AnkiCard, CardSide
from chemdraw_tool.server import export_anki_deck


def _cards() -> list[AnkiCard]:
    return [
        AnkiCard(
            front=CardSide(text="Welche Substanz?", structure="CC(=O)Oc1ccccc1C(=O)O"),
            back=CardSide(text="Aspirin"),
        ),
        AnkiCard(
            front=CardSide(text="Trivialname von Ethansäure?"),
            back=CardSide(text="Essigsäure"),
        ),
    ]


def test_export_anki_deck_writes_apkg_and_returns_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    payload = export_anki_deck("Pharmazie Basics", _cards())
    assert payload.type == "anki_deck"
    assert payload.name == "Pharmazie Basics"
    assert payload.cards == 2
    assert payload.media == 1
    assert payload.fronts == ["Welche Substanz?", "Trivialname von Ethansäure?"]
    file = Path(payload.file)
    assert file.exists()
    assert file.suffix == ".apkg"
    assert file.parent == tmp_path


def test_export_anki_deck_rejects_empty_deck(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="[Kk]arte|[Cc]ard"):
        export_anki_deck("Leer", [])


def test_generate_3d_writes_sdf_and_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.THREED_DIR", tmp_path)
    from chemdraw_tool.server import generate_3d

    payload = generate_3d("CCO", label="Ethanol")
    assert payload.type == "molecule3d"
    assert payload.name == "Ethanol"
    assert len(payload.atoms) == 9  # C2H6O mit expliziten H
    assert len(payload.bonds) == 8
    sdf = Path(payload.files["sdf"])
    assert sdf.exists()
    assert "V2000" in sdf.read_text()
