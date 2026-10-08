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


def _p(x: float) -> str:
    """Zahl, wie man sie in den TI tippt: Dezimalpunkt, kein Komma."""
    return f"{x:g}"


ANS = "[2nd] [(−)]"  # Ans: das letzte Ergebnis, ungerundet
E_HOCH = "[2nd] [ln]"  # e^(
VZ_MINUS = "[(−)] ist das Vorzeichen-Minus — die [−]-Taste gibt an dieser Stelle einen Syntaxfehler."


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
                    f"ke = {de(ke, 4)} 1/h", "Anteil des Körperbestands, der pro Stunde eliminiert wird.",
                    [f"{_p(cl)} ÷ {_p(vd)} [enter] → {de(ke, 4)}"]),
            schritt("Halbwertszeit", "t½ = ln 2 / ke", f"t½ = 0,693 / {de(ke, 4)} 1/h", f"t½ = {de(t_half, 2)} h",
                    "Gleiche Clearance, doppeltes Vd → doppelte Halbwertszeit.",
                    [f"[ln] 2 [)] ÷ {ANS} [enter] → {de(t_half, 2)}",
                     f"{ANS} setzt Ans ein, das letzte Ergebnis — der TI rechnet so ungerundet weiter."]),
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
            *_iv_schritte(dose, vd, t_half, t, c0, ke, c),
            ],
    }


def _iv_schritte(dose, vd, t_half, t, c0, ke, c) -> list[dict]:
    """C₀ → ke → C(t) nach i.v.-Bolus; gemeinsam für Konzentration und Tangente."""
    return [
        schritt("Anfangskonzentration", "C₀ = D / Vd", f"C₀ = {_g(dose)} mg / {_g(vd)} L", f"C₀ = {de(c0, 3)} mg/L", "",
                [f"{_p(dose)} ÷ {_p(vd)} [enter] → {de(c0, 3)}"]),
        schritt("Eliminationskonstante", "ke = ln 2 / t½", f"ke = 0,693 / {_g(t_half)} h", f"ke = {de(ke, 4)} 1/h", "",
                [f"[ln] 2 [)] ÷ {_p(t_half)} [enter] → {de(ke, 4)}"]),
        schritt("Konzentration zur Zeit t", "C(t) = C₀ · e^(−ke·t)",
                f"C = {de(c0, 3)} mg/L · e^(−{de(ke, 4)} · {_g(t)})", f"C = {de(c, 3)} mg/L",
                f"{_g(t)} h sind {de(t / t_half, 2)} Halbwertszeiten — so oft wurde halbiert.",
                [f"{_p(dose)} ÷ {_p(vd)} × {E_HOCH} [(−)] {ANS} × {_p(t)} [)] [enter] → {de(c, 3)}",
                 f"{E_HOCH} öffnet e^(, {ANS} ist das ke von eben. {VZ_MINUS}"]),
    ]


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
                    "Nur der resorbierte Anteil erreicht den Kreislauf.",
                    [f"{_p(f)} × {_p(dose)} [enter] → {de(f * dose, 1)}"]),
            schritt("Mittlere Konzentration", "Css,av = F · D / (CL · τ)",
                    f"Css,av = {de(f * dose, 1)} mg / ({_g(cl)} L/h · {_g(tau)} h)", f"Css,av = {de(css, 3)} mg/L",
                    "Im Steady State wird pro Intervall genau so viel eliminiert wie aufgenommen.",
                    [f"{ANS} ÷ ( {_p(cl)} × {_p(tau)} ) [enter] → {de(css, 3)}",
                     "Die Klammer um CL · τ ist Pflicht — ohne sie teilt der TI nur durch CL und multipliziert mit τ."]),
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
                    f"A = {de(target * vd, 1)} mg", "", [f"{_p(target)} × {_p(vd)} [enter] → {de(target * vd, 1)}"]),
            schritt("Dosis", "LD = Css · Vd / F", f"LD = {de(target * vd, 1)} mg / {_g(f)}", f"LD = {de(ld, 1)} mg",
                    "Die Aufsättigungsdosis hängt vom Verteilungsvolumen ab, nicht von der Clearance.",
                    [f"{ANS} ÷ {_p(f)} [enter] → {de(ld, 1)}"]),
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
            schritt("Eliminationskonstante", "ke = ln 2 / t½", f"ke = 0,693 / {_g(t_half)} h", f"ke = {de(ke, 4)} 1/h", "",
                    [f"[ln] 2 [)] ÷ {_p(t_half)} [enter] → {de(ke, 4)}"]),
            schritt("Akkumulationsfaktor", "R = 1 / (1 − e^(−ke·τ))", f"R = 1 / (1 − e^(−{de(ke, 4)} · {_g(tau)}))",
                    f"R = {de(r, 3)}",
                    "Je kürzer das Intervall im Vergleich zur Halbwertszeit, desto mehr akkumuliert der Wirkstoff.",
                    [f"1 ÷ ( 1 − {E_HOCH} [(−)] {ANS} × {_p(tau)} [)] ) [enter] → {de(r, 3)}",
                     f"{E_HOCH} öffnet e^(. {VZ_MINUS}"]),
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
        tasten = f"[2nd] [log] {_p(ph)} − {_p(pka)} [)] [enter]"
        geladen_name = "A⁻"
    else:
        text = (
            f"Eine schwache Base hat einen pKs von {_g(pka)} (der konjugierten Säure). "
            f"Wie viel Prozent liegen {wo} ungeladen vor?"
        )
        formel, einsatz = "[BH⁺]/[B] = 10^(pKs − pH)", f"10^({_g(pka)} − {_g(ph)})"
        tasten = f"[2nd] [log] {_p(pka)} − {_p(ph)} [)] [enter]"
        geladen_name = "BH⁺"
    ratio = r["ratio_ionised_to_unionised"]
    return {
        "typ": "ionisation", "stoff": "schwache Säure" if art == "acid" else "schwache Base", "text": nbsp(text),
        "gesucht": "Ungeladener Anteil", "einheit": "%", "loesung": ungeladen, "toleranz": _toleranz(ungeladen, 0.1),
        "werte": {"pka": pka, "ph": ph, "art": art},
        "rechenweg": [
            schritt("Verhältnis geladen : ungeladen", formel, f"{geladen_name} : ungeladen = {einsatz}", f"= {de(ratio, 3)}",
                    "Bei pH = pKs ist genau die Hälfte geladen.",
                    [f"{tasten} → {de(ratio, 3)}", "[2nd] [log] öffnet 10^(."]),
            schritt("Ungeladener Anteil", "ungeladen = 1 / (1 + Verhältnis)", f"1 / (1 + {de(ratio, 3)})",
                    f"{de(ungeladen, 2)} %",
                    "Nur die ungeladene Form passiert Membranen gut — daher die Resorption im Magen oder im Darm.",
                    [f"1 ÷ ( 1 + {ANS} ) × 100 [enter] → {de(ungeladen, 2)}"]),
        ],
    }


def tangente_aufgabe(seed: int) -> dict:
    """Biopharmazie: Steigung der Konzentrations-Zeit-Kurve — auf dem TI per Tangente( im Graphen."""
    rng = random.Random(f"pk-tangente-{seed}")
    while True:
        dose = rng.choice((100, 250, 500, 1000))
        vd = rng.choice((35, 50, 70, 100))
        t_half = rng.choice((2, 3, 4, 6, 8, 12))
        t = rng.choice((1, 2, 3, 4, 6, 8, 12))
        ke = pk.ke_from_half_life(t_half)
        c = pk.c_iv(dose, vd, ke, t)
        m = -ke * c
        if t <= 3 * t_half and abs(m) >= 0.01:
            break
    c0 = dose / vd
    b = c - m * t  # Achsenabschnitt der Tangente, wie der TI ihn anzeigt
    xmax = 2 * max(t, t_half)
    ymax = round(c0 * 1.2 + 0.5)
    text = (
        f"Wirkstoff X wird als i.v.-Bolus gegeben: {_g(dose)} mg, Verteilungsvolumen {_g(vd)} L, "
        f"Halbwertszeit {_g(t_half)} h (fiktive Werte). Wie schnell ändert sich die Plasmakonzentration "
        f"{_g(t)} h nach der Gabe? Gesucht ist die Steigung der Tangente an C(t) bei t = {_g(t)} h."
    )
    return {
        "typ": "tangente", "stoff": "Wirkstoff X", "text": nbsp(text), "gesucht": f"Steigung dC/dt bei {_g(t)} h",
        "einheit": "mg/(L·h)", "loesung": m, "toleranz": _toleranz(m, 0.0005),
        "werte": {"dose": dose, "vd": vd, "t_half": t_half, "t": t},
        "rechenweg": [
            *_iv_schritte(dose, vd, t_half, t, c0, ke, c),
            schritt("Steigung der Tangente", "dC/dt = −ke · C(t)",
                    f"dC/dt = −{de(ke, 4)} 1/h · {de(c, 3)} mg/L", f"dC/dt = {de(m, 4)} mg/(L·h)",
                    "Die Ableitung von C₀ · e^(−ke·t) ist −ke · C(t): Je mehr Wirkstoff da ist, desto schneller "
                    "fällt die Konzentration (Kinetik 1. Ordnung). Das Minus heißt: Sie nimmt ab.",
                    [f"[y=], bei Y1 tippen: {_p(dose)} ÷ {_p(vd)} × {E_HOCH} [(−)] [ln] 2 [)] ÷ {_p(t_half)} "
                     f"× [x,t,θ,n] [)] [enter]",
                     f"[window]: Xmin=0 · Xmax={_p(xmax)} · Ymin=0 · Ymax={_p(ymax)}",
                     "[graph] → die Abklingkurve erscheint",
                     "[2nd] [prgm] (ZEICHNEN, englisch DRAW) → 5:Tangente( wählen",
                     f"{_p(t)} [enter] → Tangente erscheint, unten steht y = m·x + b "
                     f"mit m = {de(m, 4)} und b = {de(b, 3)}",
                     "m ist die gesuchte Steigung. Weniger Nachkommastellen: [mode] → FIX 4 statt FLOAT.",
                     f"Gegenprobe ohne Zeichnen: [2nd] [trace] (CALC) → 6:dy/dx, {_p(t)} [enter] → dy/dx = {de(m, 4)}",
                     "Tangente wieder löschen: [2nd] [prgm] → 1:LöBild (ClrDraw)"]),
        ],
    }


_BAUER = (
    halbwertszeit_aufgabe, konzentration_aufgabe, steady_state_aufgabe,
    aufsaettigung_aufgabe, akkumulation_aufgabe, ionisation_aufgabe, tangente_aufgabe,
)


def neue_aufgabe(seed: int) -> dict:
    return random.Random(f"pk-typ-{seed}").choice(_BAUER)(seed)
