"""Pharmakokinetik im Einkompartiment-Modell: reine Formeln, keine Abhängigkeiten.

Einheiten: Dosis in mg, Volumen in L, Zeit in h, Konzentration in mg/L,
ke und ka in 1/h, Clearance in L/h. Die Kurven-Werkzeuge und der Rechner benutzen
dieselben Funktionen — so stimmen Bild und Zahl überein (wie `ph_plots.exact_ph`
und `ph_calc`).
"""

from __future__ import annotations

import math

LN2 = math.log(2)


def _positiv(**werte: float) -> None:
    for name, wert in werte.items():
        if not wert > 0:
            raise ValueError(f"{name} muss größer als 0 sein (bekommen: {wert}).")


def half_life(ke: float) -> float:
    _positiv(ke=ke)
    return LN2 / ke


def ke_from_half_life(t_half: float) -> float:
    _positiv(t_half=t_half)
    return LN2 / t_half


def resolve(
    vd: float | None = None,
    ke: float | None = None,
    t_half: float | None = None,
    cl: float | None = None,
    tol: float = 0.02,
) -> dict[str, float]:
    """Aus den gegebenen Größen die übrigen ableiten (Vd, ke, t½, CL).

    Gebraucht werden Vd plus eine der Größen ke / t½ / CL, oder CL plus ke / t½.
    Sind mehr Größen gegeben als nötig und sie passen nicht zusammen, wird das benannt
    statt stillschweigend eine zu wählen.
    """
    if ke is None and t_half is not None:
        ke = ke_from_half_life(t_half)
    if ke is None and cl is not None and vd is not None:
        ke = cl / vd
    if vd is None and cl is not None and ke is not None:
        vd = cl / ke
    if ke is None or vd is None:
        raise ValueError(
            "Zu wenig Angaben: gebraucht werden das Verteilungsvolumen Vd und eine der Größen "
            "Eliminationskonstante ke, Halbwertszeit oder Clearance (oder Clearance plus ke/Halbwertszeit)."
        )
    _positiv(vd=vd, ke=ke)
    ableitung = ke * vd
    if cl is not None:
        _positiv(cl=cl)
        if abs(cl - ableitung) > tol * max(cl, ableitung):
            raise ValueError(
                f"Die Angaben widersprechen sich: ke × Vd = {ableitung:.4g} L/h, "
                f"gegeben wurde aber eine Clearance von {cl:.4g} L/h."
            )
    else:
        cl = ableitung
    if t_half is not None and abs(t_half - LN2 / ke) > tol * t_half:
        raise ValueError(
            f"Die Angaben widersprechen sich: ke = {ke:.4g}/h entspricht t½ = {LN2 / ke:.4g} h, "
            f"gegeben wurde t½ = {t_half:.4g} h."
        )
    return {"vd": vd, "ke": ke, "t_half": LN2 / ke, "cl": cl}


def c_iv(dose: float, vd: float, ke: float, t: float) -> float:
    """i.v.-Bolus: C(t) = D/Vd · e^(−ke·t)."""
    _positiv(dose=dose, vd=vd, ke=ke)
    if t < 0:
        raise ValueError("Die Zeit t darf nicht negativ sein.")
    return dose / vd * math.exp(-ke * t)


def c_oral(dose: float, f: float, vd: float, ke: float, ka: float, t: float) -> float:
    """Orale Gabe, Resorption und Elimination erster Ordnung.

    C(t) = F·D·ka / (Vd·(ka−ke)) · (e^(−ke·t) − e^(−ka·t)); bei ka = ke gilt der
    Grenzwert F·D·ka·t·e^(−ke·t)/Vd (Flip-Flop-Grenzfall), damit die Kurve stetig bleibt.
    """
    _positiv(dose=dose, f=f, vd=vd, ke=ke, ka=ka)
    if t < 0:
        raise ValueError("Die Zeit t darf nicht negativ sein.")
    if abs(ka - ke) < 1e-9 * max(ka, ke):
        return f * dose * ka * t * math.exp(-ke * t) / vd
    return f * dose * ka / (vd * (ka - ke)) * (math.exp(-ke * t) - math.exp(-ka * t))


def tmax(ka: float, ke: float) -> float:
    """Zeit des Konzentrationsmaximums nach oraler Gabe: ln(ka/ke)/(ka−ke)."""
    _positiv(ka=ka, ke=ke)
    if abs(ka - ke) < 1e-9 * max(ka, ke):
        return 1 / ke
    return math.log(ka / ke) / (ka - ke)


def cmax(dose: float, f: float, vd: float, ke: float, ka: float) -> float:
    return c_oral(dose, f, vd, ke, ka, tmax(ka, ke))


def auc_inf(dose: float, f: float, cl: float) -> float:
    """AUC von 0 bis ∞: F·D/CL."""
    _positiv(dose=dose, f=f, cl=cl)
    return f * dose / cl


def accumulation(ke: float, tau: float) -> float:
    """Akkumulationsfaktor bei Gabe alle τ Stunden: 1/(1−e^(−ke·τ))."""
    _positiv(ke=ke, tau=tau)
    return 1 / (1 - math.exp(-ke * tau))


def css_avg(dose: float, f: float, cl: float, tau: float) -> float:
    """Mittlere Steady-State-Konzentration: F·D/(CL·τ)."""
    _positiv(dose=dose, f=f, cl=cl, tau=tau)
    return f * dose / (cl * tau)


def css_max_iv(dose: float, vd: float, ke: float, tau: float) -> float:
    """Spitze im Steady State bei i.v.-Bolus alle τ: D/Vd · R."""
    return dose / vd * accumulation(ke, tau)


def css_min_iv(dose: float, vd: float, ke: float, tau: float) -> float:
    """Tal im Steady State bei i.v.-Bolus alle τ: Spitze · e^(−ke·τ)."""
    return css_max_iv(dose, vd, ke, tau) * math.exp(-ke * tau)


def time_to_fraction_ss(ke: float, fraction: float = 0.9) -> float:
    """Zeit bis zu einem Anteil des Steady State: −ln(1−Anteil)/ke."""
    _positiv(ke=ke)
    if not 0 < fraction < 1:
        raise ValueError("Der Anteil muss zwischen 0 und 1 liegen (z. B. 0,9 für 90 %).")
    return -math.log(1 - fraction) / ke


def loading_dose(target: float, vd: float, f: float = 1.0) -> float:
    """Aufsättigungsdosis: Zielkonzentration · Vd / F."""
    _positiv(target=target, vd=vd, f=f)
    return target * vd / f


def maintenance_rate(target: float, cl: float, f: float = 1.0) -> float:
    """Erhaltungsdosisrate in mg/h: Zielkonzentration · CL / F."""
    _positiv(target=target, cl=cl, f=f)
    return target * cl / f
