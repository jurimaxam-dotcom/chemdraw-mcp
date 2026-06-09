"""Ester mechanism templates (Fischer esterification)."""

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep, MechanismTemplate
from chemdraw_tool.templates import register

FISCHER_ESTER_TEMPLATE = MechanismTemplate(
    id="fischer_ester",
    name="Fischer-Veresterung",
    category="ester",
    substrate_pattern="[CX3:1](=[OX1:2])[OX2H1:3]",
    nucleophile_pattern="[OX2H1:4][#6]",
    steps=[
        MechanismStep(
            label="Edukte",
            molecules=["[CH3:5][C:1](=[O:2])[OH:3]", "[OH:4][CH3:6]", "[H+]"],
            arrows=[],
        ),
        MechanismStep(
            label="Protonierung der Carbonylgruppe",
            molecules=["[CH3:5][C:1](=[O:2])[OH:3]", "[H+:7]"],
            arrows=[
                CurvedArrow(
                    source=(2, "lone_pair"),
                    target=(7, "atom"),
                    style="full",
                ),
            ],
        ),
        MechanismStep(
            label="Nucleophiler Angriff des Alkohols",
            molecules=["[CH3:5][C+:1]([OH:2])([OH:3])", "[OH:4][CH3:6]"],
            arrows=[
                CurvedArrow(
                    source=(4, "lone_pair"),
                    target=(1, "atom"),
                    style="full",
                ),
            ],
        ),
        MechanismStep(
            label="Tetraedrisches Intermediat",
            molecules=["[CH3:5][C:1]([OH:2])([OH:3])([O:4][CH3:6])"],
            arrows=[],
        ),
        MechanismStep(
            label="Wasserabspaltung",
            molecules=["[CH3:5][C:1]([OH:2])([OH:3])([O:4][CH3:6])"],
            arrows=[
                CurvedArrow(
                    source=(1, "bond_to", 3),
                    target=(3, "atom"),
                    style="full",
                ),
            ],
        ),
        MechanismStep(
            label="Produkte",
            molecules=["[CH3:5][C:1](=[O:2])[O:4][CH3:6]", "[OH2:3]"],
            arrows=[],
        ),
    ],
)

register(FISCHER_ESTER_TEMPLATE)
