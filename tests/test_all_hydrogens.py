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


def all_h(smiles, **kw):
    """Was das Panel beim ersten Klick auf „All H“ holt."""
    payload = srv.generate_molecule(smiles, **kw)
    return srv.generate_molecule(**payload.viewRequest, view="all_h")


def test_payload_only_announces_the_hydrogen_view():
    payload = srv.generate_molecule(ETHANOL)
    assert "all_h" in payload.views
    assert payload.viewRequest["name_or_smiles"] == ETHANOL
    assert "svgAllH" not in payload.model_dump()


def test_hydrogen_view_is_fetched_on_click(_isolate):
    view = all_h(ETHANOL)
    assert "<svg" in view.viewSvg
    assert view.viewSvg != view.svg == srv.generate_molecule(ETHANOL).svg
    # Ethanol: 3 Schweratome + 6 H
    assert len(view.viewAtoms) == 9
    assert sum(a.el == "H" for a in view.viewAtoms) == 6
    assert view.files == {}


def test_heavy_atom_indices_survive_so_highlights_stay_valid():
    payload = srv.generate_molecule(ETHANOL)
    heavy = [(a.idx, a.el) for a in payload.atoms]
    assert [(a.idx, a.el) for a in all_h(ETHANOL).viewAtoms[: len(heavy)]] == heavy


def test_tooltip_still_counts_hydrogens_on_heavy_atoms():
    assert [a.hCount for a in all_h(ETHANOL).viewAtoms[:3]] == [3, 2, 1]


def test_skeletal_drawing_is_unchanged():
    payload = srv.generate_molecule(ETHANOL)
    mol = generate_2d(Chem.MolFromSmiles(ETHANOL))
    assert payload.svg == render_svg(mol, fill_container=True)


def test_stereocenter_gets_exactly_one_hydrogen():
    view = all_h(IBUPROFEN_S, annotate_stereo=True)
    # Ibuprofen C13H18O2: 18 H, keins doppelt am Stereozentrum
    assert sum(a.el == "H" for a in view.viewAtoms) == 18


def test_view_request_repeats_the_drawing_options():
    payload = srv.generate_molecule(IBUPROFEN_S, annotate_stereo=True, render_style="compact")
    assert payload.viewRequest["annotate_stereo"] is True
    assert payload.viewRequest["render_style"] == "compact"


def test_abbreviated_drawing_has_no_hydrogen_view():
    payload = srv.generate_molecule("CC(=O)Oc1ccccc1C(=O)O", abbreviate_groups=True)
    assert "all_h" not in payload.views


def test_molecule_answer_stays_small():
    """Jay 26.10.: Ibuprofen war 29,4 KB, das Modell liest alles mit."""
    import json

    payload = srv.generate_molecule(IBUPROFEN_S)
    assert len(json.dumps(payload.model_dump(exclude_defaults=True))) < 15_000
