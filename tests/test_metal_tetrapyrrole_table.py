"""Feste Strukturtabelle für Metall-Tetrapyrrole im Resolver (E11, 10.11.2026).

PubChem beantwortete „heme b“ und „Fe-coproporphyrin III“ zeitweise mit
anderen Datensätzen (Ferriheme b, neutrales Fe); „12,18-didecarboxysiroheme“
findet PubChem unter dem Namen nur als Anion. Die Identität darf nicht an
PubChems Tagesform hängen: eine kuratierte lokale Tabelle im Resolver,
einheitlich geschrieben (COOH, Fe²⁺ mit zwei N⁻ — PubChems Säureform von Häm).

Alle Referenzen hier sind gemessen, nicht aus dem Gedächtnis: InChIKeys aus
PubChem (CID im Kommentar). Läuft ohne Netz.
"""

from __future__ import annotations

import pytest
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

from chemdraw_tool import resolver
from chemdraw_tool.generator import coordination_drawing, generate_2d
from chemdraw_tool.resolver import resolve


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    resolver.resolve_name.cache_clear()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Netzquelle gefragt")

    for source in ("_opsin_lookup", "_pubchem_lookup", "_nci_cir_lookup"):
        monkeypatch.setattr(resolver, source, forbidden)
    yield
    resolver.resolve_name.cache_clear()


# InChIKey je Stoff — Quelle im Kommentar.
HEME_B = "KABFMIBPWCXCRK-UHFFFAOYSA-L"  # PubChem CID 4973 „Heme b“
SIROHEME = "DLKSSIHHLYNIKN-QIISWYHFSA-L"  # PubChem CID 439303
# Abgeleitet aus CID 91820468 (Anion), s. test_didecarboxysiroheme_*; PubChem
# führt die Säureform als CID 134694609 mit demselben Schlüssel (abgerufen
# 10.11.2026). CID 137349829 („12,18-Didecarboxy-Siroheme“) ist ein anderer
# Datensatz (JJIIPBCQUZPJAW-XOLYYWOLSA-L, andere Stereoschicht) — nicht die Struktur aus CID 439303.
DIDECARBOXYSIROHEME = "JJIIPBCQUZPJAW-MQNDWNIASA-L"
FE_COPRO_III = "SXDINBXHOHHTMY-UHFFFAOYSA-L"  # PubChem CID 447356 = CID 42626838 „Coproheme III“
HEME_D1 = "YTCKFKAUGWIMPJ-WVLIHFOGSA-L"  # PubChem CID 6438545 (dort mit 4 [H+])
HEMIN = "BTIJJDXEELBZFS-UHFFFAOYSA-K"  # PubChem CID 455658

NAMES = {
    HEME_B: ("heme b", "heme", "Häm", "Häm b", "haem", "protoheme", "Heme B"),
    SIROHEME: ("siroheme", "Sirohäm", "sirohaem"),
    DIDECARBOXYSIROHEME: (
        "12,18-didecarboxysiroheme",
        "didecarboxysiroheme",
        "12,18-Didecarboxysirohäm",
    ),
    FE_COPRO_III: (
        "Fe-coproporphyrin III",
        "iron-coproporphyrin III",
        "coproheme",
        "coproheme III",
        "Coprohäm",
    ),
    HEME_D1: ("heme d1", "Häm d1"),
    HEMIN: ("hemin", "Hämin"),
}
CASES = [(name, key) for key, names in NAMES.items() for name in names]


@pytest.mark.parametrize(("name", "key"), CASES)
def test_table_names_resolve_offline_to_the_fixed_structure(name, key):
    smiles, mol = resolve(name)
    assert Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)) == Chem.MolToInchiKey(mol) == key


def test_near_names_still_go_to_the_cascade():
    """Nur exakte ganze Namen: „heme oxygenase“ ist ein Enzym, kein Häm."""
    for name in ("heme oxygenase", "heme a", "protoporphyrin IX"):
        with pytest.raises(AssertionError, match="Netzquelle"):
            resolve(name)


FE2_ENTRIES = ("siroheme", "12,18-didecarboxysiroheme", "Fe-coproporphyrin III", "heme b")


@pytest.mark.parametrize("name", FE2_ENTRIES + ("heme d1",))
def test_one_notation_for_all_fe2_entries(name):
    """COOH statt COO⁻, Fe²⁺ mit genau zwei N⁻, keine losen Protonen."""
    _, mol = resolve(name)
    charges = [(a.GetSymbol(), a.GetFormalCharge()) for a in mol.GetAtoms() if a.GetFormalCharge()]
    assert sorted(charges) == [("Fe", 2), ("N", -1), ("N", -1)]


@pytest.mark.parametrize("name", FE2_ENTRIES + ("heme d1",))
def test_fe2_entries_are_drawn_alike(name):
    """Zwei Striche, zwei Pfeile — die Einträge sehen nebeneinander gleich aus."""
    mol = generate_2d(resolve(name)[1])
    drawn = coordination_drawing(mol)
    added = [
        str(b.GetBondType())
        for b in drawn.GetBonds()
        if mol.GetBondBetweenAtoms(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) is None
    ]
    assert sorted(added) == ["DATIVE", "DATIVE", "SINGLE", "SINGLE"]
    assert not [a for a in drawn.GetAtoms() if a.GetFormalCharge()]


# --- Summenformeln: Unterschiede zwischen den Einträgen ------------------------

def _counts(name):
    mol = Chem.AddHs(resolve(name)[1])
    out: dict[str, int] = {}
    for a in mol.GetAtoms():
        out[a.GetSymbol()] = out.get(a.GetSymbol(), 0) + 1
    return out


def _minus(a, b):
    keys = set(a) | set(b)
    return {k: a.get(k, 0) - b.get(k, 0) for k in keys if a.get(k, 0) - b.get(k, 0)}


def test_didecarboxysiroheme_differs_from_siroheme_by_two_co2():
    """Methyl statt Carboxymethyl an C12 und C18: Unterschied 2 CO2."""
    assert _minus(_counts("siroheme"), _counts("12,18-didecarboxysiroheme")) == {"C": 2, "O": 4}


def test_fe_coproporphyrin_iii_differs_from_didecarboxysiroheme_by_two_acetic_acids():
    """Unterschied zweimal C2H4O2 (Essigsäure) — Summenformeln aus der Tabelle."""
    diff = _minus(_counts("12,18-didecarboxysiroheme"), _counts("Fe-coproporphyrin III"))
    assert diff == {"C": 4, "H": 8, "O": 4}


def test_heme_b_differs_from_fe_coproporphyrin_iii_by_two_co2_and_four_h():
    """Zwei Vinyl statt zwei Propionat: Unterschied 2 CO2 und 4 H."""
    assert _minus(_counts("Fe-coproporphyrin III"), _counts("heme b")) == {"C": 2, "H": 4, "O": 4}


# --- Beleg für die abgeleitete Säureform ---------------------------------------

PUBCHEM_ANION = (  # CID 91820468, abgerufen 10.11.2026
    "CC1=C2C=C3[C@H]([C@](C(=N3)C=C4[C@H]([C@](C(=CC5=NC(=CC(=C1CCC(=O)[O-])[N-]2)"
    "C(=C5C)CCC(=O)[O-])[N-]4)(C)CC(=O)[O-])CCC(=O)[O-])(C)CC(=O)[O-])CCC(=O)[O-].[Fe]"
)


def _layers(mol):
    """InChI ohne Ladungs-/Protonenschicht: Formel, Konnektivität, H, Stereo."""
    inchi = Chem.MolToInchi(mol)
    return [p for p in inchi.split("/")[1:] if p[0] not in "qp"]


def test_didecarboxysiroheme_has_pubchems_skeleton_and_stereo():
    _, mol = resolve("12,18-didecarboxysiroheme")
    assert _layers(mol) == _layers(Chem.MolFromSmiles(PUBCHEM_ANION))


def test_didecarboxysiroheme_is_siroheme_with_methyl_at_c12_and_c18():
    """Strukturvergleich: entfernt man in CID 439303 genau die zwei Carboxylgruppen
    der Acetate an sp²-Ringkohlenstoffen (C12, C18), entsteht der Tabelleneintrag —
    die Acetate an C2/C7 sitzen an sp³-Zentren und bleiben."""
    siro = resolve("siroheme")[1]
    hits = siro.GetSubstructMatches(Chem.MolFromSmarts("[#6X3;R]-[CH2;!R]-[CX3](=O)[OX2H1]"))
    assert len(hits) == 2
    rw = Chem.RWMol(siro)
    drop = set()
    for _, _, carboxy, *_ in hits:
        drop.add(carboxy)
        drop |= {n.GetIdx() for n in siro.GetAtomWithIdx(carboxy).GetNeighbors() if n.GetSymbol() == "O"}
    for i in sorted(drop, reverse=True):
        rw.RemoveAtom(i)
    made = rw.GetMol()
    Chem.SanitizeMol(made)
    assert Chem.MolToInchiKey(made) == DIDECARBOXYSIROHEME
    assert CalcMolFormula(made) == "C40H44FeN4O12"
