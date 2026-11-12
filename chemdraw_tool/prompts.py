"""Feste Lernabläufe als MCP-Prompts — Vorlagen, die der Nutzer im Client wählt.

Ein Prompt ruft selbst kein Tool auf; er schreibt die Nutzernachricht vor, die
das Modell dann mit den Tools abarbeitet. Deshalb gilt für den Text dasselbe
wie für Tool-Beschreibungen: nur Tools nennen, die im Standardprofil `mvp`
registriert sind (sonst läuft der Ablauf im Desktop ins Leere), und beschreiben
statt werben. Beides prüft tests/test_prompts.py.

Argumente kommen als Text an (MCP-Prompt-Argumente sind Strings), Listen also
kommagetrennt.
"""

from __future__ import annotations

import json
import re
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS
from pydantic import Field

MECHANISMS = {
    "sn1": "SN1",
    "sn2": "SN2",
    "fischer_ester": "Fischer esterification",
}


# Komma zwischen zwei Stoffen, nicht in einem Namen: ein Lokanten-Komma steht
# ohne Leerzeichen zwischen Ziffern, Strichen oder N/O-Lokanten („2,3-“, „N,N-“).
_LOCANT_COMMA = re.compile(r"(?<=[0-9NOS'])\s*,(?=[0-9NOS][0-9']*[,\-])")


def _items(text: str) -> list[str]:
    """Liste aus einem Textargument. Semikolons trennen immer; ohne Semikolon
    trennen Kommas — außer dem Lokanten-Komma in einem IUPAC-Namen
    („2-bromo-2,3-dimethylbutane“ bleibt ein Stoff). Leeres fällt weg."""
    if ";" in text:
        parts = text.split(";")
    else:
        parts = _LOCANT_COMMA.sub("\x00", text).split(",")
    return [p.replace("\x00", ",").strip(" ,") for p in parts if p.replace("\x00", ",").strip(" ,")]


def _listing(items: list[str]) -> str:
    return ", ".join(items)


def study_compound(
    compound: Annotated[str, Field(description="Compound name or SMILES, e.g. caffeine.")],
) -> str:
    return (
        f"I want to study {compound}.\n\n"
        f"1. Draw its structure with generate_molecule.\n"
        f"2. I will open the Study tab in the panel: it keeps the drawing and covers "
        f"the name, key values and functional groups until I uncover them.\n"
        f"3. Quiz me one question at a time — the name, each functional group, "
        f"and one or two properties. Wait for my answer, then say whether it was "
        f"right and why, before asking the next question.\n"
        f"4. At the end, list what I got wrong so I can repeat it."
    )


def practice_mechanism(
    reaction_type: Annotated[
        str, Field(description='Mechanism: "sn1", "sn2" or "fischer_ester".')
    ],
    substrates: Annotated[
        str,
        Field(
            description="Optional, separated by semicolons or commas: halide and nucleophile, or acid "
            "and alcohol. Empty = the textbook example."
        ),
    ] = "",
) -> str:
    key = reaction_type.strip().lower()
    if key not in MECHANISMS:
        # MCPError, weil das SDK jede andere Exception zu „Error rendering
        # prompt …“ verschluckt — der Nutzer soll lesen, was erlaubt ist.
        raise MCPError(
            INVALID_PARAMS,
            f"Unknown mechanism '{reaction_type}' — use sn1, sn2 or fischer_ester.",
        )
    items = _items(substrates)
    source = f"with {_listing(items)}" if items else "with the textbook example"
    fallback = (
        "\nIf the substrates are outside what the mechanism covers, the tool says "
        "why — tell me the reason and continue with the textbook example."
        if items
        else ""
    )
    return (
        f"Let me practise the {MECHANISMS[key]} mechanism {source}, step by step.\n\n"
        f'1. Call generate_mechanism with reaction_type="{key}", '
        f"substrates={json.dumps(items)} and current_step=0 for the overview.\n"
        f"2. Then go through current_step=1, 2, … one step per turn. Before you "
        f"show a step, ask me where the electrons move next and wait for my answer.\n"
        f"3. After my answer, show the step and explain the curved arrows."
        f"{fallback}"
    )


def exam_flashcards(
    compounds: Annotated[
        str, Field(description="Compound names or SMILES for the deck, separated by semicolons or commas.")
    ],
    deck_name: Annotated[
        str, Field(description="Deck name, also the file name. Re-use it to update the deck.")
    ] = "",
) -> str:
    name = deck_name.strip() or "Exam compounds"
    return (
        f"Make Anki flashcards for my exam on: {_listing(_items(compounds))}.\n\n"
        f"1. Write one card per compound: the front shows the structure (structure "
        f"field with the English or IUPAC name or SMILES), the back gives the name "
        f"and one fact that is worth knowing for an exam.\n"
        f'2. Call export_anki_deck with deck_name "{name}" and these cards, '
        f'deliver "apkg".\n'
        f"3. Tell me where the file is and how many cards it has."
    )


def compare_compounds(
    compounds: Annotated[
        str, Field(description="Names or SMILES, two or more, separated by semicolons or commas.")
    ],
) -> str:
    return (
        f"Compare these compounds: {_listing(_items(compounds))}.\n\n"
        f"1. Draw them side by side with compare_molecules, which marks where the "
        f"structures differ.\n"
        f"2. Explain each difference and what it changes, for example acidity, "
        f"polarity or reactivity.\n"
        f"3. Quote property values only from lookup, and name the source."
    )


PROMPTS = (
    (study_compound, "Study a compound",
     "Draw a compound, then quiz the user on it with the panel's Study tab."),
    (practice_mechanism, "Practise a mechanism",
     "Step through an SN1, SN2 or Fischer esterification mechanism, asking for "
     "each electron move before showing it."),
    (exam_flashcards, "Exam flashcards",
     "Turn a list of compounds into an Anki deck with structure → name cards."),
    (compare_compounds, "Compare compounds",
     "Draw two or more compounds side by side and explain the differences."),
)


def register_prompts(instance: MCPServer) -> None:
    """Alle Lernabläufe registrieren — in beiden Profilen dieselben."""
    for fn, title, description in PROMPTS:
        instance.prompt(title=title, description=description)(fn)
