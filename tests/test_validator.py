"""Tests for chemdraw_tool.validator — input + round-trip validation."""

from rdkit import Chem

from chemdraw_tool.cdxml_writer import mol_to_cdxml
from chemdraw_tool.generator import generate_2d
from chemdraw_tool.validator import (
    Severity,
    ValidationReport,
    validate_input,
    validate_roundtrip,
)


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, f"Bad test SMILES: {smiles}"
    return generate_2d(mol)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestValidateInput:
    def test_valid_simple(self):
        mol = _make_mol("CCO")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)

    def test_none_mol(self):
        issues = validate_input(None)
        assert any(i.severity == Severity.ERROR for i in issues)

    def test_no_conformer(self):
        mol = Chem.MolFromSmiles("CCO")
        issues = validate_input(mol)
        assert any(
            "conformer" in i.message.lower() or "2d" in i.message.lower()
            for i in issues
            if i.severity == Severity.ERROR
        )

    def test_valence_violation(self):
        """Pentavalent carbon — chemically impossible."""
        mol = Chem.RWMol()
        c = mol.AddAtom(Chem.Atom(6))
        for _ in range(5):
            h = mol.AddAtom(Chem.Atom(1))
            mol.AddBond(c, h, Chem.BondType.SINGLE)
        issues = validate_input(mol.GetMol())
        assert any(i.severity == Severity.ERROR for i in issues)

    def test_aromatic_with_substituent(self):
        """Aspirin — aromatic ring + ester + carboxylic acid."""
        mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)

    def test_stereocenter(self):
        """L-Alanine with defined chirality."""
        mol = _make_mol("N[C@@H](C)C(=O)O")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)

    def test_cis_trans(self):
        """cis-2-Butene — E/Z isomerism."""
        mol = _make_mol(r"C/C=C\C")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)

    def test_charged_molecule(self):
        """Sodium acetate — charged."""
        mol = _make_mol("[Na+].[O-]C(C)=O")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)

    def test_heteroaromatic(self):
        """Imidazole — heteroaromatic."""
        mol = _make_mol("c1c[nH]cn1")
        issues = validate_input(mol)
        assert all(i.severity != Severity.ERROR for i in issues)


# ---------------------------------------------------------------------------
# Round-trip validation
# ---------------------------------------------------------------------------


class TestValidateRoundtrip:
    def _roundtrip(self, smiles: str) -> ValidationReport:
        mol = _make_mol(smiles)
        cdxml = mol_to_cdxml(mol)
        return validate_roundtrip(mol, cdxml)

    def test_ethanol(self):
        report = self._roundtrip("CCO")
        assert report.valid

    def test_aspirin(self):
        """Aromatic + substituents — the kekulize hotspot."""
        report = self._roundtrip("CC(=O)Oc1ccccc1C(=O)O")
        assert report.valid

    def test_alanine_stereo(self):
        """Stereocenter must survive round-trip."""
        report = self._roundtrip("N[C@@H](C)C(=O)O")
        assert report.valid

    def test_cis_butene(self):
        """Cis/trans double bond."""
        report = self._roundtrip(r"C/C=C\C")
        assert report.valid

    def test_sodium_acetate(self):
        """Charged / ionic molecule."""
        report = self._roundtrip("[Na+].[O-]C(C)=O")
        assert report.valid

    def test_pyridine(self):
        """Heteroaromatic."""
        report = self._roundtrip("c1ccncc1")
        assert report.valid

    def test_imidazole(self):
        report = self._roundtrip("c1c[nH]cn1")
        assert report.valid

    def test_naphthalene(self):
        """Fused aromatic rings."""
        report = self._roundtrip("c1ccc2ccccc2c1")
        assert report.valid

    def test_caffeine(self):
        """Complex heteroaromatic with methyls."""
        report = self._roundtrip("Cn1c(=O)c2c(ncn2C)n(C)c1=O")
        assert report.valid

    def test_atom_count_mismatch_detected(self):
        """Corrupted CDXML with a node removed should fail."""
        mol = _make_mol("CCO")
        cdxml = mol_to_cdxml(mol)
        # Remove first <n .../> node from CDXML to simulate corruption
        import re

        corrupted = re.sub(r"<n [^/]*/>\n?", "", cdxml, count=1)
        report = validate_roundtrip(mol, corrupted)
        assert not report.valid

    def test_report_contains_checks(self):
        """Report should list which checks were performed."""
        report = self._roundtrip("CCO")
        assert len(report.checks) > 0
        assert any("atom" in c.lower() or "inchi" in c.lower() for c in report.checks)

    def test_invalid_xml(self):
        """Completely broken XML should produce error, not crash."""
        mol = _make_mol("CCO")
        report = validate_roundtrip(mol, "<not>valid cdxml")
        assert not report.valid
