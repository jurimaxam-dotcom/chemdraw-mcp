"""Kuratierte Anki-Decks — kleine, geprüfte Bibliothek (bewusst 2 Decks).

Kurations-Regeln:
- Nur Lehrbuch-Klassiker; jede Struktur steht in VERIFIED_STRUCTURES und
  wird im Test gegen ihre Summenformel verifiziert (Tippfehler-Gate).
- Die Bibliothek wächst nur durch bewusste Entscheidung — sie ist ein
  Starter-Angebot, kein Content-Management-System. Eigene Decks entstehen
  über export_anki_deck mit modellgenerierten Karten.
"""

from __future__ import annotations

from chemdraw_tool.payloads import AnkiCard, CardSide, ReactionSpec

# SMILES → erwartete Summenformel. Der Test rechnet via RDKit nach.
VERIFIED_STRUCTURES: dict[str, str] = {
    "CC(=O)Oc1ccccc1C(=O)O": "C9H8O4",  # Aspirin
    "CC(=O)Nc1ccc(O)cc1": "C8H9NO2",  # Paracetamol
    "CC(C)Cc1ccc(cc1)C(C)C(=O)O": "C13H18O2",  # Ibuprofen
    "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O": "C14H14O3",  # Naproxen (S)
    "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl": "C14H11Cl2NO2",  # Diclofenac
    "CC(C(=O)O)c1cccc(c1)C(=O)c1ccccc1": "C16H14O3",  # Ketoprofen
    "CN1CC[C@]23c4c5ccc(O)c4O[C@H]2[C@@H](O)C=C[C@H]3[C@H]1C5": "C17H19NO3",  # Morphin
    "Cc1ccc(cc1)-c1cc(C(F)(F)F)nn1-c1ccc(cc1)S(N)(=O)=O": "C17H14F3N3O2S",  # Celecoxib
}

_ANALGESICS: list[tuple[str, str, str]] = [
    ("Aspirin (acetylsalicylic acid)", "CC(=O)Oc1ccccc1C(=O)O",
     "Irreversible COX inhibitor — antiplatelet at low dose"),
    ("Paracetamol (acetaminophen)", "CC(=O)Nc1ccc(O)cc1",
     "Analgesic/antipyretic; hepatotoxic in overdose (NAPQI)"),
    ("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
     "NSAID, propionic acid class (profen)"),
    ("Naproxen", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O",
     "NSAID, profen with naphthalene core; long half-life"),
    ("Diclofenac", "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl",
     "NSAID, acetic acid class; COX-2 preference"),
    ("Ketoprofen", "CC(C(=O)O)c1cccc(c1)C(=O)c1ccccc1",
     "NSAID, profen with benzophenone core"),
    ("Morphine", "CN1CC[C@]23c4c5ccc(O)c4O[C@H]2[C@@H](O)C=C[C@H]3[C@H]1C5",
     "Opioid analgesic — µ-receptor agonist, phenanthrene alkaloid"),
    ("Celecoxib", "Cc1ccc(cc1)-c1cc(C(F)(F)F)nn1-c1ccc(cc1)S(N)(=O)=O",
     "Selective COX-2 inhibitor (coxib), pyrazole sulfonamide"),
]


def _analgesics_cards() -> list[AnkiCard]:
    cards = []
    for name, smiles, note in _ANALGESICS:
        cards.append(
            AnkiCard(
                front=CardSide(text="Which analgesic is this?", structure=smiles),
                back=CardSide(text=f"<b>{name}</b><br>{note}"),
                tags=["chemdraw-mcp", "analgesics"],
            )
        )
    return cards


def _identity_cards() -> list[AnkiCard]:
    text_qa = [
        ("Ph.Eur. identity: chloride — reagent and observation?",
         "AgNO₃ in dilute HNO₃ → white curdy precipitate of AgCl, "
         "soluble in dilute ammonia."),
        ("Ph.Eur. identity: sulfate — reagent and observation?",
         "BaCl₂ → white precipitate of BaSO₄, insoluble in dilute HCl."),
        ("Ph.Eur. identity: iron(III) — reagent and observation?",
         "Potassium thiocyanate → deep red Fe(SCN)₃ complex; "
         "potassium hexacyanoferrate(II) → Prussian blue."),
        ("Ph.Eur. identity: ammonium — reagent and observation?",
         "Warm with NaOH → ammonia gas: characteristic smell, "
         "turns moist red litmus paper blue."),
    ]
    cards = [
        AnkiCard(
            front=CardSide(text=q),
            back=CardSide(text=a),
            tags=["chemdraw-mcp", "pheur-identity"],
        )
        for q, a in text_qa
    ]
    cards.append(
        AnkiCard(
            front=CardSide(
                text="Ph.Eur. identity: acetate — reaction and observation?"
            ),
            back=CardSide(
                text="Warm with ethanol and sulfuric acid → fruity smell of "
                "ethyl acetate (esterification).",
                reaction=ReactionSpec(
                    reactants=["CCO", "CC(=O)O"],
                    products=["CCOC(C)=O", "O"],
                    conditions="H₂SO₄ (cat.), Δ",
                ),
            ),
            tags=["chemdraw-mcp", "pheur-identity"],
        )
    )
    cards.append(
        AnkiCard(
            front=CardSide(
                text="Ph.Eur. identity: carbonate — reaction and observation?"
            ),
            back=CardSide(
                text="Dilute acid → effervescence of CO₂, which turns "
                "lime water turbid.",
                reaction=ReactionSpec(
                    reactants=["O=C([O-])[O-]"],
                    products=["O=C=O", "O"],
                    conditions="2 HCl (dil.)",
                ),
            ),
            tags=["chemdraw-mcp", "pheur-identity"],
        )
    )
    return cards


CURATED_DECKS: dict[str, dict] = {
    "analgesics-structures": {
        "name": "Common Analgesics — Structures",
        "description": "Structure → name drills for 8 classic analgesics "
        "(NSAIDs, paracetamol, morphine, celecoxib).",
        "build": _analgesics_cards,
    },
    "pheur-identity-basics": {
        "name": "Ph.Eur. Identity Reactions — Basics",
        "description": "Classic pharmacopoeia identity tests: reagent, "
        "observation and (where it helps) the reaction scheme.",
        "build": _identity_cards,
    },
}


def get_curated_deck(deck_id: str) -> tuple[str, list[AnkiCard]]:
    if deck_id not in CURATED_DECKS:
        available = ", ".join(sorted(CURATED_DECKS))
        raise ValueError(f"Unbekanntes Deck {deck_id!r} — verfügbar: {available}")
    entry = CURATED_DECKS[deck_id]
    return entry["name"], entry["build"]()
