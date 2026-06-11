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


def _draw_molecule(drawer, mol, legend: str, annotate_stereo: bool = False) -> None:
    # Gleiche Strichstärke wie die UI-Vorschau (gemeinsame Konstante) — die Datei
    # darf nicht anders aussehen als das, was der Nutzer im Chat gesehen hat.
    # Bewusst NICHT übernommen: fixedBondLength (Datei soll die Canvas füllen)
    # und clearBackground=False (Datei braucht weißen Hintergrund).
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    if annotate_stereo:
        drawer.drawOptions().addStereoAnnotation = True
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend)
    drawer.FinishDrawing()


def render_molecule_png(
    mol,
    legend: str = "",
    size: tuple[int, int] = MOL_PNG_SIZE,
    annotate_stereo: bool = False,
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    _draw_molecule(drawer, mol, legend, annotate_stereo)
    return drawer.GetDrawingText()


def render_molecule_svg(
    mol,
    legend: str = "",
    size: tuple[int, int] = MOL_SVG_SIZE,
    annotate_stereo: bool = False,
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    _draw_molecule(drawer, mol, legend, annotate_stereo)
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
    reactants: list[Chem.Mol], products: list[Chem.Mol]
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
    arrow_head = arrow_tail + ARROW_LENGTH
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


def _draw_reaction(drawer, reactants, products) -> tuple[tuple[float, float], float]:
    """Zeichnet das Schema (ohne Conditions) und liefert die Pixel-Position
    der Pfeilmitte plus die Skala (Pixel pro Mol-Koordinaten-Einheit).

    Conditions-Text geht NICHT über drawer.DrawString: das rendert Strings
    mit der Atomlabel-Engine, die 'H2SO4 (cat.)' als chemische Formel parst
    und mehrzeilig um ein Anker-Atom stapelt. Die Backends overlayen den
    Text selbst (SVG: <text>, PNG: Pillow).
    """
    layout = _compose_reaction(reactants, products)
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, layout.mol)
    drawer.SetColour((0.0, 0.0, 0.0))
    for px, py in layout.plus_positions:
        drawer.DrawString("+", Point2D(px, py))
    (tx, ty), (hx, hy) = layout.arrow
    drawer.DrawArrow(Point2D(tx, ty), Point2D(hx, hy), True, 0.12)

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
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    (mid_x, mid_y), scale = _draw_reaction(drawer, reactants, products)
    drawer.FinishDrawing()
    png = drawer.GetDrawingText()
    if not conditions:
        return png

    import io

    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image)
    # Pillows Default-Font fehlen ₂/₄/Δ (Tofu-Boxen). matplotlib (ohnehin
    # Dependency) bündelt DejaVu Sans mit vollem Glyphen-Satz auf allen OS.
    font = ImageFont.truetype(
        font_manager.findfont("DejaVu Sans"),
        size=max(10, round(CONDITIONS_FONT * scale)),
    )
    draw.text(
        (mid_x, mid_y - 0.35 * scale),
        conditions,
        fill=(0, 0, 0),
        font=font,
        anchor="ms",  # zentriert über dem Pfeil, Baseline oberhalb
    )
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def render_reaction_svg(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    conditions: str = "",
    size: tuple[int, int] = RXN_SVG_SIZE,
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    (mid_x, mid_y), scale = _draw_reaction(drawer, reactants, products)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    if not conditions:
        return svg

    from xml.sax.saxutils import escape

    text_el = (
        f"<text x='{mid_x:.1f}' y='{mid_y - 0.35 * scale:.1f}' "
        f"text-anchor='middle' font-family='sans-serif' "
        f"font-size='{CONDITIONS_FONT * scale:.1f}px' fill='#000000'>"
        f"{escape(conditions)}</text>\n"
    )
    return svg.replace("</svg>", text_el + "</svg>")


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
