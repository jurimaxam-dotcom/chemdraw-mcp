"""Lehrbuch-Fälle: erwartetes Produkt samt Deskriptor aus einer veröffentlichten Quelle, nicht aus
unserer eigenen Ableitung (Jay 05.11.2026: „wie können wir mit Sicherheit sagen, ob es stimmt?").

Die Matrix in tests/mechanism_matrix.py trägt Deskriptoren, die die Bau-Session selbst
hergeleitet hat; hier steht je Familie mindestens ein Fall, dessen Ergebnis ein Lehrbuch nennt.
Quellen (frei zugänglich):
- [OS-11.2] OpenStax *Organic Chemistry* (McMurry, 2023), 11.2 „The SN2 Reaction": (R)-2-Bromoctan +
  Hydroxid gibt (S)-Octan-2-ol — Walden-Inversion am Beispiel Hughes/Ingold.
- [OS-11.4] OpenStax 11.4 „The SN1 Reaction": ein chirales tertiäres Halogenid gibt über das
  planare Kation ein racemisches Produkt.
- [OS-21.3] OpenStax 21.3 „Chemistry of Acid Halides"/Clayden Kap. 10: Fischer-Veresterung von
  Essigsäure mit Ethanol gibt Ethylacetat und Wasser, H⁺ wird zurückgebildet. Seit Etappe E2
  (06.11.2026) wandern Protonen über das Lösungsmittel: das zurückgebildete H⁺ steht als
  protonierter Alkohol (EtOH₂⁺) da — dasselbe Proton, im Alkohol gelöst, kein freies H⁺.
"""

from rdkit import Chem

from chemdraw_tool.mechanism_substrate import build_steps, cip_labels


def _plain(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    for a in mol.GetAtoms():
        a.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.MolFromSmiles(Chem.MolToSmiles(mol)))


def _canon(smiles: str) -> str:
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def _product_descriptor(step, pattern: str) -> str:
    for smi in step.molecules:
        if Chem.MolFromSmiles(smi).HasSubstructMatch(Chem.MolFromSmarts(pattern)):
            mol = Chem.MolFromSmiles(smi)
            labels = cip_labels(mol)
            assert len(labels) == 1, labels
            return next(iter(labels.values()))
    raise AssertionError("Produkt fehlt")


def test_os_11_2_r_2_bromoctan_hydroxid_gibt_s_octan_2_ol():
    steps = build_steps("sn2", ["CCCCCC[C@@H](C)Br", "[OH-]"])  # (R)-2-Bromoctan
    assert cip_labels(Chem.MolFromSmiles(steps[0].molecules[0])) and \
        next(iter(cip_labels(Chem.MolFromSmiles(steps[0].molecules[0])).values())) == "R"
    produkte = [_plain(s) for s in steps[-1].molecules]
    assert _canon("CCCCCC[C@H](C)O") in produkte, produkte  # (S)-Octan-2-ol [OS-11.2]
    assert _product_descriptor(steps[-1], "[OX2H]") == "S"
    assert steps[-1].label.endswith("(S)")


def test_os_11_4_chirales_tertiaeres_halogenid_racemisiert():
    steps = build_steps("sn1", ["CCCC(C)(Br)CC", "O"])  # 3-Brom-3-methylhexan, Zentrum stereogen
    assert "racemic" in steps[-1].label
    assert all("@" not in s for s in steps[-1].molecules)
    assert _canon("CCCC(C)(O)CC") in [_plain(s) for s in steps[-1].molecules]


def test_clayden_fischer_essigsaeure_ethanol_gibt_ethylacetat():
    steps = build_steps("fischer_ester", ["CC(=O)O", "CCO"])
    produkte = sorted(_plain(s) for s in steps[-1].molecules)
    assert produkte == sorted([_canon("CCOC(C)=O"), _canon("O"), _canon("CC[OH2+]")]), produkte
