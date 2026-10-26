"""Fischer- und Haworth-Projektion für Zucker und Aminosäuren.

RDKit kennt keine Projektionen (GitHub-First-Verdikt 26.10.2026: Eigenbau).
Die Seite eines Substituenten wird ohne CIP und ohne 3D bestimmt: der
Chiralitätstag gilt für die Reihenfolge der Bindungen am Atom; liest man die
Nachbarn in einer festen Zielreihenfolge, kippt eine ungerade Permutation den
Drehsinn. Verglichen wird mit einer Referenz, deren Bild feststeht —
D-Glycerinaldehyd (Fischer, OH rechts) und β-D-Glucopyranose (Haworth, C1-OH
oben). Die lokale Geometrie ist an jedem Zentrum dieselbe, deshalb trägt eine
Referenz für alle Positionen.

Gezeichnet wird als eigenes SVG mit Textbeschriftung (CHO, CH₂OH, HO, H), weil
Lehrbuch-Projektionen Endgruppen als Formeltext schreiben — Skelett-Ecken an
den Kettenenden wären in einer Fischer-Projektion unlesbar.

Alles hier ist opt-in: `None`/"" heißt „keine Projektion für diesen Stoff“,
und der Aufrufer zeichnet dann nur die Skelettformel.
"""

from __future__ import annotations

from rdkit import Chem

from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

_CW = Chem.ChiralType.CHI_TETRAHEDRAL_CW
_UNSPECIFIED = Chem.ChiralType.CHI_UNSPECIFIED
_ELEMENTS = {1, 6, 7, 8}


def _parity(src: list[int], dst: list[int]) -> int:
    perm = [src.index(x) for x in dst]
    return (
        sum(
            perm[i] > perm[j] for i in range(len(perm)) for j in range(i + 1, len(perm))
        )
        % 2
    )


def _clockwise_in(m: Chem.Mol, idx: int, order: list[int]) -> bool:
    """Drehsinn des Zentrums, wenn die Nachbarn in `order` gelesen werden."""
    atom = m.GetAtomWithIdx(idx)
    bonded = [b.GetOtherAtomIdx(idx) for b in atom.GetBonds()]
    return (atom.GetChiralTag() == _CW) ^ bool(_parity(bonded, order))


def _with_h(mol: Chem.Mol) -> Chem.Mol:
    # Nur die Topologie zählt — eine Kopie ohne Konformer, damit AddHs nicht
    # an vorhandenen 2D-Koordinaten hängt.
    return Chem.AddHs(Chem.Mol(mol, quickCopy=True))


def _h_count(m: Chem.Mol, idx: int) -> int:
    return sum(n.GetAtomicNum() == 1 for n in m.GetAtomWithIdx(idx).GetNeighbors())


def _heavy_neighbors(m: Chem.Mol, idx: int, exclude: tuple[int, ...] = ()) -> list:
    return [
        n
        for n in m.GetAtomWithIdx(idx).GetNeighbors()
        if n.GetAtomicNum() != 1 and n.GetIdx() not in exclude
    ]


def _bond_order(m: Chem.Mol, a: int, b: int) -> float:
    return m.GetBondBetweenAtoms(a, b).GetBondTypeAsDouble()


def _hetero_label(m: Chem.Mol, atom) -> str | None:
    """OH oder NH2 am Zentrum (rechte Schreibweise), sonst None."""
    if len(_heavy_neighbors(m, atom.GetIdx())) != 1 or atom.GetFormalCharge():
        return None
    hs = _h_count(m, atom.GetIdx())
    if atom.GetAtomicNum() == 8 and hs == 1:
        return "OH"
    if atom.GetAtomicNum() == 7 and hs == 2:
        return "NH2"
    return None


_LEFT = {"OH": "HO", "NH2": "H2N", "NH3+": "H3N+", "H": "H"}


# --- Fischer --------------------------------------------------------------


def _reference(smiles: str, finder) -> bool:
    m = _with_h(Chem.MolFromSmiles(smiles))
    return finder(m)


def _end_label(m: Chem.Mol, c: int, chain_neighbor: int) -> str | None:
    subs = _heavy_neighbors(m, c, (chain_neighbor,))
    hs = _h_count(m, c)
    if not subs and hs == 3:
        return "CH3"
    if len(subs) == 1 and subs[0].GetAtomicNum() == 8:
        o = subs[0]
        if _bond_order(m, c, o.GetIdx()) == 2 and hs == 1:
            return "CHO"
        if _hetero_label(m, o) == "OH" and hs == 2:
            return "CH2OH"
    if len(subs) == 2 and hs == 0 and all(s.GetAtomicNum() == 8 for s in subs):
        double = [s for s in subs if _bond_order(m, c, s.GetIdx()) == 2]
        single = [s for s in subs if s not in double]
        if len(double) == 1 and len(single) == 1:
            if single[0].GetFormalCharge() == -1:
                return "COO-"
            if _hetero_label(m, single[0]) == "OH":
                return "COOH"
    return None


def _carbon_path(m: Chem.Mol) -> list[int] | None:
    """Unverzweigte Kohlenstoffkette über alle C, von einem Ende zum anderen."""
    carbons = [a.GetIdx() for a in m.GetAtoms() if a.GetAtomicNum() == 6]
    if not 3 <= len(carbons) <= 8:
        return None
    c_nbrs = {
        c: [
            n.GetIdx()
            for n in m.GetAtomWithIdx(c).GetNeighbors()
            if n.GetAtomicNum() == 6
        ]
        for c in carbons
    }
    ends = [c for c in carbons if len(c_nbrs[c]) == 1]
    if len(ends) != 2 or any(len(v) > 2 for v in c_nbrs.values()):
        return None
    path = [ends[0]]
    while len(path) < len(carbons):
        nxt = [n for n in c_nbrs[path[-1]] if n not in path]
        if not nxt:
            return None
        path.append(nxt[0])
    return path


def _sugar_chain(m: Chem.Mol) -> list[int] | None:
    path = _carbon_path(m)
    if path is None:
        return None
    top_label = _end_label(m, path[0], path[1])
    bottom_label = _end_label(m, path[-1], path[-2])
    if top_label is None or bottom_label is None:
        return None

    def is_ketone(c: int) -> bool:
        return any(
            s.GetAtomicNum() == 8 and _bond_order(m, c, s.GetIdx()) == 2
            for s in _heavy_neighbors(m, c)
        )

    # C1 oben: Aldehyd vor Keton (an C2) vor Carbonsäure.
    if bottom_label == "CHO" and top_label != "CHO":
        path.reverse()
    elif top_label != "CHO" and is_ketone(path[-2]) and not is_ketone(path[1]):
        path.reverse()
    elif top_label not in ("CHO", "COOH", "COO-") and not is_ketone(path[1]):
        if bottom_label in ("COOH", "COO-"):
            path.reverse()
        else:
            return None
    return path


def _center_row(m: Chem.Mol, chain: list[int], k: int, ref: bool) -> dict | None:
    c, up, down = chain[k], chain[k - 1], chain[k + 1]
    subs = [
        n for n in m.GetAtomWithIdx(c).GetNeighbors() if n.GetIdx() not in (up, down)
    ]
    heavy = [s for s in subs if s.GetAtomicNum() != 1]
    if not heavy and len(subs) == 2:
        return {"kind": "center", "left": "H", "right": "H"}
    if len(heavy) == 1 and len(subs) == 1:
        x = heavy[0]
        if x.GetAtomicNum() == 8 and _bond_order(m, c, x.GetIdx()) == 2:
            return {"kind": "carbonyl"}
        return None
    if len(heavy) != 1 or len(subs) != 2:
        return None
    x = heavy[0]
    label = _hetero_label(m, x)
    if label is None or m.GetAtomWithIdx(c).GetChiralTag() == _UNSPECIFIED:
        return None
    h = [s for s in subs if s.GetAtomicNum() == 1][0]
    right = _clockwise_in(m, c, [up, down, x.GetIdx(), h.GetIdx()]) == ref
    if right:
        return {"kind": "center", "left": "H", "right": label}
    return {"kind": "center", "left": _LEFT[label], "right": "H"}


def _fischer_ref(m: Chem.Mol) -> bool:
    # D-Glycerinaldehyd O=C[C@H](O)CO: C2 mit (oben, unten, OH, H), OH rechts.
    h = [
        n.GetIdx() for n in m.GetAtomWithIdx(2).GetNeighbors() if n.GetAtomicNum() == 1
    ][0]
    return _clockwise_in(m, 2, [1, 4, 3, h])


_FISCHER_REF = _reference("O=C[C@H](O)CO", _fischer_ref)


def _side_chain_key(m: Chem.Mol, alpha: int, root: int) -> str:
    atoms, stack = set(), [root]
    while stack:
        a = stack.pop()
        if a in atoms or a == alpha:
            continue
        atoms.add(a)
        stack.extend(
            n.GetIdx()
            for n in m.GetAtomWithIdx(a).GetNeighbors()
            if n.GetAtomicNum() != 1
        )
    return Chem.MolFragmentToSmiles(
        m, atomsToUse=sorted(atoms), rootedAtAtom=root, isomericSmiles=False
    )


# Proteinogene Seitenketten mit einem einzigen Stereozentrum. Ile und Thr
# fehlen absichtlich: ihr zweites Zentrum stünde als Formeltext ohne Seite da.
_SIDE_CHAIN_LABELS = {
    "NC(C)C(=O)O": "CH3",
    "NC(CO)C(=O)O": "CH2OH",
    "NC(CS)C(=O)O": "CH2SH",
    "NC(C(C)C)C(=O)O": "CH(CH3)2",
    "NC(CC(C)C)C(=O)O": "CH2CH(CH3)2",
    "NC(CCSC)C(=O)O": "CH2CH2SCH3",
    "NC(Cc1ccccc1)C(=O)O": "CH2C6H5",
    "NC(Cc1ccc(O)cc1)C(=O)O": "CH2C6H4OH",
    "NC(CC(=O)O)C(=O)O": "CH2COOH",
    "NC(CCC(=O)O)C(=O)O": "CH2CH2COOH",
    "NC(CC(N)=O)C(=O)O": "CH2CONH2",
    "NC(CCC(N)=O)C(=O)O": "CH2CH2CONH2",
    "NC(CCCCN)C(=O)O": "(CH2)4NH2",
    "NC(CCCNC(=N)N)C(=O)O": "(CH2)3NHC(NH)NH2",
    "NC(Cc1c[nH]cn1)C(=O)O": "CH2-imidazolyl",
    "NC(Cc1c[nH]c2ccccc12)C(=O)O": "CH2-indolyl",
}

_ALPHA = Chem.MolFromSmarts(
    "[CX4;H1;!R]([$([NX3;H2;!R]),$([NX4;H3;+1;!R])])[CX3](=[OX1])[$([OX2;H1]),$([OX1;-1])]"
)


def _amino_key_table() -> dict[str, str]:
    table = {}
    for smiles, label in _SIDE_CHAIN_LABELS.items():
        # Jeder Eintrag beginnt mit N-Cα(Seitenkette…): Atom 1 ist Cα, Atom 2 die Wurzel.
        table[_side_chain_key(Chem.MolFromSmiles(smiles), 1, 2)] = label
    return table


_AMINO_KEYS = _amino_key_table()


def _amino_rows(m: Chem.Mol) -> list[dict] | None:
    heavy = Chem.RemoveHs(m)
    matches = heavy.GetSubstructMatches(_ALPHA)
    if len(matches) != 1:
        return None
    alpha, n_idx, carboxyl = matches[0][0], matches[0][1], matches[0][2]
    if heavy.GetAtomWithIdx(alpha).GetChiralTag() == _UNSPECIFIED:
        return None
    side = [
        a.GetIdx()
        for a in heavy.GetAtomWithIdx(alpha).GetNeighbors()
        if a.GetIdx() not in (n_idx, carboxyl)
    ]
    if len(side) != 1:
        return None
    label = _AMINO_KEYS.get(_side_chain_key(heavy, alpha, side[0]))
    if label is None:
        return None
    # AddHs hängt die H hinten an — Schweratom-Indizes bleiben gültig.
    h = [
        a.GetIdx()
        for a in m.GetAtomWithIdx(alpha).GetNeighbors()
        if a.GetAtomicNum() == 1
    ][0]
    n_label = "NH3+" if heavy.GetAtomWithIdx(n_idx).GetFormalCharge() == 1 else "NH2"
    top = (
        "COO-"
        if any(
            a.GetFormalCharge() == -1
            for a in heavy.GetAtomWithIdx(carboxyl).GetNeighbors()
        )
        else "COOH"
    )
    right = _clockwise_in(m, alpha, [carboxyl, side[0], n_idx, h]) == _FISCHER_REF
    center = (
        {"kind": "center", "left": "H", "right": n_label}
        if right
        else {"kind": "center", "left": _LEFT[n_label], "right": "H"}
    )
    return [{"kind": "end", "label": top}, center, {"kind": "end", "label": label}]


def fischer_rows(mol: Chem.Mol) -> list[dict] | None:
    """Zeilen der Fischer-Projektion von oben nach unten, oder None.

    Offenkettige Zucker (Aldosen, Ketosen, Aldon-/Uronsäuren) und α-Aminosäuren
    mit festgelegter Konfiguration. Ringzucker bekommen keine Fischer-
    Projektion: das wäre ein anderer Stoff (offene Form) und das Anomer ginge
    still verloren — dafür gibt es `projection_note`.
    """
    if mol is None or any(a.GetAtomicNum() not in _ELEMENTS for a in mol.GetAtoms()):
        return None
    # Aminosäure zuerst: Asparaginsäure ist auch eine unverzweigte Kette mit
    # zwei COOH-Enden, gehört aber mit der α-COOH nach oben.
    if any(a.GetAtomicNum() == 7 for a in mol.GetAtoms()):
        rows = _amino_rows(_with_h(mol))
        if rows is not None:
            return rows
    if mol.GetRingInfo().NumRings() == 0:
        m = _with_h(mol)
        chain = _sugar_chain(m)
        if chain is not None:
            rows = [{"kind": "end", "label": _end_label(m, chain[0], chain[1])}]
            for k in range(1, len(chain) - 1):
                row = _center_row(m, chain, k, _FISCHER_REF)
                if row is None:
                    return None
                rows.append(row)
            rows.append({"kind": "end", "label": _end_label(m, chain[-1], chain[-2])})
            stereo = [
                r for r in rows if r["kind"] == "center" and r["left"] != r["right"]
            ]
            return rows if stereo else None
    return None


# --- Haworth --------------------------------------------------------------


def _ring_order(m: Chem.Mol) -> list[int] | None:
    rings = m.GetRingInfo().AtomRings()
    if len(rings) != 1 or len(rings[0]) not in (5, 6):
        return None
    ring = rings[0]
    oxygens = [i for i in ring if m.GetAtomWithIdx(i).GetAtomicNum() == 8]
    others = [i for i in ring if m.GetAtomWithIdx(i).GetAtomicNum() == 6]
    if len(oxygens) != 1 or len(others) != len(ring) - 1:
        return None
    if any(m.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
        return None
    o = oxygens[0]
    flanks = [
        n.GetIdx() for n in m.GetAtomWithIdx(o).GetNeighbors() if n.GetIdx() in ring
    ]
    anomeric = [
        c
        for c in flanks
        if any(
            x.GetAtomicNum() == 8 and x.GetIdx() not in ring
            for x in m.GetAtomWithIdx(c).GetNeighbors()
        )
    ]
    if len(anomeric) != 1:
        return None
    order = [o, anomeric[0]]
    while len(order) < len(ring):
        nxt = [
            n.GetIdx()
            for n in m.GetAtomWithIdx(order[-1]).GetNeighbors()
            if n.GetIdx() in ring and n.GetIdx() not in order
        ]
        order.append(nxt[0])
    return order


def _substituent_label(m: Chem.Mol, atom, ring_atom: int) -> str | None:
    if atom.GetAtomicNum() == 1:
        return "H"
    hetero = _hetero_label(m, atom)
    if hetero:
        return hetero
    if atom.GetAtomicNum() == 6:
        return _end_label(m, atom.GetIdx(), ring_atom)
    return None


def _haworth_ref(m: Chem.Mol) -> bool:
    order = _ring_order(m)
    c1 = order[1]
    subs = [
        n
        for n in m.GetAtomWithIdx(c1).GetNeighbors()
        if n.GetIdx() not in (order[0], order[2])
    ]
    oh = [s.GetIdx() for s in subs if s.GetAtomicNum() == 8][0]
    h = [s.GetIdx() for s in subs if s.GetAtomicNum() == 1][0]
    return _clockwise_in(m, c1, [order[0], order[2], oh, h])


_HAWORTH_REF = _reference("OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O", _haworth_ref)


def haworth_ring(mol: Chem.Mol) -> list[dict] | None:
    """Ringpositionen ab Ring-O im Uhrzeigersinn (O hinten rechts), oder None.

    Jede C-Position trägt `up`/`down` (H, OH, CH2OH, …). Ein offenes
    anomeres Zentrum bekommt `wavy` (Schlangenlinie) statt einer Seite; jedes
    andere offene Zentrum heißt: keine Projektion.
    """
    if mol is None or any(a.GetAtomicNum() not in _ELEMENTS for a in mol.GetAtoms()):
        return None
    m = _with_h(mol)
    order = _ring_order(m)
    if order is None:
        return None
    out = [{"idx": order[0], "label": "O"}]
    specified = 0
    for k in range(1, len(order)):
        c, prev, nxt = order[k], order[k - 1], order[(k + 1) % len(order)]
        atom = m.GetAtomWithIdx(c)
        subs = [n for n in atom.GetNeighbors() if n.GetIdx() not in (prev, nxt)]
        if len(subs) != 2:
            return None
        labels = [_substituent_label(m, s, c) for s in subs]
        if None in labels:
            return None
        if labels == ["H", "H"]:
            out.append({"idx": c, "up": "H", "down": "H"})
            continue
        if atom.GetChiralTag() == _UNSPECIFIED:
            if k != 1 or "H" not in labels:
                return None
            other = [lab for lab in labels if lab != "H"][0]
            out.append({"idx": c, "up": None, "down": None, "wavy": other})
            continue
        specified += 1
        first_up = (
            _clockwise_in(m, c, [prev, nxt, subs[0].GetIdx(), subs[1].GetIdx()])
            == _HAWORTH_REF
        )
        up, down = (labels[0], labels[1]) if first_up else (labels[1], labels[0])
        out.append({"idx": c, "up": up, "down": down})
    return out if specified else None


def projection_note(mol: Chem.Mol) -> str:
    """Ein Satz für Ringzucker: warum es keine Fischer-Projektion gibt."""
    if mol is None or haworth_ring(mol) is None:
        return ""
    return (
        "The Fischer projection shows the open-chain form. Draw the open-chain "
        "sugar (e.g. 'D-glucose' instead of 'beta-D-glucopyranose') to get it."
    )


# --- SVG ------------------------------------------------------------------

_FONT = "Helvetica, Arial, sans-serif"
_FONT_SIZE = 16
_SUB_SIZE = 11
_SUB_SHIFT = 4
_PAD = 14
_STROKE = "#000000"
_FRONT_EDGE = 5.0


def _label_width(text: str) -> float:
    return sum(
        (_SUB_SIZE if ch.isdigit() or ch in "+-" else _FONT_SIZE) * 0.62 for ch in text
    )


def _text(text: str, x: float, y: float, anchor: str = "middle") -> str:
    """Formeltext mit tiefgestellten Ziffern und hochgestellter Ladung."""
    runs, shift = [], 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isdigit():
            j = i
            while j < len(text) and text[j].isdigit():
                j += 1
            runs.append(
                f"<tspan dy='{_SUB_SHIFT - shift}' font-size='{_SUB_SIZE}'>{text[i:j]}</tspan>"
            )
            shift, i = _SUB_SHIFT, j
            continue
        if ch in "+-" and i == len(text) - 1:
            sign = "+" if ch == "+" else "−"
            runs.append(
                f"<tspan dy='{-_SUB_SHIFT - 2 - shift}' font-size='{_SUB_SIZE}'>{sign}</tspan>"
            )
            shift = -_SUB_SHIFT - 2
            i += 1
            continue
        j = i
        while (
            j < len(text)
            and not text[j].isdigit()
            and not (text[j] in "+-" and j == len(text) - 1)
        ):
            j += 1
        dy = f" dy='{-shift}'" if shift else ""
        runs.append(f"<tspan{dy}>{text[i:j]}</tspan>" if dy else text[i:j])
        shift, i = 0, j
    return (
        f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{anchor}' "
        f"font-family='{_FONT}' font-size='{_FONT_SIZE}' fill='{_STROKE}'>"
        f"{''.join(runs)}</text>"
    )


def _line(x1, y1, x2, y2, width=BOND_LINE_WIDTH, cap="butt") -> str:
    return (
        f"<path d='M {x1:.1f},{y1:.1f} L {x2:.1f},{y2:.1f}' style='fill:none;"
        f"stroke:{_STROKE};stroke-width:{width}px;stroke-linecap:{cap}' />"
    )


class _Box:
    def __init__(self):
        self.x0 = self.y0 = float("inf")
        self.x1 = self.y1 = float("-inf")

    def add(self, x0, y0, x1, y1):
        self.x0, self.y0 = min(self.x0, x0), min(self.y0, y0)
        self.x1, self.y1 = max(self.x1, x1), max(self.y1, y1)

    def label(self, text, x, y, anchor):
        w = _label_width(text)
        left = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        self.add(left, y - _FONT_SIZE, left + w, y + _SUB_SHIFT + 2)


def _wrap(parts: list[str], box: _Box) -> str:
    vx, vy = box.x0 - _PAD, box.y0 - _PAD
    vw, vh = box.x1 - box.x0 + 2 * _PAD, box.y1 - box.y0 + 2 * _PAD
    return (
        "<svg style='width:100%;height:100%;display:block' version='1.1' "
        "xmlns='http://www.w3.org/2000/svg' width='100%' height='100%' "
        f"viewBox='{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}'>" + "".join(parts) + "</svg>"
    )


_ROW = 46
_ARM = 40
_TEXT_GAP = 11
_BASELINE = 5.5


def fischer_svg(mol: Chem.Mol) -> str:
    """Fischer-Projektion als SVG, "" wenn der Stoff keine hat."""
    rows = fischer_rows(mol)
    if rows is None:
        return ""
    parts, box = [], _Box()
    for i, row in enumerate(rows):
        y = i * _ROW
        if i:
            above = 0 if rows[i - 1]["kind"] == "center" else _TEXT_GAP
            below = 0 if row["kind"] == "center" else _TEXT_GAP
            parts.append(_line(0, (i - 1) * _ROW + above, 0, y - below))
        if row["kind"] == "end":
            parts.append(_text(row["label"], 0, y + _BASELINE))
            box.label(row["label"], 0, y + _BASELINE, "middle")
        elif row["kind"] == "carbonyl":
            parts.append(_text("C", 0, y + _BASELINE))
            parts.append(_line(8, y - 2.5, _ARM, y - 2.5))
            parts.append(_line(8, y + 2.5, _ARM, y + 2.5))
            parts.append(_text("O", _ARM + 4, y + _BASELINE, "start"))
            box.label("O", _ARM + 4, y + _BASELINE, "start")
        else:
            parts.append(_line(-_ARM, y, _ARM, y))
            parts.append(_text(row["left"], -_ARM - 4, y + _BASELINE, "end"))
            parts.append(_text(row["right"], _ARM + 4, y + _BASELINE, "start"))
            box.label(row["left"], -_ARM - 4, y + _BASELINE, "end")
            box.label(row["right"], _ARM + 4, y + _BASELINE, "start")
    return _wrap(parts, box)


_S = 62
_STEM_OUT = 30
# Nach innen (vorn nach oben, hinten nach unten) kürzer: sonst treffen sich die
# Beschriftungen von Vorder- und Hinterkante in der Ringmitte.
_STEM_IN = 17
# Flach und breit wie im Lehrbuch; Vorder- und Hinterkante sind seitlich
# versetzt, damit keine zwei senkrechten Striche übereinander stehen.
_RING_XY = {
    6: [
        (1.4, -0.55),
        (2.2, 0.0),
        (1.65, 0.55),
        (0.35, 0.55),
        (-0.2, 0.0),
        (0.6, -0.55),
    ],
    5: [(0.75, -0.55), (1.75, 0.0), (1.3, 0.55), (0.2, 0.55), (-0.25, 0.0)],
}


def haworth_svg(mol: Chem.Mol) -> str:
    """Haworth-Projektion als SVG, "" wenn der Stoff keine hat."""
    ring = haworth_ring(mol)
    if ring is None:
        return ""
    n = len(ring)
    pts = [(x * _S, y * _S) for x, y in _RING_XY[n]]
    # Vorderkante: die drei Bindungen zwischen C1 und C(n-2) kommen auf den Betrachter zu.
    front = {(1, 2), (2, 3), (3, 4)}
    parts, box = [], _Box()
    cx = sum(p[0] for p in pts) / n
    for k in range(n):
        j = (k + 1) % n
        (x1, y1), (x2, y2) = pts[k], pts[j]
        # Am Ring-O Platz für die Beschriftung lassen
        if k == 0 or j == 0:
            ox, oy = pts[0]
            fx, fy = (x2, y2) if k == 0 else (x1, y1)
            d = ((fx - ox) ** 2 + (fy - oy) ** 2) ** 0.5
            sx, sy = ox + (fx - ox) * 9 / d, oy + (fy - oy) * 9 / d
            x1, y1, x2, y2 = (sx, sy, x2, y2) if k == 0 else (x1, y1, sx, sy)
        if (k, j) in front:
            parts.append(_line(x1, y1, x2, y2, _FRONT_EDGE, "round"))
        else:
            parts.append(_line(x1, y1, x2, y2))
        box.add(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    parts.append(_text("O", pts[0][0], pts[0][1] + _BASELINE))
    box.label("O", pts[0][0], pts[0][1] + _BASELINE, "middle")
    for k, pos in enumerate(ring[1:], start=1):
        x, y = pts[k]
        if pos.get("wavy"):
            out = 1 if x >= cx else -1
            zig = " ".join(
                f"L {x + out * (i + 1) * 5:.1f},{y + (4 if i % 2 == 0 else -4):.1f}"
                for i in range(5)
            )
            parts.append(
                f"<path d='M {x:.1f},{y:.1f} {zig} L {x + out * _STEM_OUT:.1f},{y:.1f}' "
                f"style='fill:none;stroke:{_STROKE};stroke-width:{BOND_LINE_WIDTH}px' />"
            )
            anchor = "start" if out > 0 else "end"
            parts.append(
                _text(pos["wavy"], x + out * (_STEM_OUT + 4), y + _BASELINE, anchor)
            )
            box.label(pos["wavy"], x + out * (_STEM_OUT + 4), y + _BASELINE, anchor)
            continue
        for label, sign in ((pos["up"], -1), (pos["down"], 1)):
            inward = (sign < 0 and y > 0) or (sign > 0 and y < 0)
            end = y + sign * (_STEM_IN if inward else _STEM_OUT)
            parts.append(_line(x, y, x, end))
            ty = end - 4 if sign < 0 else end + _FONT_SIZE - 2
            # Seitenatome (C1, C4) schreiben nach außen weg, damit ein langes
            # CH2OH nicht in die Beschriftung des Nachbarn an der Vorderkante läuft.
            anchor, tx = "middle", x
            if y == 0 and len(label) > 2:
                anchor, tx = ("start", x - 7) if x > cx else ("end", x + 7)
            parts.append(_text(label, tx, ty, anchor))
            box.label(label, tx, ty, anchor)
    return _wrap(parts, box)
