"""Übungsaufgaben zum Löslichkeitsprodukt — Quali-Klausur im 1. Semester.

Der KL-Wert steht in jeder Aufgabe, die Lösung hängt also nur an der
Stöchiometrie des Salzes AₓBᵧ: KL = (x·L)ˣ · (y·L)ʸ. Tabellenwerte (25 °C,
Lehrbuch-Größenordnung) dienen nur als realistische Vorgabe.

Nur Standardbibliothek — läuft per Pyodide im Browser.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .basis import nbsp, pruefe, schritt  # noqa: F401 — pruefe ist Modul-API

MAX_VERSUCHE = 200


@dataclass(frozen=True)
class Salz:
    name: str
    formel: str
    x: int  # Kationen je Formeleinheit
    y: int  # Anionen je Formeleinheit
    kation: str
    anion: str
    kl: float
    zusatz_kation: str  # leicht lösliches Salz mit demselben Kation
    zusatz_anion: str  # leicht lösliches Salz mit demselben Anion


SALZE: tuple[Salz, ...] = (
    Salz("Silberchlorid", "AgCl", 1, 1, "Ag⁺", "Cl⁻", 1.8e-10, "Silbernitrat", "Natriumchlorid"),
    Salz("Silberbromid", "AgBr", 1, 1, "Ag⁺", "Br⁻", 5.0e-13, "Silbernitrat", "Kaliumbromid"),
    Salz("Bariumsulfat", "BaSO₄", 1, 1, "Ba²⁺", "SO₄²⁻", 1.1e-10, "Bariumchlorid", "Natriumsulfat"),
    Salz("Calciumcarbonat", "CaCO₃", 1, 1, "Ca²⁺", "CO₃²⁻", 3.4e-9, "Calciumchlorid", "Natriumcarbonat"),
    Salz("Calciumfluorid", "CaF₂", 1, 2, "Ca²⁺", "F⁻", 3.9e-11, "Calciumchlorid", "Natriumfluorid"),
    Salz("Bleiiodid", "PbI₂", 1, 2, "Pb²⁺", "I⁻", 9.8e-9, "Bleinitrat", "Kaliumiodid"),
    Salz("Magnesiumhydroxid", "Mg(OH)₂", 1, 2, "Mg²⁺", "OH⁻", 5.6e-12, "Magnesiumchlorid", "Natriumhydroxid"),
    Salz("Silberchromat", "Ag₂CrO₄", 2, 1, "Ag⁺", "CrO₄²⁻", 1.1e-12, "Silbernitrat", "Kaliumchromat"),
)

_HOCH = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def sci(x: float, stellen: int = 2) -> str:
    """1,8 · 10⁻¹⁰ — wie es auf dem Klausurbogen steht."""
    mantisse, exp = f"{x:.{stellen - 1}e}".split("e")
    return f"{mantisse.replace('.', ',')} · 10{str(int(exp)).translate(_HOCH)}"


def _einheit_kl(n: int) -> str:
    return f"mol{str(n).translate(_HOCH)}/L{str(n).translate(_HOCH)}"


def _vf(vorfaktor: int) -> str:
    """Vorfaktor nur schreiben, wenn er nicht 1 ist: "4 · L³", aber "L²"."""
    return "" if vorfaktor == 1 else f"{vorfaktor} · "


def _klammerform(s: Salz) -> str:
    """(2L)² · L für Ag₂CrO₄, L · (2L)² für CaF₂, L · L für AgCl."""
    def teil(anzahl: int) -> str:
        return "L" if anzahl == 1 else f"({anzahl}L){str(anzahl).translate(_HOCH)}"
    return f"{teil(s.x)} · {teil(s.y)}"


def _kl_ausdruck(s: Salz) -> str:
    teile = []
    for anzahl, ion in ((s.x, s.kation), (s.y, s.anion)):
        teile.append(f"c({ion})" + ("" if anzahl == 1 else str(anzahl).translate(_HOCH)))
    return "KL = " + " · ".join(teile)


def _bisektion(kl: float, x: int, y: int, c_kat: float = 0.0, c_an: float = 0.0) -> float:
    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if (x * mid + c_kat) ** x * (y * mid + c_an) ** y > kl:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def loeslichkeit_aufgabe(seed: int) -> dict:
    rng = random.Random(f"loesl-{seed}")
    s = rng.choice(SALZE)
    n = s.x + s.y
    vorfaktor = s.x**s.x * s.y**s.y
    loesung = (s.kl / vorfaktor) ** (1 / n)
    text = (
        f"Das Löslichkeitsprodukt von {s.name} ({s.formel}) beträgt KL = {sci(s.kl)} {_einheit_kl(n)}. "
        f"Berechne die Löslichkeit L in mol/L."
    )
    weg = [
        schritt(
            "Dissoziation",
            f"{s.formel} ⇌ {s.x if s.x > 1 else ''}{s.kation} + {s.y if s.y > 1 else ''}{s.anion}",
            f"c({s.kation}) = {s.x if s.x > 1 else ''}L, c({s.anion}) = {s.y if s.y > 1 else ''}L",
            f"{_kl_ausdruck(s)} = {_vf(vorfaktor)}L{str(n).translate(_HOCH)}",
            "Jede gelöste Formeleinheit liefert x Kationen und y Anionen.",
        ),
        schritt(
            "Nach L auflösen",
            f"L = (KL / {vorfaktor})^(1/{n})" if vorfaktor > 1 else f"L = KL^(1/{n})",
            f"L = ({sci(s.kl)} / {vorfaktor})^(1/{n})" if vorfaktor > 1 else f"L = ({sci(s.kl)})^(1/{n})",
            f"L = {sci(loesung, 3)} mol/L",
        ),
    ]
    return {
        "typ": "loeslichkeit", "stoff": s.name, "text": nbsp(text), "gesucht": "Löslichkeit L",
        "einheit": "mol/L", "loesung": loesung, "loesung_text": f"{sci(loesung, 3)} mol/L",
        "toleranz": loesung * 0.02,
        "werte": {"kl": s.kl, "x": s.x, "y": s.y}, "rechenweg": weg,
    }


def kl_aufgabe(seed: int) -> dict:
    rng = random.Random(f"kl-{seed}")
    s = rng.choice(SALZE)
    n = s.x + s.y
    vorfaktor = s.x**s.x * s.y**s.y
    L = float(f"{(s.kl / vorfaktor) ** (1 / n) * rng.uniform(0.9, 1.1):.2e}")
    loesung = vorfaktor * L**n
    text = (
        f"In einer gesättigten Lösung von {s.name} ({s.formel}) sind {sci(L, 3)} mol/L gelöst. "
        f"Berechne das Löslichkeitsprodukt KL."
    )
    weg = [
        schritt(
            "Ionenkonzentrationen",
            f"c({s.kation}) = {s.x if s.x > 1 else ''}L, c({s.anion}) = {s.y if s.y > 1 else ''}L",
            f"L = {sci(L, 3)} mol/L",
            f"{_kl_ausdruck(s)} = {_vf(vorfaktor)}L{str(n).translate(_HOCH)}",
        ),
        schritt(
            "Einsetzen",
            f"KL = {_klammerform(s)} = {_vf(vorfaktor)}L{str(n).translate(_HOCH)}",
            f"KL = {_vf(vorfaktor)}({sci(L, 3)}){str(n).translate(_HOCH)}",
            f"KL = {sci(loesung, 3)} {_einheit_kl(n)}",
            "Achtung: Der stöchiometrische Faktor steht in der Klammer mit und wird mit potenziert."
            if vorfaktor > 1 else "",
        ),
    ]
    return {
        "typ": "kl", "stoff": s.name, "text": nbsp(text), "gesucht": "Löslichkeitsprodukt KL",
        "einheit": _einheit_kl(n), "loesung": loesung, "loesung_text": f"{sci(loesung, 3)} {_einheit_kl(n)}",
        "toleranz": loesung * 0.02,
        "werte": {"L": L, "x": s.x, "y": s.y}, "rechenweg": weg,
    }


def zusatz_aufgabe(seed: int) -> dict:
    """Gleichioniger Zusatz: Löslichkeit sinkt — Näherung c(Zusatz) ≫ Beitrag des Salzes."""
    rng = random.Random(f"zusatz-{seed}")
    # CaCO₃ fehlt: Carbonat protolysiert (pKb ≈ 3,7), das reine KL-Modell läge
    # >10 % daneben. Halogenid-Überschuss bildet [AgX₂]⁻ bzw. [PbI₄]²⁻ — dort
    # nur verdünnte Zusätze (Zweitgutachten 02.10.2026).
    kandidaten = [x for x in SALZE if x.name != "Calciumcarbonat"]
    for _ in range(MAX_VERSUCHE):
        s = rng.choice(kandidaten)
        ueber_anion = rng.random() < 0.5
        komplex = ueber_anion and s.name in ("Silberchlorid", "Silberbromid", "Bleiiodid")
        c = rng.choice((0.01, 0.02) if komplex else (0.01, 0.02, 0.05, 0.1, 0.2))
        if ueber_anion:
            # Ein Na₂SO₄, NaF … liefert c Anionen je Formeleinheit (1 Anion pro Formel).
            loesung = (s.kl / c**s.y) ** (1 / s.x) / s.x
            exakt = _bisektion(s.kl, s.x, s.y, c_an=c)
        else:
            loesung = (s.kl / c**s.x) ** (1 / s.y) / s.y
            exakt = _bisektion(s.kl, s.x, s.y, c_kat=c)
        if abs(loesung - exakt) <= 0.01 * exakt:
            break
    zusatz = s.zusatz_anion if ueber_anion else s.zusatz_kation
    ion = s.anion if ueber_anion else s.kation
    n_fest, n_frei = (s.y, s.x) if ueber_anion else (s.x, s.y)
    text = (
        f"Wie viel {s.name} ({s.formel}, KL = {sci(s.kl)} {_einheit_kl(s.x + s.y)}) löst sich in einer {str(c).replace('.', ',')} M "
        f"{zusatz}-Lösung? Gib L in mol/L an."
    )
    weg = [
        schritt(
            "Gleichioniger Zusatz",
            f"c({ion}) ≈ c(Zusatz)",
            f"c({ion}) ≈ {str(c).replace('.', ',')} mol/L",
            f"{s.name} selbst trägt praktisch nichts bei, weil L ≪ c(Zusatz)",
            "Näherung geprüft: Im KL-Modell (ohne Protolyse, Komplexbildung und Aktivitäten) "
            "weicht die exakte Rechnung um weniger als 1 % ab.",
        ),
        schritt(
            "Nach L auflösen",
            _kl_ausdruck(s),
            f"{sci(s.kl)} = {'(' + str(n_frei) + 'L)' + str(n_frei).translate(_HOCH) if n_frei > 1 else 'L'} · "
            f"({str(c).replace('.', ',')}){str(n_fest).translate(_HOCH) if n_fest > 1 else ''}",
            f"L = {sci(loesung, 3)} mol/L",
            "Verglichen mit reinem Wasser ist die Löslichkeit deutlich kleiner — Prinzip von Le Chatelier.",
        ),
    ]
    werte = {"kl": s.kl, "x": s.x, "y": s.y}
    werte["c_an" if ueber_anion else "c_kat"] = c
    return {
        "typ": "zusatz", "stoff": s.name, "text": nbsp(text), "gesucht": "Löslichkeit L",
        "einheit": "mol/L", "loesung": loesung, "loesung_text": f"{sci(loesung, 3)} mol/L",
        "toleranz": loesung * 0.02, "werte": werte, "rechenweg": weg,
    }


_BAUER = (loeslichkeit_aufgabe, kl_aufgabe, zusatz_aufgabe)


def neue_aufgabe(seed: int) -> dict:
    return random.Random(f"loesl-typ-{seed}").choice(_BAUER)(seed)
