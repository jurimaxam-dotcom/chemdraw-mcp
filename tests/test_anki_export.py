"""Tests für chemdraw_tool/anki_export.py — Anki-Decks (.apkg) aus Kartenlisten.

Spec (2026-06-11): Das Modell liefert die Fachinhalte (wie bei Spektren),
das Tool rendert verlässliche Bilder. Eine Karte hat zwei Seiten; jede Seite
trägt Text und optional EIN Visual (structure | reaction | spectrum), das als
PNG ins Deck eingebettet wird.

Determinismus ist Pflicht: gleiche deck_id für gleichen Decknamen und stabile
Note-GUIDs, damit ein Re-Export in Anki aktualisiert statt dupliziert. GUIDs
hängen nur an Deck + Vorderseite — eine korrigierte Rückseite ersetzt die
Karte, statt eine zweite zu erzeugen.

Offline: Strukturen in Tests sind SMILES (parse-first, kein Netz).
"""

import zipfile

from chemdraw_tool.anki_export import (
    CLOZE_MODEL_ID,
    MODEL_ID,
    build_package,
    deck_id_for,
    write_deck,
)
from chemdraw_tool.payloads import AnkiCard, CardSide, ReactionSpec

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _structure_card(smiles: str = "CC(=O)Oc1ccccc1C(=O)O") -> AnkiCard:
    return AnkiCard(
        front=CardSide(text="Welche Substanz ist das?", structure=smiles),
        back=CardSide(text="Aspirin (Acetylsalicylsäure)"),
    )


def _text_card() -> AnkiCard:
    return AnkiCard(
        front=CardSide(text="Trivialname von 2-Acetoxybenzoesäure?"),
        back=CardSide(text="Aspirin"),
    )


# ---------------------------------------------------------------------------
# Determinismus
# ---------------------------------------------------------------------------


def test_deck_id_is_deterministic_and_distinct():
    assert deck_id_for("Analgetika") == deck_id_for("Analgetika")
    assert deck_id_for("Analgetika") != deck_id_for("Antibiotika")
    # Anki erwartet große positive IDs
    assert deck_id_for("Analgetika") > 1 << 30


def test_note_guids_stable_across_builds(tmp_path):
    pkg1 = build_package("Deck", [_structure_card(), _text_card()], tmp_path / "m1")
    pkg2 = build_package("Deck", [_structure_card(), _text_card()], tmp_path / "m2")
    guids1 = [n.guid for n in pkg1.decks[0].notes]
    guids2 = [n.guid for n in pkg2.decks[0].notes]
    assert guids1 == guids2
    assert len(set(guids1)) == 2


def test_note_guid_ignores_the_back_side(tmp_path):
    """Korrigierte Rückseite ⇒ gleiche GUID ⇒ Anki aktualisiert die Karte."""
    card_v1 = _structure_card()
    card_v2 = AnkiCard(front=card_v1.front, back=CardSide(text="Aspirin — korrigiert"))
    pkg1 = build_package("Deck", [card_v1], tmp_path / "m1")
    pkg2 = build_package("Deck", [card_v2], tmp_path / "m2")
    assert pkg1.decks[0].notes[0].guid == pkg2.decks[0].notes[0].guid


def test_guid_differs_between_decks(tmp_path):
    """Gleiche Karte in zwei Decks = zwei eigenständige Notes."""
    pkg1 = build_package("Deck A", [_text_card()], tmp_path / "m1")
    pkg2 = build_package("Deck B", [_text_card()], tmp_path / "m2")
    assert pkg1.decks[0].notes[0].guid != pkg2.decks[0].notes[0].guid


# ---------------------------------------------------------------------------
# Visuals → eingebettete Medien
# ---------------------------------------------------------------------------


def test_structure_visual_becomes_png_media(tmp_path):
    pkg = build_package("Deck", [_structure_card()], tmp_path / "media")
    assert len(pkg.media_files) == 1
    data = open(pkg.media_files[0], "rb").read()
    assert data[: len(PNG_MAGIC)] == PNG_MAGIC


def test_card_html_embeds_the_image(tmp_path):
    pkg = build_package("Deck", [_structure_card()], tmp_path / "media")
    front_html = pkg.decks[0].notes[0].fields[0]
    assert "<img src=" in front_html
    assert "Welche Substanz ist das?" in front_html


def test_text_only_cards_need_no_media(tmp_path):
    pkg = build_package("Deck", [_text_card()], tmp_path / "media")
    assert pkg.media_files == []


def test_identical_visuals_are_deduplicated(tmp_path):
    """Zwei Karten mit derselben Struktur teilen sich eine Mediendatei
    (content-addressed Dateinamen)."""
    cards = [
        AnkiCard(front=CardSide(text="A", structure="c1ccccc1"), back=CardSide(text="x")),
        AnkiCard(front=CardSide(text="B", structure="c1ccccc1"), back=CardSide(text="y")),
    ]
    pkg = build_package("Deck", cards, tmp_path / "media")
    assert len(pkg.media_files) == 1


def test_reaction_visual_renders_scheme(tmp_path):
    card = AnkiCard(
        front=CardSide(text="Nachweis: Veresterung von Essigsäure mit Ethanol?"),
        back=CardSide(
            text="Fischer-Veresterung",
            reaction=ReactionSpec(
                reactants=["CCO", "CC(=O)O"],
                products=["CCOC(C)=O", "O"],
                conditions="H₂SO₄ (cat.), Δ",
            ),
        ),
    )
    pkg = build_package("Deck", [card], tmp_path / "media")
    assert len(pkg.media_files) == 1
    assert "<img src=" in pkg.decks[0].notes[0].fields[1]


# ---------------------------------------------------------------------------
# Datei-Export
# ---------------------------------------------------------------------------


def test_write_deck_produces_an_apkg_archive(tmp_path):
    out = tmp_path / "analgetika.apkg"
    stats = write_deck("Analgetika", [_structure_card(), _text_card()], out)
    assert out.exists()
    assert stats == {"cards": 2, "media": 1}
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "media" in names
        assert any(n.startswith("collection.anki2") for n in names)


# ---------------------------------------------------------------------------
# Optionen-Paket (2026-06-11): reversed, Cloze, default_tags, AnkiConnect
# ---------------------------------------------------------------------------


def test_reversed_card_uses_the_two_template_model(tmp_path):
    card = AnkiCard(
        front=CardSide(text="Ibuprofen?", structure="CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
        back=CardSide(text="Ibuprofen"),
        reversed=True,
    )
    pkg = build_package("Deck", [card], tmp_path / "m")
    note = pkg.decks[0].notes[0]
    assert len(note.model.templates) == 2  # Front→Back UND Back→Front
    assert note.model.model_id != MODEL_ID  # eigenes, festes Modell


def test_cloze_card_uses_the_cloze_model(tmp_path):
    card = AnkiCard(
        front=CardSide(text="Die Ester-C=O-Bande liegt bei {{c1::~1740 cm⁻¹}}."),
        back=CardSide(text="Typisch für Ethylacetat."),
        cloze=True,
    )
    pkg = build_package("Deck", [card], tmp_path / "m")
    note = pkg.decks[0].notes[0]
    assert note.model.model_id == CLOZE_MODEL_ID
    assert "{{c1::" in note.fields[0]
    assert "Typisch für Ethylacetat." in note.fields[1]  # im Styling-<div>


def test_cloze_and_reversed_are_mutually_exclusive(tmp_path):
    import pytest

    card = AnkiCard(
        front=CardSide(text="{{c1::x}}"),
        back=CardSide(text=""),
        cloze=True,
        reversed=True,
    )
    with pytest.raises(ValueError, match="[Cc]loze"):
        build_package("Deck", [card], tmp_path / "m")


def test_default_tags_are_added_and_normalized(tmp_path):
    pkg = build_package(
        "Deck",
        [_text_card()],
        tmp_path / "m",
        default_tags=["klausur 2026", "pharma"],
    )
    tags = list(pkg.decks[0].notes[0].tags)
    assert "klausur_2026" in tags
    assert "pharma" in tags


def test_guids_stay_stable_for_all_card_types(tmp_path):
    cards = [
        AnkiCard(front=CardSide(text="A?"), back=CardSide(text="a"), reversed=True),
        AnkiCard(front=CardSide(text="{{c1::b}}"), back=CardSide(text=""), cloze=True),
    ]
    g1 = [n.guid for n in build_package("D", cards, tmp_path / "m1").decks[0].notes]
    g2 = [n.guid for n in build_package("D", cards, tmp_path / "m2").decks[0].notes]
    assert g1 == g2


def test_ankiconnect_import_calls_the_local_api(tmp_path, monkeypatch):
    from unittest.mock import MagicMock

    from chemdraw_tool import anki_export

    fake = MagicMock()
    fake.return_value.json.return_value = {"result": True, "error": None}
    monkeypatch.setattr(anki_export.requests, "post", fake)
    out = tmp_path / "deck.apkg"
    out.write_bytes(b"x")
    status = anki_export.push_via_ankiconnect(out)
    assert status == "ankiconnect"
    payload = fake.call_args.kwargs.get("json") or fake.call_args.args[1]
    assert payload["action"] == "importPackage"
    assert payload["params"]["path"] == str(out)


def test_ankiconnect_unreachable_degrades_gracefully(tmp_path, monkeypatch):
    from chemdraw_tool import anki_export

    def boom(*a, **k):
        raise anki_export.requests.ConnectionError("no anki")

    monkeypatch.setattr(anki_export.requests, "post", boom)
    status = anki_export.push_via_ankiconnect(tmp_path / "x.apkg")
    assert status == "ankiconnect-unreachable"
