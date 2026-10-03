"""Pharmakokinetik-Kurve und Dosis-Wirkungs-Kurve als matplotlib-Diagramme.

Die Zahlen kommen aus `chemdraw_tool.pk` — dieselben Funktionen wie im Rechner
`calculate_pharmacokinetics`, damit Bild und Zahl übereinstimmen (wie bei
`ph_plots.exact_ph` und `ph_calc`). Das Speichern übernehmen die Helfer aus `ph_plots`.
"""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from chemdraw_tool import pk  # noqa: E402
from chemdraw_tool.ph_plots import (  # noqa: E402
    CURVE_POINTS,
    FIGSIZE,
    _fig_png,
    _fig_svg,
)

ORAL = "#1f77b4"
IV = "#d62728"
SINGLE = "#999999"
WINDOW = "#2ca02c"
MAX_DOSES = 40


def _legend_outside(ax) -> None:
    ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))


def pk_plan(ke: float, tau: float | None, ka: float | None) -> tuple[int, float]:
    """Anzahl Gaben und Zeitachsenlänge: bis etwa 97 % des Steady State (5 t½), sonst 6 t½."""
    t_half = pk.half_life(ke)
    if tau:
        n = min(max(math.ceil(5 * t_half / tau) + 1, 3), MAX_DOSES)
        return n, n * tau
    dauer = 6 * t_half
    if ka:
        dauer = max(dauer, 3 * pk.tmax(ka, ke))
    return 1, dauer


def build_pk_figure(
    dose: float,
    vd: float,
    ke: float,
    f: float = 1.0,
    ka: float | None = None,
    tau: float | None = None,
    mec: float | None = None,
    mtc: float | None = None,
    drug: str = "",
) -> Figure:
    n, dauer = pk_plan(ke, tau, ka)
    zeiten = [dauer * i / (CURVE_POINTS - 1) for i in range(CURVE_POINTS)]
    farbe = ORAL if ka else IV
    weg = "oral" if ka else "i.v. bolus"

    fig = Figure(figsize=FIGSIZE, dpi=100)
    ax = fig.add_subplot()

    if n > 1:
        einzel = pk.concentration_profile(dose, f, vd, ke, ka, zeiten)
        ax.plot(zeiten, einzel, color=SINGLE, linewidth=1.2, linestyle="--", label="single dose")
    gesamt = pk.concentration_profile(dose, f, vd, ke, ka, zeiten, tau=tau, n_doses=n)
    ax.plot(zeiten, gesamt, color=farbe, linewidth=2.0, label=f"{weg}, every {tau:g} h" if n > 1 else weg)

    if tau:
        cl = ke * vd
        avg = pk.css_avg(dose, f if ka else 1.0, cl, tau)
        ax.axhline(avg, color=farbe, linewidth=0.9, linestyle=":", label=f"Css,av = {avg:.3g} mg/L")
    elif ka:
        tm, cm = pk.tmax(ka, ke), pk.cmax(dose, f, vd, ke, ka)
        ax.plot([tm], [cm], marker="o", color=farbe)
        ax.annotate(f"Cmax {cm:.3g} mg/L\nat {tm:.3g} h", (tm, cm), textcoords="offset points", xytext=(10, 4), fontsize=9)

    if mec:
        ax.axhline(mec, color=WINDOW, linewidth=1.2, label=f"MEC {mec:g} mg/L")
    if mtc:
        ax.axhline(mtc, color=IV if farbe != IV else "#ff7f0e", linewidth=1.2, label=f"MTC {mtc:g} mg/L")
    if mec and mtc:
        ax.axhspan(mec, mtc, color=WINDOW, alpha=0.08)

    ax.set_xlim(0, dauer)
    ax.set_ylim(0, None)
    ax.set_xlabel("Time t [h]")
    ax.set_ylabel("Plasma concentration C [mg/L]")
    ax.set_title(f"Pharmacokinetics: {drug}" if drug else "Pharmacokinetics (one-compartment model)")
    _legend_outside(ax)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, linewidth=0.4, alpha=0.3)
    fig.tight_layout()
    return fig


def build_dose_response_figure(
    ec50: float,
    unit: str = "nM",
    emax: float = 100.0,
    hill: float = 1.0,
    antagonist: float | None = None,
    kb: float | None = None,
    drug: str = "",
) -> Figure:
    r = pk.dose_ratio(antagonist, kb) if antagonist is not None and kb is not None else 1.0
    lo = math.log10(ec50) - 3
    hi = math.log10(ec50 * max(r, 1.0)) + 3
    log_c = [lo + (hi - lo) * i / (CURVE_POINTS - 1) for i in range(CURVE_POINTS)]
    conc = [10**x for x in log_c]

    fig = Figure(figsize=FIGSIZE, dpi=100)
    ax = fig.add_subplot()
    ax.plot(conc, [pk.response(c, ec50, emax, hill) for c in conc], color=ORAL, linewidth=2.0, label=f"agonist, EC50 = {ec50:g} {unit}")
    ax.axvline(ec50, color=ORAL, linewidth=0.8, linestyle=":")
    if r > 1.0:
        ec_shift = ec50 * r
        ax.plot(
            conc,
            [pk.response(c, ec_shift, emax, hill) for c in conc],
            color=IV,
            linewidth=2.0,
            label=f"+ competitive antagonist {antagonist:g} {unit} (r = {r:.3g})",
        )
        ax.axvline(ec_shift, color=IV, linewidth=0.8, linestyle=":")
    ax.axhline(emax / 2, color="#bbbbbb", linewidth=0.8, linestyle="--")

    ax.set_xscale("log")
    ax.set_xlim(10**lo, 10**hi)
    ax.set_ylim(0, emax * 1.03)
    ax.set_xlabel(f"Agonist concentration [{unit}] (log scale)")
    ax.set_ylabel("Response [% of Emax]" if emax == 100 else "Response")
    ax.set_title(f"Dose-response: {drug}" if drug else "Dose-response")
    _legend_outside(ax)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, which="both", linewidth=0.3, alpha=0.25)
    fig.tight_layout()
    return fig


def render_pk_png(**kwargs) -> bytes:
    return _fig_png(build_pk_figure(**kwargs))


def render_pk_svg(**kwargs) -> str:
    return _fig_svg(build_pk_figure(**kwargs))


def render_dose_response_png(**kwargs) -> bytes:
    return _fig_png(build_dose_response_figure(**kwargs))


def render_dose_response_svg(**kwargs) -> str:
    return _fig_svg(build_dose_response_figure(**kwargs))
