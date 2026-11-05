"""SN1 and SN2 mechanism templates.

Die Schritte sind der Substratweg (mechanism_substrate) mit den Beispiel-Substraten — Vorlage und
eigene Moleküle laufen durch dasselbe verankerte Layout. Die alte SN2-Vorlage lief über
stabilize_sequence und dehnte die Produkt-C–O-Bindung auf 3,4 Bindungslängen (Befund 05.11.2026).
"""

from chemdraw_tool.mechanism import MechanismTemplate
from chemdraw_tool.mechanism_substrate import build_steps
from chemdraw_tool.templates import register

SN2_TEMPLATE = MechanismTemplate(
    id="sn2",
    name="Nucleophilic Substitution (SN2)",
    example="bromomethane + hydroxide",
    category="substitution",
    substrate_pattern="[C:1][F,Cl,Br,I:2]",
    nucleophile_pattern="[O,N,S:3]",
    steps=build_steps("sn2", ["CBr", "[OH-]"]),
)

SN1_TEMPLATE = MechanismTemplate(
    id="sn1",
    name="Nucleophilic Substitution (SN1)",
    example="2-bromo-2-methylpropane + water",
    category="substitution",
    substrate_pattern="[CX4:1]([#6])([#6])[F,Cl,Br,I:2]",
    nucleophile_pattern="[O,N,S:3]",
    steps=build_steps("sn1", ["CC(C)(C)Br", "O"]),
)

register(SN2_TEMPLATE)
register(SN1_TEMPLATE)
