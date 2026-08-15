"""Kalibriergerade als Diagramm — Standards, Regressionsgerade, Unbekannte.

Nutzt bewusst `_fig_png`/`_fig_svg` aus `ph_plots`: Bildgröße, DPI, weisser
Hintergrund und die `svg.fonttype`-Regel (Text bleibt Text) sind damit
dieselben wie bei allen anderen matplotlib-Grafiken des Servers.
"""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib.figure import Figure

from chemdraw_tool.ph_plots import DPI, FIGSIZE, _fig_png, _fig_svg  # noqa: F401

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
        ax.annotate(
            f"{conc:.4g}" + (" (extrapolated)" if u.get("extrapolated") else ""),
            xy=(conc, sig),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color=UNKNOWN_COLOR,
        )

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
    return fig


def render_png(**kwargs) -> bytes:
    return _fig_png(build_figure(**kwargs))


def render_svg(**kwargs) -> str:
    return _fig_svg(build_figure(**kwargs))
