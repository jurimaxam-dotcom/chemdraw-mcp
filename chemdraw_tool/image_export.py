"""Serverseitiges Struktur-Rendering als PNG/SVG-Dateien — der Primärpfad.

Seit der ChemDraw-Entkopplung (2026-06-09) sind PNG und SVG die primären
Artefakte der generate_*-Tools; CDXML ist ein optionales Zusatzformat.
PNG kommt aus RDKits Cairo-Backend (im PyPI-Wheel enthalten), SVG aus
MolDraw2DSVG — beides offline, ohne ChemDraw, ohne neue Dependencies.

Abgrenzung zu svg_renderer.py: dort entstehen UI-Vorschau-SVGs (ViewBox-
Cropping, fill_container, Atom-Highlights). Hier entstehen eigenständige
*Dateien* mit fester Größe und Legende (Name unter der Struktur) —
druckfertig fürs Protokoll.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point2D, Point3D

from chemdraw_tool.render_style import apply_style, get_style
from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# 1000x800 px ≈ 8,5 cm Bildbreite bei 300 dpi — druckfertig für Protokolle.
MOL_PNG_SIZE = (1000, 800)
MOL_SVG_SIZE = (500, 400)
# Reaktionen sind breit (Edukte + Pfeil + Produkte).
RXN_PNG_SIZE = (1600, 480)
RXN_SVG_SIZE = (900, 270)

# Reaktions-Layout in Mol-Koordinaten (RDKit-Bondlänge ≈ 1.5 Einheiten).
# Atomlabels (OH, H2O) werden um die Atom-KOORDINATE herum gezeichnet und
# ragen darüber hinaus — LABEL_PAD reserviert diesen Überhang, damit '+'
# und Pfeil nie mit Labels kollidieren (RDKits DrawReaction tat genau das).
LABEL_PAD = 0.9
PLUS_GAP = 1.2
ARROW_LENGTH = 4.0
ARROW_PAD = 0.9
# Texthöhe der Conditions-Zeile in Mol-Koordinaten (Atomlabels sind ~0.7).
CONDITIONS_FONT = 0.55

# Pfeiltypen (Etappe 3). "forward" ist der bisherige Pfeil und bleibt
# bytegleich; die beiden anderen sind Opt-in.
ARROW_TYPES = ("forward", "equilibrium", "retro")
# Vorwärtspfeil: RDKit DrawArrow mit frac=0.12, Winkel 30° — halbe Kopfbreite.
_HEAD_FRAC = 0.12
_TAN30 = 0.5773502691896257
# Abstand der Bedingungs-Grundlinie über der Pfeilachse beim Vorwärtspfeil
# (Mol-Koordinaten). Andere Pfeile ragen höher und schieben den Text mit.
_ABOVE_BASELINE = 0.35
_LINE_SPACING = 1.25


def _check_arrow(arrow: str) -> None:
    if arrow not in ARROW_TYPES:
        raise ValueError(
            f"Unknown arrow {arrow!r}; use one of {', '.join(ARROW_TYPES)}."
        )


def _arrow_extent(arrow: str, arrow_length: float) -> float:
    """Wie weit der Pfeil über/unter seine Achse ragt (Mol-Koordinaten)."""
    f = arrow_length / ARROW_LENGTH
    if arrow == "equilibrium":
        return 0.15 * f + _HEAD_FRAC * arrow_length * _TAN30
    if arrow == "retro":
        return 0.3 * f
    return _HEAD_FRAC * arrow_length * _TAN30


def _draw_arrow_glyph(drawer, tail, head, arrow: str, arrow_length: float) -> None:
    """Zeichnet den Pfeil in Mol-Koordinaten — PNG und SVG gehen durch
    dieselben Aufrufe, die Parität bleibt also ohne Backend-Sonderwege.

    equilibrium (⇌): oberer Schaft nach rechts mit Halbspitze oben, unterer
    nach links mit Halbspitze unten. retro (⇒): Doppelschaft mit offener
    Winkelspitze, die Schäfte enden auf den Spitzenschenkeln.
    """
    (tx, ty), (hx, hy) = tail, head
    if arrow == "forward":
        drawer.DrawArrow(Point2D(tx, ty), Point2D(hx, hy), True, 0.12)
        return
    f = arrow_length / ARROW_LENGTH
    if arrow == "equilibrium":
        d = 0.15 * f
        h = _HEAD_FRAC * arrow_length
        w = h * _TAN30
        drawer.SetFillPolys(True)
        drawer.DrawLine(Point2D(tx, ty + d), Point2D(hx, hy + d))
        drawer.DrawPolygon(
            [Point2D(hx, hy + d), Point2D(hx - h, hy + d), Point2D(hx - h, hy + d + w)]
        )
        drawer.DrawLine(Point2D(hx, hy - d), Point2D(tx, ty - d))
        drawer.DrawPolygon(
            [Point2D(tx, ty - d), Point2D(tx + h, ty - d), Point2D(tx + h, ty - d - w)]
        )
        return
    # retro
    d = 0.12 * f
    h = 0.45 * f
    w = 0.3 * f
    shaft_end = hx - h * d / w
    drawer.DrawLine(Point2D(tx, ty + d), Point2D(shaft_end, hy + d))
    drawer.DrawLine(Point2D(tx, ty - d), Point2D(shaft_end, hy - d))
    drawer.DrawLine(Point2D(hx - h, hy + w), Point2D(hx, hy))
    drawer.DrawLine(Point2D(hx, hy), Point2D(hx - h, hy - w))


def _text_baselines(
    above: str, below: str, arrow: str, style: str
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Zeilen mit Grundlinien-Abstand zur Pfeilachse (Mol-Koordinaten,
    positiv = nach oben). Oben stapeln die Zeilen nach oben, unten nach unten;
    die erste Zeile steht jeweils oben."""
    arrow_length, font = _reaction_metrics(style)
    line = font * _LINE_SPACING
    if arrow == "forward":
        first_above = _ABOVE_BASELINE
    else:
        first_above = _ABOVE_BASELINE + (
            _arrow_extent(arrow, arrow_length) - _arrow_extent("forward", arrow_length)
        )
    above_lines = above.split("\n") if above else []
    n = len(above_lines)
    out_above = [
        (text, first_above + (n - 1 - i) * line) for i, text in enumerate(above_lines)
    ]
    first_below = _arrow_extent(arrow, arrow_length) + 0.1 + 0.75 * font
    out_below = [
        (text, -(first_below + i * line))
        for i, text in enumerate(below.split("\n") if below else [])
    ]
    return out_above, out_below


def _reaction_metrics(style: str) -> tuple[float, float]:
    """(Pfeillänge, Conditions-Schriftgröße) in Mol-Koordinaten für einen Stil.

    Beide skalieren mit demselben Faktor: der Text sitzt mittig über dem Pfeil,
    der Zwischenraum zwischen Edukten und Produkten ist aber fest. Würde nur
    die Schrift wachsen, schöbe sich der Text in die Strukturen (bei
    'presentation' reproduziert). Gemeinsam skaliert bleibt das
    Kollisionsverhalten exakt das des Standardstils.
    """
    preset = get_style(style)
    factor = preset.conditions_font_scale if preset else 1.0
    return ARROW_LENGTH * factor, CONDITIONS_FONT * factor


def _draw_molecule(
    drawer,
    mol,
    legend: str,
    annotate_stereo: bool = False,
    style: str = "",
    transparent: bool = False,
) -> None:
    # Gleiche Strichstärke wie die UI-Vorschau (gemeinsame Konstante) — die Datei
    # darf nicht anders aussehen als das, was der Nutzer im Chat gesehen hat.
    # Bewusst NICHT übernommen: fixedBondLength (Datei soll die Canvas füllen)
    # und clearBackground=False (Datei braucht weißen Hintergrund). Ausnahme
    # per Opt-in: die Anki-Karte legt das Bild auf ihren eigenen Hintergrund.
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    if transparent:
        drawer.drawOptions().clearBackground = False
    if annotate_stereo:
        drawer.drawOptions().addStereoAnnotation = True
    # Nach der Basis, damit ein Preset die Strichstärke überschreiben kann,
    # ohne BOND_LINE_WIDTH umzudefinieren — svg_renderer.render_svg wendet das
    # Preset an derselben Stelle an, deshalb bleibt die Parität je Stil erhalten.
    apply_style(drawer.drawOptions(), style)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend)
    drawer.FinishDrawing()


def render_molecule_png(
    mol,
    legend: str = "",
    size: tuple[int, int] = MOL_PNG_SIZE,
    annotate_stereo: bool = False,
    style: str = "",
    transparent: bool = False,
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    _draw_molecule(drawer, mol, legend, annotate_stereo, style, transparent)
    return drawer.GetDrawingText()


def render_molecule_svg(
    mol,
    legend: str = "",
    size: tuple[int, int] = MOL_SVG_SIZE,
    annotate_stereo: bool = False,
    style: str = "",
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    _draw_molecule(drawer, mol, legend, annotate_stereo, style)
    return drawer.GetDrawingText()


@dataclass(frozen=True)
class ReactionLayout:
    """Alle Komponenten als EIN Mol mit nebeneinander verschobenen Conformern
    plus die Positionen der Schema-Glyphen (Mol-Koordinaten)."""

    mol: Chem.Mol
    plus_positions: list[tuple[float, float]]
    arrow: tuple[tuple[float, float], tuple[float, float]]


def _shifted_copy(mol: Chem.Mol, dx: float, dy: float) -> Chem.Mol:
    copy = Chem.Mol(mol)
    conf = copy.GetConformer()
    for i in range(copy.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + dx, p.y + dy, 0.0))
    return copy


def _compose_reaction(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    arrow_length: float = ARROW_LENGTH,
) -> ReactionLayout:
    """Layoutet Edukte + Produkte auf einer Mittellinie (y=0).

    Eigenes Compositing statt RDKit DrawReaction: das verlor Ein-Atom-
    Moleküle (H₂O) und setzte '+' kollidierend in Atomlabels. Ein
    kombiniertes Mol garantiert zudem eine einheitliche Bindungslänge
    über alle Komponenten.
    """
    placed: list[Chem.Mol] = []
    plus_positions: list[tuple[float, float]] = []
    cursor = 0.0

    def place(mol: Chem.Mol) -> None:
        nonlocal cursor
        conf = mol.GetConformer()
        xs = [conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())]
        ys = [conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())]
        dx = cursor + LABEL_PAD - min(xs)
        dy = -(min(ys) + max(ys)) / 2
        placed.append(_shifted_copy(mol, dx, dy))
        cursor += LABEL_PAD + (max(xs) - min(xs)) + LABEL_PAD

    for i, mol in enumerate(reactants):
        if i > 0:
            plus_positions.append((cursor + PLUS_GAP / 2, 0.0))
            cursor += PLUS_GAP
        place(mol)

    arrow_tail = cursor + ARROW_PAD
    arrow_head = arrow_tail + arrow_length
    cursor = arrow_head + ARROW_PAD

    for i, mol in enumerate(products):
        if i > 0:
            plus_positions.append((cursor + PLUS_GAP / 2, 0.0))
            cursor += PLUS_GAP
        place(mol)

    combined = placed[0]
    for m in placed[1:]:
        combined = Chem.CombineMols(combined, m)
    return ReactionLayout(
        combined, plus_positions, ((arrow_tail, 0.0), (arrow_head, 0.0))
    )


def _draw_reaction(
    drawer,
    reactants,
    products,
    style: str = "",
    transparent: bool = False,
    arrow: str = "forward",
) -> tuple[tuple[float, float], float]:
    """Zeichnet das Schema (ohne Conditions) und liefert die Pixel-Position
    der Pfeilmitte plus die Skala (Pixel pro Mol-Koordinaten-Einheit).

    Conditions-Text geht NICHT über drawer.DrawString: das rendert Strings
    mit der Atomlabel-Engine, die 'H2SO4 (cat.)' als chemische Formel parst
    und mehrzeilig um ein Anker-Atom stapelt. Die Backends overlayen den
    Text selbst (SVG: <text>, PNG: Pillow).
    """
    arrow_length, _ = _reaction_metrics(style)
    layout = _compose_reaction(reactants, products, arrow_length)
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    if transparent:
        drawer.drawOptions().clearBackground = False
    apply_style(drawer.drawOptions(), style)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, layout.mol)
    drawer.SetColour((0.0, 0.0, 0.0))
    for px, py in layout.plus_positions:
        drawer.DrawString("+", Point2D(px, py))
    (tx, ty), (hx, hy) = layout.arrow
    _draw_arrow_glyph(drawer, (tx, ty), (hx, hy), arrow, arrow_length)

    mid = drawer.GetDrawCoords(Point2D((tx + hx) / 2, 0.0))
    origin = drawer.GetDrawCoords(Point2D(0.0, 0.0))
    unit = drawer.GetDrawCoords(Point2D(1.0, 0.0))
    scale = abs(unit.x - origin.x)
    return (mid.x, mid.y), scale


def render_reaction_png(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    conditions: str = "",
    size: tuple[int, int] = RXN_PNG_SIZE,
    style: str = "",
    transparent: bool = False,
    *,
    arrow: str = "forward",
    conditions_below: str = "",
) -> bytes:
    _check_arrow(arrow)
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    (mid_x, mid_y), scale = _draw_reaction(
        drawer, reactants, products, style, transparent, arrow
    )
    drawer.FinishDrawing()
    png = drawer.GetDrawingText()
    if not conditions and not conditions_below:
        return png

    import io

    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    # RGBA nur beim transparenten Opt-in — die Datei bleibt bytegleich RGB.
    image = Image.open(io.BytesIO(png)).convert("RGBA" if transparent else "RGB")
    draw = ImageDraw.Draw(image)
    # Pillows Default-Font fehlen ₂/₄/Δ (Tofu-Boxen). matplotlib (ohnehin
    # Dependency) bündelt DejaVu Sans mit vollem Glyphen-Satz auf allen OS.
    font = ImageFont.truetype(
        font_manager.findfont("DejaVu Sans"),
        size=max(10, round(_reaction_metrics(style)[1] * scale)),
    )
    above, below = _text_baselines(conditions, conditions_below, arrow, style)
    for text, offset in above + below:
        draw.text(
            (mid_x, mid_y - offset * scale),
            text,
            fill=(0, 0, 0),
            font=font,
            anchor="ms",  # horizontal zentriert am Pfeil, y = Grundlinie
        )
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def render_reaction_svg(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    conditions: str = "",
    size: tuple[int, int] = RXN_SVG_SIZE,
    style: str = "",
    *,
    arrow: str = "forward",
    conditions_below: str = "",
) -> str:
    _check_arrow(arrow)
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    (mid_x, mid_y), scale = _draw_reaction(
        drawer, reactants, products, style, arrow=arrow
    )
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    if not conditions and not conditions_below:
        return svg

    from xml.sax.saxutils import escape

    # Ein <text> je Zeile: SVG faltet "\n" sonst zu einem Leerzeichen.
    above, below = _text_baselines(conditions, conditions_below, arrow, style)
    text_els = "".join(
        f"<text x='{mid_x:.1f}' y='{mid_y - offset * scale:.1f}' "
        f"text-anchor='middle' font-family='sans-serif' "
        f"font-size='{_reaction_metrics(style)[1] * scale:.1f}px' fill='#000000'>"
        f"{escape(text)}</text>\n"
        for text, offset in above + below
    )
    return svg.replace("</svg>", text_els + "</svg>")


def write_files(base: Path, artifacts: dict[str, bytes | str]) -> dict[str, str]:
    """Schreibt {format: inhalt} als base.<format> neben­einander.

    Überschreibt vorhandene Dateien bewusst (Regenerieren = Update, kein
    -2-Suffix — anders als der User-Export in png_writer.save_png_bytes).
    Returns {format: absoluter Pfad als str}.
    """
    base.parent.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for fmt, content in artifacts.items():
        path = base.with_suffix(f".{fmt}")
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        written[fmt] = str(path)
    return written


# ---------------------------------------------------------------------------
# Molekül-Vergleich: Panel-Grid mit MCS-Differenz-Highlights
# ---------------------------------------------------------------------------

CMP_PANEL = (500, 450)


def _mcs_diff_highlights(
    mols: list[Chem.Mol],
) -> tuple[list[list[int]], list[list[int]]]:
    """Atome/Bindungen je Molekül, die NICHT zum gemeinsamen Gerüst gehören.

    Das MCS bleibt neutral, die Differenz wird hervorgehoben — sie ist beim
    Vergleichen das Lernziel. Ohne jedes gemeinsame Gerüst ist alles Differenz.
    """
    from rdkit.Chem import rdFMCS

    mcs = rdFMCS.FindMCS(mols, timeout=10)
    query = Chem.MolFromSmarts(mcs.smartsString) if mcs.smartsString else None

    atom_highlights: list[list[int]] = []
    bond_highlights: list[list[int]] = []
    for mol in mols:
        match = set(mol.GetSubstructMatch(query)) if query is not None else set()
        atom_highlights.append(
            [a.GetIdx() for a in mol.GetAtoms() if a.GetIdx() not in match]
        )
        bond_highlights.append(
            [
                b.GetIdx()
                for b in mol.GetBonds()
                if b.GetBeginAtomIdx() not in match or b.GetEndAtomIdx() not in match
            ]
        )
    return atom_highlights, bond_highlights


def _draw_comparison(drawer, mols, labels) -> None:
    atom_hl, bond_hl = _mcs_diff_highlights(mols)
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    prepared = [rdMolDraw2D.PrepareMolForDrawing(m) for m in mols]
    drawer.DrawMolecules(
        prepared,
        highlightAtoms=atom_hl,
        highlightBonds=bond_hl,
        legends=list(labels or [""] * len(mols)),
    )
    drawer.FinishDrawing()


def render_comparison_png(
    mols: list[Chem.Mol],
    labels: list[str] | None = None,
    panel: tuple[int, int] = CMP_PANEL,
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(panel[0] * len(mols), panel[1], *panel)
    _draw_comparison(drawer, mols, labels)
    return drawer.GetDrawingText()


def render_comparison_svg(
    mols: list[Chem.Mol],
    labels: list[str] | None = None,
    panel: tuple[int, int] = CMP_PANEL,
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(panel[0] * len(mols), panel[1], *panel)
    _draw_comparison(drawer, mols, labels)
    return drawer.GetDrawingText()
