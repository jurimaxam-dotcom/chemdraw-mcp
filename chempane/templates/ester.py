"""Ester mechanism templates (Fischer esterification).

Die Schritte sind der Substratweg (mechanism_substrate) mit den Beispiel-Substraten — Vorlage und
eigene Moleküle zeigen dieselbe Folge (Etappe E, 05.11.2026: Protonentransfer, Wasser als OH₂⁺).
"""

from chempane.mechanism import MechanismTemplate
from chempane.mechanism_substrate import build_steps
from chempane.templates import register

FISCHER_ESTER_TEMPLATE = MechanismTemplate(
    id="fischer_ester",
    name="Fischer esterification",
    example="acetic acid + methanol",
    category="ester",
    substrate_pattern="[CX3:1](=[OX1:2])[OX2H1:3]",
    nucleophile_pattern="[OX2H1:4][#6]",
    steps=build_steps("fischer_ester", ["CC(=O)O", "CO"]),
)

register(FISCHER_ESTER_TEMPLATE)
