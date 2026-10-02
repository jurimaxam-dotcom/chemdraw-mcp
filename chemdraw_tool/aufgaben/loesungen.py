"""Übungsaufgaben zum Lösungsrechnen — Allgemeine Chemie im 1. Semester.

Einwaage (m = c · V · M), Verdünnung (c₁V₁ = c₂V₂), Mischungskreuz und die
Stoffmengenkonzentration konzentrierter Säuren aus Massenanteil und Dichte.
Die Molmasse steht in jeder Aufgabe; die Tests rechnen sie gegen die
Summenformel nach und jede Lösung gegen solution.py.

Nur Standardbibliothek — läuft per Pyodide im Browser.
"""

from __future__ import annotations

import random

from .basis import de, nbsp, pruefe, schritt  # noqa: F401 — pruefe ist Modul-API

# (Name, Summenformel für den Test, Molmasse g/mol)
EINWAAGE_STOFFE = (
    ("Natriumchlorid", "NaCl", 58.44),
    ("Natriumhydroxid", "NaOH", 40.00),
    ("Kaliumpermanganat", "KMnO4", 158.03),
    ("Kupfer(II)-sulfat-Pentahydrat", "CuSO4.5H2O", 249.69),
    ("Natriumthiosulfat-Pentahydrat", "Na2S2O3.5H2O", 248.18),
    ("Natriumedetat (Dinatriumsalz-Dihydrat)", "C10H14N2Na2O8.2H2O", 372.24),
    ("Kaliumhydrogenphthalat", "C8H5KO4", 204.22),
    ("Glucose", "C6H12O6", 180.16),
    ("Natriumcarbonat", "Na2CO3", 105.99),
    ("Silbernitrat", "AgNO3", 169.87),
)

# (Name, Massenanteil %, Dichte g/mL, Molmasse g/mol) — Handelsware, Lehrbuchwerte
KONZ_SAEUREN = (
    ("Salzsäure", 37.0, 1.19, 36.46),
    ("Schwefelsäure", 96.0, 1.84, 98.08),
    ("Salpetersäure", 65.0, 1.39, 63.01),
    ("Ammoniak-Lösung", 25.0, 0.91, 17.03),
    ("Essigsäure", 99.0, 1.05, 60.05),
)


def _g(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def einwaage_aufgabe(seed: int) -> dict:
    rng = random.Random(f"einwaage-{seed}")
    name, _formel, M = rng.choice(EINWAAGE_STOFFE)
    c = rng.choice((0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0))
    v_ml = rng.choice((50, 100, 250, 500, 1000))
    n = c * v_ml / 1000
    m = n * M
    text = (
        f"Du sollst {v_ml} mL einer {_g(c)} M {name}-Lösung ansetzen (M = {de(M, 2)} g/mol). "
        f"Wie viel g wägst du ein?"
    )
    return {
        "typ": "einwaage", "stoff": name, "text": nbsp(text), "gesucht": "Einwaage", "einheit": "g",
        "loesung": m, "toleranz": max(0.0005, m * 0.005),
        "werte": {"c": c, "v_ml": v_ml, "M": M},
        "rechenweg": [
            schritt("Stoffmenge", "n = c · V", f"n = {_g(c)} mol/L · {_g(v_ml / 1000)} L",
                    f"n = {de(n, 5)} mol", f"{v_ml} mL = {_g(v_ml / 1000)} L — erst in Liter umrechnen."),
            schritt("Masse", "m = n · M", f"m = {de(n, 5)} mol · {de(M, 2)} g/mol", f"m = {de(m, 4)} g",
                    "Bei Hydraten gehört das Kristallwasser zur Molmasse — es wird mit eingewogen."
                    if "hydrat" in name.lower() else ""),
        ],
    }


def verduennung_aufgabe(seed: int) -> dict:
    rng = random.Random(f"verd-{seed}")
    for _ in range(200):
        c1 = rng.choice((0.1, 0.5, 1.0, 2.0, 5.0))
        c2 = rng.choice((0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5))
        v2 = rng.choice((50, 100, 250, 500, 1000))
        v1 = c2 * v2 / c1
        if c1 > c2 and 0.5 <= v1 <= 250:
            break
    stoff = rng.choice(("Salzsäure", "Natronlauge", "Schwefelsäure", "Essigsäure"))
    text = (
        f"Aus einer {_g(c1)} M {stoff} sollen {v2} mL einer {_g(c2)} M Lösung werden. "
        f"Wie viel mL der Stammlösung brauchst du?"
    )
    return {
        "typ": "verduennung", "stoff": stoff, "text": nbsp(text), "gesucht": "Volumen Stammlösung",
        "einheit": "mL", "loesung": v1, "toleranz": max(0.02, v1 * 0.005),
        "werte": {"c1": c1, "c2": c2, "v2_ml": v2},
        "rechenweg": [
            schritt("Stoffmenge bleibt gleich", "c₁ · V₁ = c₂ · V₂", f"{_g(c1)} · V₁ = {_g(c2)} · {v2} mL", "",
                    "Beim Verdünnen kommt nur Lösungsmittel dazu."),
            schritt("Nach V₁ auflösen", "V₁ = c₂ · V₂ / c₁", f"V₁ = {_g(c2)} · {v2} mL / {_g(c1)}",
                    f"V₁ = {de(v1, 2)} mL", f"Mit Wasser auf {v2} mL auffüllen, nicht {de(v1, 2)} mL + {v2} mL."),
        ],
    }


def mischkreuz_aufgabe(seed: int) -> dict:
    rng = random.Random(f"misch-{seed}")
    for _ in range(200):
        hoch = rng.choice((96, 90, 70, 50, 40, 30))
        tief = rng.choice((0, 0, 5, 10, 20))
        ziel = rng.choice((10, 15, 20, 25, 35, 45, 60, 70))
        gesamt = rng.choice((100, 200, 250, 500, 1000))
        if tief < ziel < hoch:
            break
    teile_hoch, teile_tief = ziel - tief, hoch - ziel
    m_hoch = gesamt * teile_hoch / (teile_hoch + teile_tief)
    tief_text = "Wasser" if tief == 0 else f"Ethanol mit {tief} % (m/m)"
    text = (
        f"Du brauchst {gesamt} g Ethanol mit {ziel} % (m/m) und hast Ethanol mit {hoch} % (m/m) "
        f"und {tief_text}. Wie viel g des {hoch}%igen Ethanols setzt du ein?"
    )
    return {
        "typ": "mischkreuz", "stoff": "Ethanol", "text": nbsp(text), "gesucht": f"Masse {hoch} % (m/m)",
        "einheit": "g", "loesung": m_hoch, "toleranz": max(0.05, m_hoch * 0.005),
        "werte": {"hoch": hoch, "tief": tief, "ziel": ziel, "gesamt": gesamt},
        "rechenweg": [
            schritt("Mischungskreuz", "Teile = Differenzen über Kreuz",
                    f"{hoch} % → {ziel} − {tief} = {teile_hoch} Teile; {tief} % → {hoch} − {ziel} = {teile_tief} Teile",
                    f"{teile_hoch} : {teile_tief}",
                    "Gilt für Massenanteile; Volumenprozente von Ethanol mischen sich nicht additiv (Kontraktion)."),
            schritt("Auf die Menge hochrechnen", "m = Gesamt · Teile / Summe der Teile",
                    f"m = {gesamt} g · {teile_hoch} / {teile_hoch + teile_tief}", f"m = {de(m_hoch, 2)} g"),
        ],
    }


def konz_aufgabe(seed: int) -> dict:
    rng = random.Random(f"konz-{seed}")
    name, w, rho, M = rng.choice(KONZ_SAEUREN)
    c = w / 100 * rho * 1000 / M
    text = (
        f"Konzentrierte {name} hat einen Massenanteil von {_g(w)} % und die Dichte "
        f"{de(rho, 2)} g/mL (M = {de(M, 2)} g/mol). Berechne die Stoffmengenkonzentration in mol/L."
    )
    masse_l = rho * 1000
    return {
        "typ": "konz", "stoff": name, "text": nbsp(text), "gesucht": "Konzentration", "einheit": "mol/L",
        "loesung": c, "toleranz": max(0.02, c * 0.005),
        "werte": {"w": w, "rho": rho, "M": M},
        "rechenweg": [
            schritt("Masse von 1 L Lösung", "m(Lsg) = ρ · V", f"m = {de(rho, 2)} g/mL · 1000 mL", f"m = {_g(masse_l)} g"),
            schritt("Davon der Stoff", "m(Stoff) = w · m(Lsg)", f"m = {_g(w)} % · {_g(masse_l)} g",
                    f"m = {de(w / 100 * masse_l, 1)} g"),
            schritt("Stoffmenge pro Liter", "c = m(Stoff) / (M · 1 L)",
                    f"c = {de(w / 100 * masse_l, 1)} g / {de(M, 2)} g/mol", f"c = {de(c, 2)} mol/L"),
        ],
    }


_BAUER = (einwaage_aufgabe, verduennung_aufgabe, mischkreuz_aufgabe, konz_aufgabe)


def neue_aufgabe(seed: int) -> dict:
    return random.Random(f"loesung-typ-{seed}").choice(_BAUER)(seed)
