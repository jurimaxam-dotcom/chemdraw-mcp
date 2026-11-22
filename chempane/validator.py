"""Validation for molecular input and CDXML round-trip integrity."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from lxml import etree
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.inchi import MolToInchi

logger = logging.getLogger(__name__)


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    severity: Severity
    message: str
    check: str


@dataclass
class ValidationReport:
    valid: bool
    issues: list[Issue] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_input(mol: Chem.Mol | None) -> list[Issue]:
    issues: list[Issue] = []

    if mol is None:
        issues.append(Issue(Severity.ERROR, "Mol object is None", "mol_exists"))
        return issues

    # Valency / sanitization
    try:
        Chem.SanitizeMol(
            Chem.RWMol(mol),
            sanitizeOps=(
                Chem.SanitizeFlags.SANITIZE_FINDRADICALS
                | Chem.SanitizeFlags.SANITIZE_SETAROMATICITY
                | Chem.SanitizeFlags.SANITIZE_SETCONJUGATION
                | Chem.SanitizeFlags.SANITIZE_SETHYBRIDIZATION
                | Chem.SanitizeFlags.SANITIZE_PROPERTIES
            ),
        )
    except Exception as e:
        issues.append(Issue(Severity.ERROR, f"Sanitization failed: {e}", "sanitize"))

    # Conformer (2D coordinates)
    try:
        mol.GetConformer()
    except ValueError:
        issues.append(
            Issue(
                Severity.ERROR,
                "No 2D conformer — call generate_2d() before writing",
                "conformer",
            )
        )

    # Basic counts
    if mol.GetNumAtoms() == 0:
        issues.append(Issue(Severity.ERROR, "Molecule has 0 atoms", "atom_count"))

    if mol.GetNumBonds() == 0 and mol.GetNumAtoms() > 1:
        issues.append(
            Issue(
                Severity.WARNING,
                "Molecule has atoms but no bonds (salt/ion pair?)",
                "bond_count",
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Round-trip validation
# ---------------------------------------------------------------------------


def validate_roundtrip(mol: Chem.Mol, cdxml_str: str) -> ValidationReport:
    issues: list[Issue] = []
    checks: list[str] = []

    # --- XML well-formedness ---
    checks.append("xml_parse")
    try:
        root = etree.fromstring(cdxml_str.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        issues.append(Issue(Severity.ERROR, f"Invalid XML: {e}", "xml_parse"))
        return ValidationReport(valid=False, issues=issues, checks=checks)

    # --- Node/Bond count parity ---
    xml_nodes = root.findall(".//n")
    xml_bonds = root.findall(".//b")
    expected_atoms = mol.GetNumAtoms()
    expected_bonds = mol.GetNumBonds()

    checks.append("atom_count_parity")
    if len(xml_nodes) != expected_atoms:
        issues.append(
            Issue(
                Severity.ERROR,
                f"Atom count mismatch: CDXML has {len(xml_nodes)}, expected {expected_atoms}",
                "atom_count_parity",
            )
        )

    checks.append("bond_count_parity")
    if len(xml_bonds) != expected_bonds:
        issues.append(
            Issue(
                Severity.ERROR,
                f"Bond count mismatch: CDXML has {len(xml_bonds)}, expected {expected_bonds}",
                "bond_count_parity",
            )
        )

    # --- All nodes have coordinates ---
    checks.append("coordinates_present")
    missing_coords = [n.get("id", "?") for n in xml_nodes if "p" not in n.attrib]
    if missing_coords:
        issues.append(
            Issue(
                Severity.ERROR,
                f"Nodes without coordinates: IDs {missing_coords}",
                "coordinates_present",
            )
        )

    # --- Orphan bonds (reference non-existent node IDs) ---
    checks.append("bond_references")
    node_ids = {n.get("id") for n in xml_nodes}
    for b in xml_bonds:
        for attr in ("B", "E"):
            ref = b.get(attr)
            if ref and ref not in node_ids:
                issues.append(
                    Issue(
                        Severity.ERROR,
                        f"Bond {b.get('id', '?')} references non-existent node {ref}",
                        "bond_references",
                    )
                )

    # --- InChI round-trip (structural identity) ---
    checks.append("inchi_roundtrip")
    try:
        parsed_mols = Chem.MolsFromCDXML(cdxml_str)
        if not parsed_mols:
            issues.append(
                Issue(
                    Severity.WARNING,
                    "RDKit could not parse CDXML back (MolsFromCDXML returned empty)",
                    "inchi_roundtrip",
                )
            )
        else:
            original_inchi = MolToInchi(mol)
            for i, parsed_mol in enumerate(parsed_mols):
                if parsed_mol is None:
                    issues.append(
                        Issue(
                            Severity.WARNING,
                            f"Fragment {i} parsed as None",
                            "inchi_roundtrip",
                        )
                    )
                    continue
                parsed_inchi = MolToInchi(parsed_mol)
                if original_inchi != parsed_inchi:
                    issues.append(
                        Issue(
                            Severity.ERROR,
                            f"InChI mismatch — original: {original_inchi}, "
                            f"parsed: {parsed_inchi}",
                            "inchi_roundtrip",
                        )
                    )

    except Exception as e:
        issues.append(
            Issue(
                Severity.WARNING,
                f"InChI round-trip check failed: {e}",
                "inchi_roundtrip",
            )
        )

    # --- Molecular formula parity ---
    checks.append("formula_parity")
    try:
        if parsed_mols and parsed_mols[0] is not None:
            orig_formula = Descriptors.MolecularFormula(mol)
            parsed_formula = Descriptors.MolecularFormula(parsed_mols[0])
            if orig_formula != parsed_formula:
                issues.append(
                    Issue(
                        Severity.ERROR,
                        f"Formula mismatch — original: {orig_formula}, "
                        f"parsed: {parsed_formula}",
                        "formula_parity",
                    )
                )
    except Exception:
        pass

    has_error = any(i.severity == Severity.ERROR for i in issues)
    return ValidationReport(valid=not has_error, issues=issues, checks=checks)
