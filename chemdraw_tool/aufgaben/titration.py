"""Übungsaufgaben zur Gehaltsbestimmung per Titration, frisch erzeugt.

Für den Praktikumsrechner (Produkt, 02.10.2026): Der Rechenkern läuft per
Pyodide im Browser, deshalb nur Standardbibliothek — kein molmass, kein RDKit.
Die Molmassen stehen als Zahl in der Tabelle; die Tests rechnen sie gegen die
Summenformel nach.

Zahlen werden so gezogen, wie sie im Praktikum vorkommen: Verbrauch 5–25 mL
(Bürette), abgelesen auf 0,05 mL, Einwaage auf 0,1 mg, Titer 0,97–1,03, Gehalt
96–103 %. Gezogen wird, bis die Bedingungen halten (höchstens MAX_VERSUCHE Mal,
Muster aus Numbas' `maxRuns`). Die Lösung wird aus den GERUNDETEN Angaben
berechnet, damit sie zu dem passt, was auf dem Blatt steht.

Rechenweg-Schema wie in `solution.py` und `calculator/`:
{label, formula, substitution, result, explanation}.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .basis import de as _de
from .basis import nbsp as _nbsp
from .basis import pruefe  # noqa: F401 — Teil der Modul-API (Browser, Tests)
from .basis import schritt as _schritt

MAX_VERSUCHE = 200


@dataclass(frozen=True)
class Stoff:
    name: str
    formel: str  # Summenformel, Hydrate mit Punkt (molmass-Schreibweise)
    molmasse: float  # g/mol
    massloesung: str  # wie im Praktikum genannt
    c: float  # mol/L der Maßlösung
    z: int  # mol Maßlösung je mol Stoff
    methode: str

    @property
    def faktor(self) -> float:
        """mg Stoff je mL Maßlösung, auf 4 geltende Ziffern wie in Monographien."""
        f = self.molmasse * self.c / self.z
        return float(f"{f:.4g}")


STOFFE: tuple[Stoff, ...] = (
    Stoff("Ibuprofen", "C13H18O2", 206.28, "Natriumhydroxid-Lösung", 0.1, 1, "Alkalimetrie"),
    Stoff("Benzoesäure", "C7H6O2", 122.12, "Natriumhydroxid-Lösung", 0.1, 1, "Alkalimetrie"),
    Stoff("Salicylsäure", "C7H6O3", 138.12, "Natriumhydroxid-Lösung", 0.1, 1, "Alkalimetrie"),
    Stoff("Citronensäure", "C6H8O7", 192.12, "Natriumhydroxid-Lösung", 1.0, 3, "Alkalimetrie"),
    Stoff("Natriumhydrogencarbonat", "NaHCO3", 84.01, "Salzsäure", 1.0, 1, "Acidimetrie"),
    Stoff("Ascorbinsäure", "C6H8O6", 176.12, "Iod-Lösung", 0.05, 1, "Iodimetrie"),
    Stoff("Paracetamol", "C8H9NO2", 151.16, "Cer(IV)-sulfat-Lösung", 0.1, 2,
          "Cerimetrie nach saurer Hydrolyse zu 4-Aminophenol"),
    Stoff("Natriumchlorid", "NaCl", 58.44, "Silbernitrat-Lösung", 0.1, 1, "Argentometrie"),
    Stoff("Calciumgluconat", "C12H22CaO14.H2O", 448.39, "Natriumedetat-Lösung", 0.1, 1, "Komplexometrie"),
    Stoff("Lidocain", "C14H22N2O", 234.34, "Perchlorsäure", 0.1, 1, "Titration in wasserfreiem Medium"),
)



def _f_text(f: float) -> str:
    """Faktor mit 4 geltenden Ziffern: 20,63 · 8,806 · 84,01."""
    return _de(f, max(0, 4 - len(str(int(f)))))


def _c_text(c: float) -> str:
    return _de(c, 2 if c < 0.1 else 1)


def _faktor_schritt(s: Stoff) -> dict:
    return _schritt(
        "Titrationsäquivalent",
        "Ä = M · c / ν",
        f"Ä = {_de(s.molmasse, 2)} g/mol · {_c_text(s.c)} mol/L / {s.z}",
        f"Ä = {_f_text(s.faktor)} mg/mL",
        f"1 mL {_c_text(s.c)} M {s.massloesung} entspricht Ä mg {s.name}; "
        f"ν = {s.z} mol Maßlösung je mol {s.name} ({s.methode}).",
    )


def gehalt_aufgabe(seed: int) -> dict:
    """Gehalt in % aus Einwaage, Verbrauch, Titer und Blindwert."""
    rng = random.Random(f"gehalt-{seed}")
    s = rng.choice(STOFFE)
    for _ in range(MAX_VERSUCHE):
        w_wahr = rng.uniform(97.0, 102.0)
        v_ziel = rng.uniform(8.0, 20.0)
        titer = round(rng.uniform(0.975, 1.025), 4)
        v_blind = rng.choice([0.0, 0.0, 0.05, 0.10, 0.15])
        m_mg = round(s.faktor * titer * v_ziel / w_wahr * 100, 1)
        v_ml = round(round((v_ziel + v_blind) / 0.05) * 0.05, 2)
        gehalt = s.faktor * titer * (v_ml - v_blind) / m_mg * 100
        if 5.0 <= v_ml <= 25.0 and 96.0 <= gehalt <= 103.0:
            break
    else:  # pragma: no cover — bei diesen Spannen praktisch unerreichbar
        raise RuntimeError("keine plausible Aufgabe gefunden")

    blind_satz = (
        f" Der Blindwert beträgt {_de(v_blind, 2)} mL." if v_blind else " Ein Blindwert entfällt."
    )
    text = (
        f"Gehaltsbestimmung von {s.name} ({s.methode}): Einwaage {_de(m_mg, 1)} mg, "
        f"Verbrauch {_de(v_ml, 2)} mL {_c_text(s.c)} M {s.massloesung} "
        f"(Faktor f = {_de(titer, 4)}).{blind_satz} "
        f"1 mL {_c_text(s.c)} M {s.massloesung} entspricht {_f_text(s.faktor)} mg "
        f"{s.name}. Berechne den Gehalt in Prozent."
    )
    rechenweg = [
        _faktor_schritt(s),
        _schritt(
            "Korrigierter Verbrauch",
            "V_korr = (V − V_blind) · f",
            f"V_korr = ({_de(v_ml, 2)} − {_de(v_blind, 2)}) mL · {_de(titer, 4)}",
            f"V_korr = {_de((v_ml - v_blind) * titer, 4)} mL",
            "Der Faktor f rechnet die Ablesung auf eine Maßlösung exakt der Nennkonzentration um.",
        ),
        _schritt(
            "Gehalt",
            "w = Ä · V_korr / m · 100 %",
            f"w = {_f_text(s.faktor)} mg/mL · {_de((v_ml - v_blind) * titer, 4)} mL / {_de(m_mg, 1)} mg · 100 %",
            f"w = {_de(gehalt, 2)} %",
        ),
    ]
    return {
        "typ": "gehalt",
        "stoff": s.name,
        "text": _nbsp(text),
        "gesucht": "Gehalt",
        "einheit": "%",
        "loesung": gehalt,
        "toleranz": 0.05,
        "werte": {"m_mg": m_mg, "v_ml": v_ml, "v_blind_ml": v_blind, "faktor": s.faktor, "titer": titer},
        "rechenweg": rechenweg,
    }


def sollverbrauch_aufgabe(seed: int) -> dict:
    """Erwarteter Verbrauch bei 100 % Gehalt — die Frage aus dem Antestat."""
    rng = random.Random(f"soll-{seed}")
    s = rng.choice(STOFFE)
    for _ in range(MAX_VERSUCHE):
        titer = round(rng.uniform(0.975, 1.025), 4)
        m_mg = round(s.faktor * titer * rng.uniform(8.0, 20.0), 1)
        v_soll = m_mg / (s.faktor * titer)
        if 5.0 <= v_soll <= 25.0:
            break
    text = (
        f"Du wägst {_de(m_mg, 1)} mg {s.name} ein und titrierst mit {_c_text(s.c)} M "
        f"{s.massloesung} (Faktor f = {_de(titer, 4)}; {s.methode}). Wie viel mL erwartest du "
        f"bei einem Gehalt von 100,0 %?"
    )
    rechenweg = [
        _faktor_schritt(s),
        _schritt(
            "Sollverbrauch",
            "V_soll = m / (Ä · f)",
            f"V_soll = {_de(m_mg, 1)} mg / ({_f_text(s.faktor)} mg/mL · {_de(titer, 4)})",
            f"V_soll = {_de(v_soll, 2)} mL",
            "Aus w = Ä · f · V / m · 100 % mit w = 100 % nach V umgestellt.",
        ),
    ]
    return {
        "typ": "sollverbrauch",
        "stoff": s.name,
        "text": _nbsp(text),
        "gesucht": "Sollverbrauch",
        "einheit": "mL",
        "loesung": v_soll,
        "toleranz": 0.03,
        "werte": {"m_mg": m_mg, "faktor": s.faktor, "titer": titer},
        "rechenweg": rechenweg,
    }


def faktor_aufgabe(seed: int) -> dict:
    """Titrationsäquivalent (mg je mL) aus Molmasse, Konzentration und Stöchiometrie."""
    rng = random.Random(f"faktor-{seed}")
    s = rng.choice(STOFFE)
    f_exakt = s.molmasse * s.c / s.z
    text = (
        f"{s.name} (M = {_de(s.molmasse, 2)} g/mol) wird mit {_c_text(s.c)} M {s.massloesung} "
        f"bestimmt ({s.methode}); dabei reagiert 1 mol {s.name} mit {s.z} mol Maßlösung. "
        f"Wie viel mg {s.name} entspricht 1 mL Maßlösung?"
    )
    return {
        "typ": "faktor",
        "stoff": s.name,
        "text": _nbsp(text),
        "gesucht": "Titrationsäquivalent",
        "einheit": "mg/mL",
        "loesung": f_exakt,
        "toleranz": max(0.006, f_exakt * 0.0005),
        "werte": {"molmasse": s.molmasse, "c": s.c, "z": s.z},
        "rechenweg": [_faktor_schritt(s)],
    }


@dataclass(frozen=True)
class Urtiter:
    name: str
    formel: str
    molmasse: float
    massloesung: str
    c: float
    z: int  # mol Maßlösung je mol Urtitersubstanz


URTITER: tuple[Urtiter, ...] = (
    Urtiter("Kaliumhydrogenphthalat", "C8H5KO4", 204.22, "Natriumhydroxid-Lösung", 0.1, 1),
    Urtiter("Trometamol", "C4H11NO3", 121.14, "Salzsäure", 0.1, 1),
    Urtiter("Natriumcarbonat", "Na2CO3", 105.99, "Salzsäure", 0.1, 2),
    Urtiter("Natriumchlorid", "NaCl", 58.44, "Silbernitrat-Lösung", 0.1, 1),
    Urtiter("Zink", "Zn", 65.38, "Natriumedetat-Lösung", 0.1, 1),
)


def titer_aufgabe(seed: int) -> dict:
    """Faktor (Titer) einer Maßlösung aus einer Urtitersubstanz — Quanti, 2. Semester."""
    rng = random.Random(f"titer-{seed}")
    u = rng.choice(URTITER)
    for _ in range(MAX_VERSUCHE):
        f_wahr = rng.uniform(0.97, 1.03)
        v_ziel = rng.uniform(8.0, 24.0)
        m_mg = round(v_ziel * u.c * f_wahr * u.molmasse / u.z, 1)
        v_ml = round(round(v_ziel / 0.05) * 0.05, 2)
        titer = u.z * m_mg / (u.molmasse * u.c * v_ml)
        if 5.0 <= v_ml <= 25.0 and 0.95 <= titer <= 1.05 and m_mg >= 100.0:
            break
    n_u = m_mg / u.molmasse
    n_soll = u.c * v_ml
    text = (
        f"Zur Faktorbestimmung der {_c_text(u.c)} M {u.massloesung} wägst du {_de(m_mg, 1)} mg "
        f"{u.name} (M = {_de(u.molmasse, 2)} g/mol) ein und verbrauchst {_de(v_ml, 2)} mL. "
        f"1 mol {u.name} reagiert mit {u.z} mol Maßlösung. Berechne den Faktor."
    )
    rechenweg = [
        _schritt(
            "Stoffmenge Urtitersubstanz",
            "n(U) = m / M",
            f"n(U) = {_de(m_mg, 1)} mg / {_de(u.molmasse, 2)} g/mol",
            f"n(U) = {_de(n_u, 4)} mmol",
            "mg durch g/mol ergibt mmol.",
        ),
        _schritt(
            "Stoffmenge Maßlösung, nominal",
            "n(ML) = c · V",
            f"n(ML) = {_c_text(u.c)} mol/L · {_de(v_ml, 2)} mL",
            f"n(ML) = {_de(n_soll, 4)} mmol",
            "Was die Lösung enthielte, wenn sie exakt die Nennkonzentration hätte.",
        ),
        _schritt(
            "Faktor",
            "f = ν · n(U) / n(ML)",
            f"f = {u.z} · {_de(n_u, 4)} / {_de(n_soll, 4)}",
            f"f = {_de(titer, 4)}",
            "f > 1: die Lösung ist stärker als nominal. Ph. Eur. verlangt 0,9–1,1.",
        ),
    ]
    return {
        "typ": "titer",
        "stoff": u.name,
        "text": _nbsp(text),
        "gesucht": "Faktor f",
        "einheit": "",
        "loesung": titer,
        "toleranz": 0.0006,
        "werte": {"m_mg": m_mg, "v_ml": v_ml, "molmasse": u.molmasse, "c": u.c, "z": u.z},
        "rechenweg": rechenweg,
    }


_BAUER = (gehalt_aufgabe, sollverbrauch_aufgabe, faktor_aufgabe, titer_aufgabe)


def neue_aufgabe(seed: int) -> dict:
    """Mischt die vier Typen; gleicher Seed, gleiche Aufgabe."""
    return random.Random(f"typ-{seed}").choice(_BAUER)(seed)
