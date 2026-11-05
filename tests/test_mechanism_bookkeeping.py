"""Elektronen-Buchführung: jeder gebogene Pfeil muss genau die Bindungsänderung beschreiben, die
zwischen zwei Schritten tatsächlich passiert — und jede Änderung braucht ihren Pfeil.

Hintergrund (Jay 05.11.2026): Jay kann die Chemie der Kontaktbögen nicht selbst prüfen. Was ein
Dozent am Bogen abhakt — „der Pfeil geht vom freien Paar zum richtigen Atom, die Bindung, die
bricht, hat einen Pfeil, nichts entsteht aus dem Nichts" — wird hier maschinell über die ganze
Substrat-Matrix geprüft, netzfrei an den gemappten Schritt-SMILES (nicht am SVG).

Regeln, die ein Pfeil bedeutet (docs/mechanismus-substrate-design.md (g) 1–4):
- (a, lone_pair) → (b, atom):          Bindung a–b entsteht (Ordnung +1)
- (a, bond_to, b) → (a|b, atom):       Bindung a–b bricht (Ordnung −1), Paar geht zum Ziel
- (a, lone_pair) → (a, bond_to, b):    Bindung a–b wird um eins höher (z. B. C–O → C=O)
Wasserstoffe zählen am schweren Partner (implizit oder als gemapptes Atom gezeichnet), damit ein
H, das in einem Schritt als Atom und im nächsten implizit vorliegt, dieselbe Buchung ergibt.

Bekannte, bewusst zugelassene Vereinfachungen (jede steht hier mit Namen, keine stillschweigend):
- SN1-Schlussschritt „after deprotonation" fasst Angriff und Deprotonierung zusammen — das
  Nucleophil verliert dort ein H ohne eigenen Pfeil.
- Fischer „Protonation of the carbonyl group": ein Pfeil (O-Paar → H⁺) ergibt C=O⁺H; gezeichnet
  wird die gleichwertige Grenzformel C⁺(OH)₂ (Design-Notiz (b)), also zusätzlich C=O → C–O ohne
  Resonanzpfeil. Wer die C=O⁺H-Form zeichnet, streicht diese Ausnahme.
Nicht geprüft wird die Lage der Formalladung (Grenzformel C⁺(OH)₂ ist erlaubt); dafür steht
tests/test_mechanism_substrate.py.
"""

from __future__ import annotations

import copy

import pytest
from rdkit import Chem

from chemdraw_tool.mechanism import CurvedArrow
from chemdraw_tool.mechanism_substrate import NU, build_steps
from tests.mechanism_matrix import MATRIX

Delta = dict[object, float]  # frozenset{a, b} → Ordnungsänderung · ("H", a) → H-Zahl am Atom a


def _mols(step) -> list[Chem.Mol]:
    out = []
    for smi in step.molecules:
        mol = Chem.MolFromSmiles(smi, sanitize=False)  # gemappte H bleiben Atome
        assert mol is not None, (step.label, smi)
        Chem.SanitizeMol(mol)
        out.append(mol)
    return out


def _state(step) -> tuple[dict[object, float], set[int]]:
    """Bindungsordnungen zwischen schweren gemappten Atomen + H-Zahl je schwerem Atom."""
    state: dict[object, float] = {}
    heavy: set[int] = set()
    for mol in _mols(step):
        for atom in mol.GetAtoms():
            if atom.GetAtomicNum() == 1 or not atom.GetAtomMapNum():
                continue
            heavy.add(atom.GetAtomMapNum())
            state[("H", atom.GetAtomMapNum())] = float(atom.GetTotalNumHs(includeNeighbors=True))
        for bond in mol.GetBonds():
            a, b = bond.GetBeginAtom(), bond.GetEndAtom()
            if a.GetAtomicNum() == 1 or b.GetAtomicNum() == 1:
                continue
            state[frozenset((a.GetAtomMapNum(), b.GetAtomMapNum()))] = bond.GetBondTypeAsDouble()
    return state, heavy


def _h_maps(steps) -> set[int]:
    return {a.GetAtomMapNum() for s in steps for m in _mols(s) for a in m.GetAtoms() if a.GetAtomicNum() == 1}


def _key(a: int, b: int, h_maps: set[int]):
    if a in h_maps and b in h_maps:
        raise AssertionError(f"Pfeil zwischen zwei Wasserstoffen {a}–{b}")
    if a in h_maps:
        return ("H", b)
    if b in h_maps:
        return ("H", a)
    return frozenset((a, b))


def _expected(arrows: list[CurvedArrow], h_maps: set[int]) -> Delta:
    delta: Delta = {}
    for arrow in arrows:
        src, dst = arrow.source, arrow.target
        if src[1] == "lone_pair" and dst[1] == "atom":
            key, change = _key(src[0], dst[0], h_maps), +1
        elif src[1] == "bond_to" and dst[1] == "atom" and dst[0] in (src[0], src[2]):
            key, change = _key(src[0], src[2], h_maps), -1
        elif src[1] == "lone_pair" and dst[1] == "bond_to" and src[0] in (dst[0], dst[2]):
            key, change = _key(dst[0], dst[2], h_maps), +1
        else:
            raise AssertionError(f"Pfeilform ohne Bedeutung: {arrow}")
        delta[key] = delta.get(key, 0) + change
    return {k: v for k, v in delta.items() if v}


def _actual(before, after) -> Delta:
    """Änderungen zwischen zwei Schritten, beschränkt auf Atome, die in beiden gezeichnet sind."""
    s0, heavy0 = _state(before)
    s1, heavy1 = _state(after)
    common = heavy0 & heavy1

    def visible(key) -> bool:
        atoms = {key[1]} if isinstance(key, tuple) else set(key)
        return atoms <= common

    delta: Delta = {}
    for key in set(s0) | set(s1):
        atoms = {key[1]} if isinstance(key, tuple) else set(key)
        if not visible(key):
            # Ein Atom, das nur auf einer Seite steht, darf keine Bindung zu einem sichtbaren
            # Atom haben — sonst entstünde oder verschwände eine Bindung ohne Pfeil
            assert not (atoms & common) or isinstance(key, tuple), (
                f"Bindung {set(key)} zu einem Atom, das nur in einem der Schritte gezeichnet ist")
            continue
        change = s1.get(key, 0.0) - s0.get(key, 0.0)
        if change:
            delta[key] = change
    return delta


def check_bookkeeping(steps) -> None:
    h_maps = _h_maps(steps)
    for i, step in enumerate(steps):
        if step.is_transition_state:
            continue  # wird vom Vorgänger aus über den ÜZ hinweg geprüft
        if i + 1 >= len(steps):
            continue
        nxt = steps[i + 1]
        if nxt.is_transition_state:
            assert i + 2 < len(steps), "Übergangszustand ohne Produktschritt"
            arrows, after = nxt.arrows, steps[i + 2]
            expected = _expected(arrows, h_maps)
            partial = {frozenset(p) for p in nxt.partial_bonds}
            assert partial == {k for k in expected if isinstance(k, frozenset)}, (
                f"{nxt.label}: Teilbindungen {partial} ≠ Pfeile {expected}")
        else:
            arrows, after = step.arrows, nxt
            expected = _expected(arrows, h_maps)
        actual = _actual(step, after)
        if step.label.startswith("Protonation of the carbonyl"):
            # Fischer: Grenzformel C⁺(OH)₂ statt C=O⁺H — die C=O-Bindung sinkt ohne Resonanzpfeil
            c_o = next(k for k in actual if isinstance(k, frozenset) and actual[k] == -1.0)
            assert actual.pop(c_o) == -1.0
        if "after deprotonation" in after.label:
            # SN1: Angriff + Deprotonierung in einem Bild; das Nucleophil gibt ein H ab
            assert actual.pop(("H", NU), None) == -1.0, f"{after.label}: Deprotonierung ohne H-Verlust am Nucleophil"
        assert actual == expected, (
            f"{step.label} → {after.label}: Pfeile sagen {expected}, Moleküle zeigen {actual}")


@pytest.mark.parametrize("cid, rt, subs, _cip", MATRIX, ids=[m[0] for m in MATRIX])
def test_pfeile_und_bindungsaenderungen_stimmen_ueberein(cid, rt, subs, _cip):
    check_bookkeeping(build_steps(rt, subs))


def test_falscher_pfeil_faellt_auf():
    """Der Prüfer selbst: ein Pfeil zum falschen Atom muss rot werden (einmal rot gesehen)."""
    steps = copy.deepcopy(build_steps("sn2", ["CCBr", "[I-]"]))
    ts = steps[1]
    ts.arrows[0] = CurvedArrow(source=(NU, "lone_pair"), target=(ts.partial_bonds[1][1], "atom"), style="full")
    with pytest.raises(AssertionError, match="Teilbindungen|Pfeile sagen"):
        check_bookkeeping(steps)


def test_fehlender_pfeil_faellt_auf():
    steps = copy.deepcopy(build_steps("fischer_ester", ["CC(=O)O", "CO"]))
    loss = next(s for s in steps if s.label.startswith("Loss of water"))
    loss.arrows.pop()  # C=O-Rückbildung ohne Pfeil
    with pytest.raises(AssertionError, match="Pfeile sagen"):
        check_bookkeeping(steps)
