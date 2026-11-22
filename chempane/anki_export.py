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

import base64
import hashlib
import html
import io
import re
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

import genanki
import requests

from chempane.payloads import AnkiCard, CardSide

# Fix — niemals ändern: eine neue model_id würde in bestehenden
# Anki-Sammlungen einen zweiten Notiztyp anlegen.
MODEL_ID = 1716400001
REVERSED_MODEL_ID = 1716400002
CLOZE_MODEL_ID = 1716400003

ANKICONNECT_URL = "http://127.0.0.1:8765"

# Kartenbild nach dem Design-Entwurf vom 25.10.2026: vorn nur Struktur und
# Frage, hinten das Bild klein über Name, Formel, CAS. Die Templates bleiben
# unverändert (sonst legt Anki beim Import einen zweiten Notiztyp an) — die
# Antwortseite erkennt das CSS an hr#answer, das nur dort steht.
# Nachtmodus: Anki setzt .nightMode (älter: .night_mode) auf .card bzw. body;
# das PNG wird invertiert, hue-rotate holt die Elementfarben (O rot, N blau)
# zurück. Strukturen und Reaktionen kommen mit transparentem Hintergrund
# (_render_visual), damit kein heller bzw. dunkler Kasten auf der Karte liegt.
_CSS = """\
.card {
  font-family: -apple-system, system-ui, sans-serif;
  font-size: 18px;
  text-align: center;
  color: #1C1C1E;
  background-color: #FAFAF7;
}
.text { margin: 10px 0; }
img {
  max-width: 100%;
  max-height: 300px;
}
.prompt { margin-top: 24px; font-size: 15px; color: #6B6B6B; }
.card:has(#answer) img { max-height: 180px; }
.card:has(#answer) .prompt { display: none; }
hr#answer { border: 0; border-top: 1px solid #DADAD5; margin: 20px 0; }
.name { font-size: 40px; font-weight: 700; line-height: 1.1; }
.formula { font-size: 22px; margin-top: 8px; }
.meta { font-size: 14px; color: #6B6B6B; margin-top: 8px; line-height: 1.4; }
.card.nightMode, .card.night_mode, .nightMode .card, .night_mode .card {
  color: #F2F2F2;
  background-color: #1C1C1E;
}
.card.nightMode img, .card.night_mode img, .nightMode .card img, .night_mode .card img {
  filter: invert(1) hue-rotate(180deg);
}
.card.nightMode .prompt, .card.night_mode .prompt, .nightMode .card .prompt, .night_mode .card .prompt,
.card.nightMode .meta, .card.night_mode .meta, .nightMode .card .meta, .night_mode .card .meta {
  color: #9A9A9A;
}
.card.nightMode hr#answer, .card.night_mode hr#answer, .nightMode .card hr#answer, .night_mode .card hr#answer {
  border-top-color: #3A3A3C;
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

_MODEL_REVERSED = genanki.Model(
    REVERSED_MODEL_ID,
    "chemdraw-mcp card (and reversed)",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
        },
        {
            "name": "Card 2",
            "qfmt": "{{Back}}",
            "afmt": "{{FrontSide}}<hr id=answer>{{Front}}",
        },
    ],
    css=_CSS,
)

_MODEL_CLOZE = genanki.Model(
    CLOZE_MODEL_ID,
    "chemdraw-mcp cloze",
    model_type=genanki.Model.CLOZE,
    fields=[{"name": "Text"}, {"name": "Back Extra"}],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": "{{cloze:Text}}<br>{{Back Extra}}",
        }
    ],
    css=_CSS,
)


def deck_id_for(name: str) -> int:
    """Deterministische, große positive Deck-ID aus dem Decknamen."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return (1 << 30) + (int.from_bytes(digest[:8], "big") % (1 << 30))


# Zuletzt gezeichnete Kartenbilder (Etappe 5): die Panel-Vorschau nimmt dasselbe PNG wie das
# Deck, ohne den Namen ein zweites Mal aufzulösen oder neu zu zeichnen.
_VISUALS: OrderedDict[str, bytes | None] = OrderedDict()
_VISUALS_MAX = 64


def _render_visual(side: CardSide) -> bytes | None:
    """Das Kartenbild einer Seite, aus dem Zwischenspeicher oder frisch gezeichnet."""
    key = side.model_dump_json(exclude={"text"})
    if key in _VISUALS:
        _VISUALS.move_to_end(key)
        return _VISUALS[key]
    png = _draw_visual(side)
    _VISUALS[key] = png
    while len(_VISUALS) > _VISUALS_MAX:
        _VISUALS.popitem(last=False)
    return png


def _draw_visual(side: CardSide) -> bytes | None:
    """Rendert das (höchstens eine) Visual einer Kartenseite als PNG."""
    # Lazy imports: RDKit/matplotlib nur laden, wenn wirklich gezeichnet wird.
    if side.structure:
        from chempane.generator import generate_2d
        from chempane.image_export import render_molecule_png
        from chempane.resolver import resolve

        _, mol = resolve(side.structure)
        return render_molecule_png(generate_2d(mol), transparent=True)

    if side.reaction is not None:
        from chempane.generator import generate_2d
        from chempane.image_export import render_reaction_png
        from chempane.resolver import resolve

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
            transparent=True,
        )

    if side.spectrum is not None:
        from chempane.spectrum import render_spectrum_png

        peaks = [p.model_dump() for p in side.spectrum.peaks]
        return render_spectrum_png(
            side.spectrum.spectrum_type, peaks, title=side.spectrum.title
        )

    return None


# Kartentext kommt vom Modell und damit potenziell aus einer Prompt-Injection;
# Anki rendert Felder als HTML in einem Webview mit JavaScript. Deshalb alles
# escapen und nur attributlose Formatierungs-Tags plus Entities zurückholen
# (Sicherheitsscan B1).
_ALLOWED_TAG = re.compile(r"&lt;/?(?:b|i|sub|sup)&gt;|&lt;br\s*/?&gt;")
_ENTITY = re.compile(r"&amp;(#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")


def _safe_text(text: str) -> str:
    out = html.escape(text, quote=False)
    out = _ALLOWED_TAG.sub(lambda m: html.unescape(m[0]), out)
    return _ENTITY.sub(r"&\1;", out)


def _side_html(
    side: CardSide, media_dir: Path, media: dict[str, Path], prompt: bool = False
) -> str:
    """HTML einer Kartenseite; schreibt das Visual content-addressed nach
    media_dir und dedupliziert identische Bilder über den Inhalts-Hash.
    prompt: eine Vorderseite, die nur ein Bild ist, bekommt die Frage darunter."""
    parts = []
    if side.text:
        parts.append(f"<div class='text'>{_safe_text(side.text)}</div>")
    png = _render_visual(side)
    if png is not None:
        name = f"chemdraw-mcp-{hashlib.sha1(png).hexdigest()[:12]}.png"
        if name not in media:
            media_dir.mkdir(parents=True, exist_ok=True)
            (media_dir / name).write_bytes(png)
            media[name] = media_dir / name
        parts.append(f'<img src="{name}">')
        if prompt and not side.text:
            parts.append("<div class='prompt'>Which molecule?</div>")
    return "\n".join(parts)


def _model_for(card: AnkiCard) -> genanki.Model:
    if card.cloze and card.reversed:
        raise ValueError("A card cannot be both cloze and reversed.")
    if card.cloze:
        return _MODEL_CLOZE
    return _MODEL_REVERSED if card.reversed else _MODEL


def build_package(
    deck_name: str,
    cards: list[AnkiCard],
    media_dir: Path,
    default_tags: list[str] | None = None,
) -> genanki.Package:
    deck = genanki.Deck(deck_id_for(deck_name), deck_name)
    media: dict[str, Path] = {}
    for card in cards:
        model = _model_for(card)
        front_html = _side_html(
            card.front, media_dir, media, prompt=model is _MODEL
        )
        back_html = _side_html(card.back, media_dir, media)
        note = genanki.Note(
            model=model,
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
            tags=[
                t.replace(" ", "_")
                for t in [*card.tags, *(default_tags or [])]
            ],
        )
        deck.add_note(note)
    package = genanki.Package(deck)
    package.media_files = list(media.values())
    return package


def push_via_ankiconnect(apkg_path: Path) -> str:
    """Lässt das laufende Anki die .apkg selbst importieren (AnkiConnect-
    Add-on, Action importPackage) — so greift dieselbe GUID-Update-Semantik
    wie beim manuellen Import. Kein Anki/Add-on erreichbar ⇒ degradiert
    still, die Datei bleibt der Weg."""
    try:
        resp = requests.post(
            ANKICONNECT_URL,
            json={
                "action": "importPackage",
                "version": 6,
                "params": {"path": str(apkg_path)},
            },
            timeout=5,
        )
        result = resp.json()
    except Exception:
        return "ankiconnect-unreachable"
    if result.get("error"):
        return f"ankiconnect-error: {result['error']}"
    return "ankiconnect"


def open_with_default_app(apkg_path: Path) -> str:
    """Öffnet die .apkg mit dem Standardprogramm — auf macOS startet Anki
    und zeigt den Import. Anderswo nur speichern; scheitert `open`, bleibt
    die Datei der Weg. Der Rückgabewert meldet ehrlich, was passiert ist."""
    if sys.platform != "darwin":
        return "apkg"
    try:
        subprocess.run(["open", str(apkg_path)], check=True, timeout=10)
    except Exception:
        return "apkg"
    return "open"


def write_deck(
    deck_name: str,
    cards: list[AnkiCard],
    out_path: Path,
    default_tags: list[str] | None = None,
) -> dict:
    """Schreibt das Deck als .apkg. Returns {"cards": n, "media": m}."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chemdraw_anki_") as tmp:
        package = build_package(deck_name, cards, Path(tmp), default_tags)
        package.write_to_file(str(out_path))
        return {
            "cards": len(package.decks[0].notes),
            "media": len(package.media_files),
        }


# Vorschau im Panel (Etappe 5, 16.11.2026): die ersten Karten mit Vorder- und Rückseite und
# dem Bild der Karte als kleines PNG. Mehr Karten zeigt das Panel als „+ n more“ — jede
# Vorschau reist im Tool-Ergebnis mit, das auch Claude liest.
PREVIEW_CARDS = 6
_THUMB = (300, 200)


def _thumbnail(png: bytes | None) -> str:
    if not png:
        return ""
    from PIL import Image

    with Image.open(io.BytesIO(png)) as img:
        img.thumbnail(_THUMB)
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def card_previews(cards: list[AnkiCard], limit: int = PREVIEW_CARDS) -> list[dict]:
    """Vorder- und Rückseite der ersten Karten: Text wie im Deck (Anki-HTML), Bild als data-URI.
    Nach write_deck aufgerufen, kommen die Bilder aus dem Zwischenspeicher."""
    previews = []
    for card in cards[:limit]:
        previews.append({
            "front": card.front.text,
            "back": card.back.text,
            "front_image": _thumbnail(_render_visual(card.front)),
            "back_image": _thumbnail(_render_visual(card.back)),
        })
    return previews
