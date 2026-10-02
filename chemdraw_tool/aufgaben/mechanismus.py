"""SN1, SN2, E1 oder E2? — Entscheidungsaufgaben für Halogenalkane.

Für die OC-Eingangsklausur (Pharmazie 3. Semester) und OC I im Chemie-B.Sc.
Erzeugt werden nur Fälle, die jedes Lehrbuch gleich beantwortet; Mischfälle
(sekundäres Substrat in Solvolyse, tertiäres mit gutem Nucleophil/schwacher
Base) bleiben draußen, weil eine eindeutige Musterlösung dort lügen würde.

Nur Standardbibliothek — läuft per Pyodide im Browser.
"""

from __future__ import annotations

import random

from .basis import nbsp, pruefe, schritt  # noqa: F401 — pruefe ist Modul-API

AUSWAHL = ["SN1", "SN2", "E1", "E2"]

SUBSTRATE = {
    "methyl": ("Methyl", ("Iodmethan", "Brommethan")),
    "primaer": ("primär", ("1-Brombutan", "1-Brompropan", "1-Iodbutan")),
    "sekundaer": ("sekundär", ("2-Brombutan", "2-Brompropan", "Bromcyclohexan")),
    "tertiaer": ("tertiär", ("2-Brom-2-methylpropan", "2-Chlor-2-methylpropan", "2-Brom-2-methylbutan")),
}

# Reagenzklasse → (Beschreibung, [(Reagenz, Lösungsmittel, Bedingung)])
REAGENZIEN = {
    "nuc": (
        "starkes Nucleophil, schwache Base",
        (("Natriumiodid", "Aceton", "Raumtemperatur"),
         ("Natriumazid", "DMSO", "Raumtemperatur"),
         ("Natriummethanthiolat", "DMF", "Raumtemperatur")),
    ),
    "base": (
        "starke Base, zugleich starkes Nucleophil",
        (("Natriumethanolat", "Ethanol", "Raumtemperatur"),
         ("Natriummethanolat", "Methanol", "Raumtemperatur"),
         ("Natriumhydroxid", "Ethanol/Wasser", "Raumtemperatur")),
    ),
    "sperrig": (
        "starke, sperrige Base",
        (("Kalium-tert-butanolat", "tert-Butanol", "Raumtemperatur"),
         ("DBU", "THF", "Raumtemperatur")),
    ),
    "solvolyse_kalt": (
        "schwaches Nucleophil, schwache Base (Solvolyse)",
        (("Wasser", "Wasser/Aceton", "Raumtemperatur"),
         ("Ethanol", "Ethanol", "Raumtemperatur")),
    ),
    "solvolyse_warm": (
        "schwaches Nucleophil, schwache Base (Solvolyse)",
        (("Ethanol", "Ethanol", "Erwärmen unter Rückfluss"),
         ("Wasser", "Wasser", "Erwärmen")),
    ),
}

# Die eindeutigen Fälle und ihre Antwort, mit Begründung.
FAELLE = {
    ("methyl", "nuc"): ("SN2", "Methylgruppen bilden kein Carbokation und haben kein β-H — nur SN2 ist möglich."),
    ("methyl", "base"): ("SN2", "Ohne β-Wasserstoff gibt es keine Eliminierung; das Alkoholat greift als Nucleophil an."),
    ("methyl", "sperrig"): ("SN2", "Kein β-H, also keine E2. Das sperrige Alkoholat substituiert, wenn auch langsam."),
    ("primaer", "nuc"): ("SN2", "Primäres C ist kaum abgeschirmt, das gute Nucleophil greift rückseitig an."),
    ("primaer", "base"): ("SN2", "Am primären C gewinnt die Substitution; E2 ist nur Nebenreaktion."),
    ("primaer", "sperrig"): ("E2", "Die sperrige Base kommt nicht an das C heran und zieht stattdessen ein β-H ab."),
    ("sekundaer", "nuc"): ("SN2", "Gutes Nucleophil, kaum basisch, im polar aprotischen Lösungsmittel: SN2 mit Inversion."),
    ("sekundaer", "base"): ("E2", "Am sekundären C ist die starke Base im Vorteil: E2 überwiegt."),
    ("sekundaer", "sperrig"): ("E2", "Sperrige starke Base am sekundären C: E2."),
    ("tertiaer", "base"): ("E2", "Tertiäres C ist für SN2 blockiert; die starke Base eliminiert."),
    ("tertiaer", "sperrig"): ("E2", "Tertiär plus sperrige Base: E2."),
    ("tertiaer", "solvolyse_kalt"): ("SN1", "Stabiles tertiäres Carbokation, schwaches Nucleophil, kalt: SN1."),
    ("tertiaer", "solvolyse_warm"): ("E1", "Gleiches Carbokation, aber Wärme begünstigt die Eliminierung (Entropie): E1."),
}

# Substrate, die nur EIN Alken bilden können — dort gibt es keine Regioselektivität.
SYMMETRISCH = {"2-Brompropan", "Bromcyclohexan", "2-Brom-2-methylpropan", "2-Chlor-2-methylpropan"}


def _regio(weg: str, mittel: str, substrat: str) -> str:
    if weg != "E2" or substrat in SYMMETRISCH or substrat.startswith("1-"):
        return ""
    if mittel == "DBU":
        return ""  # DBU liefert je nach Substrat oft Saytzeff — keine Pauschalaussage
    if mittel == "Kalium-tert-butanolat":
        return " Regioselektivität: Die sperrige Base holt das zugänglichste β-H — bevorzugt das Hofmann-Produkt (weniger substituiertes Alken)."
    return " Regioselektivität: Saytzeff — bevorzugt das höher substituierte, stabilere Alken."


_LOESUNGSMITTEL = {
    "Aceton": "polar aprotisch", "DMSO": "polar aprotisch", "DMF": "polar aprotisch", "THF": "aprotisch",
    "Ethanol": "polar protisch", "Methanol": "polar protisch", "Ethanol/Wasser": "polar protisch",
    "tert-Butanol": "polar protisch", "Wasser/Aceton": "polar protisch", "Wasser": "polar protisch",
}


def weg_aufgabe(seed: int) -> dict:
    rng = random.Random(f"mech-{seed}")
    klasse, reagenz = rng.choice(sorted(FAELLE))
    klasse_text, substrate = SUBSTRATE[klasse]
    reagenz_text, varianten = REAGENZIEN[reagenz]
    substrat = rng.choice(substrate)
    # Iodid an einem Iodalkan tauscht Iod gegen Iod — das ist keine Reaktion.
    varianten = [v for v in varianten if not ("Iod" in substrat and v[0] == "Natriumiodid")]
    mittel, lm, bedingung = rng.choice(varianten)
    weg, warum = FAELLE[(klasse, reagenz)]

    text = (
        f"{substrat} reagiert mit {mittel} in {lm} ({bedingung}). "
        f"Über welchen Mechanismus läuft die Hauptreaktion?"
    )
    rechenweg = [
        schritt("Substrat", "Wie substituiert ist das C mit der Abgangsgruppe?", substrat,
                f"{klasse_text}", "Methyl/primär: SN2 möglich. Tertiär: SN2 blockiert, Carbokation stabil."),
        schritt("Reagenz", "Nucleophil oder Base, stark oder schwach, sperrig?", mittel,
                reagenz_text, ""),
        schritt("Bedingungen", "Lösungsmittel und Temperatur", f"{lm}, {bedingung}",
                _LOESUNGSMITTEL.get(lm, ""), "Polar aprotisch stärkt Nucleophile (SN2). Wärme begünstigt Eliminierung."),
        schritt("Entscheidung", "Substrat × Reagenz × Bedingungen", f"{klasse_text} + {reagenz_text}",
                weg, warum + _regio(weg, mittel, substrat)),
    ]
    return {
        "typ": "mechanismus",
        "stoff": substrat,
        "text": nbsp(text),
        "gesucht": "Mechanismus",
        "einheit": "",
        "auswahl": list(AUSWAHL),
        "loesung": weg,
        "toleranz": 0,
        "werte": {"klasse": klasse, "reagenz": reagenz, "substrat": substrat, "reagenz_name": mittel},
        "rechenweg": rechenweg,
    }


def neue_aufgabe(seed: int) -> dict:
    return weg_aufgabe(seed)
