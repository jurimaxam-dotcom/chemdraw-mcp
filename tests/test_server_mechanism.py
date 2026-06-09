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
    with pytest.raises(ValueError, match="nicht gefunden"):
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
    with pytest.raises(ValueError, match="passen nicht"):
        generate_mechanism(
            reaction_type="sn2",
            substrates=["CC=O", "CC"],
        )
