"""Anki-Deck-Export (.apkg) aus Kartenlisten — genanki + die eigenen Renderer.

Philosophie wie bei generate_spectrum: Das Modell liefert die Fachinhalte
(Kartentexte, Substanzwahl), das Tool rendert die verlässlichen Bilder
(Strukturen, Reaktionsschemata, Spektren) und bettet sie als Medien ein.

Determinismus ist Teil der Spec: deck_id ist ein Hash des Decknamens und
Note-GUIDs hängen nur an Deck + Vorderseite — ein Re-Export (z.B. mit
korrigierten Rückseiten) aktualisiert die Karten in Anki, statt sie zu
duplizieren. Mediendateien sind content-addressed benannt und kollidieren
deshalb weder untereinander noch in Ankis globalem Medienordner.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import genanki

from chemdraw_tool.payloads import AnkiCard, CardSide

# Fix — niemals ändern: eine neue model_id würde in bestehenden
# Anki-Sammlungen einen zweiten Notiztyp anlegen.
MODEL_ID = 1716400001

_CSS = """\
.card {
  font-family: -apple-system, system-ui, sans-serif;
  font-size: 18px;
  text-align: center;
  color: #1a1a1a;
  background-color: #fafafa;
}
.text { margin: 10px 0; }
img {
  max-width: 100%;
  background: #ffffff;
  padding: 8px;
  border-radius: 8px;
}
"""

_MODEL = genanki.Model(
    MODEL_ID,
    "chemdraw-mcp card",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
        }
    ],
    css=_CSS,
)


def deck_id_for(name: str) -> int:
    """Deterministische, große positive Deck-ID aus dem Decknamen."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return (1 << 30) + (int.from_bytes(digest[:8], "big") % (1 << 30))


def _render_visual(side: CardSide) -> bytes | None:
    """Rendert das (höchstens eine) Visual einer Kartenseite als PNG."""
    # Lazy imports: RDKit/matplotlib nur laden, wenn wirklich gezeichnet wird.
    if side.structure:
        from chemdraw_tool.generator import generate_2d
        from chemdraw_tool.image_export import render_molecule_png
        from chemdraw_tool.resolver import resolve

        _, mol = resolve(side.structure)
        return render_molecule_png(generate_2d(mol))

    if side.reaction is not None:
        from chemdraw_tool.generator import generate_2d
        from chemdraw_tool.image_export import render_reaction_png
        from chemdraw_tool.resolver import resolve

        def mols(specs: list[str]):
            out = []
            for s in specs:
                _, mol = resolve(s)
                out.append(generate_2d(mol))
            return out

        return render_reaction_png(
            mols(side.reaction.reactants),
            mols(side.reaction.products),
            side.reaction.conditions,
        )

    if side.spectrum is not None:
        from chemdraw_tool.spectrum import render_spectrum_png

        peaks = [p.model_dump() for p in side.spectrum.peaks]
        return render_spectrum_png(
            side.spectrum.spectrum_type, peaks, title=side.spectrum.title
        )

    return None


def _side_html(side: CardSide, media_dir: Path, media: dict[str, Path]) -> str:
    """HTML einer Kartenseite; schreibt das Visual content-addressed nach
    media_dir und dedupliziert identische Bilder über den Inhalts-Hash."""
    parts = []
    if side.text:
        # Anki-Konvention: Felder dürfen HTML enthalten — bewusst nicht escaped.
        parts.append(f"<div class='text'>{side.text}</div>")
    png = _render_visual(side)
    if png is not None:
        name = f"chemdraw-mcp-{hashlib.sha1(png).hexdigest()[:12]}.png"
        if name not in media:
            media_dir.mkdir(parents=True, exist_ok=True)
            (media_dir / name).write_bytes(png)
            media[name] = media_dir / name
        parts.append(f'<img src="{name}">')
    return "\n".join(parts)


def build_package(
    deck_name: str, cards: list[AnkiCard], media_dir: Path
) -> genanki.Package:
    deck = genanki.Deck(deck_id_for(deck_name), deck_name)
    media: dict[str, Path] = {}
    for card in cards:
        front_html = _side_html(card.front, media_dir, media)
        back_html = _side_html(card.back, media_dir, media)
        note = genanki.Note(
            model=_MODEL,
            fields=[front_html, back_html],
            # GUID nur aus Deck + Vorderseite: korrigierte Rückseiten
            # AKTUALISIEREN die Karte beim Re-Import.
            guid=genanki.guid_for(
                deck_name,
                card.front.text,
                card.front.structure,
                repr(card.front.reaction),
                repr(card.front.spectrum),
            ),
            # Anki verbietet Leerzeichen in Tags — Modell-Input normalisieren.
            tags=[t.replace(" ", "_") for t in card.tags],
        )
        deck.add_note(note)
    package = genanki.Package(deck)
    package.media_files = list(media.values())
    return package


def write_deck(deck_name: str, cards: list[AnkiCard], out_path: Path) -> dict:
    """Schreibt das Deck als .apkg. Returns {"cards": n, "media": m}."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chemdraw_anki_") as tmp:
        package = build_package(deck_name, cards, Path(tmp))
        package.write_to_file(str(out_path))
        return {
            "cards": len(package.decks[0].notes),
            "media": len(package.media_files),
        }
