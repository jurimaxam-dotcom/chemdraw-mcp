"""Mechanism template data classes and SMARTS validation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CurvedArrow:
    source: tuple
    target: tuple
    style: str  # "full" (2e⁻) | "half" (1e⁻)


@dataclass
class MechanismStep:
    label: str
    molecules: list[str]
    arrows: list[CurvedArrow]
    is_transition_state: bool = False
    partial_bonds: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class MechanismTemplate:
    id: str
    name: str
    category: str
    substrate_pattern: str
    nucleophile_pattern: str | None
    steps: list[MechanismStep]


def validate_substrates(template: MechanismTemplate, smiles_list: list[str]) -> bool:
    """Check if substrates match the template SMARTS patterns via RDKit."""
    from rdkit import Chem

    substrate_pat = Chem.MolFromSmarts(template.substrate_pattern)
    if substrate_pat is None:
        raise ValueError(
            f"Ungültiges SMARTS-Substrat-Pattern im Template '{template.id}': "
            f"{template.substrate_pattern!r}"
        )

    matched_substrate = False
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        if mol.HasSubstructMatch(substrate_pat):
            matched_substrate = True
            break

    if not matched_substrate:
        return False

    if template.nucleophile_pattern is not None:
        nuc_pat = Chem.MolFromSmarts(template.nucleophile_pattern)
        if nuc_pat is None:
            raise ValueError(
                f"Ungültiges SMARTS-Nucleophil-Pattern im Template "
                f"'{template.id}': {template.nucleophile_pattern!r}"
            )
        for smi in smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol and mol.HasSubstructMatch(nuc_pat):
                return True
        return False

    return True
