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
            raise ValueError(f"{name} must be greater than 0 (got {wert}).")


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
    # Erst prüfen, dann teilen: vd = 0 oder ke = 0 endete sonst in ZeroDivisionError.
    _positiv(**{k: v for k, v in (("vd", vd), ("ke", ke), ("t_half", t_half), ("cl", cl)) if v is not None})
    if ke is None and t_half is not None:
        ke = ke_from_half_life(t_half)
    if ke is None and cl is not None and vd is not None:
        ke = cl / vd
    if vd is None and cl is not None and ke is not None:
        vd = cl / ke
    if ke is None or vd is None:
        raise ValueError(
            "Not enough data: needs the volume of distribution Vd and one of elimination "
            "constant ke, half-life or clearance (or clearance plus ke/half-life)."
        )
    _positiv(vd=vd, ke=ke)
    ableitung = ke * vd
    if cl is not None:
        _positiv(cl=cl)
        if abs(cl - ableitung) > tol * max(cl, ableitung):
            raise ValueError(
                f"The values contradict each other: ke × Vd = {ableitung:.4g} L/h, "
                f"but the clearance given is {cl:.4g} L/h."
            )
    else:
        cl = ableitung
    if t_half is not None and abs(t_half - LN2 / ke) > tol * t_half:
        raise ValueError(
            f"The values contradict each other: ke = {ke:.4g}/h means t½ = {LN2 / ke:.4g} h, "
            f"but t½ = {t_half:.4g} h was given."
        )
    return {"vd": vd, "ke": ke, "t_half": LN2 / ke, "cl": cl}


def c_iv(dose: float, vd: float, ke: float, t: float) -> float:
    """i.v.-Bolus: C(t) = D/Vd · e^(−ke·t)."""
    _positiv(dose=dose, vd=vd, ke=ke)
    if t < 0:
        raise ValueError("The time t must not be negative.")
    return dose / vd * math.exp(-ke * t)


def c_oral(dose: float, f: float, vd: float, ke: float, ka: float, t: float) -> float:
    """Orale Gabe, Resorption und Elimination erster Ordnung.

    C(t) = F·D·ka / (Vd·(ka−ke)) · (e^(−ke·t) − e^(−ka·t)); bei ka = ke gilt der
    Grenzwert F·D·ka·t·e^(−ke·t)/Vd (Flip-Flop-Grenzfall), damit die Kurve stetig bleibt.
    """
    _positiv(dose=dose, f=f, vd=vd, ke=ke, ka=ka)
    if t < 0:
        raise ValueError("The time t must not be negative.")
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
        raise ValueError("The fraction must lie between 0 and 1 (e.g. 0.9 for 90 %).")
    return -math.log(1 - fraction) / ke


def loading_dose(target: float, vd: float, f: float = 1.0) -> float:
    """Aufsättigungsdosis: Zielkonzentration · Vd / F."""
    _positiv(target=target, vd=vd, f=f)
    return target * vd / f


def maintenance_rate(target: float, cl: float, f: float = 1.0) -> float:
    """Erhaltungsdosisrate in mg/h: Zielkonzentration · CL / F."""
    _positiv(target=target, cl=cl, f=f)
    return target * cl / f


def concentration_profile(
    dose: float,
    f: float,
    vd: float,
    ke: float,
    ka: float | None,
    times: list[float],
    tau: float | None = None,
    n_doses: int = 1,
) -> list[float]:
    """Konzentration zu den Zeiten `times`, bei Mehrfachgabe durch Überlagerung.

    Das Einkompartiment-Modell ist linear: jede Gabe trägt unabhängig bei, die Kurve
    ist die Summe der um τ verschobenen Einzelkurven. `ka=None` heißt i.v.-Bolus
    (dann gilt F = 1 für die Dosis, f wird ignoriert).
    """
    if n_doses < 1:
        raise ValueError("n_doses must be at least 1.")
    if n_doses > 1 and not tau:
        raise ValueError("Repeated doses need the dosing interval tau.")
    werte = []
    for t in times:
        summe = 0.0
        for k in range(n_doses):
            dt = t - k * (tau or 0.0)
            if dt < 0:
                continue
            summe += c_iv(dose, vd, ke, dt) if ka is None else c_oral(dose, f, vd, ke, ka, dt)
        werte.append(summe)
    return werte


def response(c: float, ec50: float, emax: float = 100.0, hill: float = 1.0) -> float:
    """Hill-Gleichung: E = Emax · c^n / (EC50^n + c^n)."""
    _positiv(ec50=ec50, emax=emax, hill=hill)
    if c < 0:
        raise ValueError("The concentration must not be negative.")
    if c == 0:
        return 0.0
    x = c**hill
    return emax * x / (ec50**hill + x)


def dose_ratio(antagonist: float, kb: float) -> float:
    """Dosisverhältnis eines kompetitiven Antagonisten: r = 1 + [B]/KB (Schild, Steigung 1).

    Die Agonisten-Kurve wandert parallel nach rechts, Emax bleibt: EC50' = r · EC50.
    """
    _positiv(kb=kb)
    if antagonist < 0:
        raise ValueError("The antagonist concentration must not be negative.")
    return 1 + antagonist / kb
