"""Unbestimmte Stereoelemente werden gemeldet statt still gezeichnet (Etappe 4).

Anlass: Ein getipptes SMILES ohne @/@@ verliert die Stereochemie, ohne dass es
jemand merkt — das Bild zeigt dann ein unbestimmtes Isomer, und nichts im Panel
sagt das. Gezaehlt werden nur Elemente, die RDKit als `Unspecified` meldet;
ein bestimmtes Zentrum ist keine Warnung.

Alle Eingaben sind SMILES → resolve() geht nicht ins Netz; PubChem ist gemockt.
"""

import asyncio
from unittest.mock import patch

import pytest
from mcp import Client
from rdkit import Chem

from chemdraw_tool import server as srv
from chemdraw_tool.generator import find_unspecified_stereo, generate_2d, stereo_note
from chemdraw_tool.payloads import DatabasePayload, MoleculePayload

IBUPROFEN = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
GLUCOSE_OPEN = "OCC(O)C(O)C(O)C(O)C=O"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    yield tmp_path


# --- Erkennung -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("smiles", "atoms", "bonds"),
    [
        ("CC(O)CC", 1, 0),  # 2-Butanol ohne Stereo
        ("C[C@H](O)CC", 0, 0),  # bestimmt
        ("CC=CC", 0, 1),  # 2-Buten, E/Z offen
        ("C/C=C/C", 0, 0),  # (E)-2-Buten
        (IBUPROFEN, 1, 0),
        (ASPIRIN, 0, 0),
        (GLUCOSE_OPEN, 4, 0),
    ],
)
def test_counts_only_unspecified_elements(smiles, atoms, bonds):
    found = find_unspecified_stereo(Chem.MolFromSmiles(smiles))
    assert sum(w["kind"] == "atom" for w in found) == atoms
    assert sum(w["kind"] == "double_bond" for w in found) == bonds


def test_double_bond_marks_both_atoms_of_the_bond():
    (warning,) = find_unspecified_stereo(Chem.MolFromSmiles("CC=CC"))
    assert warning["kind"] == "double_bond"
    assert sorted(warning["atoms"]) == [1, 2]
    assert warning["label"]


def test_does_not_touch_the_molecule():
    """Die Erkennung laeuft neben der Zeichnung, nicht in ihr."""
    mol = generate_2d(Chem.MolFromSmiles("CC(O)CC"))
    before = Chem.MolToMolBlock(mol)
    find_unspecified_stereo(mol)
    assert Chem.MolToMolBlock(mol) == before


def test_note_names_counts_and_says_the_drawing_does_not_fix_them():
    assert stereo_note([]) == ""
    three = stereo_note(find_unspecified_stereo(Chem.MolFromSmiles("CC1CCC(C)C(O)C1")))
    assert three.startswith("3 stereocenters are unspecified")
    one = stereo_note(find_unspecified_stereo(Chem.MolFromSmiles("CC(O)CC")))
    assert one.startswith("1 stereocenter is unspecified")
    both = stereo_note(find_unspecified_stereo(Chem.MolFromSmiles("CC=CC(O)CC")))
    assert "1 stereocenter" in both and "1 double bond" in both
    assert "does not fix" in both


# --- Payload: Index zeigt auf das richtige Atom ---------------------------------


@pytest.mark.parametrize(("smiles", "expected_idx"), [("CC(O)CC", 1), (IBUPROFEN, 10)])
def test_generate_molecule_index_points_at_the_stereocenter(smiles, expected_idx):
    payload = srv.generate_molecule(smiles)
    (warning,) = payload.stereoWarnings
    assert warning.kind == "atom"
    assert warning.atoms == [expected_idx]
    atom = next(a for a in payload.atoms if a.idx == expected_idx)
    # Das markierte Atom ist das CH mit vier verschiedenen Nachbarn.
    assert (atom.el, atom.hCount) == ("C", 1)


def test_generate_molecule_double_bond_marks_the_two_alkene_carbons():
    payload = srv.generate_molecule("CC=CC")
    (warning,) = payload.stereoWarnings
    marked = [a for a in payload.atoms if a.idx in warning.atoms]
    assert [(a.el, a.hCount) for a in marked] == [("C", 1), ("C", 1)]
    assert "double bond" in payload.stereoNote


def test_specified_and_achiral_inputs_carry_no_warning():
    for smiles in ("C[C@H](O)CC", "C/C=C/C", ASPIRIN):
        payload = srv.generate_molecule(smiles)
        assert payload.stereoWarnings == []
        assert payload.stereoNote == ""


def test_glucose_open_chain_reports_four():
    payload = srv.generate_molecule(GLUCOSE_OPEN)
    assert len(payload.stereoWarnings) == 4
    assert payload.stereoNote.startswith("4 stereocenters are unspecified")


def test_abbreviated_drawing_keeps_the_note_but_drops_the_highlight():
    """Abgekuerzt fehlen dem Bild Atome — die Hervorhebung muss weg, der Satz bleibt."""
    smiles = "CC(=O)OC(C)CC"  # OAc wird zum Label, das Zentrum bleibt unbestimmt
    payload = srv.generate_molecule(smiles, abbreviate_groups=True)
    assert payload.atoms == []
    assert len(payload.stereoWarnings) == 1
    assert payload.stereoWarnings[0].atoms == []
    assert payload.stereoNote.startswith("1 stereocenter is unspecified")
    drawn_idx = {a.idx for a in payload.atoms}
    for w in payload.stereoWarnings:
        assert set(w.atoms) <= drawn_idx


def test_batch_generate_carries_warnings_per_molecule():
    result = srv.batch_generate(["CC(O)CC", ASPIRIN])
    by_name = {m.name: m for m in result.molecules}
    assert len(by_name["CC(O)CC"].stereoWarnings) == 1
    assert by_name[ASPIRIN].stereoWarnings == []


@patch("chemdraw_tool.server.pubchem_ghs", return_value={"status": "empty", "record_title": "", "sources": []})
def test_lookup_molecule_data_carries_the_same_warnings(_safety):
    payload = srv.lookup_molecule_data(IBUPROFEN)
    assert isinstance(payload, DatabasePayload)
    (warning,) = payload.stereoWarnings
    atom = next(a for a in payload.atoms if a.idx == warning.atoms[0])
    assert (atom.el, atom.hCount) == ("C", 1)
    assert payload.stereoNote.startswith("1 stereocenter is unspecified")


@pytest.mark.parametrize("field", ["stereoWarnings", "stereoNote"])
def test_both_panel_payloads_have_the_same_field(field):
    assert (
        DatabasePayload.model_fields[field].annotation
        == MoleculePayload.model_fields[field].annotation
    )


def test_note_reaches_the_model_without_a_panel():
    """Ohne Panel liest das Modell nur den Textteil der Antwort."""

    async def run():
        async with Client(srv.create_server("mvp")) as client:
            return await client.call_tool("generate_molecule", {"name_or_smiles": "CC(O)CC"})

    result = asyncio.run(run())
    text = "\n".join(getattr(b, "text", "") for b in result.content)
    assert "1 stereocenter is unspecified" in text
