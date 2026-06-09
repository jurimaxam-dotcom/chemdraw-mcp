"""SN1 and SN2 mechanism templates."""

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep, MechanismTemplate
from chemdraw_tool.templates import register

SN2_TEMPLATE = MechanismTemplate(
    id="sn2",
    name="Nucleophile Substitution (SN2)",
    category="substitution",
    substrate_pattern="[C:1][F,Cl,Br,I:2]",
    nucleophile_pattern="[O,N,S:3]",
    steps=[
        MechanismStep(
            label="Edukte",
            molecules=["[OH-:3]", "[CH3:1][Br:2]"],
            arrows=[],
        ),
        MechanismStep(
            label="Rückseitenangriff (Übergangszustand)",
            molecules=["[O-:3].[CH3:1].[Br-:2]"],
            arrows=[
                CurvedArrow(
                    source=(3, "lone_pair"),
                    target=(1, "atom"),
                    style="full",
                ),
                CurvedArrow(
                    source=(1, "bond_to", 2),
                    target=(2, "atom"),
                    style="full",
                ),
            ],
            is_transition_state=True,
            partial_bonds=[(3, 1), (1, 2)],
        ),
        MechanismStep(
            label="Produkte",
            molecules=["[OH:3][CH3:1]", "[Br-:2]"],
            arrows=[],
        ),
    ],
)

SN1_TEMPLATE = MechanismTemplate(
    id="sn1",
    name="Nucleophile Substitution (SN1)",
    category="substitution",
    substrate_pattern="[CX4:1]([#6])([#6])[F,Cl,Br,I:2]",
    nucleophile_pattern="[O,N,S:3]",
    steps=[
        MechanismStep(
            label="Edukte",
            molecules=["[C:1]([CH3])([CH3])[Br:2]", "[OH2:3]"],
            arrows=[],
        ),
        MechanismStep(
            label="Abgangsgruppe tritt aus",
            molecules=["[C:1]([CH3])([CH3])[Br:2]"],
            arrows=[
                CurvedArrow(
                    source=(1, "bond_to", 2),
                    target=(2, "atom"),
                    style="full",
                ),
            ],
        ),
        MechanismStep(
            label="Carbokation (Intermediat)",
            molecules=["[C+:1]([CH3])([CH3])", "[Br-:2]"],
            arrows=[],
        ),
        MechanismStep(
            label="Nucleophiler Angriff",
            molecules=["[C+:1]([CH3])([CH3])", "[OH2:3]"],
            arrows=[
                CurvedArrow(
                    source=(3, "lone_pair"),
                    target=(1, "atom"),
                    style="full",
                ),
            ],
        ),
        MechanismStep(
            label="Produkt (nach Deprotonierung)",
            molecules=["[C:1]([CH3])([CH3])[OH:3]", "[Br-:2]"],
            arrows=[],
        ),
    ],
)

register(SN2_TEMPLATE)
register(SN1_TEMPLATE)
