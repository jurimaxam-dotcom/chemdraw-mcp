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
            f"Unbekannter Spektrentyp {spectrum_type!r} — "
            f"erlaubt sind {sorted(SPECTRUM_TYPES)}"
        )
    return cfg


def _parse_peaks(cfg: SpectrumConfig, peaks: Sequence[Mapping]) -> list[_Peak]:
    if not peaks:
        raise ValueError("Mindestens ein Peak wird benötigt")
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
        raise ValueError("Alle Intensitäten sind 0 — mindestens eine muss ≠ 0 sein")
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
    ys = [sum(_peak_value(cfg, p, x) for p in parsed) for x in xs]
    if cfg.kind == "transmission":
        ys = [max(0.0, 100.0 - _TRANSMISSION_DEPTH * y) for y in ys]
    return xs, ys


def _apex(cfg: SpectrumConfig, p: _Peak) -> tuple[float, float, bool]:
    """(x, y, oberhalb?) für die Label-Position eines Peaks."""
    if cfg.kind == "transmission":
        return p.position, 100.0 - _TRANSMISSION_DEPTH * p.intensity, False
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

    ax.set_xlim(*_x_range(cfg, parsed))
    if cfg.invert_x:
        ax.invert_xaxis()

    for p in parsed:
        if not p.label:
            continue
        lx, ly, above = _apex(cfg, p)
        ax.annotate(
            p.label,
            xy=(lx, ly),
            xytext=(0, 8 if above else -14),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    ax.set_xlabel(cfg.x_label)
    ax.set_ylabel(cfg.y_label)
    ax.set_title(f"{cfg.title}: {title}" if title else cfg.title)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


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
