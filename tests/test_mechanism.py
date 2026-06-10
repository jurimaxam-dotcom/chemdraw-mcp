"""Tests for mechanism data types, registry, and SMARTS validation."""

import pytest

from chemdraw_tool.payloads import MechanismPayload, MechanismStepPayload


def test_mechanism_step_payload_defaults():
    step = MechanismStepPayload(svg="<svg></svg>", label="Edukte")
    assert step.svg == "<svg></svg>"
    assert step.label == "Edukte"
    assert step.is_transition_state is False


def test_mechanism_payload_defaults():
    step = MechanismStepPayload(svg="<svg></svg>", label="Edukte")
    payload = MechanismPayload(
        name="SN2: Bromethan + OH⁻",
        reaction_type="sn2",
        steps=[step],
    )
    assert payload.type == "mechanism"
    assert payload.current_step == 0
    assert len(payload.steps) == 1


from chemdraw_tool.mechanism import (
    CurvedArrow,
    MechanismStep,
    MechanismTemplate,
    validate_substrates,
)
from chemdraw_tool.templates import get_template, list_templates


def test_curved_arrow_creation():
    arrow = CurvedArrow(
        source=(3, "lone_pair"),
        target=(1, "atom"),
        style="full",
    )
    assert arrow.source == (3, "lone_pair")
    assert arrow.style == "full"


def test_mechanism_step_creation():
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    assert len(step.molecules) == 2
    assert step.is_transition_state is False
    assert step.partial_bonds == []


def test_mechanism_template_creation():
    step = MechanismStep(label="Edukte", molecules=["[CH3:1][Br:2]"], arrows=[])
    template = MechanismTemplate(
        id="test",
        name="Test Reaction",
        category="test",
        substrate_pattern="[C:1][Br:2]",
        nucleophile_pattern=None,
        steps=[step],
    )
    assert template.id == "test"
    assert template.nucleophile_pattern is None


def test_list_templates_not_empty():
    templates = list_templates()
    assert len(templates) > 0
    assert all(isinstance(t, str) for t in templates)


def test_get_template_sn2():
    tmpl = get_template("sn2")
    assert tmpl is not None
    assert tmpl.id == "sn2"
    assert tmpl.category == "substitution"
    assert len(tmpl.steps) >= 3


def test_get_template_unknown_returns_none():
    assert get_template("nonexistent_reaction") is None


def test_validate_substrates_sn2_matches():
    tmpl = get_template("sn2")
    assert validate_substrates(tmpl, ["CCBr", "[OH-]"]) is True


def test_validate_substrates_sn2_wrong_substrate():
    tmpl = get_template("sn2")
    assert validate_substrates(tmpl, ["CC=O", "[OH-]"]) is False


def test_validate_substrates_sn2_missing_nucleophile():
    tmpl = get_template("sn2")
    assert validate_substrates(tmpl, ["CCBr"]) is False


def test_validate_substrates_no_nucleophile_pattern():
    """Template without nucleophile_pattern should pass with just substrate match."""
    step = MechanismStep(label="test", molecules=[], arrows=[])
    tmpl = MechanismTemplate(
        id="test_no_nuc",
        name="Test",
        category="test",
        substrate_pattern="[C:1]=[O:2]",
        nucleophile_pattern=None,
        steps=[step],
    )
    assert validate_substrates(tmpl, ["CC=O"]) is True


def test_get_template_fischer_ester():
    tmpl = get_template("fischer_ester")
    assert tmpl is not None
    assert tmpl.id == "fischer_ester"
    assert tmpl.category == "ester"
    assert len(tmpl.steps) >= 4


def test_fischer_ester_validates_substrates():
    tmpl = get_template("fischer_ester")
    assert validate_substrates(tmpl, ["CC(=O)O", "CO"]) is True


def test_fischer_ester_rejects_wrong_substrate():
    tmpl = get_template("fischer_ester")
    assert validate_substrates(tmpl, ["CCBr", "CO"]) is False


def test_validate_substrates_invalid_substrate_pattern_raises():
    """A malformed SMARTS in the template is a template bug, not a non-match —
    it must raise, not silently return False."""
    bad = MechanismTemplate(
        id="bad",
        name="Bad",
        category="test",
        substrate_pattern="C(",  # invalid SMARTS
        nucleophile_pattern=None,
        steps=[],
    )
    with pytest.raises(ValueError, match="SMARTS"):
        validate_substrates(bad, ["CCO"])


def test_validate_substrates_invalid_nucleophile_pattern_raises():
    bad = MechanismTemplate(
        id="bad",
        name="Bad",
        category="test",
        substrate_pattern="[CX4][Br]",
        nucleophile_pattern="C(",  # invalid SMARTS
        steps=[],
    )
    with pytest.raises(ValueError, match="SMARTS"):
        validate_substrates(bad, ["CCBr"])


def test_template_labels_are_english():
    """Sichtbare UI-Strings (Step-Labels, Template-Namen) sind englisch —
    internationales Tool; exakt geprüft am SN2, Marker-Check für den Rest."""
    from chemdraw_tool.templates import get_template, list_templates

    sn2 = get_template("sn2")
    assert sn2.name == "Nucleophilic Substitution (SN2)"
    assert [s.label for s in sn2.steps] == [
        "Reactants",
        "Backside attack (transition state)",
        "Products",
    ]
    german_markers = ("Edukte", "Produkt", "Angriff", "Veresterung", "ierung")
    for name in list_templates():
        t = get_template(name)
        visible = t.name + " " + " ".join(s.label for s in t.steps)
        for marker in german_markers:
            assert marker not in visible, f"{name}: deutscher Marker {marker!r}"
