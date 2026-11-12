"""Feste Lernabläufe als MCP-Prompts (vom Nutzer gewählte Vorlagen).

Ein Prompt ist Text, den der Nutzer bewusst auswählt — er darf das Modell nur
zu Tools schicken, die im Standardprofil `mvp` auch registriert sind, sonst
läuft der Ablauf im Desktop ins Leere. Und er beschreibt wie eine
Tool-Beschreibung, statt zu werben (dieselben Phrasen wie im Taxonomie-Test).
"""

import asyncio
import re

import pytest

from chemdraw_tool.server import create_server
from tests.test_server_profiles import FULL, MVP
from tests.test_server_taxonomy import SUPERLATIVES

EXAMPLES = {
    "study_compound": {"compound": "caffeine"},
    "practice_mechanism": {"reaction_type": "sn2", "substrates": "bromoethane, hydroxide"},
    "exam_flashcards": {"compounds": "aspirin, paracetamol, ibuprofen", "deck_name": "Analgesics"},
    "compare_compounds": {"compounds": "ethanol, methanol"},
}
# Tool-Präfixe dieses Servers — fängt auch Tippfehler und erfundene Namen.
_TOOLISH = re.compile(r"\b(?:generate|calculate|lookup|export|compare|batch|predict|save)_[a-z0-9_]+\b")


def _prompts(profile):
    return {p.name: p for p in asyncio.run(create_server(profile).list_prompts())}


def _render(profile, name, arguments):
    result = asyncio.run(create_server(profile).get_prompt(name, arguments))
    return "\n".join(m.content.text for m in result.messages)


@pytest.mark.parametrize("profile", ["mvp", "full"])
def test_prompts_are_listed_in_both_profiles(profile):
    prompts = _prompts(profile)
    assert set(prompts) == set(EXAMPLES)
    for name, prompt in prompts.items():
        assert prompt.title and prompt.description, name
        assert prompt.arguments, name
        assert all(a.description for a in prompt.arguments), name


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_prompt_renders_with_example_arguments(name):
    text = _render("mvp", name, EXAMPLES[name])
    for value in EXAMPLES[name].values():
        assert value.split(",")[0] in text, value


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_prompt_names_only_tools_of_the_default_profile(name):
    text = _render("mvp", name, EXAMPLES[name])
    named = (set(re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", text)) & FULL) | set(_TOOLISH.findall(text))
    assert named, f"{name} nennt kein Tool"
    assert named <= MVP - {"save_png"}, named - (MVP - {"save_png"})


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_prompt_describes_instead_of_advertising(name):
    text = _render("mvp", name, EXAMPLES[name]) + _prompts("mvp")[name].description
    for phrase in SUPERLATIVES:
        assert phrase.lower() not in text.lower(), phrase


def test_study_compound_goes_through_the_molecule_panel():
    # Der Reiter „Study“ gibt es nur in der Molekülansicht.
    text = _render("mvp", "study_compound", EXAMPLES["study_compound"])
    assert "generate_molecule" in text and "Study" in text


def test_practice_mechanism_refuses_an_unknown_mechanism():
    with pytest.raises(Exception, match="sn1"):
        _render("mvp", "practice_mechanism", {"reaction_type": "e2", "substrates": ""})


def test_exam_flashcards_point_at_the_anki_export():
    assert "export_anki_deck" in _render("mvp", "exam_flashcards", EXAMPLES["exam_flashcards"])
