"""Schematische Spektren aus Peaklisten — Rendering als PNG/SVG via matplotlib.

Zweck: Lehr-/Protokoll-Spektren aus Peaklisten oder Messpunkten zeichnen
(IR, NIR, Raman, UV/Vis, Fluoreszenz, ORD, CD, ¹H-/¹³C-NMR, MS). Das Modul
*erfindet* keine Spektren — die Peaks liefert der Aufrufer.

Aufbau analog image_export.py: pure Berechnung (build_curve) getrennt vom
Datei-Rendering; der MCP-Server setzt nur noch Pfade und Payload obendrauf.

Intensitäten sind relativ und werden normiert: positive Typen auf max=1
(Transmission: 100 % − 95 %·s), signierte Typen (ord/cd) auf max|i|=1,
MS auf Basispeak = 100 %.
"""

from __future__ import annotations

import io
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

from matplotlib import rc_context  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from chemdraw_tool.ph_plots import safe_text  # noqa: E402


@dataclass(frozen=True)
class SpectrumConfig:
    title: str
    x_label: str
    y_label: str
    x_default: tuple[float, float]
    invert_x: bool
    # "absorption": Peaks nach oben ab Basislinie 0 (max 1)
    # "transmission": Basislinie 100 %, Peaks als Einbrüche (IR-Konvention)
    # "signed": vorzeichenbehaftete Banden um die Nulllinie (CD)
    # "cotton": antisymmetrische S-Kurve mit Nulldurchgang bei position (ORD)
    # "bars": diskrete Linien statt Kurve (MS)
    kind: str
    shape: str  # "lorentz" | "gauss" | "" (bars)
    default_width: float


# Englische Default-Beschriftung (internationales Tool); der freie
# title-Parameter der Tools bleibt lokalisierbar.
SPECTRUM_TYPES: dict[str, SpectrumConfig] = {
    "ir": SpectrumConfig(
        "IR spectrum", "Wavenumber [cm⁻¹]", "Transmission [%]",
        (400, 4000), True, "transmission", "lorentz", 30,
    ),
    "nir": SpectrumConfig(
        "NIR spectrum", "Wavenumber [cm⁻¹]", "Absorbance",
        (4000, 10000), True, "absorption", "gauss", 150,
    ),
    "raman": SpectrumConfig(
        "Raman spectrum", "Raman shift [cm⁻¹]", "Intensity",
        (200, 3600), False, "absorption", "lorentz", 20,
    ),
    "uv_vis": SpectrumConfig(
        "UV/Vis spectrum", "Wavelength λ [nm]", "Absorbance",
        (200, 800), False, "absorption", "gauss", 20,
    ),
    "fluorescence": SpectrumConfig(
        "Fluorescence spectrum", "Wavelength λ [nm]", "Relative intensity",
        (300, 800), False, "absorption", "gauss", 25,
    ),
    "ord": SpectrumConfig(
        "ORD spectrum", "Wavelength λ [nm]", "Specific rotation [α]",
        (200, 600), False, "cotton", "gauss", 25,
    ),
    "cd": SpectrumConfig(
        "CD spectrum", "Wavelength λ [nm]", "Δε",
        (200, 600), False, "signed", "gauss", 20,
    ),
    "nmr_1h": SpectrumConfig(
        # Bis 12 ppm, damit COOH/CHO-Signale nicht an der Achsenkante kleben.
        "¹H NMR spectrum", "δ [ppm]", "Intensity",
        (0, 12), True, "absorption", "lorentz", 0.03,
    ),
    "nmr_13c": SpectrumConfig(
        "¹³C NMR spectrum", "δ [ppm]", "Intensity",
        (0, 220), True, "absorption", "lorentz", 0.5,
    ),
    "ms": SpectrumConfig(
        "Mass spectrum", "m/z", "Relative intensity [%]",
        (0, 0), False, "bars", "", 0,
    ),
}

# Label-Layout (Offsets in Punkten): Basis-Versatz über/unter dem Apex plus
# Staffelungs-Schritt für x-nahe Nachbarn (näher als LABEL_NEAR_FRAC der
# x-Spannweite).
LABEL_BASE_ABOVE = 8
LABEL_BASE_BELOW = -14
LABEL_STACK_STEP = 12
LABEL_NEAR_FRAC = 0.06

# Tiefster IR-Einbruch: Transmission fällt bei s=1 auf 5 % (nie ganz auf 0,
# wie bei realen Spektren).
_TRANSMISSION_DEPTH = 95.0
_CURVE_POINTS = 2000


@dataclass(frozen=True)
class _Peak:
    position: float
    intensity: float
    width: float
    label: str


def _get_config(spectrum_type: str) -> SpectrumConfig:
    cfg = SPECTRUM_TYPES.get(spectrum_type)
    if cfg is None:
        raise ValueError(
            f"Unknown spectrum type {spectrum_type!r} — "
            f"allowed: {sorted(SPECTRUM_TYPES)}"
        )
    return cfg


def _parse_peaks(cfg: SpectrumConfig, peaks: Sequence[Mapping]) -> list[_Peak]:
    if not peaks:
        raise ValueError("At least one peak is needed.")
    parsed = [
        _Peak(
            position=float(p["position"]),
            intensity=float(p.get("intensity", 1.0)),
            width=float(p.get("width") or cfg.default_width),
            label=str(p.get("label", "") or ""),
        )
        for p in peaks
    ]
    norm = max(abs(p.intensity) for p in parsed)
    if norm == 0:
        raise ValueError("All intensities are 0 — at least one peak needs a nonzero intensity.")
    signed = cfg.kind in ("signed", "cotton")
    return [
        _Peak(
            p.position,
            # Nicht-signierte Typen kennen keine negativen Peaks → Betrag.
            (p.intensity if signed else abs(p.intensity)) / norm,
            p.width,
            p.label,
        )
        for p in parsed
    ]


def _x_range(cfg: SpectrumConfig, peaks: list[_Peak]) -> tuple[float, float]:
    lo = min(p.position - 3 * p.width for p in peaks)
    hi = max(p.position + 3 * p.width for p in peaks)
    if cfg.kind == "bars":
        # MS: etwas Luft um den größten m/z, Achse beginnt bei 0.
        return 0.0, hi * 1.1
    return min(cfg.x_default[0], lo), max(cfg.x_default[1], hi)


def _sample_points(cfg: SpectrumConfig, peaks: list[_Peak]) -> list[float]:
    """Gleichmäßiges Raster plus Stützpunkte an jedem Peak.

    Die expliziten Peak-Punkte garantieren, dass auch sehr schmale Linien
    (NMR) ihr volles Maximum erreichen, unabhängig von der Rasterdichte.
    """
    lo, hi = _x_range(cfg, peaks)
    step = (hi - lo) / _CURVE_POINTS
    xs = {lo + i * step for i in range(_CURVE_POINTS + 1)}
    for p in peaks:
        for k in (-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3):
            xs.add(p.position + k * p.width)
    return sorted(x for x in xs if lo <= x <= hi)


def _peak_value(cfg: SpectrumConfig, p: _Peak, x: float) -> float:
    u = (x - p.position) / p.width
    if cfg.kind == "cotton":
        # Antisymmetrische Cotton-Effekt-Kurve: Nulldurchgang bei position,
        # Extrema bei position ± width, normiert auf max|y| = |intensity|.
        return p.intensity * u * math.exp(0.5 - u * u / 2)
    if cfg.shape == "gauss":
        return p.intensity * math.exp(-(u * u) / 2)
    # Lorentz-Profil (IR/Raman/NMR-Linienform)
    return p.intensity / (1 + u * u)


def build_curve(
    spectrum_type: str, peaks: Sequence[Mapping]
) -> tuple[list[float], list[float]]:
    """Berechnet die Spektrenkurve: (x-Werte, y-Werte).

    Für "ms" sind das die Balken (Positionen, Intensitäten in %), für alle
    anderen Typen eine kontinuierliche Kurve über den Achsenbereich.
    """
    cfg = _get_config(spectrum_type)
    parsed = _parse_peaks(cfg, peaks)

    if cfg.kind == "bars":
        return (
            [p.position for p in parsed],
            [100.0 * p.intensity for p in parsed],
        )

    xs = _sample_points(cfg, parsed)
    if cfg.kind == "transmission":
        # Transmission multipliziert sich (T = T₁·T₂…). Früher addiert und bei
        # 0 % abgeschnitten: zwei starke Nachbarbanden (Aspirin C=O 1750/1690)
        # lagen als flacher Boden auf der Achse (Befund 30.10.2026).
        return xs, [_transmission(cfg, parsed, x) for x in xs]
    ys = [sum(_peak_value(cfg, p, x) for p in parsed) for x in xs]
    return xs, ys


def _transmission(cfg: SpectrumConfig, peaks: list[_Peak], x: float) -> float:
    t = 100.0
    for p in peaks:
        t *= 1.0 - (_TRANSMISSION_DEPTH / 100.0) * _peak_value(cfg, p, x)
    return t


def _apex(
    cfg: SpectrumConfig, p: _Peak, peaks: list[_Peak]
) -> tuple[float, float, bool]:
    """(x, y, oberhalb?) für die Label-Position eines Peaks."""
    if cfg.kind == "transmission":
        # Auf der Kurve, nicht auf der Einzelbande — Nachbarn vertiefen sie.
        return p.position, _transmission(cfg, peaks, p.position), False
    if cfg.kind == "bars":
        return p.position, 100.0 * p.intensity, True
    if cfg.kind == "cotton":
        return p.position + p.width, p.intensity, p.intensity > 0
    return p.position, p.intensity, p.intensity > 0


def _build_figure(
    spectrum_type: str,
    peaks: Sequence[Mapping],
    title: str,
    figsize: tuple[float, float],
) -> Figure:
    cfg = _get_config(spectrum_type)
    parsed = _parse_peaks(cfg, peaks)
    x, y = build_curve(spectrum_type, peaks)

    fig = Figure(figsize=figsize, dpi=100)
    ax = fig.add_subplot()

    if cfg.kind == "bars":
        ax.vlines(x, 0, y, color="#1a1a1a", linewidth=1.5)
        ax.set_ylim(0, 112)
    else:
        ax.plot(x, y, color="#1a1a1a", linewidth=1.2)

    if cfg.kind == "transmission":
        ax.set_ylim(-2, 112)
    elif cfg.kind in ("signed", "cotton"):
        ax.axhline(0, color="#888888", linewidth=0.8)
        limit = 1.25 * max(abs(v) for v in y)
        ax.set_ylim(-limit, limit)
    elif cfg.kind == "absorption":
        ax.set_ylim(0, 1.18)

    x_lo, x_hi = _x_range(cfg, parsed)
    ax.set_xlim(x_lo, x_hi)
    if cfg.invert_x:
        ax.invert_xaxis()

    ax.set_xlabel(cfg.x_label)
    ax.set_ylabel(cfg.y_label)
    ax.set_title(f"{cfg.title}: {safe_text(title)}" if title else cfg.title)
    ax.spines[["top", "right"]].set_visible(False)
    # Layout VOR den Labels fixieren — der Floor-Clamp unten rechnet über
    # transData in Pixel, und tight_layout würde die Achsen-Box verschieben.
    fig.tight_layout()

    # Labels x-sortiert annotieren; x-nahe Nachbarn gleicher Richtung werden
    # über 3 Ebenen rotierend gestaffelt, sonst schreiben sie ineinander
    # (z.B. die Aromaten-Banden 750/700 cm⁻¹ in einem 12-Peak-IR).
    span = abs(x_hi - x_lo)
    y_lo = ax.get_ylim()[0]
    y_span = ax.get_ylim()[1] - y_lo
    px_per_pt = fig.dpi / 72.0
    labeled = sorted(
        ((_apex(cfg, p, parsed), p) for p in parsed if p.label),
        key=lambda item: item[0][0],
    )
    placed: list = []
    prev_x: float | None = None
    prev_above: bool | None = None
    stack = 0
    for (lx, ly, above), p in labeled:
        near = prev_x is not None and abs(lx - prev_x) < LABEL_NEAR_FRAC * span
        stack = (stack + 1) % 3 if (near and above == prev_above) else 0
        offset = (
            LABEL_BASE_ABOVE + stack * LABEL_STACK_STEP
            if above
            else LABEL_BASE_BELOW - stack * LABEL_STACK_STEP
        )
        if not above:
            # Floor-Clamp: tiefe Apexe (C=O-Dip bei 3 %) dürfen ihr Label
            # nicht unter die Plot-Unterkante schieben — Baseline bleibt
            # oberhalb von y_lo + 4 % Spannweite.
            anchor_px = ax.transData.transform((lx, ly))[1]
            floor_px = ax.transData.transform((lx, y_lo + 0.04 * y_span))[1]
            min_offset = (floor_px - anchor_px) / px_per_pt
            offset = max(offset, min_offset)
        ann = ax.annotate(
            safe_text(p.label),
            xy=(lx, ly),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
        placed.append((ann, lx, ly, offset, above))
        prev_x, prev_above = lx, above

    _spread_overlapping_labels(fig, ax, placed)
    return fig


LABEL_GAP_PX = 6
# Eine gespreizte Gruppe steht so weit von ihren Apexen weg, dass die
# Führungslinien steil laufen und unter/über der Labelreihe bleiben.
LABEL_ROW_LIFT = 22
_LEADER = {"arrowstyle": "-", "color": "#888888", "linewidth": 0.6, "shrinkA": 1, "shrinkB": 2}


def _text_box(ann, renderer):
    """Nur die Textbox — Annotation.get_window_extent schlösse die Führungslinie ein."""
    from matplotlib.text import Text

    ann.update_positions(renderer)
    return Text.get_window_extent(ann, renderer)


def _spread_overlapping_labels(fig: Figure, ax, placed: list) -> None:
    """Labels, die sich wirklich überschneiden, als Reihe mit Führungslinien (E17).

    Die Staffelung oben kennt nur den x-Abstand; zwei tiefe IR-Banden (1750/
    1690 cm⁻¹) landen über den Boden-Clamp trotzdem auf derselben Höhe. Hier
    zählt die gemessene Textbox: überschneidende Labels einer Gruppe stehen
    nebeneinander (Reihenfolge wie die Banden) in einer Reihe, die um
    LABEL_ROW_LIFT vom Apex weg versetzt ist — bei IR in die Bande hinein,
    sonst darüber —, jedes mit einer dünnen Linie zu seinem Apex. Ohne
    Überschneidung passiert nichts: das Bild bleibt byteweise gleich.
    """
    if len(placed) < 2:
        return
    renderer = fig._get_renderer()
    px_per_pt = fig.dpi / 72.0
    area = ax.get_window_extent(renderer)
    group = list(range(len(placed)))

    def root(i):
        while group[i] != i:
            i = group[i]
        return i

    for _round in range(4):
        boxes = [_text_box(item[0], renderer) for item in placed]
        pairs = [
            (i, j)
            for i in range(len(boxes))
            for j in range(i + 1, len(boxes))
            if boxes[i].overlaps(boxes[j])
        ]
        if not pairs:
            return
        for i, j in pairs:
            group[root(i)] = root(j)
        members: dict[int, list[int]] = {}
        for i in range(len(placed)):
            members.setdefault(root(i), []).append(i)
        for idx in members.values():
            if len(idx) < 2:
                continue
            anchor = {i: ax.transData.transform((placed[i][1], placed[i][2])) for i in idx}
            idx.sort(key=lambda i: anchor[i][0])
            widths = [boxes[i].width for i in idx]
            total = sum(widths) + LABEL_GAP_PX * (len(idx) - 1)
            centre = sum(a[0] for a in anchor.values()) / len(idx)
            start = min(max(centre - total / 2, area.x0), area.x1 - total)
            # Reihe auf gemeinsamer Höhe: über dem höchsten Apex (IR: die
            # Labels gehen in die Bande hinein) bzw. über dem höchsten Peak.
            top = max(a[1] for a in anchor.values()) + LABEL_ROW_LIFT * px_per_pt
            for i, width in zip(idx, widths):
                ann, lx, ly, offset, above = placed[i]
                text = ann.get_text()
                ann.remove()
                dx = (start + width / 2 - anchor[i][0]) / px_per_pt
                dy = (top - anchor[i][1]) / px_per_pt
                placed[i] = (
                    ax.annotate(
                        text,
                        xy=(lx, ly),
                        xytext=(dx, dy),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        arrowprops=_LEADER,
                    ),
                    lx,
                    ly,
                    offset,
                    above,
                )
                start += width + LABEL_GAP_PX


def render_spectrum_png(
    spectrum_type: str,
    peaks: Sequence[Mapping],
    title: str = "",
    figsize: tuple[float, float] = (10.0, 6.5),
    dpi: int = 150,
) -> bytes:
    fig = _build_figure(spectrum_type, peaks, title, figsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    return buf.getvalue()


def render_spectrum_svg(
    spectrum_type: str,
    peaks: Sequence[Mapping],
    title: str = "",
    figsize: tuple[float, float] = (10.0, 6.5),
) -> str:
    fig = _build_figure(spectrum_type, peaks, title, figsize)
    buf = io.BytesIO()
    # fonttype "none": Text bleibt Text (durchsuchbar/editierbar) statt Pfade.
    with rc_context({"svg.fonttype": "none"}):
        fig.savefig(buf, format="svg", facecolor="white")
    return buf.getvalue().decode("utf-8")
