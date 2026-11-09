"""Fischer- und Haworth-Projektion für Zucker und Aminosäuren, Sessel für Sechsringe.

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


# --- Sessel ---------------------------------------------------------------
#
# RDKit kennt keinen Sessel: die 2D-Koordinaten sind immer ein flaches
# Sechseck, ein 3D-Konformer ist nicht steuerbar (Recherche 09.11.2026). Das
# Gerüst ist deshalb ein idealer Sessel (Tetraederwinkel), einmal orthogonal
# aus fester Richtung projiziert. Projektion erhält Parallelität: die
# gegenüberliegenden Ringbindungen bleiben parallel, jede äquatoriale Bindung
# parallel zur übernächsten Ringbindung, axiale Bindungen senkrecht. Das
# senkrechte Strecken (_CHAIR_STRETCH) ist eine affine Abbildung und ändert
# daran nichts — es übertreibt nur die Faltung wie im Lehrbuch.
#
# Muster übernommen (nicht der Code, nicht die Koordinaten) aus
# scotthartley/chem-svg-cdxml (MIT), chair.py: Sesselwahl über die Summe der
# A-Werte der axialen Gruppen; 1C4 als Spiegelbild des 4C1-Gerüsts; ein
# Ringatom ohne Stereo-Tag stellt seinen Substituenten äquatorial, von zwei
# geminalen ohne Tag den sperrigeren.

# Konformative freie Enthalpie (kcal/mol) eines axialen Substituenten am
# Cyclohexan. Nur die Rangfolge der beiden Sessel hängt daran.
# Alkyl, CN, COOH, CHO, NH2: E. L. Eliel, S. H. Wilen, Stereochemistry of
# Organic Compounds (Wiley 1994), Tab. 11.7 (CH3 1,74 · C2H5 1,79 ·
# CH(CH3)2 2,21 · C(CH3)3 4,7–4,9 · CN 0,2 · CO2H 1,4 · CHO 0,56–0,73 ·
# NH2 1,23–1,47). OH, OCH3, Halogene, COO⁻, NH3⁺: Tabelle im Wikipedia-Artikel
# „A value" (abgerufen 09.11.2026, Quellen dort Eliel/Wilen/Mander 1994 u. a.).
# CH2OH steht in keiner der beiden Tabellen: wie ein primäres Alkyl (C2H5).
_A_VALUES = {
    "H": 0.0,
    "CH3": 1.74,
    "CH2CH3": 1.79,
    "CH2OH": 1.79,
    "CH(CH3)2": 2.21,
    "C(CH3)3": 4.8,
    "OH": 0.87,
    "OCH3": 0.6,
    "F": 0.15,
    "Cl": 0.43,
    "Br": 0.38,
    "I": 0.43,
    "CN": 0.2,
    "COOH": 1.4,
    "COO-": 1.92,
    "CHO": 0.65,
    "NH2": 1.35,
    "NH3+": 1.9,
}

# Schreibweise links vom Ring (die Bindung kommt von rechts).
_CHAIR_LEFT = {
    "OH": "HO",
    "NH2": "H2N",
    "NH3+": "H3N+",
    "CH3": "H3C",
    "CH2OH": "HOH2C",
    "CH2CH3": "H3CH2C",
    "CH(CH3)2": "(H3C)2HC",
    "C(CH3)3": "(H3C)3C",
    "OCH3": "H3CO",
    "CN": "NC",
    "COOH": "HOOC",
    "COO-": "-OOC",
    "CHO": "OHC",
}

_HALOGENS = {9: "F", 17: "Cl", 35: "Br", 53: "I"}


def _chair_label(m: Chem.Mol, atom, ring_atom: int) -> str | None:
    """Wie `_substituent_label`, dazu Halogene, OCH3, CN und Alkyl bis tBu."""
    label = _substituent_label(m, atom, ring_atom)
    if label is not None:
        return label
    if atom.GetFormalCharge():
        return None
    num, idx = atom.GetAtomicNum(), atom.GetIdx()
    if num in _HALOGENS:
        return _HALOGENS[num]
    rest = _heavy_neighbors(m, idx, (ring_atom,))
    if num == 8 and len(rest) == 1:
        c = rest[0]
        if c.GetAtomicNum() == 6 and _h_count(m, c.GetIdx()) == 3:
            return "OCH3"
        return None
    if num != 6:
        return None
    if len(rest) == 1 and rest[0].GetAtomicNum() == 7:
        if _bond_order(m, idx, rest[0].GetIdx()) == 3:
            return "CN"
        return None
    methyls = [
        c
        for c in rest
        if c.GetAtomicNum() == 6
        and _h_count(m, c.GetIdx()) == 3
        and _bond_order(m, idx, c.GetIdx()) == 1
    ]
    if len(methyls) != len(rest) or len(rest) + _h_count(m, idx) != 3:
        return None
    return {1: "CH2CH3", 2: "CH(CH3)2", 3: "C(CH3)3"}.get(len(rest))


def chair_problem(mol: Chem.Mol) -> str:
    """Warum es keinen Sessel gibt (englischer Satz), "" wenn es einen gibt."""
    if mol is None:
        return "the structure could not be read"
    rings = list(mol.GetRingInfo().AtomRings())
    six = [r for r in rings if len(r) == 6]
    if not six:
        return "it has no six-membered ring"
    ring = six[0]
    others = [r for r in rings if r != ring]
    if any(set(r) & set(ring) for r in others):
        return "its six-membered ring is part of a fused or spiro ring system"
    if others:
        return "it has more than one ring; the chair view draws a single ring"
    elements = [mol.GetAtomWithIdx(i).GetAtomicNum() for i in ring]
    if any(e not in (6, 8) for e in elements) or elements.count(8) > 1:
        return (
            "the chair view draws only carbocycles and pyranose-type rings "
            "(one ring oxygen)"
        )
    for i in ring:
        atom = mol.GetAtomWithIdx(i)
        if atom.GetIsAromatic() or any(
            b.GetBondTypeAsDouble() != 1 for b in atom.GetBonds()
        ):
            return (
                "its ring contains a double bond or aromatic atom; a chair "
                "needs six sp3 ring atoms"
            )
    m = _with_h(mol)
    for i in ring:
        for n in m.GetAtomWithIdx(i).GetNeighbors():
            if n.GetIdx() in ring:
                continue
            if _chair_label(m, n, i) is None:
                return (
                    f"the chair view cannot label the {n.GetSymbol()} "
                    "substituent on its ring (supported: H, OH, NH2, OCH3, "
                    "halogens, CN, CH3 to C(CH3)3, CH2OH, CHO, COOH)"
                )
    return ""


def _chair_order(m: Chem.Mol, ring: tuple) -> list[int]:
    """Ringatome in Zeichenreihenfolge, Position 0 hinten rechts.

    Pyranose: ab Ring-O zum anomeren C wie bei Haworth (C1 an der rechten
    Spitze). Carbocyclus: das erste substituierte C an die rechte Spitze
    (Position 1), Laufrichtung zum nächsten substituierten Nachbarn. Jede
    Laufrichtung ist eine gültige Ansicht — `_clockwise_in` liest prev/nxt
    in derselben Richtung, die Seiten kippen also mit.
    """
    order = _ring_order(m)
    if order is not None and len(order) == 6:
        return order
    oxygens = [i for i in ring if m.GetAtomWithIdx(i).GetAtomicNum() == 8]

    def substituted(i):
        return bool(_heavy_neighbors(m, i, tuple(ring)))

    def walk(start, nxt):
        return _walk_ring(m, ring, start, nxt)

    if oxygens:
        o = oxygens[0]
        flanks = [
            n.GetIdx() for n in m.GetAtomWithIdx(o).GetNeighbors() if n.GetIdx() in ring
        ]
        flanks.sort(key=lambda i: (not substituted(i), i))
        return walk(o, flanks[0])
    subs = [i for i in sorted(ring) if substituted(i)]
    first = subs[0] if subs else min(ring)
    best = None
    for n in m.GetAtomWithIdx(first).GetNeighbors():
        if n.GetIdx() not in ring:
            continue
        path = walk(first, n.GetIdx())
        # nächster substituierter Ringplatz in dieser Richtung
        dist = next((k for k in range(1, 6) if substituted(path[k])), 6)
        if best is None or (dist, path[1]) < best[0]:
            best = ((dist, path[1]), path)
    path = best[1]
    # path[0] soll auf Position 1 (rechte Spitze): eins nach hinten drehen.
    return [path[-1]] + path[:-1]


def _hexose_d(m: Chem.Mol, order: list[int], up_of: dict) -> bool | None:
    """D/L einer Aldohexopyranose (Seite der C5-Kohlenstoffgruppe), sonst None.

    Nur dort ist „D → 4C1" Lehrbuchregel. Pentopyranosen (D-Arabinose
    bevorzugt 1C4) und Ketosen (β-D-Fructopyranose: 2C5) entscheidet die
    A-Wert-Summe.
    """
    if _ring_order(m) is None or len(order) != 6:
        return None
    if _h_count(m, order[1]) != 1:
        return None  # Ketose
    c5 = order[5]
    carbons = [n.GetIdx() for n in _heavy_neighbors(m, c5, (order[0], order[4]))]
    if len(carbons) != 1 or m.GetAtomWithIdx(carbons[0]).GetAtomicNum() != 6:
        return None
    return up_of.get(carbons[0])


def chair_ring(mol: Chem.Mol) -> dict | None:
    """Sessel: Konformer und je Ringposition axialer/äquatorialer Substituent.

    `positions[k]` sitzt auf Ecke k des Gerüsts (0 hinten rechts, 1 rechte
    Spitze, im Uhrzeigersinn von oben). Ein Ring-O trägt nur `label`; jedes
    C trägt `axial`/`equatorial` (Beschriftung) und `axialAtom`/
    `equatorialAtom` (Atomindex im Molekül mit H). `conformer` ist "4C1"
    oder "1C4" (für Carbocyclen dieselbe Gerüstbezeichnung: welche Spitze
    oben liegt).
    """
    if chair_problem(mol):
        return None
    m = _with_h(mol)
    ring = next(r for r in m.GetRingInfo().AtomRings() if len(r) == 6)
    default = _chair_order(m, ring)
    if any(m.GetAtomWithIdx(i).GetAtomicNum() == 8 for i in ring):
        # Pyranose: Lehrbuchlage fest (O hinten rechts, C1 rechte Spitze)
        return _chair_assign(m, default)
    # Carbocyclus: jede Lage ist eine gültige Ansicht. Genommen wird die erste
    # (Standardlage zuerst), in der keine Beschriftung eine Bindung oder eine
    # andere Beschriftung trifft — etwa ein axiales CH3 an einer Innenecke.
    candidates = [default]
    for start in ring:
        for n in m.GetAtomWithIdx(start).GetNeighbors():
            if n.GetIdx() in ring:
                candidates.append(_walk_ring(m, ring, start, n.GetIdx()))
    best = None
    for rank, order in enumerate(candidates):
        result = _chair_assign(m, order)
        score = (
            _chair_collisions(_chair_geometry(result)),
            _inner_heavy(result),
            rank,
        )
        if best is None or score < best[0]:
            best = (score, result)
        if score[:2] == (0, 0):
            break
    return best[1]


def _inner_heavy(ring: dict) -> int:
    """Schwere Gruppen auf einem axialen Strich, der ins Ringinnere zeigt."""
    pts, ax, _ = _chair_template(ring["conformer"] == "1C4")
    cy = sum(p[1] for p in pts) / 6
    return sum(
        1
        for k, pos in enumerate(ring["positions"])
        if pos.get("axial") not in (None, "H")
        and ((ax[k][1] < 0 and pts[k][1] > cy) or (ax[k][1] > 0 and pts[k][1] < cy))
    )


def _walk_ring(m: Chem.Mol, ring, start: int, nxt: int) -> list[int]:
    out = [start, nxt]
    while len(out) < len(ring):
        out.append(
            [
                n.GetIdx()
                for n in m.GetAtomWithIdx(out[-1]).GetNeighbors()
                if n.GetIdx() in ring and n.GetIdx() not in out
            ][0]
        )
    return out


def _chair_assign(m: Chem.Mol, order: list[int]) -> dict:
    """Konformer und Positionen für eine feste Lage `order` (Ecke k = order[k])."""
    # Seite je Substituent (True = oben), None ohne Stereo-Tag
    up_of: dict[int, bool | None] = {}
    subs_of: dict[int, list] = {}
    for k in range(6):
        c, prev, nxt = order[k], order[k - 1], order[(k + 1) % 6]
        atom = m.GetAtomWithIdx(c)
        if atom.GetAtomicNum() == 8:
            continue
        subs = [n for n in atom.GetNeighbors() if n.GetIdx() not in (prev, nxt)]
        subs_of[c] = subs
        if atom.GetChiralTag() == _UNSPECIFIED:
            for s in subs:
                up_of[s.GetIdx()] = None
            continue
        first_up = (
            _clockwise_in(m, c, [prev, nxt, subs[0].GetIdx(), subs[1].GetIdx()])
            == _HAWORTH_REF
        )
        up_of[subs[0].GetIdx()], up_of[subs[1].GetIdx()] = first_up, not first_up

    labels = {
        s.GetIdx(): _chair_label(m, s, c) for c, subs in subs_of.items() for s in subs
    }

    def assign(flip: bool) -> tuple[list[dict], float]:
        positions, energy = [], 0.0
        for k in range(6):
            c = order[k]
            if c not in subs_of:
                positions.append({"idx": c, "label": "O"})
                continue
            axial_up = (k % 2 == 0) ^ flip
            a, b = subs_of[c]
            ua = up_of[a.GetIdx()]
            if ua is None:
                # Ohne Tag: der sperrigere Substituent äquatorial
                ax_first = _A_VALUES[labels[a.GetIdx()]] < _A_VALUES[labels[b.GetIdx()]]
            else:
                ax_first = ua == axial_up
            ax, eq = (a, b) if ax_first else (b, a)
            energy += _A_VALUES[labels[ax.GetIdx()]]
            positions.append(
                {
                    "idx": c,
                    "axial": labels[ax.GetIdx()],
                    "equatorial": labels[eq.GetIdx()],
                    "axialAtom": ax.GetIdx(),
                    "equatorialAtom": eq.GetIdx(),
                }
            )
        return positions, energy

    d = _hexose_d(m, order, up_of)
    if d is not None:
        flip = not d
    else:
        e0, e1 = assign(False)[1], assign(True)[1]
        flip = e1 < e0 - 1e-9
    positions, _ = assign(flip)
    return {"conformer": "1C4" if flip else "4C1", "positions": positions}


# Lineare Abbildung des idealen Sessels aufs Blatt: x = X + SHEAR·Y,
# y_oben = RISE·Y + PUCKER·Z (X nach rechts, Y nach hinten, Z = Ringachse).
# Jede lineare Abbildung erhält Parallelität — gegenüberliegende Ringbindungen
# bleiben parallel, jede äquatoriale Bindung parallel zur übernächsten
# Ringbindung, axiale Bindungen senkrecht. Die drei Zahlen sind die
# Lehrbuchansicht (gewählt nach Ansicht der Bilder, 09.11.2026): hintere Reihe
# nach rechts versetzt und über der vorderen, Faltung übertrieben.
_CHAIR_SHEAR = 0.12
_CHAIR_RISE = 0.6
_CHAIR_PUCKER = 2.3
_CHAIR_SCALE = 60.0
_CHAIR_AXIAL = 30.0
_CHAIR_AXIAL_IN = 15.0
_CHAIR_EQUATORIAL = 30.0


def _chair_template(flip: bool) -> tuple[list, list, list]:
    """(Ecken, axiale Richtung, äquatoriale Richtung) in SVG-Koordinaten.

    Ecke k liegt bei 60° − 60°·k um die Ringachse (0 hinten rechts, 1 rechte
    Spitze, im Uhrzeigersinn von oben) — dieselbe Anordnung wie Haworth,
    deshalb gilt dessen Referenz für oben/unten. Ecke k ist oben (axial nach
    oben), wenn k gerade ist: mit Ring-O auf 0 sind C4 oben, C1 unten — 4C1.
    1C4 ist das Spiegelbild (x → −x, Ecke k ↔ 5 − k): dann ist k ungerade oben.
    """
    import math

    h = 1 / (4 * math.sqrt(2))  # Tetraederwinkel im Ring bei Radius 1
    pts3, up = [], []
    for k in range(6):
        a = math.radians(60 - 60 * k)
        u = k % 2 == 0
        pts3.append((math.cos(a), math.sin(a), h if u else -h))
        up.append(u)

    def sub(p, q):
        return tuple(x - y for x, y in zip(p, q))

    def unit(v):
        n = math.sqrt(sum(x * x for x in v))
        return tuple(x / n for x in v)

    eq3 = []
    for k in range(6):
        axis = (0.0, 0.0, 1.0 if up[k] else -1.0)
        u1 = unit(sub(pts3[k - 1], pts3[k]))
        u2 = unit(sub(pts3[(k + 1) % 6], pts3[k]))
        # vierte Tetraederrichtung: die Summe aller vier Einheitsvektoren ist 0
        eq3.append(unit(tuple(-(a + b + c) for a, b, c in zip(u1, u2, axis))))

    def proj(v):
        return (
            v[0] + _CHAIR_SHEAR * v[1],
            -(_CHAIR_RISE * v[1] + _CHAIR_PUCKER * v[2]),
        )

    pts = [proj(p) for p in pts3]
    ax = [(0.0, -1.0 if u else 1.0) for u in up]
    eq = [unit(proj(v)) for v in eq3]
    if flip:
        pts = [(-pts[5 - k][0], pts[5 - k][1]) for k in range(6)]
        ax = [ax[5 - k] for k in range(6)]
        eq = [(-eq[5 - k][0], eq[5 - k][1]) for k in range(6)]
    return pts, ax, eq


def _chair_drawing(mol: Chem.Mol):
    """(SVG-Teile, Rahmen, Beschriftungen, Strecken) oder None."""
    ring = chair_ring(mol)
    return None if ring is None else _chair_geometry(ring)


def _chair_geometry(ring: dict):
    pts, ax, eq = _chair_template(ring["conformer"] == "1C4")
    pts = [(x * _CHAIR_SCALE, y * _CHAIR_SCALE) for x, y in pts]
    pos = ring["positions"]
    parts, box, labels, segments = [], _Box(), [], []
    cy = sum(p[1] for p in pts) / 6

    def line(x1, y1, x2, y2, **kw) -> int:
        parts.append(_line(x1, y1, x2, y2, **kw))
        segments.append((x1, y1, x2, y2))
        box.add(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        return len(segments) - 1

    def put(text, x, y, anchor, own):
        # `own`: die Strecken, die an dieser Beschriftung enden
        parts.append(_text(text, x, y, anchor))
        box.label(text, x, y, anchor)
        w = _label_width(text)
        left = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        labels.append((left, y - _FONT_SIZE + 3, left + w, y + 2, frozenset(own)))

    o_slots = [k for k in range(6) if pos[k].get("label") == "O"]
    for k in range(6):
        j = (k + 1) % 6
        (x1, y1), (x2, y2) = pts[k], pts[j]
        # Am Ring-O Platz für die Beschriftung lassen (wie Haworth)
        for slot in o_slots:
            if slot in (k, j):
                ox, oy = pts[slot]
                fx, fy = (x2, y2) if slot == k else (x1, y1)
                d = ((fx - ox) ** 2 + (fy - oy) ** 2) ** 0.5
                sx, sy = ox + (fx - ox) * 9 / d, oy + (fy - oy) * 9 / d
                if slot == k:
                    x1, y1 = sx, sy
                else:
                    x2, y2 = sx, sy
        line(x1, y1, x2, y2, cap="round")
    for slot in o_slots:
        # Ringbindung k verbindet Ecke k mit k+1
        put(
            "O",
            pts[slot][0],
            pts[slot][1] + _BASELINE,
            "middle",
            {slot, (slot - 1) % 6},
        )

    for k in range(6):
        p = pos[k]
        if "label" in p or (p["axial"] == "H" and p["equatorial"] == "H"):
            continue
        x, y = pts[k]
        # axial: senkrecht; nach innen (vorn nach oben, hinten nach unten) kürzer
        dy = ax[k][1]
        inward = (dy < 0 and y > cy) or (dy > 0 and y < cy)
        end = y + dy * (_CHAIR_AXIAL_IN if inward else _CHAIR_AXIAL)
        stem = line(x, y, x, end)
        ty = end - 4 if dy < 0 else end + _FONT_SIZE - 2
        put(p["axial"], x, ty, "middle", {stem})
        # äquatorial: entlang der berechneten Richtung
        ex, ey = eq[k]
        tx, tyy = x + ex * _CHAIR_EQUATORIAL, y + ey * _CHAIR_EQUATORIAL
        stem = line(x, y, tx, tyy)
        label = p["equatorial"]
        # Text in Verlängerung des Strichs: steile Striche heben/senken ihn
        ly = tyy + _BASELINE + ey * 8
        if abs(ex) < 0.45:
            # Steiler Strich (Innenecken): Text über/unter dem Ende, zur Seite
            # weg vom Nachbaratom, dessen axialer Strich daneben steht.
            ly = tyy - 4 if ey < 0 else tyy + _FONT_SIZE - 2
            if ex < 0:
                put(label, tx - 5, ly, "start", {stem})
            else:
                put(_CHAIR_LEFT.get(label, label), tx + 5, ly, "end", {stem})
        elif ex > 0:
            put(label, tx + 2, ly, "start", {stem})
        else:
            put(_CHAIR_LEFT.get(label, label), tx - 2, ly, "end", {stem})
    return parts, box, labels, segments


def _hits(box: tuple, seg: tuple) -> bool:
    x0, y0, x1, y1 = box
    sx, sy, ex, ey = seg
    return any(
        x0 < sx + (ex - sx) * i / 24 < x1 and y0 < sy + (ey - sy) * i / 24 < y1
        for i in range(25)
    )


def _chair_collisions(drawing) -> int:
    """Beschriftung über Bindung oder Beschriftung — 0 heißt lesbar.

    Eine Strecke, die an der Beschriftung endet (ihr eigener Strich, die am
    Ring-O gekürzten Ringbindungen), zählt nicht.
    """
    _, _, labels, segments = drawing
    count = 0
    for i, b in enumerate(labels):
        # _label_width schätzt Großbuchstaben knapp: seitlich 2 px Luft
        inner = (b[0] - 2, b[1] + 1, b[2] + 2, b[3] - 1)
        for j, s in enumerate(segments):
            if j not in b[4]:
                count += _hits(inner, s)
        for c in labels[i + 1 :]:
            count += (
                b[0] - 2 < c[2] + 2
                and c[0] - 2 < b[2] + 2
                and b[1] < c[3]
                and c[1] < b[3]
            )
    return count


def _chair_label_boxes(mol: Chem.Mol) -> list[tuple]:
    drawing = _chair_drawing(mol)
    return [] if drawing is None else [b[:4] for b in drawing[2]]


def chair_collisions(mol: Chem.Mol) -> int:
    drawing = _chair_drawing(mol)
    return 0 if drawing is None else _chair_collisions(drawing)


def chair_svg(mol: Chem.Mol) -> str:
    """Sesselkonformation als SVG, "" wenn der Stoff keinen Sessel hat."""
    drawing = _chair_drawing(mol)
    if drawing is None:
        return ""
    return _wrap(drawing[0], drawing[1])
