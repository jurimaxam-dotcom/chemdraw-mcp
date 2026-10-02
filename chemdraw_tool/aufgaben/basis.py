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


def pruefe(aufgabe: dict, antwort) -> bool:
    """Antwort mit deutschem oder englischem Dezimaltrenner gegen die Toleranz."""
    try:
        wert = float(str(antwort).strip().replace(",", "."))
    except ValueError:
        return False
    return abs(wert - aufgabe["loesung"]) <= aufgabe["toleranz"]
