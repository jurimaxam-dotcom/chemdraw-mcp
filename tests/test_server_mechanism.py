"""Tests for generate_mechanism MCP tool."""

import pytest

from chemdraw_tool.payloads import MechanismPayload
from chemdraw_tool.server import generate_mechanism


def test_generate_mechanism_sn2():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
    )
    assert isinstance(result, MechanismPayload)
    assert result.type == "mechanism"
    assert result.reaction_type == "sn2"
    assert result.current_step == 0
    assert len(result.steps) >= 3
    assert all("<svg" in s.svg.lower() for s in result.steps)


def test_generate_mechanism_specific_step():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
        current_step=2,
    )
    assert result.current_step == 2


def test_generate_mechanism_unknown_type():
    with pytest.raises(ValueError, match="Unknown mechanism 'nonexistent'.*fischer_ester, sn1, sn2"):
        generate_mechanism(
            reaction_type="nonexistent",
            substrates=["CCBr"],
        )


def test_generate_mechanism_sn1():
    result = generate_mechanism(
        reaction_type="sn1",
        substrates=["CC(C)(C)Br", "O"],
    )
    assert isinstance(result, MechanismPayload)
    assert result.reaction_type == "sn1"
    assert len(result.steps) >= 4


def test_generate_mechanism_all_steps_have_svg():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
    )
    for step in result.steps:
        assert step.svg.strip() != ""
        assert "<svg" in step.svg.lower()


def test_generate_mechanism_wrong_substrates():
    with pytest.raises(ValueError, match="do not fit the sn2 mechanism"):
        generate_mechanism(
            reaction_type="sn2",
            substrates=["CC=O", "CC"],
        )


def test_title_names_the_textbook_example_that_is_drawn():
    """Befund 30.10.2026: Das Bild ist immer das feste Template-Beispiel, der Titel
    nannte aber die Nutzer-Substrate („SN2: CCCCBr + [SH-]" über CH3Br + OH-).
    Entscheid Jay/Chef: ehrliche Lehrbuch-Galerie — der Titel nennt, was gezeichnet ist."""
    result = generate_mechanism("sn2", ["CCCCBr", "[SH-]"])
    assert result.name == "Nucleophilic Substitution (SN2) — textbook example: bromomethane + hydroxide"
    assert "CCCCBr" not in result.name


@pytest.mark.parametrize("reaction_type, example", [
    ("sn1", "2-bromopropane + water"),
    ("fischer_ester", "acetic acid + methanol"),
])
def test_every_template_names_its_drawn_example(reaction_type, example):
    from chemdraw_tool.templates import get_template
    assert get_template(reaction_type).example == example


def test_drawing_does_not_depend_on_the_substrates():
    """Hält die Galerie-Aussage ehrlich: ändert sich das, muss der Titel mitwandern."""
    a = generate_mechanism("sn2", ["CBr", "[OH-]"])
    b = generate_mechanism("sn2", ["CCCCBr", "[SH-]"])
    assert [s.svg for s in a.steps] == [s.svg for s in b.steps]


def test_reaction_type_lists_every_template_and_nothing_else():
    """Kein „e.g." mehr: das Schema nennt genau die vorhandenen Typen."""
    import inspect
    import typing

    from chemdraw_tool.templates import list_templates
    hint = inspect.signature(generate_mechanism).parameters["reaction_type"].annotation
    assert sorted(typing.get_args(hint)) == list_templates()


def test_description_says_it_is_a_textbook_gallery():
    doc = generate_mechanism.__doc__
    assert "textbook" in doc and "e.g." not in doc
