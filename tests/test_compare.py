"""Tests für den Molekül-Vergleich (MCS-Differenz-Highlights, Panel-Grid).

Spec (2026-06-11): 2-4 Strukturen nebeneinander; das gemeinsame Gerüst
(Maximum Common Substructure) bleibt neutral, die UNTERSCHIEDE werden
hervorgehoben — didaktisch ist die Differenz das Lernziel ("Was
unterscheidet Ibuprofen von Naproxen?").
"""

from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.image_export import (
    PNG_MAGIC,
    _mcs_diff_highlights,
    render_comparison_png,
    render_comparison_svg,
)


def _mols(*smiles_list):
    out = []
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        AllChem.Compute2DCoords(mol)
        out.append(mol)
    return out


def test_diff_highlights_mark_only_the_difference():
    """Toluol vs. Chlorbenzol: MCS ist der Benzolring — markiert wird je
    genau der Substituent (Atom 0 in beiden SMILES)."""
    mols = _mols("Cc1ccccc1", "Clc1ccccc1")
    atom_hl, bond_hl = _mcs_diff_highlights(mols)
    assert atom_hl == [[0], [0]]
    # die Bindung zum Substituenten gehört zur Differenz
    assert all(len(b) == 1 for b in bond_hl)


def test_identical_molecules_have_no_highlights():
    mols = _mols("CCO", "CCO")
    atom_hl, bond_hl = _mcs_diff_highlights(mols)
    assert atom_hl == [[], []]
    assert bond_hl == [[], []]


def test_subset_molecule_highlights_nothing_on_the_smaller():
    """Ethanol ⊂ Propanol: beim Ethanol ist nichts verschieden, beim
    Propanol genau ein C."""
    mols = _mols("CCO", "CCCO")
    atom_hl, _ = _mcs_diff_highlights(mols)
    assert atom_hl[0] == []
    assert len(atom_hl[1]) == 1


def test_render_comparison_png_and_svg():
    mols = _mols("Cc1ccccc1", "Clc1ccccc1", "Oc1ccccc1")
    png = render_comparison_png(mols, labels=["Toluene", "Chlorobenzene", "Phenol"])
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    svg = render_comparison_svg(mols, labels=["Toluene", "Chlorobenzene", "Phenol"])
    assert "<svg" in svg
    # Highlights rendern als gefüllte Ellipsen hinter den Atomen
    assert "<ellipse" in svg
