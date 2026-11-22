"""Explizite H-Atome für die Ansicht „All H“ kollisionsarm platzieren.

`Chem.AddHs(addCoords=True)` setzt jedes H nur nach der lokalen Geometrie
seines Schweratoms. In verbrückten Polycyclen (Morphin, Campher, Adamantan,
Steroide) liegt dort aber ein anderes Gerüstatom oder ein fremdes H — die
Beschriftungen stapeln sich. Hier werden nur die H solcher Engstellen neu
gesetzt: Kreis um das eigene Schweratom absuchen, freieste Richtung nehmen,
nötigenfalls die H-Bindung kürzen. Schweratome bleiben, wo sie sind (der
Umschalter 2D ⇄ All H verschiebt das Gerüst nicht), saubere Moleküle bleiben
exakt, wie AddHs sie liefert.
"""

from __future__ import annotations

import numpy as np
from rdkit import Chem
from rdkit.Geometry import Point3D

# Ab dieser Nähe (in mittleren Bindungslängen) gilt ein H als Kollision. Ein
# H-Label ist im Bild ≈ 0,3 Bindungslängen breit. Ethanol, Ibuprofen, Koffein
# liegen nach AddHs bei ≥ 0,61 und bleiben unberührt; von 349 Test-SMILES des
# Repos bewegt das 76, davon 74 mit echter Berührung (< 0,4) — gemessen 11.11.2026.
CLEARANCE = 0.45
# Zielabstand beim Neusetzen: etwas Luft über der Kollisionsgrenze.
_TARGET = 0.55
# Ab hier berühren sich zwei H-Labels sicher nicht (Label ≈ 0,3 Bindungslängen):
# beim Vergleich ganzer Anordnungen zählt darüber die freie Linie mehr.
_GOOD = 0.45
# Ein Label darf näher an eine Linie rücken als an ein anderes Label.
_LINE_CLEARANCE = 0.25
_LINE_TARGET = 0.30
_LINE_WEIGHT = 60
# Erlaubte Kürzung der C–H-Bindung, längste zuerst bevorzugt.
_RADII = np.array([1.0, 0.9, 0.8, 0.7, 0.6])
_ANGLES = np.radians(np.arange(0, 360, 5))
_PASSES = 4
# Nur die Nachbarschaft zählt (in Bindungslängen um das Schweratom) —
# hält 20-Reste-Peptide schnell.
_REACH = 2.5


def _seg_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Abstände der Punkte p (…, 2) zu den Strecken a–b (…, 2), broadcastend."""
    d = b - a
    n = np.maximum((d * d).sum(-1), 1e-12)
    t = np.clip(((p - a) * d).sum(-1) / n, 0.0, 1.0)
    return np.linalg.norm(p - (a + t[..., None] * d), axis=-1)


def _crosses(p: np.ndarray, q: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Je Kandidat q (k, 2): schneidet die Strecke p–q eine der Strecken a–b (m, 2)?"""

    def side(o, u, v):
        return (u[..., 0] - o[..., 0]) * (v[..., 1] - o[..., 1]) - (
            u[..., 1] - o[..., 1]
        ) * (v[..., 0] - o[..., 0])

    q = q[:, None]
    d1 = side(a[None], b[None], p)
    d2 = side(a[None], b[None], q)
    d3 = side(p, q, a[None])
    d4 = side(p, q, b[None])
    # Toleranz: ein Schweratom, das genau auf einer Bindungslinie liegt (Cuban),
    # soll seine H nicht durch Rundungsrauschen als „kreuzend“ verlieren.
    eps = 1e-9
    return ((d1 * d2 < -eps) & (d3 * d4 < -eps)).any(1)


def add_hydrogens_2d(mol: Chem.Mol) -> Chem.Mol:
    """AddHs mit 2D-Koordinaten; H in Engstellen werden neu gesetzt.

    Die Schweratom-Indizes bleiben vorn und ihre Koordinaten unverändert;
    ohne Engstelle ist das Ergebnis identisch mit AddHs.
    """
    mol_h = Chem.AddHs(mol, addCoords=True)
    if mol_h.GetNumConformers() == 0:
        return mol_h
    conf = mol_h.GetConformer()
    pos = np.array(conf.GetPositions()[:, :2], dtype=float)
    n = len(pos)
    is_h = np.array([a.GetAtomicNum() == 1 for a in mol_h.GetAtoms()])
    bonds = np.array(
        [
            (b.GetBeginAtomIdx(), b.GetEndAtomIdx())
            for b in mol_h.GetBonds()
            if not is_h[b.GetBeginAtomIdx()] and not is_h[b.GetEndAtomIdx()]
        ],
        dtype=int,
    ).reshape(-1, 2)
    unit = (
        float(np.linalg.norm(pos[bonds[:, 0]] - pos[bonds[:, 1]], axis=1).mean())
        if len(bonds)
        else 1.5
    )
    parent = {
        a.GetIdx(): a.GetNeighbors()[0].GetIdx()
        for a in mol_h.GetAtoms()
        # Nur die von AddHs angehängten H; explizite H der Eingabe ([2H]) gehören
        # zum Gerüst der 2D-Ansicht und bleiben stehen.
        if a.GetAtomicNum() == 1
        and a.GetDegree() == 1
        and a.GetIdx() >= mol.GetNumAtoms()
    }
    placed = np.ones(n, dtype=bool)  # H, die gerade neu gesetzt werden, zählen nicht

    def clearance(h: int, cand: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Freiraum der Kandidaten cand (k, 2) in Bindungslängen: (zu Atomen, zu Linien).

        Linien sind fremde wie eigene Gerüstbindungen sowie die eigene C–H-Linie
        über fremde Schweratome hinweg — ein H auf einem Strich verschwindet darin.
        """
        par = parent[h]
        near = np.linalg.norm(pos - pos[par], axis=1) < _REACH * unit
        others = placed & near
        others[[h, par]] = False
        k = len(cand)
        point = line = np.full(k, np.inf)
        if others.any():
            point = np.linalg.norm(cand[:, None] - pos[others][None], axis=-1).min(1)
        heavy = others & ~is_h
        if heavy.any():
            line = _seg_dist(pos[heavy][None], pos[par], cand[:, None]).min(1)
        if len(bonds):
            close = near[bonds[:, 0]] | near[bonds[:, 1]]
            if close.any():
                a, b = pos[bonds[close, 0]], pos[bonds[close, 1]]
                line = np.minimum(
                    line, _seg_dist(cand[:, None], a[None], b[None]).min(1)
                )
                # Die C–H-Linie darf keine fremde Bindung kreuzen.
                foreign = (bonds[close, 0] != par) & (bonds[close, 1] != par)
                if foreign.any():
                    hit = _crosses(pos[par], cand, a[foreign], b[foreign])
                    line = np.where(hit, 0.0, line)
        return point / unit, line / unit

    def clear_now(h: int) -> tuple[float, float]:
        point, line = clearance(h, pos[h][None])
        return float(point[0]), float(line[0])

    crowded = {
        h
        for h in parent
        if (c := clear_now(h))[0] < CLEARANCE or c[1] < _LINE_CLEARANCE
    }
    if not crowded:
        return mol_h
    # Alle H eines betroffenen Schweratoms werden gemeinsam neu verteilt.
    parents = {parent[c] for c in crowded}
    movable = sorted(h for h in parent if parent[h] in parents)
    # Ursprüngliche C–H-Länge je H: Bezug für die Kürzung, auch nach dem ersten Zug.
    h_len = {
        h: float(np.linalg.norm(pos[h] - pos[parent[h]])) or 0.67 * unit
        for h in movable
    }
    ring = np.stack([np.cos(_ANGLES), np.sin(_ANGLES)], axis=1)
    offsets = (_RADII[:, None, None] * ring[None]).reshape(-1, 2)
    radii = np.repeat(_RADII, len(_ANGLES))

    def best_spot(h: int) -> tuple[np.ndarray, float]:
        cand = pos[parent[h]] + h_len[h] * offsets
        scores = _score(*clearance(h, cand), radii)
        i = int(np.argmax(scores))  # erstes Maximum: längste Bindung, kleinster Winkel
        return cand[i], float(scores[i])

    def settle(order: list[int]) -> None:
        placed[movable] = False
        for h in order:
            pos[h] = best_spot(h)[0]
            placed[h] = True
        # Nachbessern: jedes H noch einmal gegen alle anderen.
        for _ in range(_PASSES):
            changed = False
            for h in order:
                radius = float(np.linalg.norm(pos[h] - pos[parent[h]])) / h_len[h]
                current = float(_score(*map(np.array, clear_now(h)), np.array(radius)))
                spot, score = best_spot(h)
                if score > current + 1e-6:
                    pos[h] = spot
                    changed = True
            if not changed:
                break

    def quality() -> tuple:
        """Gesamturteil: engstes H (bis _GOOD), dann engste Linie, dann Summe."""
        cs = [clear_now(h) for h in movable]
        return (
            round(min(min(c[0] for c in cs), _GOOD), 3),
            round(min(min(c[1] for c in cs), _LINE_TARGET), 3),
            float(
                sum(_score(np.array(c[0]), np.array(c[1]), np.array(1.0)) for c in cs)
            ),
        )

    # Gierig platziert hängt das Ergebnis an der Reihenfolge: einige probieren,
    # das beste behalten. Engste zuerst ist der Normalfall.
    crowded_first = sorted(movable, key=lambda h: clear_now(h)[0])
    best_pos, best_q = None, None
    for order in (crowded_first, crowded_first[::-1], movable, movable[::-1]):
        settle(order)
        q = quality()
        if best_q is None or q > best_q:
            best_pos, best_q = pos.copy(), q
    pos[:] = best_pos
    for h in movable:
        conf.SetAtomPosition(h, Point3D(float(pos[h][0]), float(pos[h][1]), 0.0))
    return mol_h


def _score(point: np.ndarray, line: np.ndarray, radius: np.ndarray) -> np.ndarray:
    """Erst Abstand zu Atomen/H, dann zu Linien (je bis zum Ziel), dann möglichst
    lange Bindung, dann mehr Luft."""
    return (
        np.minimum(point, _TARGET) * 100
        + np.minimum(line, _LINE_TARGET) * _LINE_WEIGHT
        + radius
        + 0.01 * np.minimum(point, 2.0)
    )
