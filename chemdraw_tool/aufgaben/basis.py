"""Gemeinsames der Aufgabengeneratoren: Zahlformat, Rechenweg-Schritt, Prüfen.

Nur Standardbibliothek — läuft per Pyodide im Browser.
"""

from __future__ import annotations

import re

_ZAHL_EINHEIT = re.compile(r"(\d) (mL|mg|%|g/mol|mol/L|M)(?=[\s.,;:)?]|$)")


def de(x: float, stellen: int) -> str:
    """Zahl mit deutschem Dezimalkomma."""
    return f"{x:.{stellen}f}".replace(".", ",")


def nbsp(text: str) -> str:
    """Zahl und Einheit bleiben auf einer Zeile ("100,0 %" bricht sonst vor dem %)."""
    return _ZAHL_EINHEIT.sub("\\1\u00a0\\2", text)


def schritt(label: str, formula: str, substitution: str, result: str, explanation: str = "") -> dict:
    """Ein Rechenweg-Schritt im Schema von solution.py und calculator/."""
    return {
        "label": label,
        "formula": formula,
        "substitution": substitution,
        "result": result,
        "explanation": explanation,
    }


_ZEHNERPOTENZ = re.compile(r"\s*[·x×*]\s*10\s*\^?\s*", re.I)


def zahl(text) -> float:
    """Liest 12,5 · 12.5 · 1,3e-5 · 1,3E-5 · 1,3 · 10^-5 · 1,3 x 10-5."""
    t = str(text).strip().replace("−", "-").replace(",", ".")
    t = _ZEHNERPOTENZ.sub("e", t)
    return float(t.replace(" ", ""))


def _norm(text) -> str:
    return "".join(str(text).split()).upper()


def pruefe(aufgabe: dict, antwort) -> bool:
    """Auswahlaufgabe: Text vergleichen (Leerzeichen und Groß/klein egal).
    Rechenaufgabe: Zahl mit deutschem oder englischem Dezimaltrenner gegen die Toleranz."""
    if aufgabe.get("auswahl"):
        return _norm(antwort) == _norm(aufgabe["loesung"])
    try:
        wert = zahl(antwort)
    except ValueError:
        return False
    return abs(wert - aufgabe["loesung"]) <= aufgabe["toleranz"]
