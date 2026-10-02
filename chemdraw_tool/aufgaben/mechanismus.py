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

# Reagenzklasse → (Beschreibung, [(Reagenz, Lösungsmittel, Bedingung, erlaubte Substratklassen)])
# Die Klassenliste schneidet die Kombinationen weg, die nicht eindeutig sind
# (Chemie-Gutachten 02.10.2026): OH⁻ in wässrigem Ethanol an sek./tert. C ist das
# klassische SN1-Medium bzw. ~1:1 SN2/E2; DBU eliminiert primäre Halogenide kaum.
ALLE = ("methyl", "primaer", "sekundaer", "tertiaer")
REAGENZIEN = {
    "nuc": (
        "starkes Nucleophil, schwache Base",
        (("Natriumiodid", "Aceton", "Raumtemperatur", ALLE),
         ("Natriumazid", "DMSO", "Raumtemperatur", ALLE),
         ("Natriummethanthiolat", "DMF", "Raumtemperatur", ALLE)),
    ),
    "base": (
        "starke Base, zugleich starkes Nucleophil",
        (("Natriumethanolat", "Ethanol", "Raumtemperatur", ALLE),
         ("Natriummethanolat", "Methanol", "Raumtemperatur", ALLE),
         ("Natriumhydroxid", "Ethanol/Wasser", "Raumtemperatur", ("methyl", "primaer"))),
    ),
    "sperrig": (
        "starke, sperrige Base",
        (("Kalium-tert-butanolat", "tert-Butanol", "Raumtemperatur", ALLE),
         ("DBU", "THF", "Raumtemperatur", ("sekundaer", "tertiaer"))),
    ),
    "solvolyse": (
        "schwaches Nucleophil, schwache Base (Solvolyse)",
        (("Wasser", "Wasser/Aceton", "Raumtemperatur", ALLE),
         ("Ethanol", "Ethanol", "Raumtemperatur", ALLE)),
    ),
}

# Die eindeutigen Fälle und ihre Antwort. {mittel} wird durch das Reagenz ersetzt,
# damit die Begründung nie ein anderes Reagenz nennt als die Aufgabe.
# Bewusst NICHT dabei: tertiär + Solvolyse + Wärme (SN1 und E1 konkurrieren,
# Hughes/Ingold) und sekundär + Solvolyse.
FAELLE = {
    ("methyl", "nuc"): ("SN2", "Methylgruppen bilden kein Carbokation und haben kein β-H — nur SN2 ist möglich."),
    ("methyl", "base"): ("SN2", "Ohne β-Wasserstoff gibt es keine Eliminierung; {mittel} greift als Nucleophil an."),
    ("methyl", "sperrig"): ("SN2", "Kein β-H, also keine E2. {mittel} substituiert, wenn auch langsam."),
    ("primaer", "nuc"): ("SN2", "Primäres C ist kaum abgeschirmt, das gute Nucleophil greift von der Rückseite an."),
    ("primaer", "base"): ("SN2", "Am primären C gewinnt die Substitution; E2 ist nur Nebenreaktion."),
    ("primaer", "sperrig"): ("E2", "{mittel} ist zu sperrig für den Rückseitenangriff und zieht stattdessen ein β-H ab."),
    ("sekundaer", "nuc"): ("SN2", "Gutes Nucleophil, kaum basisch, im polar aprotischen Lösungsmittel: SN2 (Rückseitenangriff)."),
    ("sekundaer", "base"): ("E2", "Am sekundären C ist die starke Base im Vorteil: E2 überwiegt."),
    ("sekundaer", "sperrig"): ("E2", "Sperrige starke Base am sekundären C: E2."),
    ("tertiaer", "base"): ("E2", "Tertiäres C ist für SN2 blockiert; die starke Base eliminiert."),
    ("tertiaer", "sperrig"): ("E2", "Tertiär plus sperrige Base: E2."),
    ("tertiaer", "solvolyse"): ("SN1", "Stabiles tertiäres Carbokation, schwaches Nucleophil, Raumtemperatur: SN1 (E1 nur als Nebenreaktion)."),
}

# Substrate, die nur EIN Alken bilden können — dort gibt es keine Regioselektivität.
SYMMETRISCH = {"2-Brompropan", "Bromcyclohexan", "2-Brom-2-methylpropan", "2-Chlor-2-methylpropan"}


def _regio(weg: str, mittel: str, substrat: str) -> str:
    if weg != "E2" or substrat in SYMMETRISCH or substrat.startswith("1-"):
        return ""
    if mittel == "DBU":
        return ""  # DBU liefert je nach Substrat oft Saytzeff — keine Pauschalaussage
    if mittel == "Kalium-tert-butanolat":
        if substrat == "2-Brom-2-methylbutan":
            return (" Regioselektivität: Die sperrige Base holt das zugänglichste β-H — bevorzugt "
                    "das Hofmann-Produkt 2-Methylbut-1-en (rund 70 %).")
        return (" Regioselektivität: Mit der sperrigen Base steigt der Anteil des weniger substituierten "
                "Alkens deutlich (Hofmann-Tendenz); bei 2-Brombutan ist das Verhältnis aber knapp, etwa 1 : 1.")
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
    varianten = [v for v in varianten if klasse in v[3]]
    mittel, lm, bedingung, _ = rng.choice(varianten)
    weg, warum = FAELLE[(klasse, reagenz)]
    warum = warum.format(mittel=mittel)

    if reagenz == "solvolyse":
        text = (
            f"{substrat} wird in {lm} gelöst und bei {bedingung} stehen gelassen (Solvolyse). "
            f"Über welchen Mechanismus läuft die Hauptreaktion?"
        )
    else:
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
