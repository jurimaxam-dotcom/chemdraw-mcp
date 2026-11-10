"""Schematisches 2D-Bild eines humanen IgG1-Antikörpers (matplotlib, Agg).

Zweck: die Lehrbuch-Y-Form für Protein-Einträge — zwei schwere Ketten
(VH, CH1, Gelenk, CH2, CH3), zwei leichte Ketten (VL, CL), Fab/Fc,
Antigenbindestelle, N297-Glykan und die Disulfidbrücken. Das Modul zeichnet
ein festes Schema; es rechnet nichts aus einer Sequenz.

Fachliche Festlegungen (humanes IgG1, κ-Leichtkette, EU-Nummerierung):
* Leichte Kette lagert sich außen an VH–CH1 an (VL neben VH, CL neben CH1);
  das Gelenk liegt unter CH1, darunter CH2 (mit Glykan), unten CH3.
* Interketten-Disulfide in IgG1: zwei H–H-Brücken im Gelenk (Cys226, Cys229)
  und je Arm eine L–H-Brücke von Cys214 (C-terminales Cys der κ-Kette) zu
  Cys220 der schweren Kette im oberen Gelenk — zusammen 4 Interketten-
  Brücken. Dazu je Ig-Domäne eine Intraketten-Brücke, 12 insgesamt
  (4 Domänen × 2 schwere + 2 Domänen × 2 leichte Ketten).
  Quelle: Liu H, May K (2012) „Disulfide bond structures of IgG molecules:
  structural variations, chemical modifications and possible impacts to
  stability and biological function“, mAbs 4(1):17–23; Vidarsson G, Dekkers G,
  Rispens T (2014) „IgG subclasses and allotypes: from structure to effector
  functions“, Front. Immunol. 5:520.
* N-Glykan an Asn297 im CH2 jeder schweren Kette; die beiden Glykane liegen
  im Zwischenraum der CH2-Domänen (Vidarsson et al. 2014).

Aufbau analog tlc.py: build_igg_figure liefert die Figur, render_igg_png/
render_igg_svg nur noch die Bytes.
"""

from __future__ import annotations

import io
import math

import matplotlib

matplotlib.use("Agg")

from matplotlib import rc_context  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, Ellipse, Patch, Polygon, Rectangle  # noqa: E402

from chemdraw_tool.ph_plots import safe_text  # noqa: E402

DEFAULT_TITLE = "IgG antibody — schematic (IgG1)"
FIGSIZE = (7.0, 7.0)

# Okabe-Ito-Palette: farbenblind-sicher, Blau vs. Orange.
HEAVY_FACE = "#0072B2"
HEAVY_TEXT = "white"
LIGHT_FACE = "#E69F00"
LIGHT_TEXT = "#1a1a1a"
EDGE = "#1a1a1a"
SS_COLOR = "#B8860B"  # Disulfid: dunkles Goldgelb (Schwefel)
GLCNAC = "#0072B2"  # SNFG: GlcNAc blaues Quadrat
MANNOSE = "#009E73"  # SNFG: Mannose grüner Kreis
FUCOSE = "#D55E00"  # SNFG: Fucose rot (hier als Kreis vereinfacht)
NOTE = "#444444"

# Geometrie in Datenkoordinaten (0…10 × 0…10, gleiche Achsenskalierung).
DOM_W = 1.15  # Domänenlänge entlang der Kette
DOM_H = 0.82  # Domänenbreite quer zur Kette
CH3_X = 0.58  # Abstand CH3-Mitte von der Symmetrieachse (CH3 paaren eng)
CH2_X = 0.82  # CH2 weiter auseinander: Platz für die Glykane
CH3_Y = 1.75
CH2_Y = 3.15
HINGE_Y0 = 3.75
HINGE_Y1 = 4.75
ARM_ANGLE = 45.0  # Grad gegen die Senkrechte
CX = 5.0


def _ellipse(ax, center, angle, face, label, text_color, fontsize=9):
    """Eine Ig-Domäne als Ellipse mit Namen und angedeuteter Intraketten-Brücke."""
    ax.add_patch(
        Ellipse(center, DOM_H, DOM_W, angle=angle, facecolor=face,
                edgecolor=EDGE, linewidth=1.0, zorder=3)
    )
    ax.text(center[0], center[1] + 0.07, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, zorder=5)
    # Intraketten-Disulfid: kurzer, dezenter Strich unter dem Namen.
    ax.add_line(Line2D([center[0] - 0.12, center[0] + 0.12],
                       [center[1] - 0.2, center[1] - 0.2],
                       color=text_color, linewidth=1.0, alpha=0.7, zorder=4))


def _ss(ax, p, q):
    """Disulfidbrücke als goldgelber Strich mit zwei Schwefelpunkten."""
    ax.add_line(Line2D([p[0], q[0]], [p[1], q[1]], color=SS_COLOR,
                       linewidth=2.2, solid_capstyle="round", zorder=4))
    for pt in (p, q):
        ax.add_patch(Circle(pt, 0.045, facecolor=SS_COLOR, edgecolor=EDGE,
                            linewidth=0.5, zorder=5))


def _glycan(ax, attach, root):
    """Vereinfachtes core-fucosyliertes Kern-Glykan (SNFG-Symbole) an Asn297.

    attach: Punkt am CH2-Rand (Asn297); root: Lage des ersten GlcNAc.
    Aufbau von unten: Fuc – GlcNAc – GlcNAc – Man – 2 × Man.
    """
    s = 0.06  # halbe Symbolgröße
    step = 0.17
    x, y = root
    pts = [(x, y), (x, y + step)]  # GlcNAc–GlcNAc
    man = (x, y + 2 * step)
    branches = [(x - 0.1, y + 3 * step), (x + 0.1, y + 3 * step)]
    fuc = (x, y - step)
    lines = [(attach, pts[0]), (pts[0], pts[1]), (pts[1], man),
             (man, branches[0]), (man, branches[1]), (pts[0], fuc)]
    for a, b in lines:
        ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], color=EDGE,
                           linewidth=0.7, zorder=5))
    for px, py in pts:
        ax.add_patch(Rectangle((px - s, py - s), 2 * s, 2 * s, facecolor=GLCNAC,
                               edgecolor=EDGE, linewidth=0.5, zorder=6))
    for c, color in [(man, MANNOSE), (branches[0], MANNOSE),
                     (branches[1], MANNOSE), (fuc, FUCOSE)]:
        ax.add_patch(Circle(c, s, facecolor=color, edgecolor=EDGE,
                            linewidth=0.5, zorder=6))


def _arm(ax, side):
    """Ein Fab-Arm. side = −1 links, +1 rechts. Gibt Punkte für Beschriftungen."""
    a = math.radians(ARM_ANGLE)
    d = (side * math.sin(a), math.cos(a))  # Richtung entlang des Arms
    n = (side * math.cos(a), -math.sin(a))  # quer, nach außen-unten
    angle = -side * ARM_ANGLE
    top = (CX + side * CH2_X * 0.55, HINGE_Y1)

    def along(t, off=0.0):
        return (top[0] + d[0] * t + n[0] * off, top[1] + d[1] * t + n[1] * off)

    ch1 = along(0.85)
    vh = along(0.85 + DOM_W + 0.05)
    loff = DOM_H + 0.06
    cl = along(0.85, loff)
    vl = along(0.85 + DOM_W + 0.05, loff)

    # Kettenstrich der schweren Kette vom Gelenk zu CH1.
    ax.add_line(Line2D([top[0], ch1[0]], [top[1], ch1[1]], color=EDGE,
                       linewidth=1.6, zorder=2))
    _ellipse(ax, ch1, angle, HEAVY_FACE, "CH1", HEAVY_TEXT)
    _ellipse(ax, vh, angle, HEAVY_FACE, "VH", HEAVY_TEXT)
    _ellipse(ax, cl, angle, LIGHT_FACE, "CL", LIGHT_TEXT)
    _ellipse(ax, vl, angle, LIGHT_FACE, "VL", LIGHT_TEXT)

    # C-terminales Ende der leichten Kette (Cys214) → Cys220 im oberen Gelenk.
    lc_tail = along(0.85 - DOM_W / 2 - 0.12, loff)
    ax.add_line(Line2D([cl[0] - d[0] * DOM_W / 2, lc_tail[0]],
                       [cl[1] - d[1] * DOM_W / 2, lc_tail[1]],
                       color=EDGE, linewidth=1.6, zorder=2))
    hc220 = (top[0] + d[0] * 0.08, top[1] + d[1] * 0.08)
    _ss(ax, lc_tail, hc220)

    tip = along(0.85 + 1.5 * DOM_W + 0.1, loff / 2)
    return {"tip": tip, "vh": vh, "vl": vl, "cl": cl, "ch1": ch1, "d": d, "n": n,
            "along": along}


def _fab_box(ax, arm):
    """Gestrichelter Rahmen um VH+CH1+VL+CL eines Arms."""
    along = arm["along"]
    loff = DOM_H + 0.06
    t0, t1 = 0.85 - DOM_W / 2 - 0.08, 0.85 + 1.5 * DOM_W + 0.15
    o0, o1 = -DOM_H / 2 - 0.08, loff + DOM_H / 2 + 0.08
    corners = [along(t0, o0), along(t1, o0), along(t1, o1), along(t0, o1)]
    ax.add_patch(Polygon(corners, closed=True, fill=False, edgecolor=NOTE,
                         linewidth=0.9, linestyle=(0, (4, 3)), zorder=1))
    return corners


def build_igg_figure(title: str = "", subtitle: str = "") -> Figure:
    """Baut die Figur des IgG1-Schemas (7 × 7 Zoll, weißer Hintergrund)."""
    fig = Figure(figsize=FIGSIZE, dpi=100, facecolor="white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 0.88])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.8)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.5, 0.965, safe_text(title.strip() or DEFAULT_TITLE),
             ha="center", va="top", fontsize=13, fontweight="bold")
    if subtitle.strip():
        fig.text(0.5, 0.925, safe_text(subtitle.strip()), ha="center",
                 va="top", fontsize=10, color=NOTE)

    # Fc-Stamm: je schwere Kette CH3 (unten), CH2, Gelenkstrich.
    for side in (-1, 1):
        x3 = CX + side * CH3_X
        x2 = CX + side * CH2_X
        xh = CX + side * CH2_X * 0.55
        ax.add_line(Line2D([x3, x2, x2, xh, xh],
                           [CH3_Y, CH2_Y - 0.3, CH2_Y, HINGE_Y0, HINGE_Y1],
                           color=EDGE, linewidth=1.6, zorder=2))
        _ellipse(ax, (x3, CH3_Y), 0, HEAVY_FACE, "CH3", HEAVY_TEXT)
        _ellipse(ax, (x2, CH2_Y), 0, HEAVY_FACE, "CH2", HEAVY_TEXT)
        # N297-Glykan an der Innenseite von CH2.
        gy = CH2_Y - 0.2
        _glycan(ax, (CX + side * (CH2_X - DOM_H / 2 + 0.02), gy),
                (CX + side * 0.2, gy))

    # Zwei H–H-Disulfide im Gelenk (Cys226, Cys229).
    xh = CH2_X * 0.55
    for y in (4.05, 4.4):
        _ss(ax, (CX - xh, y), (CX + xh, y))

    arms = [_arm(ax, -1), _arm(ax, 1)]
    for arm in arms:
        _fab_box(ax, arm)

    # --- Beschriftungen --------------------------------------------------
    note = {"fontsize": 9, "color": "#1a1a1a"}
    arrow = {"arrowstyle": "-", "color": NOTE, "linewidth": 0.8,
             "shrinkA": 2, "shrinkB": 2}

    ax.annotate("Hinge\n(H–H S–S: Cys226, Cys229)", xy=(CX + xh + 0.05, 3.9),
                xytext=(7.0, 3.95), ha="left", va="center", arrowprops=arrow,
                **note)
    # Pfeil hinter CH2 (zorder 1), damit er auf das Glykan zeigt statt
    # quer über die Domäne zu laufen.
    ax.annotate("N297 glycan", xy=(CX + 0.3, CH2_Y - 0.2),
                xytext=(7.0, 2.85), ha="left", va="center", arrowprops=arrow,
                zorder=1, **note)

    # Fc-Klammer rechts neben dem Stamm.
    fx = CX + CH2_X + DOM_H / 2 + 0.35
    y0, y1 = CH3_Y - DOM_W / 2, CH2_Y + DOM_W / 2
    ax.add_line(Line2D([fx - 0.12, fx, fx, fx - 0.12], [y0, y0, y1, y1],
                       color=NOTE, linewidth=1.0, zorder=2))
    ax.text(fx + 0.15, CH3_Y + 0.3, "Fc", ha="left", va="center",
            fontsize=12, fontweight="bold", color="#1a1a1a")

    # Fab-Beschriftung je Arm außen oben neben dem Rahmen.
    for arm, side in zip(arms, (-1, 1), strict=True):
        corner = arm["along"](0.85 + 1.5 * DOM_W + 0.15, -DOM_H / 2 - 0.08)
        ax.text(corner[0] + side * 0.1, corner[1] + 0.25, "Fab",
                ha="center", va="bottom", fontsize=12, fontweight="bold",
                color="#1a1a1a")

    # Antigenbindestelle: Markierung an beiden Spitzen, Text am linken Arm.
    for arm in arms:
        tx, ty = arm["tip"]
        ax.add_patch(Circle((tx, ty), 0.16, facecolor="none", edgecolor="#CC79A7",
                            linewidth=2.0, zorder=6))
    ltip = arms[0]["tip"]
    ax.annotate("Antigen-binding site\n(VH + VL)", xy=(ltip[0] - 0.12, ltip[1] + 0.12),
                xytext=(0.3, 8.2), ha="left", va="center", arrowprops=arrow,
                **note)

    # L–H-Disulfid am linken Arm benennen.
    lt = arms[0]["along"](0.85 - DOM_W / 2 - 0.12, DOM_H + 0.06)
    ax.annotate("L–H S–S\n(LC Cys214–HC Cys220)", xy=(lt[0] - 0.05, lt[1] - 0.05),
                xytext=(0.3, 3.3), ha="left", va="center", arrowprops=arrow,
                **note)

    # Legende.
    handles = [
        Patch(facecolor=HEAVY_FACE, edgecolor=EDGE, label="Heavy chain"),
        Patch(facecolor=LIGHT_FACE, edgecolor=EDGE, label="Light chain (κ)"),
        Line2D([], [], color=SS_COLOR, linewidth=2.2, label="Inter-chain disulfide"),
        Line2D([], [], color=NOTE, linewidth=1.0,
               label="Intra-chain disulfide (1 per domain)"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.02, 0.0),
              frameon=False, fontsize=8.5)
    ax.text(9.8, 0.15, "EU numbering", ha="right", va="bottom", fontsize=8,
            color=NOTE)
    return fig


def _svg_bytes(fig: Figure) -> str:
    buf = io.BytesIO()
    # fonttype "none": Text bleibt Text (durchsuchbar); hashsalt + Date=None
    # machen die Ausgabe byte-gleich über Aufrufe hinweg.
    with rc_context({"svg.fonttype": "none", "svg.hashsalt": "chemdraw-igg"}):
        fig.savefig(buf, format="svg", facecolor="white",
                    metadata={"Date": None})
    return buf.getvalue().decode("utf-8")


def render_igg_png(title: str = "", subtitle: str = "", dpi: int = 200) -> bytes:
    """PNG-Bytes des IgG1-Schemas."""
    buf = io.BytesIO()
    build_igg_figure(title, subtitle).savefig(buf, format="png", dpi=dpi,
                                              facecolor="white")
    return buf.getvalue()


def render_igg_svg(title: str = "", subtitle: str = "") -> str:
    """SVG-Text des IgG1-Schemas, deterministisch."""
    return _svg_bytes(build_igg_figure(title, subtitle))
