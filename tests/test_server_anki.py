"""Tests für das export_anki_deck-Server-Tool.

Schreibt das .apkg nach ANKI_DIR und liefert einen AnkiDeckPayload fürs
UI-Panel. Offline: Strukturen als SMILES.
"""

from pathlib import Path

from chempane.payloads import AnkiCard, CardSide
from chempane.server import export_anki_deck


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
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
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
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="[Kk]arte|[Cc]ard"):
        export_anki_deck("Leer", [])


def test_generate_3d_writes_sdf_and_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.THREED_DIR", tmp_path)
    from chempane.server import generate_3d

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
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)

    payload = export_anki_deck(curated_deck_id="analgesics-structures")
    assert payload.type == "anki_deck"
    assert payload.name == "Common Analgesics — Structures"
    assert payload.cards == 8
    assert Path(payload.file).exists()


def test_curated_deck_id_beats_own_cards(tmp_path, monkeypatch):
    """Beides gesetzt: das kuratierte Deck gewinnt — inklusive seines Namens.

    Sonst entstünde ein Deck, dessen Name nicht zu seinem Inhalt passt.
    """
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)

    payload = export_anki_deck(
        "Mein Name", _cards(), curated_deck_id="analgesics-structures"
    )
    assert payload.name == "Common Analgesics — Structures"
    assert payload.cards == 8


def test_curated_deck_unknown_id(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="pheur-identity-basics"):
        export_anki_deck(curated_deck_id="nope")


def test_export_anki_deck_needs_a_name_for_own_cards(tmp_path, monkeypatch):
    """Ohne kuratiertes Deck bleiben Name und Karten Pflicht."""
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    import pytest

    with pytest.raises(ValueError, match="name"):
        export_anki_deck("", _cards())


def test_export_anki_deck_with_ankiconnect_delivery(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(
        "chempane.anki_export.push_via_ankiconnect",
        lambda path: calls.append(path) or "ankiconnect",
    )
    payload = export_anki_deck("Direct", _cards(), deliver="ankiconnect")
    assert payload.delivery == "ankiconnect"
    assert calls and str(calls[0]).endswith(".apkg")


def test_export_anki_deck_default_delivery_is_apkg(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    payload = export_anki_deck("File", _cards())
    assert payload.delivery == "apkg"


def test_export_anki_deck_passes_default_tags(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    seen = {}
    import chempane.anki_export as ax

    original = ax.write_deck

    def spy(deck_name, cards, out_path, default_tags=None):
        seen["tags"] = default_tags
        return original(deck_name, cards, out_path, default_tags)

    monkeypatch.setattr("chempane.anki_export.write_deck", spy)
    export_anki_deck("Tagged", _cards(), default_tags=["klausur"])
    assert seen["tags"] == ["klausur"]


def test_open_delivery_hands_the_file_to_the_default_app_on_macos(tmp_path, monkeypatch):
    """deliver="open": Datei schreiben und mit dem Standardprogramm öffnen —
    auf macOS zeigt Anki dann den Import. Im Test läuft nie ein echtes `open`."""
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    monkeypatch.setattr("sys.platform", "darwin")
    calls = []
    monkeypatch.setattr(
        "chempane.anki_export.subprocess.run",
        lambda args, **kw: calls.append(args),
    )
    payload = export_anki_deck("ChemDraw", _cards(), deliver="open")
    assert payload.delivery == "open"
    assert calls == [["open", payload.file]]
    assert Path(payload.file).exists()


def test_open_delivery_only_saves_outside_macos(tmp_path, monkeypatch):
    """Anderswo kein Öffnen — und delivery meldet ehrlich nur die Datei."""
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    monkeypatch.setattr("sys.platform", "linux")
    calls = []
    monkeypatch.setattr(
        "chempane.anki_export.subprocess.run",
        lambda args, **kw: calls.append(args),
    )
    payload = export_anki_deck("ChemDraw", _cards(), deliver="open")
    assert payload.delivery == "apkg"
    assert calls == []
    assert Path(payload.file).exists()


def test_open_delivery_falls_back_to_the_file_when_open_fails(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    monkeypatch.setattr("sys.platform", "darwin")

    def boom(args, **kw):
        raise OSError("kein open")

    monkeypatch.setattr("chempane.anki_export.subprocess.run", boom)
    payload = export_anki_deck("ChemDraw", _cards(), deliver="open")
    assert payload.delivery == "apkg"
    assert Path(payload.file).exists()


# Etappe 5 (16.11.2026): das Panel zeigt eine Vorschau der Karten — Vorder- und Rückseite,
# mit dem Bild, das auch im Deck steht (verkleinert), für die ersten Karten.
def test_payload_carries_card_previews_with_thumbnails(tmp_path, monkeypatch):
    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    payload = export_anki_deck("Vorschau", _cards())
    assert len(payload.previews) == 2
    first, second = payload.previews
    assert first.front == "Welche Substanz?" and first.back == "Aspirin"
    assert first.front_image.startswith("data:image/png;base64,")
    assert first.back_image == ""
    assert second.front == "Trivialname von Ethansäure?" and second.front_image == ""


def test_preview_thumbnail_is_small(tmp_path, monkeypatch):
    import base64
    import io

    from PIL import Image

    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    image = export_anki_deck("Klein", _cards()).previews[0].front_image
    png = base64.b64decode(image.split(",", 1)[1])
    width, height = Image.open(io.BytesIO(png)).size
    assert width <= 320 and height <= 220, (width, height)
    assert len(image) < 30_000


def test_previews_only_for_the_first_cards(tmp_path, monkeypatch):
    from chempane.anki_export import PREVIEW_CARDS

    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    cards = [AnkiCard(front=CardSide(text=f"Frage {i}"), back=CardSide(text=f"Antwort {i}")) for i in range(10)]
    payload = export_anki_deck("Viele", cards)
    assert payload.cards == 10
    assert len(payload.previews) == PREVIEW_CARDS < 10
    assert payload.previews[-1].front == f"Frage {PREVIEW_CARDS - 1}"


def test_preview_reuses_the_rendered_deck_image(tmp_path, monkeypatch):
    """Die Vorschau zeichnet nicht ein zweites Mal: ein Name wird einmal aufgelöst."""
    from collections import OrderedDict

    import chempane.anki_export as ax
    import chempane.resolver as resolver

    monkeypatch.setattr("chempane.server.ANKI_DIR", tmp_path)
    monkeypatch.setattr(ax, "_VISUALS", OrderedDict())  # Zwischenspeicher früherer Tests leeren
    calls = []
    original = resolver.resolve

    def counting(text, *a, **kw):
        calls.append(text)
        return original(text, *a, **kw)

    monkeypatch.setattr(resolver, "resolve", counting)
    export_anki_deck("Einmal", [AnkiCard(front=CardSide(structure="CCO"), back=CardSide(text="Ethanol"))])
    assert calls == ["CCO"]
