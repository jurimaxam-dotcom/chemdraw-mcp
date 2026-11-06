"""Identitäts-Eval: Tautomer ≠ falscher Stoff (rifabutin, Lauf 9, 06.11.2026).

PubChem und ChEMBL führen rifabutin als verschiedene Tautomere; die
Standard-InChI führt diese Tautomerie nicht zusammen, der Lauf zählte das
als „falscher Stoff (skelett)". Gelb nur, wenn alle drei gleich sind:
Summenformel, InChI-/c-Schicht, RDKit-Kanontautomer (Chef-Vorgabe).
"""

import pytest
from rdkit import Chem

from scripts import identitaet
from tests.test_resolver import _RIFABUTIN_PC

_RIFABUTIN_REF = (  # ChEMBL444633, Referenz aus stoffe-masse.json
    "C[C@H]1/C=C/C=C(\\C(=O)NC2=C3C(=NC4(N3)CCN(CC4)CC(C)C)C5=C6C(=C(C(=C5C2=O)O)C)"
    "O[C@@](C6=O)(O/C=C/[C@@H]([C@H]([C@H]([C@@H]([C@@H]([C@@H]([C@H]1O)C)O)C)"
    "OC(=O)C)C)OC)C)/C"
)


def _eintrag(referenz: str) -> dict:
    return {
        "eingabe": "x",
        "inchikey": Chem.MolToInchiKey(Chem.MolFromSmiles(referenz)),
        "smiles_referenz": referenz,
    }


def _pruefe(monkeypatch, erhalten: str, referenz: str) -> dict:
    monkeypatch.setattr(identitaet, "resolve", lambda e: (erhalten, Chem.MolFromSmiles(erhalten)))
    return identitaet.pruefe(_eintrag(referenz))


def test_tautomer_of_the_reference_is_yellow(monkeypatch):
    ergebnis = _pruefe(monkeypatch, _RIFABUTIN_PC, _RIFABUTIN_REF)
    assert (ergebnis["status"], ergebnis["art"]) == (identitaet.GELB, "tautomer")


@pytest.mark.parametrize("erhalten, referenz", [
    ("CCCO", "CC(C)O"),                  # gleiche Formel, andere /c
    ("C1=CC=CCC1", "C1=CCC=CC1"),        # gleiche Formel + /c, kein Tautomer
])
def test_constitutional_isomer_stays_red(monkeypatch, erhalten, referenz):
    ergebnis = _pruefe(monkeypatch, erhalten, referenz)
    assert (ergebnis["status"], ergebnis["art"]) == (identitaet.ROT, "skelett")


def test_tautomers_are_counted_apart_from_green_and_other_yellow():
    ergebnisse = [
        {"status": identitaet.GRUEN},
        {"status": identitaet.GELB, "art": "tautomer"},
        {"status": identitaet.GELB, "text": "Quelle weg (partial)"},
        {"status": identitaet.ROT},
    ]
    assert identitaet.zaehlung(ergebnisse) == (
        "1 grün · 1 gelb (Quelle/Luecke) · 1 gelb (Tautomer) · 0 gelb (E/Z fehlt) · "
        "1 rot (falscher Stoff/Fehler)"
    )
