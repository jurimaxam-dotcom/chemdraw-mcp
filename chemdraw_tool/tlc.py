"""Schematische DC-Platten aus Rf-Werten — Rendering als PNG/SVG via matplotlib.

Zweck: die Plattenskizze, die im Praktikumsprotokoll verlangt wird —
Startlinie, Laufmittelfront, pro Substanz ein Fleck auf Höhe seines
Rf-Werts, Bahnen beschriftet (Edukt / Reaktion / Co-Spot). Das Modul
*misst* nichts: die Rf-Werte liefert der Aufrufer.

Aufbau analog spectrum.py: pure Geometrie (build_plate) getrennt vom
Datei-Rendering; der MCP-Server setzt nur noch Pfade und Payload obendrauf.

Fachliche Festlegungen:
* Rf = Laufstrecke Substanz / Laufstrecke Front ⇒ 0 ≤ Rf ≤ 1. Werte
  außerhalb sind ein Eingabefehler und werden gemeldet, nicht beschnitten.
* Die Platte wird von unten gelesen: Start unten (Rf 0), Front oben (Rf 1).
* Intensität ist optional (0…1, Default 1) und steuert nur die Deckkraft
  des Flecks — ein schwacher Fleck wird blasser gezeichnet.
"""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import matplotlib

matplotlib.use("Agg")

from matplotlib import rc_context  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Ellipse, Rectangle  # noqa: E402

# Plattenkoordinaten: x = Bahnindex (1, 2, 3 …), y = Rf.
START_Y = 0.0
FRONT_Y = 1.0
LANE_SPACING = 1.0
PLATE_BOTTOM = -0.12  # Platte reicht unter die Startlinie (Eintauchzone)
PLATE_TOP = 1.12

# Fleck: elliptisch wie in der Realität (in x breiter als in Rf hoch).
SPOT_WIDTH = 0.44
SPOT_HEIGHT = 0.05

# Zwei Flecken einer Bahn, die enger als LABEL_MIN_GAP beieinander liegen,
# bekämen übereinanderliegende Beschriftungen — der untere weicht nach unten
# aus. Unterhalb von LABEL_FLOOR_RF ist dafür kein Platz mehr (Startlinie),
# oberhalb von LABEL_CEILING_RF liegen Frontlinie und Front-Beschriftung.
LABEL_MIN_GAP = 0.09
LABEL_FLOOR_RF = 0.10
LABEL_CEILING_RF = 0.93

# Feste Bahnbreite in Zoll: die Beschriftung bleibt bei 2 wie bei 8 Bahnen
# gleich luftig, die Figur wächst stattdessen in der Breite.
LANE_WIDTH_IN = 1.8
FIG_PAD_IN = 1.8
FIG_HEIGHT_IN = 6.5

PLATE_FACE = "#fbfaf6"  # Kieselgel-Weiß
PLATE_EDGE = "#9aa0a6"
LINE_COLOR = "#555555"
SPOT_FACE = "#5a5a5a"
SPOT_EDGE = "#1a1a1a"


@dataclass(frozen=True)
class PlacedSpot:
    lane: str
    x: float
    y: float
    rf: float
    intensity: float
    label: str
    label_above: bool


@dataclass(frozen=True)
class PlateGeometry:
    lanes: list[str]
    lane_x: list[float]
    spots: list[PlacedSpot] = field(default_factory=list)
    start_y: float = START_Y
    front_y: float = FRONT_Y


def default_figsize(lane_count: int) -> tuple[float, float]:
    """Figurgröße für n Bahnen — feste Breite je Bahn, konstante Höhe."""
    return (LANE_WIDTH_IN * max(1, lane_count) + FIG_PAD_IN, FIG_HEIGHT_IN)


def _spot_number(value, lane: str, what: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{what} in Bahn {lane!r} ist keine Zahl: {value!r}"
        ) from None


def _parse_lane(lane: Mapping) -> tuple[str, list[Mapping]]:
    name = str(lane.get("name", "") or "").strip()
    if not name:
        raise ValueError(
            "Jede Bahn braucht einen Namen (z.B. 'Edukt', 'Reaktion', 'Co-Spot') — "
            "unbeschriftete Bahnen sind im Protokoll nicht auswertbar"
        )
    spots = list(lane.get("spots") or [])
    return name, spots


def _label_sides(rfs: Sequence[float]) -> list[bool]:
    """Pro Fleck: Beschriftung oberhalb (True) oder unterhalb (False).

    Ein Fleck weicht nach unten aus, wenn der nächste Fleck DERSELBEN Bahn
    zu dicht darüber sitzt — sonst schreiben die Texte ineinander. Direkt
    über der Startlinie fehlt dafür der Platz, dort bleibt es oben.
    """
    order = sorted(range(len(rfs)), key=lambda i: rfs[i])
    sides = [rf <= LABEL_CEILING_RF for rf in rfs]
    for pos, idx in enumerate(order[:-1]):
        above_rf = rfs[order[pos + 1]]
        if above_rf - rfs[idx] < LABEL_MIN_GAP and rfs[idx] >= LABEL_FLOOR_RF:
            sides[idx] = False
    return sides


def build_plate(lanes: Sequence[Mapping]) -> PlateGeometry:
    """Rechnet Bahnen/Rf-Werte in Plattenkoordinaten um.

    lanes: [{"name": str, "spots": [{"rf": float, "label": str,
            "intensity": float}, …]}, …]
    """
    if not lanes:
        raise ValueError(
            "Mindestens eine Bahn (lane) wird benötigt — eine DC-Platte ohne "
            "Bahn hat nichts zu zeigen"
        )

    names: list[str] = []
    lane_x: list[float] = []
    spots: list[PlacedSpot] = []

    for index, lane in enumerate(lanes):
        name, raw_spots = _parse_lane(lane)
        x = LANE_SPACING * (index + 1)
        names.append(name)
        lane_x.append(x)

        parsed: list[tuple[float, float, str]] = []
        for spot in raw_spots:
            if "rf" not in spot:
                raise ValueError(
                    f"Fleck in Bahn {name!r} ohne Rf-Wert — Rf ist Pflicht "
                    "(Laufstrecke Substanz / Laufstrecke Front)"
                )
            rf = _spot_number(spot["rf"], name, "Rf-Wert")
            if not START_Y <= rf <= FRONT_Y:
                raise ValueError(
                    f"Rf-Wert {rf:g} in Bahn {name!r} liegt außerhalb von 0–1. "
                    "Rf ist ein Verhältnis (Laufstrecke Substanz / Laufstrecke "
                    "Front) und kann nicht größer als 1 oder negativ sein — "
                    "bitte die Messwerte prüfen."
                )
            intensity = _spot_number(
                spot.get("intensity", 1.0) if spot.get("intensity") is not None else 1.0,
                name,
                "Intensität",
            )
            if not 0.0 < intensity <= 1.0:
                raise ValueError(
                    f"Intensität {intensity:g} in Bahn {name!r} liegt außerhalb "
                    "von 0–1 (1 = kräftiger Fleck, 0.3 = schwacher Fleck)"
                )
            parsed.append((rf, intensity, str(spot.get("label", "") or "")))

        sides = _label_sides([rf for rf, _, _ in parsed])
        for (rf, intensity, label), above in zip(parsed, sides, strict=True):
            spots.append(
                PlacedSpot(
                    lane=name,
                    x=x,
                    y=START_Y + rf * (FRONT_Y - START_Y),
                    rf=rf,
                    intensity=intensity,
                    label=label,
                    label_above=above,
                )
            )

    return PlateGeometry(lanes=names, lane_x=lane_x, spots=spots)


def _caption(solvent: str, detection: str) -> str:
    parts = []
    if solvent:
        parts.append(f"Mobile phase: {solvent}")
    if detection:
        parts.append(f"Detection: {detection}")
    return "  ·  ".join(parts)


def build_figure(
    lanes: Sequence[Mapping],
    title: str = "",
    solvent: str = "",
    detection: str = "",
    figsize: tuple[float, float] | None = None,
) -> Figure:
    geo = build_plate(lanes)
    n = len(geo.lanes)

    fig = Figure(figsize=figsize or default_figsize(n), dpi=100)
    ax = fig.add_subplot()

    left, right = 0.5, n + 0.5
    ax.add_patch(
        Rectangle(
            (left, PLATE_BOTTOM),
            right - left,
            PLATE_TOP - PLATE_BOTTOM,
            facecolor=PLATE_FACE,
            edgecolor=PLATE_EDGE,
            linewidth=1.0,
            zorder=0,
        )
    )

    # Startlinie (Bleistift, gestrichelt) unten, Laufmittelfront oben.
    ax.hlines(START_Y, left, right, color=LINE_COLOR, linewidth=1.0, linestyles="--")
    ax.hlines(FRONT_Y, left, right, color=LINE_COLOR, linewidth=1.0)
    ax.text(
        left + 0.06, START_Y - 0.025, "Start (Rf 0)",
        fontsize=8, color=LINE_COLOR, ha="left", va="top",
    )
    ax.text(
        left + 0.06, FRONT_Y + 0.02, "Solvent Front (Rf 1)",
        fontsize=8, color=LINE_COLOR, ha="left", va="bottom",
    )

    for spot in geo.spots:
        ax.add_patch(
            Ellipse(
                (spot.x, spot.y),
                width=SPOT_WIDTH,
                height=SPOT_HEIGHT,
                facecolor=SPOT_FACE,
                edgecolor=SPOT_EDGE,
                linewidth=0.8,
                # Deckkraft = Intensität; ein schwacher Fleck bleibt sichtbar.
                alpha=0.25 + 0.75 * spot.intensity,
                zorder=3,
            )
        )
        ax.annotate(
            f"{spot.rf:.2f}",
            xy=(spot.x + SPOT_WIDTH / 2, spot.y),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
            color="#333333",
            zorder=4,
        )
        if spot.label:
            edge = SPOT_HEIGHT / 2 if spot.label_above else -SPOT_HEIGHT / 2
            ax.annotate(
                spot.label,
                xy=(spot.x, spot.y + edge),
                xytext=(0, 5 if spot.label_above else -5),
                textcoords="offset points",
                ha="center",
                va="bottom" if spot.label_above else "top",
                fontsize=8,
                zorder=4,
            )

    ax.set_xlim(left - 0.15, right + 0.15)
    ax.set_ylim(PLATE_BOTTOM - 0.07, PLATE_TOP + 0.07)
    ax.set_xticks(geo.lane_x)
    ax.set_xticklabels(geo.lanes, fontsize=9)
    ax.tick_params(axis="x", length=0, pad=6)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # Die Rf-Skala gilt nur zwischen Start und Front — die Achse endet dort.
    ax.spines["left"].set_bounds(START_Y, FRONT_Y)
    ax.set_ylabel("Rf value")
    ax.set_xlabel(_caption(solvent, detection), fontsize=9, color="#444444", labelpad=10)
    ax.set_title(f"TLC: {title}" if title else "TLC plate")
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    fig.tight_layout()
    return fig


def render_tlc_png(
    lanes: Sequence[Mapping],
    title: str = "",
    solvent: str = "",
    detection: str = "",
    figsize: tuple[float, float] | None = None,
    dpi: int = 150,
) -> bytes:
    fig = build_figure(lanes, title, solvent, detection, figsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    return buf.getvalue()


def render_tlc_svg(
    lanes: Sequence[Mapping],
    title: str = "",
    solvent: str = "",
    detection: str = "",
    figsize: tuple[float, float] | None = None,
) -> str:
    fig = build_figure(lanes, title, solvent, detection, figsize)
    buf = io.BytesIO()
    # fonttype "none": Text bleibt Text (durchsuchbar/editierbar) statt Pfade.
    with rc_context({"svg.fonttype": "none"}):
        fig.savefig(buf, format="svg", facecolor="white")
    return buf.getvalue().decode("utf-8")
