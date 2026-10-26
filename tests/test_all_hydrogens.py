"""Alle H-Atome zeigen (Grundlagen, Etappe 1).

Das Panel schaltet zwischen Skelettformel und Formel mit allen H-Atomen um.
Der Server liefert dafür ein zweites SVG mit eigener Atomliste, damit der
Klick lokal bleibt. Die Skelettformel (`svg`) ändert sich dadurch nicht —
die Golden-SVGs bleiben gültig.

Alle Eingaben sind SMILES → resolve() geht nicht ins Netz; PubChem ist gemockt.
"""

import pytest
from rdkit import Chem

from chemdraw_tool import server as srv
from chemdraw_tool.generator import generate_2d
from chemdraw_tool.svg_renderer import render_svg

ETHANOL = "CCO"
IBUPROFEN_S = "CC(C)Cc1ccc(cc1)[C@H](C)C(=O)O"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    yield tmp_path


def test_payload_carries_a_second_drawing_with_all_hydrogens():
    payload = srv.generate_molecule(ETHANOL)
    assert "<svg" in payload.svgAllH
    assert payload.svgAllH != payload.svg
    # Ethanol: 3 Schweratome + 6 H
    assert len(payload.atomsAllH) == 9
    assert sum(a.el == "H" for a in payload.atomsAllH) == 6


def test_heavy_atom_indices_survive_so_highlights_stay_valid():
    payload = srv.generate_molecule(ETHANOL)
    heavy = [(a.idx, a.el) for a in payload.atoms]
    assert [(a.idx, a.el) for a in payload.atomsAllH[: len(heavy)]] == heavy


def test_tooltip_still_counts_hydrogens_on_heavy_atoms():
    payload = srv.generate_molecule(ETHANOL)
    counts = [a.hCount for a in payload.atomsAllH[:3]]
    assert counts == [3, 2, 1]


def test_skeletal_drawing_is_unchanged():
    payload = srv.generate_molecule(ETHANOL)
    mol = generate_2d(Chem.MolFromSmiles(ETHANOL))
    assert payload.svg == render_svg(mol, fill_container=True)


def test_stereocenter_gets_exactly_one_hydrogen():
    payload = srv.generate_molecule(IBUPROFEN_S, annotate_stereo=True)
    # Ibuprofen C13H18O2: 18 H, keins doppelt am Stereozentrum
    assert sum(a.el == "H" for a in payload.atomsAllH) == 18


def test_abbreviated_drawing_has_no_hydrogen_view():
    payload = srv.generate_molecule("CC(=O)Oc1ccccc1C(=O)O", abbreviate_groups=True)
    assert payload.svgAllH == ""
    assert payload.atomsAllH == []
