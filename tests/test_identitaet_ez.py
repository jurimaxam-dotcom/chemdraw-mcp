"""Identitäts-Eval: fehlende E/Z-Angabe ≠ falscher Stoff (Sulfasalazin, 06.11.2026).

PubChem führt Sulfasalazin (CID 5339) ohne E/Z an der Azo-Doppelbindung;
ChEMBL, ChEBI, FDA GSRS und Wikidata führen die E-Form. Gelb ('ez_fehlt')
nur, wenn der erste Key-Block gleich ist, das Ergebnis KEINE Stereoschicht
trägt und die Referenz als einzige Stereoschicht /b hat (Chef-Entscheid).
Fehlt stattdessen Zentrums- oder Ringstereo, bleibt es rot: Racemat statt
R-Adrenalin, cis/trans-offene Tranexamsäure sind echte Fehler.
"""

import pytest
from rdkit import Chem

from scripts import identitaet

_SULFASALAZIN_E = "C1=CC=NC(=C1)NS(=O)(=O)C2=CC=C(C=C2)/N=N/C3=CC=C(C(=C3)C(=O)O)O"
_SULFASALAZIN_OHNE = "C1=CC=NC(=C1)NS(=O)(=O)C2=CC=C(C=C2)N=NC3=CC=C(C(=C3)C(=O)O)O"


def _pruefe(monkeypatch, erhalten: str, referenz: str) -> dict:
    monkeypatch.setattr(identitaet, "resolve", lambda e: (erhalten, Chem.MolFromSmiles(erhalten)))
    return identitaet.pruefe({
        "eingabe": "x",
        "inchikey": Chem.MolToInchiKey(Chem.MolFromSmiles(referenz)),
        "smiles_referenz": referenz,
    })


def test_missing_double_bond_geometry_is_yellow(monkeypatch):
    ergebnis = _pruefe(monkeypatch, _SULFASALAZIN_OHNE, _SULFASALAZIN_E)
    assert (ergebnis["status"], ergebnis["art"]) == (identitaet.GELB, "ez_fehlt")


@pytest.mark.parametrize("erhalten, referenz", [
    ("CNCC(O)C1=CC(=C(C=C1)O)O", "CNC[C@@H](C1=CC(=C(C=C1)O)O)O"),       # Adrenalin: Racemat statt R
    ("C1CC(CCC1CN)C(=O)O", "C1C[C@@H](CC[C@H]1CN)C(=O)O"),               # Tranexamsäure: cis/trans offen
    ("C/C=C/C(O)CC", "C/C=C/[C@H](O)CC"),                                 # E da, Zentrum fehlt
    ("CC=CC(O)CC", "C/C=C/[C@H](O)CC"),                                   # E UND Zentrum fehlen
])
def test_missing_other_stereo_stays_red(monkeypatch, erhalten, referenz):
    ergebnis = _pruefe(monkeypatch, erhalten, referenz)
    assert (ergebnis["status"], ergebnis["art"]) == (identitaet.ROT, "stereo")


def test_wrong_double_bond_geometry_stays_red(monkeypatch):
    z = "C1=CC=NC(=C1)NS(=O)(=O)C2=CC=C(C=C2)/N=N\\C3=CC=C(C(=C3)C(=O)O)O"
    ergebnis = _pruefe(monkeypatch, z, _SULFASALAZIN_E)
    assert (ergebnis["status"], ergebnis["art"]) == (identitaet.ROT, "stereo")


def test_ez_counted_on_its_own_line():
    ergebnisse = [
        {"status": identitaet.GRUEN},
        {"status": identitaet.GELB, "art": "ez_fehlt"},
        {"status": identitaet.GELB, "art": "tautomer"},
        {"status": identitaet.ROT},
    ]
    assert identitaet.zaehlung(ergebnisse) == (
        "1 grün · 0 gelb (Quelle/Luecke) · 1 gelb (Tautomer) · 1 gelb (E/Z fehlt) · "
        "1 rot (falscher Stoff/Fehler)"
    )
