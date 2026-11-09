"""„X zwitterion“ / „X Zwitterion“ (E4, 09.11.2026).

Gemessen vorher:
  - "alanine zwitterion": PubChem führt den Namen beim Racemat-Eintrag
    (CC(C(=O)[O-])[NH3+]) — „alanine“ allein ist dort L-Alanin. Stereo weg.
  - "Alanin Zwitterion": OPSIN und PubChem kennen ihn nicht, english_variant
    macht daraus „Alanine Zwitterione“ → not_found.
  - "Ala zwitterion": PubChem liefert das Tripeptid Ala-Leu-Ala als Zwitterion.
Lösung: Zwitterion heißt „Grundname auflösen, dann α-NH2 → NH3+ und α-COOH →
COO-“. Die Netzquellen sind hier Attrappen mit genau diesen Antworten.
"""

import pytest
from rdkit import Chem

from chemdraw_tool import resolver
from chemdraw_tool.resolver import NameResolutionError, resolve

L_ALA = "C[C@H](N)C(=O)O"
L_ALA_ZWITTERION = Chem.CanonSmiles("C[C@H]([NH3+])C(=O)[O-]")

OPSIN = {"alanine": L_ALA, "Alanin": L_ALA, "L-alanine": L_ALA, "glycine": "NCC(=O)O"}
PUBCHEM = {
    "alanine": L_ALA,
    "alanine zwitterion": "CC(C(=O)[O-])[NH3+]",
    "L-alanine zwitterion": "C[C@@H](C(=O)[O-])[NH3+]",
    "glycine zwitterion": "C(C(=O)[O-])[NH3+]",
    "Ala": L_ALA,
    "Ala zwitterion": "C[C@@H](C(=O)N[C@@H](CC(C)C)C(=O)N[C@@H](C)C(=O)[O-])[NH3+]",
    "lysine": "NCCCC[C@H](N)C(=O)O",
    "proline": "OC(=O)[C@@H]1CCCN1",
    "ethanol": "CCO",
    "cystine": "N[C@@H](CSSC[C@H](N)C(=O)O)C(=O)O",
}


@pytest.fixture(autouse=True)
def _sources(monkeypatch):
    resolver.resolve_name.cache_clear()
    # OPSIN liest Namen ohne Rücksicht auf Groß-/Kleinschreibung.
    opsin = {key.casefold(): value for key, value in OPSIN.items()}
    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: opsin.get(name.casefold()))
    monkeypatch.setattr(
        resolver, "_opsin_checked", lambda name, smiles, report: smiles
    )

    def pubchem(name, report):
        if name in PUBCHEM:
            return PUBCHEM[name]
        report.append(resolver._Attempt("PubChem", resolver._NOT_FOUND, "name unknown"))
        return None

    def nci(name, report):
        report.append(resolver._Attempt("NCI CIR", resolver._NOT_FOUND, "name unknown"))
        return None

    monkeypatch.setattr(resolver, "_pubchem_lookup", pubchem)
    monkeypatch.setattr(
        resolver, "_pubchem_checked", lambda name, smiles, report: (smiles, name)
    )
    monkeypatch.setattr(resolver, "_nci_cir_lookup", nci)
    yield
    resolver.resolve_name.cache_clear()


def _canon(smiles):
    return Chem.CanonSmiles(smiles)


@pytest.mark.parametrize(
    "name",
    [
        "alanine zwitterion",
        "Alanin Zwitterion",
        "L-alanine zwitterion",
        "Ala zwitterion",
        "alanine-zwitterion",
        "ALANINE ZWITTERION",
    ],
)
def test_alanine_zwitterion_keeps_l(name):
    smiles, _ = resolve(name)
    assert _canon(smiles) == L_ALA_ZWITTERION


def test_glycine_zwitterion_is_unchanged():
    smiles, _ = resolve("glycine zwitterion")
    assert _canon(smiles) == _canon("[NH3+]CC(=O)[O-]")


def test_only_the_alpha_groups_are_charged():
    smiles, _ = resolve("lysine zwitterion")
    assert _canon(smiles) == _canon("NCCCC[C@H]([NH3+])C(=O)[O-]")
    smiles, _ = resolve("proline zwitterion")
    assert _canon(smiles) == _canon("[O-]C(=O)[C@@H]1CCC[NH2+]1")


@pytest.mark.parametrize("name", ["ethanol zwitterion", "cystine zwitterion"])
def test_without_exactly_one_alpha_amino_acid_nothing_is_invented(name):
    """Kein α-Aminosäure-Motiv (oder zwei) → die alte Kaskade wie bisher."""
    with pytest.raises(NameResolutionError) as exc:
        resolve(name)
    assert exc.value.kind == "not_found"
