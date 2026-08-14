"""Titrationskurven + Speziesverteilung — pH-Mathematik und matplotlib-Plots.

Gemeinsamer Kern beider Diagramme sind die α-Fraktionen einer (auch
mehrprotonigen) Säure als Funktion des pH. Die Titrationskurve löst pro
Titrantvolumen die exakte Ladungsbilanz per Bisektion, statt mit den
Lehrbuch-Näherungsformeln zu rechnen — die Näherungen dienen nur als
Test-Referenzen.

Wie bei den Spektren gilt: Das Modell liefert die Stoffdaten (pKa-Werte,
Konzentrationen, Indikator-Umschlagbereich), das Tool rechnet und zeichnet.
MVP-Scope: schwache/mehrprotonige SÄURE titriert mit STARKER BASE — der
Klausur- und Arzneibuch-Standardfall.
"""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

from matplotlib import rc_context  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

FIGSIZE = (10.0, 6.5)
DPI = 150
CURVE_POINTS = 400
INDICATOR_COLOR = "#9467bd"
SPECIES_COLORS = ("#1a1a1a", "#d62728", "#1f77b4", "#2ca02c", "#9467bd")


def alpha_fractions(pka_values: Sequence[float], ph: float) -> list[float]:
    """Anteile der Protonierungsspezies H(n)A … A(n-) bei gegebenem pH.

    Index 0 = vollprotonierte Form. Summe ist 1.
    """
    h = 10.0 ** (-ph)
    kas = [10.0 ** (-pka) for pka in pka_values]
    n = len(kas)
    terms = []
    for k in range(n + 1):
        ka_product = 1.0
        for j in range(k):
            ka_product *= kas[j]
        terms.append(h ** (n - k) * ka_product)
    denominator = sum(terms)
    return [t / denominator for t in terms]


@dataclass(frozen=True)
class TitrationCurve:
    volumes_ml: list[float]
    ph: list[float]
    eq_volumes_ml: list[float]


def _charge_balance_ph(
    pka_values: Sequence[float], c_acid: float, c_na: float
) -> float:
    """pH aus der Ladungsbilanz [Na+] + [H+] = [OH-] + Σ k·α_k·C_A,
    gelöst per Bisektion (f ist in pH streng monoton)."""

    def f(ph: float) -> float:
        h = 10.0 ** (-ph)
        oh = 10.0 ** (ph - 14.0)
        alphas = alpha_fractions(pka_values, ph)
        bound = sum(k * a for k, a in enumerate(alphas)) * c_acid
        return c_na + h - oh - bound

    lo, hi = 0.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def titration_curve(
    pka_values: Sequence[float],
    c_acid: float,
    v_acid_ml: float,
    c_titrant: float,
) -> TitrationCurve:
    n = len(pka_values)
    v_eq1 = c_acid * v_acid_ml / c_titrant
    eq_volumes = [v_eq1 * (k + 1) for k in range(n)]
    v_max = eq_volumes[-1] * 1.5

    volumes = [v_max * i / (CURVE_POINTS - 1) for i in range(CURVE_POINTS)]
    phs = []
    for v_b in volumes:
        total = v_acid_ml + v_b
        phs.append(
            _charge_balance_ph(
                pka_values,
                c_acid=c_acid * v_acid_ml / total,
                c_na=c_titrant * v_b / total,
            )
        )
    return TitrationCurve(volumes, phs, eq_volumes)


def build_titration_figure(
    pka_values: Sequence[float],
    c_acid: float,
    v_acid_ml: float,
    c_titrant: float,
    title: str = "",
    indicator: Mapping | None = None,
) -> Figure:
    curve = titration_curve(pka_values, c_acid, v_acid_ml, c_titrant)

    fig = Figure(figsize=FIGSIZE, dpi=100)
    ax = fig.add_subplot()
    ax.plot(curve.volumes_ml, curve.ph, color="#1a1a1a", linewidth=1.6)

    # Äquivalenzpunkte je Protolysestufe
    for i, v_eq in enumerate(curve.eq_volumes_ml, start=1):
        ax.axvline(v_eq, color="#888888", linewidth=0.9, linestyle="--")
        suffix = f" {i}" if len(curve.eq_volumes_ml) > 1 else ""
        ax.annotate(
            f"EP{suffix}",
            xy=(v_eq, 0.4),
            ha="center",
            fontsize=9,
            color="#555555",
        )

    # Halbäquivalenz: pH = pKa (Pufferpunkte)
    for k, pka in enumerate(pka_values):
        v_half = curve.eq_volumes_ml[0] * (k + 0.5)
        if 0 < pka < 14:
            ax.plot([v_half], [pka], marker="o", markersize=5, color="#d62728")
            ax.annotate(
                f"pH = pKa{k + 1 if len(pka_values) > 1 else ''} = {pka:g}",
                xy=(v_half, pka),
                xytext=(8, -4),
                textcoords="offset points",
                fontsize=9,
                color="#d62728",
            )

    if indicator:
        lo, hi = indicator["ph_range"]
        ax.axhspan(lo, hi, color=INDICATOR_COLOR, alpha=0.12)
        ax.annotate(
            str(indicator.get("name", "Indicator")),
            xy=(0.99, (lo + hi) / 2),
            xycoords=("axes fraction", "data"),
            ha="right",
            va="center",
            fontsize=9,
            color=INDICATOR_COLOR,
        )

    ax.set_xlim(0, curve.volumes_ml[-1])
    ax.set_ylim(0, 14)
    ax.set_xlabel("Titrant volume [mL]")
    ax.set_ylabel("pH")
    ax.set_title(f"Titration curve: {title}" if title else "Titration curve")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def _default_species_labels(n: int) -> list[str]:
    subscripts = "₀₁₂₃₄₅₆₇₈₉"

    def sub(k: int) -> str:
        return "".join(subscripts[int(d)] for d in str(k)) if k > 1 else ""

    superscripts = {1: "⁻", 2: "²⁻", 3: "³⁻", 4: "⁴⁻"}
    labels = []
    for k in range(n + 1):
        protons = n - k
        if protons > 0:
            labels.append(f"H{sub(protons)}A{superscripts.get(k, '')}")
        else:
            labels.append(f"A{superscripts.get(k, '⁻')}")
    return labels


def build_species_figure(
    pka_values: Sequence[float],
    labels: Sequence[str] | None = None,
    title: str = "",
) -> Figure:
    n = len(pka_values)
    labels = list(labels) if labels else _default_species_labels(n)
    if len(labels) != n + 1:
        raise ValueError(
            f"{n} pKa-Werte ergeben {n + 1} Spezies — {len(labels)} Labels übergeben."
        )

    phs = [14.0 * i / (CURVE_POINTS - 1) for i in range(CURVE_POINTS)]
    fractions = [alpha_fractions(pka_values, ph) for ph in phs]

    fig = Figure(figsize=FIGSIZE, dpi=100)
    ax = fig.add_subplot()
    for k, label in enumerate(labels):
        ax.plot(
            phs,
            [f[k] for f in fractions],
            label=label,
            linewidth=1.6,
            color=SPECIES_COLORS[k % len(SPECIES_COLORS)],
        )
    for pka in pka_values:
        ax.axvline(pka, color="#bbbbbb", linewidth=0.8, linestyle="--")

    ax.set_xlim(0, 14)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("pH")
    ax.set_ylabel("Species fraction α")
    ax.set_title(f"Species distribution: {title}" if title else "Species distribution")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def _fig_png(fig: Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    return buf.getvalue()


def _fig_svg(fig: Figure) -> str:
    buf = io.BytesIO()
    # fonttype "none": Text bleibt Text (durchsuchbar) statt Pfade.
    with rc_context({"svg.fonttype": "none"}):
        fig.savefig(buf, format="svg", facecolor="white")
    return buf.getvalue().decode("utf-8")


def render_titration_png(**kwargs) -> bytes:
    return _fig_png(build_titration_figure(**kwargs))


def render_titration_svg(**kwargs) -> str:
    return _fig_svg(build_titration_figure(**kwargs))


def render_species_png(pka_values, labels=None, title="") -> bytes:
    return _fig_png(build_species_figure(pka_values, labels, title))


def render_species_svg(pka_values, labels=None, title="") -> str:
    return _fig_svg(build_species_figure(pka_values, labels, title))
