"""Übungsaufgaben zur Pharmakokinetik (Pharmakologie; Praktikumsrechner 03.10.2026).

Einkompartiment-Modell: Halbwertszeit aus Clearance und Vd, Konzentration nach i.v.-Gabe,
mittlere Steady-State-Konzentration, Aufsättigungsdosis, Akkumulationsfaktor und der
ungeladene Anteil eines Wirkstoffs bei gegebenem pH. Jede Lösung kommt aus
`chemdraw_tool.pk` bzw. `ph_calc.ionisation` — dieselben Formeln wie im Rechner.

Der Wirkstoff heißt „Wirkstoff X" und seine Werte sind Übungszahlen: so geht keine erfundene
Zahl als echte Wirkstoffdaten durch.

Nur Standardbibliothek — läuft per Pyodide im Browser.
"""

from __future__ import annotations

import random

from .. import pk
from .basis import de, nbsp, pruefe, schritt  # noqa: F401 — pruefe ist Modul-API


def _g(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _toleranz(wert: float, untergrenze: float) -> float:
    return max(untergrenze, abs(wert) * 0.005)


def halbwertszeit_aufgabe(seed: int) -> dict:
    rng = random.Random(f"pk-halbwertszeit-{seed}")
    while True:
        vd = rng.choice((35, 50, 70, 100, 140, 200))
        cl = rng.choice((3.5, 5, 7, 10, 14, 20, 35))
        t_half = pk.resolve(vd=vd, cl=cl)["t_half"]
        if 0.5 <= t_half <= 60:
            break
    ke = cl / vd
    text = (
        f"Wirkstoff X hat ein Verteilungsvolumen von {_g(vd)} L und eine Clearance von {_g(cl)} L/h "
        f"(fiktive Werte). Wie lang ist die Eliminationshalbwertszeit?"
    )
    return {
        "typ": "halbwertszeit", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": "Halbwertszeit",
        "einheit": "h", "loesung": t_half, "toleranz": _toleranz(t_half, 0.02),
        "werte": {"vd": vd, "cl": cl},
        "rechenweg": [
            schritt("Eliminationskonstante", "ke = CL / Vd", f"ke = {_g(cl)} L/h / {_g(vd)} L",
                    f"ke = {de(ke, 4)} 1/h", "Anteil des Körperbestands, der pro Stunde eliminiert wird."),
            schritt("Halbwertszeit", "t½ = ln 2 / ke", f"t½ = 0,693 / {de(ke, 4)} 1/h", f"t½ = {de(t_half, 2)} h",
                    "Gleiche Clearance, doppeltes Vd → doppelte Halbwertszeit."),
        ],
    }


def konzentration_aufgabe(seed: int) -> dict:
    rng = random.Random(f"pk-iv-{seed}")
    while True:
        dose = rng.choice((100, 250, 500, 1000))
        vd = rng.choice((35, 50, 70, 100))
        t_half = rng.choice((2, 3, 4, 6, 8, 12))
        t = rng.choice((1, 2, 3, 4, 6, 8, 12, 24))
        ke = pk.ke_from_half_life(t_half)
        c = pk.c_iv(dose, vd, ke, t)
        if c >= 0.05:
            break
    c0 = dose / vd
    text = (
        f"Wirkstoff X wird als i.v.-Bolus gegeben: {_g(dose)} mg, Verteilungsvolumen {_g(vd)} L, "
        f"Halbwertszeit {_g(t_half)} h (fiktive Werte). Wie hoch ist die Plasmakonzentration {_g(t)} h nach der Gabe?"
    )
    return {
        "typ": "iv_c", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": f"Konzentration nach {_g(t)} h",
        "einheit": "mg/L", "loesung": c, "toleranz": _toleranz(c, 0.005),
        "werte": {"dose": dose, "vd": vd, "t_half": t_half, "t": t},
        "rechenweg": [
            schritt("Anfangskonzentration", "C₀ = D / Vd", f"C₀ = {_g(dose)} mg / {_g(vd)} L", f"C₀ = {de(c0, 3)} mg/L"),
            schritt("Eliminationskonstante", "ke = ln 2 / t½", f"ke = 0,693 / {_g(t_half)} h", f"ke = {de(ke, 4)} 1/h"),
            schritt("Konzentration zur Zeit t", "C(t) = C₀ · e^(−ke·t)",
                    f"C = {de(c0, 3)} mg/L · e^(−{de(ke, 4)} · {_g(t)})", f"C = {de(c, 3)} mg/L",
                    f"{_g(t)} h sind {de(t / t_half, 2)} Halbwertszeiten — so oft wurde halbiert."),
        ],
    }


def steady_state_aufgabe(seed: int) -> dict:
    rng = random.Random(f"pk-css-{seed}")
    f = rng.choice((0.5, 0.7, 0.8, 0.9, 1.0))
    dose = rng.choice((100, 200, 250, 500))
    cl = rng.choice((5, 7.5, 10, 15, 20))
    tau = rng.choice((6, 8, 12, 24))
    css = pk.css_avg(dose, f, cl, tau)
    f_text = "vollständig resorbiert" if f == 1.0 else f"Bioverfügbarkeit F = {_g(f)}"
    text = (
        f"Wirkstoff X wird alle {_g(tau)} h oral gegeben: {_g(dose)} mg, {f_text}, "
        f"Clearance {_g(cl)} L/h (fiktive Werte). Wie hoch ist die mittlere Plasmakonzentration im Steady State?"
    )
    return {
        "typ": "css", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": "Css,av", "einheit": "mg/L",
        "loesung": css, "toleranz": _toleranz(css, 0.005),
        "werte": {"dose": dose, "f": f, "cl": cl, "tau": tau},
        "rechenweg": [
            schritt("Aufgenommene Menge pro Intervall", "F · D", f"{_g(f)} · {_g(dose)} mg", f"{de(f * dose, 1)} mg",
                    "Nur der resorbierte Anteil erreicht den Kreislauf."),
            schritt("Mittlere Konzentration", "Css,av = F · D / (CL · τ)",
                    f"Css,av = {de(f * dose, 1)} mg / ({_g(cl)} L/h · {_g(tau)} h)", f"Css,av = {de(css, 3)} mg/L",
                    "Im Steady State wird pro Intervall genau so viel eliminiert wie aufgenommen."),
        ],
    }


def aufsaettigung_aufgabe(seed: int) -> dict:
    rng = random.Random(f"pk-ld-{seed}")
    target = rng.choice((2, 4, 5, 10, 15))
    vd = rng.choice((35, 50, 70, 100, 140))
    f = rng.choice((1.0, 0.8, 0.7, 0.5))
    ld = pk.loading_dose(target, vd, f)
    weg = "i.v." if f == 1.0 else f"oral (F = {_g(f)})"
    text = (
        f"Für Wirkstoff X ({weg} gegeben, Verteilungsvolumen {_g(vd)} L; fiktive Werte) soll sofort eine "
        f"Plasmakonzentration von {_g(target)} mg/L erreicht werden. Wie groß ist die Aufsättigungsdosis?"
    )
    return {
        "typ": "aufsaettigung", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": "Aufsättigungsdosis",
        "einheit": "mg", "loesung": ld, "toleranz": _toleranz(ld, 0.5),
        "werte": {"target": target, "vd": vd, "f": f},
        "rechenweg": [
            schritt("Benötigte Menge im Körper", "A = Css · Vd", f"A = {_g(target)} mg/L · {_g(vd)} L",
                    f"A = {de(target * vd, 1)} mg"),
            schritt("Dosis", "LD = Css · Vd / F", f"LD = {de(target * vd, 1)} mg / {_g(f)}", f"LD = {de(ld, 1)} mg",
                    "Die Aufsättigungsdosis hängt vom Verteilungsvolumen ab, nicht von der Clearance."),
        ],
    }


def akkumulation_aufgabe(seed: int) -> dict:
    rng = random.Random(f"pk-r-{seed}")
    t_half = rng.choice((2, 3, 4, 6, 8, 12, 24, 36))
    tau = rng.choice((4, 6, 8, 12, 24))
    ke = pk.ke_from_half_life(t_half)
    r = pk.accumulation(ke, tau)
    text = (
        f"Wirkstoff X hat eine Halbwertszeit von {_g(t_half)} h und wird alle {_g(tau)} h gegeben "
        f"(fiktive Werte). Wie groß ist der Akkumulationsfaktor?"
    )
    return {
        "typ": "akkumulation", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": "Akkumulationsfaktor R",
        "einheit": "", "loesung": r, "toleranz": _toleranz(r, 0.005),
        "werte": {"t_half": t_half, "tau": tau},
        "rechenweg": [
            schritt("Eliminationskonstante", "ke = ln 2 / t½", f"ke = 0,693 / {_g(t_half)} h", f"ke = {de(ke, 4)} 1/h"),
            schritt("Akkumulationsfaktor", "R = 1 / (1 − e^(−ke·τ))", f"R = 1 / (1 − e^(−{de(ke, 4)} · {_g(tau)}))",
                    f"R = {de(r, 3)}",
                    "Je kürzer das Intervall im Vergleich zur Halbwertszeit, desto mehr akkumuliert der Wirkstoff."),
        ],
    }


def ionisation_aufgabe(seed: int) -> dict:
    from .. import ph_calc

    rng = random.Random(f"pk-ion-{seed}")
    while True:
        art = rng.choice(("acid", "base"))
        pka = rng.choice([x / 2 for x in range(6, 20)])  # 3,0 … 9,5
        ph = rng.choice((1.5, 2.0, 5.0, 6.5, 7.4, 8.0))
        r = ph_calc.ionisation(pka=pka, ph=ph, kind=art)
        ungeladen = r["fraction_unionised"] * 100
        if abs(pka - ph) <= 2.5 and 2 <= ungeladen <= 98:
            break
    wo = {1.5: "im Magen (pH 1,5)", 2.0: "im Magen (pH 2,0)", 5.0: "bei pH 5,0",
          6.5: "im Dünndarm (pH 6,5)", 7.4: "im Blut (pH 7,4)", 8.0: "bei pH 8,0"}[ph]
    if art == "acid":
        text = f"Eine schwache Säure hat einen pKs von {_g(pka)}. Wie viel Prozent liegen {wo} ungeladen vor?"
        formel, einsatz = "[A⁻]/[HA] = 10^(pH − pKs)", f"10^({_g(ph)} − {_g(pka)})"
        geladen_name = "A⁻"
    else:
        text = (
            f"Eine schwache Base hat einen pKs von {_g(pka)} (der konjugierten Säure). "
            f"Wie viel Prozent liegen {wo} ungeladen vor?"
        )
        formel, einsatz = "[BH⁺]/[B] = 10^(pKs − pH)", f"10^({_g(pka)} − {_g(ph)})"
        geladen_name = "BH⁺"
    ratio = r["ratio_ionised_to_unionised"]
    return {
        "typ": "ionisation", "stoff": "schwache Säure" if art == "acid" else "schwache Base", "text": nbsp(text),
        "gesucht": "Ungeladener Anteil", "einheit": "%", "loesung": ungeladen, "toleranz": _toleranz(ungeladen, 0.1),
        "werte": {"pka": pka, "ph": ph, "art": art},
        "rechenweg": [
            schritt("Verhältnis geladen : ungeladen", formel, f"{geladen_name} : ungeladen = {einsatz}", f"= {de(ratio, 3)}",
                    "Bei pH = pKs ist genau die Hälfte geladen."),
            schritt("Ungeladener Anteil", "ungeladen = 1 / (1 + Verhältnis)", f"1 / (1 + {de(ratio, 3)})",
                    f"{de(ungeladen, 2)} %",
                    "Nur die ungeladene Form passiert Membranen gut — daher die Resorption im Magen oder im Darm."),
        ],
    }


_BAUER = (
    halbwertszeit_aufgabe, konzentration_aufgabe, steady_state_aufgabe,
    aufsaettigung_aufgabe, akkumulation_aufgabe, ionisation_aufgabe,
)


def neue_aufgabe(seed: int) -> dict:
    return random.Random(f"pk-typ-{seed}").choice(_BAUER)(seed)
