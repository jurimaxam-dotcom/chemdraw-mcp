"""Deutsche Trivialnamen in die englische Schreibweise umschreiben.

PubChem führt viele Arzneistoffe nur unter dem englischen INN: "Amilorid",
"Dexamethason" oder "Maleinsäure" findet keine Quelle, "amiloride",
"dexamethasone" und "maleinic acid" schon. Die Masse-Evaluation 11/2026
(docs/evidence/masse-eval-2026-11/identitaet.md) zählte 75 solche Eingaben.

Nur Regeln, die in der Messung gegen PubChem getroffen haben, stehen hier —
eine Regel, die nichts auflöst, kostet bei jedem Fehlschlag einen Netzaufruf.
Die Variante wird im Resolver erst gefragt, wenn alle Quellen den
Originalnamen verworfen haben; ein heute aufgelöster Name ändert sich dadurch nie.
Reine Funktion, kein Netz.
"""

from __future__ import annotations

import re

_RACEMATE_PREFIX = re.compile(r"^\((?:RS|rs|±)\)-")

_GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta"}

# Kation vorn: "Natriumlactat" → "sodium lactate".
_CATIONS = {
    "natrium": "sodium",
    "kalium": "potassium",
    "calcium": "calcium",
    "magnesium": "magnesium",
    "silber": "silver",
    "zink": "zinc",
    "lithium": "lithium",
}

# Anion hinten, zusammengeschrieben, mit Bindestrich oder Leerzeichen.
# Längere zuerst: "dihydrochlorid" vor "hydrochlorid" vor "chlorid" — sonst
# bleibt "hydro" am Stamm ("Bendamustinhydro chloride" kennt keine Quelle;
# Salznamen-Messung 06.11.2026, docs/evidence/masse-eval-2026-11/README.md).
_ANIONS = {
    "dihydrochlorid": "dihydrochloride",
    "hydrochlorid": "hydrochloride",
    "hydrobromid": "hydrobromide",
    "dipropionat": "dipropionate",
    "tartrat": "tartrate",
    "maleat": "maleate",
    "fumarat": "fumarate",
    "mesilat": "mesilate",
    "succinat": "succinate",
    "gluconat": "gluconate",
    "phosphat": "phosphate",
    "besilat": "besilate",
    "acetat": "acetate",
    "chlorid": "chloride",
    "bromid": "bromide",
    "iodid": "iodide",
    "sulfat": "sulfate",
    "nitrat": "nitrate",
    "lactat": "lactate",
    "citrat": "citrate",
    "furoat": "furoate",
    # Kation hinter dem Stamm ("Cefalotin-Natrium", "Metamizolnatrium") ist das
    # Gegenion; vorn ("Natriumchlorid") greift _CATIONS zuerst.
    "natrium": "sodium",
    "kalium": "potassium",
}

# Deutsche Säurestämme, die sich nicht nur in der Endung unterscheiden.
_ACID_STEMS = {
    "bernstein": "succin",
    "butter": "butyr",
    "essig": "acet",
    "ameisen": "form",
    "milch": "lact",
    "citronen": "citr",
    "zitronen": "citr",
}

# INN-Eindeutschung: das deutsche Wort lässt das End-e weg.
_ENDINGS = (
    ("on", "one"),
    ("id", "ide"),
    ("in", "ine"),
    ("at", "ate"),
    ("im", "ime"),
    ("an", "ane"),
)

# "Fluorcytosin" → "Fluorocytosine": Halogen vor Konsonant bekommt den Bindevokal.
_HALOGEN = re.compile(r"(?i)(fluor|chlor|brom)(?=[bcdfgklmnpqrstvz])")

_SEPARATOR = re.compile(r"([ \-])")


def _acid(stem: str) -> str:
    for german, english in _ACID_STEMS.items():
        if stem.lower().endswith(german):
            stem = stem[: len(stem) - len(german)] + english
            break
    return stem.removesuffix("e") + "ic acid"


def _word(word: str) -> str:
    lower = word.lower()
    if len(lower) < 4 or lower == "acid":
        return word  # "L", "N", Lokanten; "acid" ist schon englisch
    for german, english in _CATIONS.items():
        if lower.startswith(german) and len(lower) > len(german) + 2:
            return f"{english} {_word(word[len(german) :])}"
    if lower.endswith("säure"):
        return _acid(word[: -len("säure")])
    for german, english in _ANIONS.items():
        if lower == german:
            return english
        if lower.endswith(german) and len(lower) > len(german) + 3:
            return f"{_word(word[: -len(german)])} {english}"
    word = _HALOGEN.sub(r"\1o", word)
    lower = word.lower()
    for german, english in _ENDINGS:
        if lower.endswith(german):
            return word + english[len(german) :]
    return word


def english_variant(name: str) -> str | None:
    """Englische Schreibweise eines deutschen Trivialnamens, oder None.

    None heißt: nichts umzuschreiben — der Resolver fragt dann kein zweites Mal.
    Klammerzusätze ("Metamizol (freie Säure)") werden nicht angefasst.
    """
    if not name or "(" in _RACEMATE_PREFIX.sub("", name) or "+" in name:
        return None
    text = _RACEMATE_PREFIX.sub("", name)
    for greek, latin in _GREEK.items():
        text = text.replace(greek, latin)
    parts = _SEPARATOR.split(text)
    # "Vecuronium-Bromid": Anion nach Bindestrich ist ein eigenes Wort
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == "-" and parts[i + 1].lower() in _ANIONS:
            parts[i] = " "
    variant = "".join(p if p in (" ", "-") else _word(p) for p in parts)
    return variant if variant != name else None


_SALT_SUFFIX = re.compile(
    r"(?i)^(?P<stem>.{4,}?)[ \-]?(?P<ion>" + "|".join(_ANIONS) + r")$"
)


def salt_variant(name: str) -> str | None:
    """Salzname mit englischem Gegenion, Stamm unverändert — oder None.

    Salznamen-Messung 06.11.2026: PubChem führt manche Salze nur unter dem INN
    ohne Endungs-e ("Cefalotin sodium", "Anamorelin hydrochloride"), die
    english_variant ("Cefalotine sodium") verfehlt. None, wenn kein Gegenion am
    Ende steht oder die Schreibweise mit english_variant zusammenfällt — dann
    kostet sie keinen zweiten Netzaufruf.
    """
    match = _SALT_SUFFIX.match(_RACEMATE_PREFIX.sub("", name or ""))
    if not match:
        return None
    variant = f"{match['stem']} {_ANIONS[match['ion'].lower()]}"
    return variant if variant not in (name, english_variant(name)) else None
