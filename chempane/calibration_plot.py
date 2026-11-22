"""Kalibriergerade als Diagramm — Standards, Regressionsgerade, Unbekannte.

Nutzt bewusst `_fig_png`/`_fig_svg` aus `ph_plots`: Bildgröße, DPI, weisser
Hintergrund und die `svg.fonttype`-Regel (Text bleibt Text) sind damit
dieselben wie bei allen anderen matplotlib-Grafiken des Servers.
"""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib.figure import Figure

from chempane.ph_plots import DPI, FIGSIZE, _fig_png, _fig_svg, safe_text  # noqa: F401

POINT_COLOR = "#1f77b4"
LINE_COLOR = "#1a1a1a"
UNKNOWN_COLOR = "#d62728"


def build_figure(
    regression: dict,
    unknowns: Sequence[dict] = (),
    title: str = "",
    x_label: str = "Concentration",
    y_label: str = "Signal",
) -> Figure:
    title, x_label, y_label = safe_text(title), safe_text(x_label), safe_text(y_label)
    fig = Figure(figsize=FIGSIZE, dpi=100)
    ax = fig.add_subplot()

    x = regression["x"]
    y = regression["y"]

    # Die Gerade über den kalibrierten Bereich, plus etwas Luft — aber nur so
    # viel, dass nicht der Eindruck entsteht, dort sei noch gemessen worden.
    span = regression["x_max"] - regression["x_min"]
    pad = span * 0.05 if span else 1.0
    line_x = [regression["x_min"] - pad, regression["x_max"] + pad]
    line_y = [regression["slope"] * xi + regression["intercept"] for xi in line_x]
    ax.plot(line_x, line_y, color=LINE_COLOR, linewidth=1.4, zorder=1)

    ax.scatter(x, y, s=42, color=POINT_COLOR, zorder=3, label="Standards")

    labels: list = []
    for u in unknowns:
        conc = u["concentration"]
        sig = u["signal"]
        # Ableselinien: waagerecht vom Signal, senkrecht zur Konzentration —
        # genau der Handgriff, den man sonst mit dem Lineal macht.
        ax.plot(
            [line_x[0], conc],
            [sig, sig],
            color=UNKNOWN_COLOR,
            linewidth=0.9,
            linestyle=":",
            zorder=2,
        )
        ax.plot(
            [conc, conc],
            [min(min(y), min(line_y)), sig],
            color=UNKNOWN_COLOR,
            linewidth=0.9,
            linestyle=":",
            zorder=2,
        )
        ax.scatter(
            [conc], [sig], s=52, color=UNKNOWN_COLOR, marker="D", zorder=4
        )
        labels.append((u, conc, sig))

    subtitle = f"{regression['equation']}    R² = {regression['r_squared']:.5f}"
    ax.set_title(f"{title}\n{subtitle}" if title else subtitle, fontsize=11)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, linewidth=0.4, alpha=0.3)
    if unknowns:
        ax.scatter([], [], s=52, color=UNKNOWN_COLOR, marker="D", label="Samples")
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    _place_sample_labels(fig, ax, regression, x, y, line_x, labels)
    return fig


def _corners(conc: float, line_x: list, rising: bool) -> list[tuple[int, int]]:
    """Ecken (dx, dy in Punkten), bevorzugte zuerst.

    Die Zahl gehört dorthin, wohin die Gerade nicht weiterläuft: steigt sie,
    rechts unten bzw. links oben; fällt sie, rechts oben bzw. links unten. In
    der rechten Hälfte nach links, damit nichts über den Achsenrand ragt.
    """
    right_half = conc > (line_x[0] + line_x[1]) / 2
    dx = -8 if right_half else 8
    dy = 8 if right_half == rising else -8
    return [(dx, dy), (-dx, -dy), (dx, -dy), (-dx, dy)]


def _place_sample_labels(fig, ax, regression, x, y, line_x, labels) -> None:
    """Probenzahlen setzen und im gerenderten Bild prüfen: frei von Gerade, Standards, Rand.

    Erst nach tight_layout, weil der Test in Pixeln rechnet. Passt keine Ecke,
    bleibt die bevorzugte (vorher: immer rechts oben, oft auf der Geraden).
    """
    if not labels:
        return
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    renderer = FigureCanvasAgg(fig).get_renderer()
    (line,) = [ln for ln in ax.lines if ln.get_zorder() == 1]
    line_path = line.get_path().transformed(line.get_transform())
    standards = ax.transData.transform(list(zip(x, y)))
    axes_box = ax.get_window_extent(renderer)
    marker_pad = 5 * fig.dpi / 72  # halber Markerdurchmesser plus Luft

    def free(box) -> bool:
        if line_path.intersects_bbox(box, filled=False):
            return False
        if box.x0 < axes_box.x0 or box.x1 > axes_box.x1 or box.y0 < axes_box.y0 or box.y1 > axes_box.y1:
            return False
        grown = box.padded(marker_pad)
        return not any(grown.contains(px, py) for px, py in standards)

    def put(text, conc, sig, dx, dy):
        return ax.annotate(
            text,
            xy=(conc, sig),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx > 0 else "right",
            va="bottom" if dy > 0 else "top",
            fontsize=9,
            color=UNKNOWN_COLOR,
        )

    for u, conc, sig in labels:
        text = f"{conc:.4g}" + (" (extrapolated)" if u.get("extrapolated") else "")
        candidates = _corners(conc, line_x, regression["slope"] >= 0)
        for dx, dy in candidates:
            ann = put(text, conc, sig, dx, dy)
            if free(ann.get_window_extent(renderer)):
                break
            ann.remove()
        else:
            put(text, conc, sig, *candidates[0])


def render_png(**kwargs) -> bytes:
    return _fig_png(build_figure(**kwargs))


def render_svg(**kwargs) -> str:
    return _fig_svg(build_figure(**kwargs))
