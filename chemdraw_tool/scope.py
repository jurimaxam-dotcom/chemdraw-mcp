"""Substrate-Scope-Figuren: ein Raster aus Produktstrukturen mit Beschriftung.

Die häufigste Abbildung der Methodenliteratur — eine Reaktion, viele
Substrate, darüber einmal die allgemeine Gleichung mit den Bedingungen,
unter jeder Struktur Bezeichner und Ausbeute ("1a, 78%", oft plus ee/dr).

Kern ist das LAYOUT, nicht die Chemie. Vier Entscheidungen tragen die Figur:

1. **Eine gemeinsame Skala.** Gezeichnet wird als RDKit-Panel-Raster mit
   `drawMolsSameScale` (Default an): alle Strukturen teilen sich eine
   Bindungslänge. Ein Raster aus einzeln gerenderten Bildern täte das
   Gegenteil — Ethanol würde auf Zellgröße aufgeblasen und wirkte größer als
   ein Steroid. Nebenwirkung, die man will: keine Struktur kann aus ihrer
   Zelle laufen, weil RDKit die Skala am größten Molekül wählt.
2. **Beschriftung selbst gesetzt, Platz von RDKit.** RDKits Legende hat
   genau eine Eigenschaft, die hier disqualifiziert: sie zentriert den
   Textblock vertikal in der Zelle und wirft Leerzeilen weg. Eine einzeilige
   Beschriftung sitzt daneben also tiefer als die erste Zeile der
   zweizeiligen Nachbarzelle (gemessen 2026-08-15) — genau der unruhige
   Eindruck, den eine Scope-Figur nicht haben darf. Jede Zelle bekommt
   deshalb ein Leerzeichen als Legende: RDKit hält den Streifen frei
   (`legendFraction`), gezeichnet wird der Text hier, auf einer über die
   ganze Figur gemeinsamen Grundlinie.
3. **Umbrechen, aber gedeckelt.** Zusatzangaben werden umgebrochen statt
   gekürzt (ee/dr sind das Ergebnis, nicht Dekoration), aber auf
   MAX_CAPTION_LINES gedeckelt und dann mit Ellipse beendet: der freie
   Streifen gilt für ALLE Zellen, jede Zeile stiehlt also jeder Struktur
   Höhe.
4. **Restzeile mittig, wenn es aufgeht.** Eine unvollständige letzte Zeile
   bekommt links und rechts eine leere Zelle (Platzhaltermolekül ohne
   Atome). Bei ungerader Lücke ginge das nur um eine halbe Zelle versetzt —
   dann bleibt sie linksbündig.
5. **Die Zellhöhe folgt der Form der Strukturen** (`struct_aspect`). Bei
   fester Zellhöhe zentriert RDKit flache Moleküle (Biphenyle) in einer viel
   zu hohen Zone: zwischen Struktur und Beschriftung klafft ein leeres Band,
   obwohl kein einziges Maß falsch ist.

Kopfreaktion und Titel entstehen NICHT im selben RDKit-Canvas: die
Reaktionszeile kommt aus dem bereits getesteten `image_export`-Pfad und wird
darübergesetzt (PNG: Pillow, SVG: verschachteltes <svg>). Der
Bedingungstext bekommt dabei eine eigene Zeile unter der Gleichung statt
über dem Pfeil zu stehen: `render_reaction_*` skaliert ihn mit der
Zeichenskala und zentriert ihn über dem Pfeil — bei realistisch langen
Bedingungen (Katalysator, Base, Solvens, Temperatur) läuft er in die
Strukturen.
"""

from __future__ import annotations

import io
import re
import string
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass, field
from math import ceil
from xml.sax.saxutils import escape

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.image_export import (
    ARROW_LENGTH,
    ARROW_PAD,
    LABEL_PAD,
    PLUS_GAP,
    render_reaction_png,
    render_reaction_svg,
)
from chemdraw_tool.render_style import apply_style, get_style
from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

# Journalfiguren sind drei- bis vierspaltig; breiter wird im Zweispaltensatz
# unleserlich, weil jede Struktur dann winzig gezeichnet wird.
PREFERRED_COLUMNS = (4, 3)
MAX_COLUMNS = 6

# Zellbreite in Pixeln (PNG); die Höhe folgt der Form der Strukturen.
CELL_WIDTH_PNG = 440
# Seitenverhältnis (Höhe/Breite) der Strukturzone, wenn nichts vermessen
# werden kann, plus die Grenzen, zwischen denen es bleiben muss.
DEFAULT_STRUCT_ASPECT = 0.75
MIN_STRUCT_ASPECT = 0.42
MAX_STRUCT_ASPECT = 1.15
# Labelüberhang über die Atomkoordinaten hinaus (wie LABEL_PAD, beidseitig).
STRUCT_PAD_UNITS = 1.8
# Die Struktur bleibt die Hauptsache: mindestens so viel Höhe wie das
# Beschriftungsband mal diesem Faktor.
MIN_STRUCT_TO_CAPTION = 1.8
# Das SVG ist dieselbe Figur in halber Größe — wie MOL_PNG_SIZE/MOL_SVG_SIZE.
SVG_SCALE = 0.5

# Beschriftung: ~26 Zeichen passen bei CAPTION_FONT_FACTOR in eine Zellbreite.
MAX_CAPTION_CHARS = 26
MAX_CAPTION_LINES = 3
CAPTION_FONT_FACTOR = 0.052  # relativ zur Zellbreite
CAPTION_LINE_FACTOR = 1.30  # Zeilenabstand relativ zur Schriftgröße
CAPTION_TOP_FACTOR = 0.55  # Luft zwischen Struktur und erster Textzeile
CAPTION_BOTTOM_FACTOR = 0.45  # Luft unter der letzten Textzeile
CAPTION_ASCENT = 0.78  # Oberlänge relativ zur Schriftgröße (Grundlinie)

TITLE_FONT_FACTOR = 0.075  # relativ zur Zellbreite
TITLE_HEIGHT_FACTOR = 2.2  # Titelzeile inkl. Luft, relativ zur Schriftgröße

# Kopfreaktion: seitlich eingerückt, damit sie nicht deutlich größer gezeichnet
# wird als die Rasterstrukturen (RDKit füllt die Canvasbreite aus).
HEADER_INSET_FACTOR = 0.10
# Fallback-Seitenverhältnis (Breite/Höhe), wenn die Gleichung nicht vermessen
# werden kann; sonst rechnet header_aspect() es aus den Molekülen aus.
HEADER_ASPECT = 3.6
# Die Kopfzeile darf nicht beliebig flach oder hoch werden — sonst zeichnet
# RDKit die Gleichung winzig bzw. die Figur kippt aus dem Gleichgewicht.
HEADER_MIN_CELLS = 0.45
HEADER_MAX_CELLS = 1.5
CONDITIONS_CHARS = 90
MAX_CONDITIONS_LINES = 2
SEPARATOR_FACTOR = 0.06  # Abstand Kopfreaktion → Raster, relativ zur Zellhöhe
SEPARATOR_COLOR = (203, 208, 214)
CAPTION_COLOR = (0, 0, 0)
CONDITIONS_COLOR = (60, 60, 60)

# Legende " " statt "": RDKit hält den Streifen nur für eine nicht-leere
# Legende frei — gezeichnet wird von einem Leerzeichen nichts.
_RESERVE_LEGEND = " "


@dataclass(frozen=True)
class ScopeItem:
    """Ein Eintrag der Figur: gezeichnete Struktur plus ihre Beschriftung."""

    mol: Chem.Mol
    label: str = ""
    yield_text: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ReactionHeader:
    """Die allgemeine Gleichung über dem Raster."""

    reactants: list[Chem.Mol] = field(default_factory=list)
    products: list[Chem.Mol] = field(default_factory=list)
    conditions: str = ""


@dataclass(frozen=True)
class GridGeometry:
    """Belegung des Rasters: `slots[i]` = Eintragsindex oder None (leere Zelle)."""

    columns: int
    rows: int
    slots: list[int | None]


@dataclass(frozen=True)
class FigureLayout:
    """Alle Maße der Figur in Pixeln — die eine Quelle für beide Backends."""

    width: int
    height: int
    cell: tuple[int, int]
    grid: GridGeometry
    title_h: int
    header_box: tuple[int, int, int, int] | None
    conditions_y: int
    grid_y: int
    legend_fraction: float
    caption_font_size: int
    caption_line_h: int
    title_font_size: int
    scale: float


# ---------------------------------------------------------------------------
# Raster
# ---------------------------------------------------------------------------


def default_columns(count: int) -> int:
    """Spaltenzahl aus der Eintragszahl: 3 oder 4, je nach Restzeile.

    Gewählt wird die Variante mit den wenigsten leeren Zellen in der letzten
    Zeile, bei Gleichstand die breitere (4) — die Figur wird dann flacher.
    Bis vier Einträge steht alles in einer Zeile.
    """
    if count <= 4:
        return max(1, count)
    return min(PREFERRED_COLUMNS, key=lambda c: ((-count) % c, -c))


def build_grid(count: int, columns: int = 0) -> GridGeometry:
    """Verteilt `count` Einträge auf ein Raster.

    columns=0 heißt "aus der Eintragszahl ableiten". Mehr Spalten als
    Einträge werden gekappt (sonst bliebe die halbe Figur leer).
    """
    if count <= 0:
        raise ValueError(
            "Mindestens ein Eintrag wird benötigt — eine Scope-Figur ohne "
            "Substrate hat nichts zu zeigen"
        )
    if columns < 0 or columns > MAX_COLUMNS:
        raise ValueError(
            f"{columns} Spalten sind nicht darstellbar — erlaubt sind 1 bis "
            f"{MAX_COLUMNS} Spalten (0 = automatisch). Mehr Spalten zwingen "
            "RDKit zu einer so kleinen Bindungslänge, dass die Strukturen "
            "unleserlich werden."
        )

    cols = min(columns or default_columns(count), count)
    rows = ceil(count / cols)

    full = (count // cols) * cols
    slots: list[int | None] = list(range(full))
    rest = count - full
    if rest:
        deficit = cols - rest
        # Nur symmetrisch auffüllen: bei ungerader Lücke säße die Restzeile
        # sonst um eine halbe Zelle versetzt — das wirkt wie ein Fehler.
        lead = deficit // 2 if deficit % 2 == 0 else 0
        slots += [None] * lead
        slots += list(range(full, count))
        slots += [None] * (deficit - lead)
    return GridGeometry(columns=cols, rows=rows, slots=slots)


# ---------------------------------------------------------------------------
# Beschriftung
# ---------------------------------------------------------------------------

_NUMBER_RE = re.compile(r"^\d+(?:[.,]\d+)?$")


def format_yield(text: str) -> str:
    """"78" → "78%", "quant." bleibt "quant.".

    Modelle liefern die Ausbeute mal mit, mal ohne Prozentzeichen; im Raster
    muss die Einheit stehen. Freitext ("quant.", "n.d.", "traces") bleibt
    unangetastet — nicht jede Ausbeute ist eine Zahl.
    """
    value = (text or "").strip()
    return f"{value}%" if _NUMBER_RE.match(value) else value


def auto_label(index: int) -> str:
    """Bezeichner wie in der Literatur: 1a, 1b, … 1z, 1aa."""
    letters = ""
    i = index
    while True:
        letters = string.ascii_lowercase[i % 26] + letters
        i = i // 26 - 1
        if i < 0:
            break
    return f"1{letters}"


def _wrap(text: str, max_chars: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(text, max_chars) or ([text] if text else [])
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max_chars - 1].rstrip() + "…"
    return lines


def caption_lines(
    label: str,
    yield_text: str = "",
    notes: str = "",
    max_chars: int = MAX_CAPTION_CHARS,
    max_lines: int = MAX_CAPTION_LINES,
) -> list[str]:
    """Beschriftung einer Zelle als Zeilenliste.

    Zeile 1 ist "Bezeichner, Ausbeute" — so steht es in Scope-Figuren, und
    zusammen auf einer Zeile bleibt mehr Zellhöhe für die Struktur.
    Zusatzangaben folgen darunter, umgebrochen statt gekürzt; erst jenseits
    von `max_lines` wird mit Ellipse abgeschnitten.
    """
    head = ", ".join(p for p in ((label or "").strip(), format_yield(yield_text)) if p)
    lines: list[str] = []
    if head:
        lines += textwrap.wrap(head, max_chars) or [head]
    if (notes or "").strip():
        lines += textwrap.wrap(notes.strip(), max_chars)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max_chars - 1].rstrip() + "…"
    return lines


# ---------------------------------------------------------------------------
# Figurgeometrie
# ---------------------------------------------------------------------------


def _extent(mol: Chem.Mol) -> tuple[float, float]:
    """Breite/Höhe eines Moleküls in Mol-Koordinaten (0/0 ohne Konformer)."""
    if mol is None or mol.GetNumConformers() == 0 or mol.GetNumAtoms() == 0:
        return (0.0, 0.0)
    conf = mol.GetConformer()
    xs = [conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())]
    ys = [conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())]
    return (max(xs) - min(xs), max(ys) - min(ys))


def struct_aspect(items: Sequence[ScopeItem]) -> float:
    """Höhe/Breite der Strukturzone, abgeleitet aus den größten Molekülen.

    Die Zellhöhe folgt daraus. Mit fester Zellhöhe zentriert RDKit flache
    Strukturen (Biphenyle) in einer viel zu hohen Zone, und zwischen Struktur
    und Beschriftung steht ein leeres Band — die Figur wirkt zerrissen, obwohl
    kein einziges Maß "falsch" ist.
    """
    extents = [e for e in (_extent(it.mol) for it in items) if e != (0.0, 0.0)]
    if not extents:
        return DEFAULT_STRUCT_ASPECT
    width = max(w for w, _ in extents) + STRUCT_PAD_UNITS
    height = max(h for _, h in extents) + STRUCT_PAD_UNITS
    return height / width


def header_aspect(header: ReactionHeader) -> float:
    """Breite/Höhe der Kopfreaktion in Mol-Koordinaten.

    Gerechnet wird mit denselben Abständen, die `image_export._compose_reaction`
    tatsächlich setzt (LABEL_PAD, PLUS_GAP, ARROW_LENGTH, ARROW_PAD) — die
    Kopfzeile bekommt dadurch genau die Höhe, die die Gleichung braucht.
    Ohne diese Kopplung reserviert eine feste Höhe zu viel und zwischen
    Gleichung und Bedingungen klafft eine leere Zone, weil RDKit die
    Zeichnung in ihrer Box zentriert.
    """
    mols = list(header.reactants) + list(header.products)
    extents = [_extent(m) for m in mols]
    if not extents:
        return HEADER_ASPECT

    width = sum(w + 2 * LABEL_PAD for w, _ in extents)
    width += PLUS_GAP * (
        max(0, len(header.reactants) - 1) + max(0, len(header.products) - 1)
    )
    width += ARROW_LENGTH + 2 * ARROW_PAD
    # Atomlabels ragen über die Atomkoordinaten hinaus — dieselbe Reserve wie
    # in der Breite, sonst schneidet die Box oben/unten knapp ab.
    height = max((h for _, h in extents), default=0.0) + 2 * LABEL_PAD
    return width / max(height, 0.5)


def plan_figure(
    count: int,
    columns: int = 0,
    title: str = "",
    has_header: bool = False,
    scale: float = 1.0,
    caption_lines_count: int = 1,
    conditions_lines: int = 0,
    header_aspect: float = HEADER_ASPECT,
    struct_aspect: float = DEFAULT_STRUCT_ASPECT,
) -> FigureLayout:
    """Rechnet die komplette Figur in Pixel aus — vor jedem Rendern.

    `scale` skaliert JEDE Länge (1.0 = PNG, 0.5 = SVG), damit beide Ausgaben
    dieselbe Figur zeigen und nicht zwei Layouts gepflegt werden müssen.
    """
    grid = build_grid(count, columns)
    cell_w = max(1, round(CELL_WIDTH_PNG * scale))
    width = grid.columns * cell_w

    caption_font = max(5, round(cell_w * CAPTION_FONT_FACTOR))
    line_h = max(1, round(caption_font * CAPTION_LINE_FACTOR))
    band = (
        round(caption_font * CAPTION_TOP_FACTOR)
        + max(1, caption_lines_count) * line_h
        + round(caption_font * CAPTION_BOTTOM_FACTOR)
    )
    aspect = min(MAX_STRUCT_ASPECT, max(MIN_STRUCT_ASPECT, struct_aspect))
    struct_h = max(round(cell_w * aspect), round(band * MIN_STRUCT_TO_CAPTION))
    cell_h = struct_h + band
    fraction = band / cell_h

    title_font = max(6, round(cell_w * TITLE_FONT_FACTOR))
    title_h = round(title_font * TITLE_HEIGHT_FACTOR) if title.strip() else 0

    header_box = None
    header_block = 0
    conditions_y = 0
    if has_header:
        inset = round(width * HEADER_INSET_FACTOR)
        header_w = width - 2 * inset
        header_h = min(
            round(cell_h * HEADER_MAX_CELLS),
            max(
                round(cell_h * HEADER_MIN_CELLS),
                round(header_w / max(header_aspect, 0.5)),
            ),
        )
        header_box = (inset, title_h, header_w, header_h)
        header_block = header_h
        if conditions_lines > 0:
            conditions_y = (
                title_h
                + header_h
                + round(caption_font * CAPTION_TOP_FACTOR)
                + round(caption_font * CAPTION_ASCENT)
            )
            header_block += round(caption_font * CAPTION_TOP_FACTOR) + (
                conditions_lines * line_h
            )
        header_block += round(cell_h * SEPARATOR_FACTOR)

    grid_y = title_h + header_block
    return FigureLayout(
        width=width,
        height=grid_y + grid.rows * cell_h,
        cell=(cell_w, cell_h),
        grid=grid,
        title_h=title_h,
        header_box=header_box,
        conditions_y=conditions_y,
        grid_y=grid_y,
        legend_fraction=fraction,
        caption_font_size=caption_font,
        caption_line_h=line_h,
        title_font_size=title_font,
        scale=scale,
    )


def cell_box(layout: FigureLayout, index: int) -> tuple[int, int, int, int]:
    """Zelle `index` (zeilenweise gezählt) als (x, y, Breite, Höhe)."""
    cell_w, cell_h = layout.cell
    row, col = divmod(index, layout.grid.columns)
    return (col * cell_w, layout.grid_y + row * cell_h, cell_w, cell_h)


def caption_baselines(
    layout: FigureLayout, index: int, lines: int
) -> list[tuple[float, float]]:
    """Grundlinien der Beschriftung von Zelle `index`: [(x_mitte, y), …].

    Die erste Grundlinie hängt NUR an der Zellhöhe, nicht an der Zeilenzahl —
    daher fluchten alle Beschriftungen der Figur, egal ob ein- oder
    dreizeilig.
    """
    x, y, w, h = cell_box(layout, index)
    band_top = y + h - layout.legend_fraction * h
    first = (
        band_top
        + round(layout.caption_font_size * CAPTION_TOP_FACTOR)
        + round(layout.caption_font_size * CAPTION_ASCENT)
    )
    return [(x + w / 2, first + i * layout.caption_line_h) for i in range(lines)]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _blank_mol() -> Chem.Mol:
    """Platzhalter für eine leere Rasterzelle.

    Ein Molekül ohne Atome belegt seine Zelle, zeichnet nichts und geht weder
    in die gemeinsame Skala noch in die Legende ein — damit lässt sich eine
    unvollständige letzte Zeile mittig setzen, ohne RDKits zeilenweise
    Platzierung nachzubauen.
    """
    mol = Chem.MolFromSmiles("")
    AllChem.Compute2DCoords(mol)
    return mol


@dataclass(frozen=True)
class _Plan:
    layout: FigureLayout
    mols: list[Chem.Mol]
    captions: list[list[str]]  # je Rasterzelle (leere Zelle: [])
    conditions: list[str]


def _prepare(
    items: Sequence[ScopeItem],
    columns: int,
    title: str,
    header: ReactionHeader | None,
    style: str,
    scale: float,
) -> _Plan:
    if not items:
        raise ValueError(
            "Mindestens ein Eintrag wird benötigt — eine Scope-Figur ohne "
            "Substrate hat nichts zu zeigen"
        )
    get_style(style)  # unbekannter Stil: scheitern, bevor gezeichnet wird

    per_item = [caption_lines(it.label, it.yield_text, it.notes) for it in items]
    conditions = (
        _wrap(header.conditions.strip(), CONDITIONS_CHARS, MAX_CONDITIONS_LINES)
        if header is not None and header.conditions.strip()
        else []
    )
    layout = plan_figure(
        len(items),
        columns=columns,
        title=title,
        has_header=header is not None,
        scale=scale,
        caption_lines_count=max((len(c) for c in per_item), default=1),
        conditions_lines=len(conditions),
        header_aspect=HEADER_ASPECT if header is None else header_aspect(header),
        struct_aspect=struct_aspect(items),
    )

    mols: list[Chem.Mol] = []
    captions: list[list[str]] = []
    for slot in layout.grid.slots:
        mols.append(_blank_mol() if slot is None else items[slot].mol)
        captions.append([] if slot is None else per_item[slot])
    return _Plan(layout, mols, captions, conditions)


def _draw_grid(drawer, plan: _Plan, style: str) -> None:
    opts = drawer.drawOptions()
    opts.bondLineWidth = BOND_LINE_WIDTH
    apply_style(opts, style)
    # Nach dem Preset: der freie Streifen ist eine Layout-Entscheidung dieser
    # Figur (Zeilenzahl der Beschriftung), keine Stilfrage.
    opts.legendFraction = plan.layout.legend_fraction
    drawer.DrawMolecules(plan.mols, legends=[_RESERVE_LEGEND] * len(plan.mols))
    drawer.FinishDrawing()


def _font(size: int, bold: bool = False):
    """DejaVu Sans über matplotlib — Pillows Default-Font kennt weder Umlaute
    noch °/Δ und ist nicht skalierbar."""
    from matplotlib import font_manager
    from PIL import ImageFont

    path = font_manager.findfont(
        font_manager.FontProperties(
            family="DejaVu Sans", weight="bold" if bold else "normal"
        )
    )
    return ImageFont.truetype(path, size=size)


def render_scope_png(
    items: Sequence[ScopeItem],
    columns: int = 0,
    title: str = "",
    header: ReactionHeader | None = None,
    style: str = "",
) -> bytes:
    from PIL import Image, ImageDraw

    plan = _prepare(items, columns, title, header, style, 1.0)
    layout = plan.layout
    cell_w, cell_h = layout.cell

    drawer = rdMolDraw2D.MolDraw2DCairo(
        layout.width, layout.grid.rows * cell_h, cell_w, cell_h
    )
    _draw_grid(drawer, plan, style)

    canvas = Image.new("RGB", (layout.width, layout.height), "white")
    canvas.paste(
        Image.open(io.BytesIO(drawer.GetDrawingText())).convert("RGB"),
        (0, layout.grid_y),
    )
    draw = ImageDraw.Draw(canvas)

    if header is not None:
        hx, hy, hw, hh = layout.header_box
        canvas.paste(
            Image.open(
                io.BytesIO(
                    render_reaction_png(
                        list(header.reactants),
                        list(header.products),
                        "",  # Bedingungen stehen unter der Gleichung, s. Modulkopf
                        size=(hw, hh),
                        style=style,
                    )
                )
            ).convert("RGB"),
            (hx, hy),
        )
        cond_font = _font(layout.caption_font_size)
        for i, line in enumerate(plan.conditions):
            draw.text(
                (layout.width / 2, layout.conditions_y + i * layout.caption_line_h),
                line,
                fill=CONDITIONS_COLOR,
                font=cond_font,
                anchor="ms",
            )
        line_y = layout.grid_y - round(cell_h * SEPARATOR_FACTOR / 2)
        draw.line(
            [(round(layout.width * 0.08), line_y), (round(layout.width * 0.92), line_y)],
            fill=SEPARATOR_COLOR,
            width=max(1, round(2 * layout.scale)),
        )

    if layout.title_h:
        draw.text(
            (layout.width / 2, layout.title_h * 0.72),
            title.strip(),
            fill=CAPTION_COLOR,
            font=_font(layout.title_font_size, bold=True),
            anchor="ms",
        )

    head_font = _font(layout.caption_font_size, bold=True)
    body_font = _font(layout.caption_font_size)
    for index, lines in enumerate(plan.captions):
        for i, ((cx, cy), line) in enumerate(
            zip(caption_baselines(layout, index, len(lines)), lines, strict=True)
        ):
            # Erste Zeile (Bezeichner + Ausbeute) fett — sie ist die Angabe,
            # die beim Überfliegen der Figur gesucht wird.
            draw.text(
                (cx, cy),
                line,
                fill=CAPTION_COLOR,
                font=head_font if i == 0 else body_font,
                anchor="ms",
            )

    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()


def _nested_svg(svg: str, x: int, y: int) -> str:
    """Bettet ein RDKit-SVG als verschachteltes <svg> an Position (x, y) ein.

    RDKit schreibt width/height identisch zur viewBox, ein verschachteltes
    <svg> mit x/y verschiebt den Inhalt daher unskaliert — kein Umrechnen von
    Koordinaten, keine Textmanipulation im Inneren. Die XML-Deklaration muss
    weg: sie ist nur am Dokumentanfang erlaubt.
    """
    start = svg.index("<svg")
    return svg[start:].replace("<svg", f"<svg x='{x}' y='{y}'", 1)


def _svg_text(
    x: float, y: float, text: str, size: int, color: tuple[int, int, int], bold: bool
) -> str:
    weight = " font-weight='600'" if bold else ""
    return (
        f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='middle' "
        f"font-family='sans-serif' font-size='{size}px'{weight} "
        f"fill='rgb{color}'>{escape(text)}</text>"
    )


def render_scope_svg(
    items: Sequence[ScopeItem],
    columns: int = 0,
    title: str = "",
    header: ReactionHeader | None = None,
    style: str = "",
) -> str:
    plan = _prepare(items, columns, title, header, style, SVG_SCALE)
    layout = plan.layout
    cell_w, cell_h = layout.cell

    drawer = rdMolDraw2D.MolDraw2DSVG(
        layout.width, layout.grid.rows * cell_h, cell_w, cell_h
    )
    _draw_grid(drawer, plan, style)

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' "
        f"xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' "
        f"width='{layout.width}px' height='{layout.height}px' "
        f"viewBox='0 0 {layout.width} {layout.height}'>",
        f"<rect x='0' y='0' width='{layout.width}' height='{layout.height}' "
        f"fill='#FFFFFF'/>",
    ]
    if layout.title_h:
        parts.append(
            _svg_text(
                layout.width / 2,
                layout.title_h * 0.72,
                title.strip(),
                layout.title_font_size,
                CAPTION_COLOR,
                True,
            )
        )
    if header is not None:
        hx, hy, hw, hh = layout.header_box
        parts.append(
            _nested_svg(
                render_reaction_svg(
                    list(header.reactants),
                    list(header.products),
                    "",
                    size=(hw, hh),
                    style=style,
                ),
                hx,
                hy,
            )
        )
        for i, line in enumerate(plan.conditions):
            parts.append(
                _svg_text(
                    layout.width / 2,
                    layout.conditions_y + i * layout.caption_line_h,
                    line,
                    layout.caption_font_size,
                    CONDITIONS_COLOR,
                    False,
                )
            )
        line_y = layout.grid_y - round(cell_h * SEPARATOR_FACTOR / 2)
        parts.append(
            f"<line x1='{layout.width * 0.08:.1f}' y1='{line_y}' "
            f"x2='{layout.width * 0.92:.1f}' y2='{line_y}' "
            f"stroke='rgb{SEPARATOR_COLOR}' "
            f"stroke-width='{max(1, round(2 * layout.scale))}'/>"
        )

    parts.append(_nested_svg(drawer.GetDrawingText(), 0, layout.grid_y))

    for index, lines in enumerate(plan.captions):
        for i, ((cx, cy), line) in enumerate(
            zip(caption_baselines(layout, index, len(lines)), lines, strict=True)
        ):
            parts.append(
                _svg_text(
                    cx, cy, line, layout.caption_font_size, CAPTION_COLOR, i == 0
                )
            )

    parts.append("</svg>")
    return "\n".join(parts)
