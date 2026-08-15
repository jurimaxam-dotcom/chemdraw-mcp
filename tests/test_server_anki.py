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


def test_curated_deck_via_parameter(tmp_path, monkeypatch):
    """Die Starter-Decks sind seit dem Bündeln ein Parameter, kein eigenes Tool."""
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)

    payload = export_anki_deck(curated_deck_id="analgesics-structures")
    assert payload.type == "anki_deck"
    assert payload.name == "Common Analgesics — Structures"
    assert payload.cards == 8
    assert Path(payload.file).exists()


def test_curated_deck_id_beats_own_cards(tmp_path, monkeypatch):
    """Beides gesetzt: das kuratierte Deck gewinnt — inklusive seines Namens.

    Sonst entstünde ein Deck, dessen Name nicht zu seinem Inhalt passt.
    """
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)

    payload = export_anki_deck(
        "Mein Name", _cards(), curated_deck_id="analgesics-structures"
    )
    assert payload.name == "Common Analgesics — Structures"
    assert payload.cards == 8


def test_curated_deck_unknown_id(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="pheur-identity-basics"):
        export_anki_deck(curated_deck_id="nope")


def test_export_anki_deck_needs_a_name_for_own_cards(tmp_path, monkeypatch):
    """Ohne kuratiertes Deck bleiben Name und Karten Pflicht."""
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="Namen"):
        export_anki_deck("", _cards())


def test_export_anki_deck_with_ankiconnect_delivery(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(
        "chemdraw_tool.anki_export.push_via_ankiconnect",
        lambda path: calls.append(path) or "ankiconnect",
    )
    payload = export_anki_deck("Direct", _cards(), deliver="ankiconnect")
    assert payload.delivery == "ankiconnect"
    assert calls and str(calls[0]).endswith(".apkg")


def test_export_anki_deck_default_delivery_is_apkg(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    payload = export_anki_deck("File", _cards())
    assert payload.delivery == "apkg"


def test_export_anki_deck_passes_default_tags(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.ANKI_DIR", tmp_path)
    seen = {}
    import chemdraw_tool.anki_export as ax

    original = ax.write_deck

    def spy(deck_name, cards, out_path, default_tags=None):
        seen["tags"] = default_tags
        return original(deck_name, cards, out_path, default_tags)

    monkeypatch.setattr("chemdraw_tool.anki_export.write_deck", spy)
    export_anki_deck("Tagged", _cards(), default_tags=["klausur"])
    assert seen["tags"] == ["klausur"]
