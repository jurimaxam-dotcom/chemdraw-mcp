"""Übungsaufgaben zu pH und Puffern, frisch erzeugt.

Gefragt wird, was Klausur und Antestat fragen: die Näherungsformel
(½ · (pKs − log c), Henderson-Hasselbalch). Damit eine Aufgabe nichts Falsches
einübt, zieht der Generator nur Fälle, in denen die Näherung höchstens 0,05
pH-Einheiten von der exakten Ladungsbilanz (`ph_core.exact_ph`) abweicht.

Nur Standardbibliothek + ph_core — läuft per Pyodide im Browser.
pKs-Werte: Lehrbuchwerte bei 25 °C.
"""

from __future__ import annotations

import math
import random

from chemdraw_tool.ph_core import exact_ph

from .basis import de, nbsp, pruefe, schritt  # noqa: F401 — pruefe ist Modul-API

PKW = 14.0
MAX_VERSUCHE = 200
GRENZE = 0.05  # erlaubte Abweichung Näherung ↔ exakt

# (Name, pKs)
SAEUREN = (
    ("Essigsäure", 4.76),
    ("Ameisensäure", 3.75),
    ("Benzoesäure", 4.20),
    ("Milchsäure", 3.86),
    ("Ammoniumchlorid (NH₄⁺)", 9.25),
)
# (Name, pKb)
BASEN = (
    ("Ammoniak", 4.75),
    ("Methylamin", 3.36),
    ("Natriumacetat (CH₃COO⁻)", 9.24),
    ("Natriumbenzoat", 9.80),
)
STARK = (
    ("Salzsäure", True),
    ("Salpetersäure", True),
    ("Natronlauge", False),
    ("Kalilauge", False),
)
# (Säure, Base, pKs)
PUFFER = (
    ("Essigsäure", "Natriumacetat", 4.76),
    ("Ameisensäure", "Natriumformiat", 3.75),
    ("Natriumdihydrogenphosphat", "Dinatriumhydrogenphosphat", 7.21),
    ("Ammoniumchlorid", "Ammoniak", 9.25),
)
KONZENTRATIONEN = (0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1.0)


def _c(c: float) -> str:
    return f"{c:g}".replace(".", ",")


def _ph(x: float) -> str:
    return de(x, 2)


def saeure_aufgabe(seed: int) -> dict:
    rng = random.Random(f"saeure-{seed}")
    for _ in range(MAX_VERSUCHE):
        name, pks = rng.choice(SAEUREN)
        c = rng.choice(KONZENTRATIONEN)
        naeherung = 0.5 * (pks - math.log10(c))
        if abs(naeherung - exact_ph([pks], c_acid=c, c_na=0.0)) <= GRENZE:
            break
    text = f"Berechne den pH-Wert einer {_c(c)} M {name}-Lösung (pKs = {de(pks, 2)})."
    return {
        "typ": "saeure",
        "stoff": name,
        "text": nbsp(text),
        "gesucht": "pH-Wert",
        "einheit": "pH",
        "loesung": naeherung,
        "toleranz": 0.02,
        "werte": {"c": c, "pks": pks},
        "rechenweg": [
            schritt(
                "pH einer schwachen Säure",
                "pH = ½ · (pKs − log c)",
                f"pH = ½ · ({de(pks, 2)} − log {_c(c)})",
                f"pH = {_ph(naeherung)}",
                "Näherung für schwache Säuren: kaum dissoziiert, Wasser trägt nichts bei. "
                "Hier hält sie — die exakte Rechnung weicht um höchstens 0,05 ab.",
            )
        ],
    }


def base_aufgabe(seed: int) -> dict:
    rng = random.Random(f"base-{seed}")
    for _ in range(MAX_VERSUCHE):
        name, pkb = rng.choice(BASEN)
        c = rng.choice(KONZENTRATIONEN)
        poh = 0.5 * (pkb - math.log10(c))
        naeherung = PKW - poh
        exakt = exact_ph([PKW - pkb], c_acid=c, c_na=c)
        if abs(naeherung - exakt) <= GRENZE:
            break
    text = f"Berechne den pH-Wert einer {_c(c)} M {name}-Lösung (pKb = {de(pkb, 2)})."
    return {
        "typ": "base",
        "stoff": name,
        "text": nbsp(text),
        "gesucht": "pH-Wert",
        "einheit": "pH",
        "loesung": naeherung,
        "toleranz": 0.02,
        "werte": {"c": c, "pkb": pkb},
        "rechenweg": [
            schritt(
                "pOH einer schwachen Base",
                "pOH = ½ · (pKb − log c)",
                f"pOH = ½ · ({de(pkb, 2)} − log {_c(c)})",
                f"pOH = {_ph(poh)}",
            ),
            schritt("pH aus pOH", "pH = 14 − pOH", f"pH = 14 − {_ph(poh)}", f"pH = {_ph(naeherung)}"),
        ],
    }


def stark_aufgabe(seed: int) -> dict:
    rng = random.Random(f"stark-{seed}")
    name, saeure = rng.choice(STARK)
    c = rng.choice((0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001))
    if saeure:
        loesung = -math.log10(c)
        weg = [schritt("Starke Säure", "pH = −log c(H₃O⁺)", f"pH = −log {_c(c)}", f"pH = {_ph(loesung)}",
                       "Starke Säuren protolysieren vollständig: c(H₃O⁺) = c(Säure).")]
    else:
        poh = -math.log10(c)
        loesung = PKW - poh
        weg = [
            schritt("Starke Base", "pOH = −log c(OH⁻)", f"pOH = −log {_c(c)}", f"pOH = {_ph(poh)}",
                    "Starke Basen dissoziieren vollständig: c(OH⁻) = c(Base)."),
            schritt("pH aus pOH", "pH = 14 − pOH", f"pH = 14 − {_ph(poh)}", f"pH = {_ph(loesung)}"),
        ]
    return {
        "typ": "stark",
        "stoff": name,
        "text": nbsp(f"Berechne den pH-Wert einer {_c(c)} M {name}."),
        "gesucht": "pH-Wert",
        "einheit": "pH",
        "loesung": loesung,
        "toleranz": 0.02,
        "werte": {"c": c, "saeure": saeure},
        "rechenweg": weg,
    }


def puffer_aufgabe(seed: int) -> dict:
    rng = random.Random(f"puffer-{seed}")
    stufen = (0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.25, 0.3)
    for _ in range(MAX_VERSUCHE):
        s_name, b_name, pks = rng.choice(PUFFER)
        cs, cb = rng.choice(stufen), rng.choice(stufen)
        hh = pks + math.log10(cb / cs)
        exakt = exact_ph([pks], c_acid=cs + cb, c_na=cb)
        if abs(hh - pks) <= 1.0 and abs(hh - exakt) <= GRENZE:
            break
    text = (
        f"Ein Puffer enthält {_c(cs)} mol/L {s_name} und {_c(cb)} mol/L {b_name} "
        f"(pKs = {de(pks, 2)}). Berechne den pH-Wert."
    )
    return {
        "typ": "puffer",
        "stoff": f"{s_name} / {b_name}",
        "text": nbsp(text),
        "gesucht": "pH-Wert",
        "einheit": "pH",
        "loesung": hh,
        "toleranz": 0.02,
        "werte": {"c_saeure": cs, "c_base": cb, "pks": pks},
        "rechenweg": [
            schritt(
                "Henderson-Hasselbalch",
                "pH = pKs + log(c(Base) / c(Säure))",
                f"pH = {de(pks, 2)} + log({_c(cb)} / {_c(cs)})",
                f"pH = {_ph(hh)}",
                "Gilt im Pufferbereich pKs ± 1, solange beide Partner deutlich konzentrierter "
                "sind als H₃O⁺ und OH⁻.",
            )
        ],
    }


def verhaeltnis_aufgabe(seed: int) -> dict:
    rng = random.Random(f"verh-{seed}")
    s_name, b_name, pks = rng.choice(PUFFER)
    ziel = round(pks + rng.choice((-0.8, -0.6, -0.5, -0.4, -0.3, -0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8)), 1)
    verhaeltnis = 10 ** (ziel - pks)
    text = (
        f"Du willst einen Puffer aus {s_name} und {b_name} (pKs = {de(pks, 2)}) mit "
        f"pH {de(ziel, 1)} ansetzen. In welchem Stoffmengenverhältnis "
        f"n({b_name}) : n({s_name}) mischst du?"
    )
    return {
        "typ": "verhaeltnis",
        "stoff": f"{s_name} / {b_name}",
        "text": nbsp(text),
        "gesucht": "Verhältnis Base : Säure",
        "einheit": ": 1",
        "loesung": verhaeltnis,
        "toleranz": max(0.01, verhaeltnis * 0.02),
        "werte": {"pks": pks, "ziel_ph": ziel},
        "rechenweg": [
            schritt(
                "Henderson-Hasselbalch umgestellt",
                "c(Base) / c(Säure) = 10^(pH − pKs)",
                f"Verhältnis = 10^({de(ziel, 1)} − {de(pks, 2)})",
                f"Verhältnis = {de(verhaeltnis, 2)} : 1",
                "Im selben Volumen ist das Konzentrationsverhältnis gleich dem Stoffmengenverhältnis.",
            )
        ],
    }


_BAUER = (saeure_aufgabe, base_aufgabe, stark_aufgabe, puffer_aufgabe, verhaeltnis_aufgabe)


def neue_aufgabe(seed: int) -> dict:
    """Mischt die fünf Typen; gleicher Seed, gleiche Aufgabe."""
    return random.Random(f"ph-typ-{seed}").choice(_BAUER)(seed)
