"""Cartoon-Geometrie eines Proteins (E13): Band, Pfeil, Röhre als Querschnittsfolge.

Ein Segment ist EIN durchgehender Spline (uniformes Catmull-Rom durch die
Kontrollpunkte, `sub` Stützstellen je Rest). Jede Stützstelle trägt einen
Querschnitt — Superellipse mit Breite, Dicke und Exponent —, der zwischen den
Resten weich überblendet. So entstehen Helixband, Strangpfeil und Schleifenröhre
aus demselben Netz, ohne Naht oder Sprung an den Übergängen.

Bandorientierung (wie Carson & Bugg 1986, MolScript, PyMOL): Die Breite liegt
in der Peptidebene, Richtung Cα→O, orthogonal zur Tangente. Im Strang zeigt das
C=O in der Faltblattebene (die H-Brücken zum Nachbarstrang), das Band liegt also
flach im Blatt; in der Helix zeigt es entlang der Achse, das Band windet sich
außen um den Helixzylinder. C=O wechselt im Strang von Rest zu Rest die Seite —
das Vorzeichen wird deshalb so gewählt, dass benachbarte Normalen nie
umklappen (Skalarprodukt > 0), danach wird im Strang geglättet.

Strangpfeil: am vorletzten Rest springt der Querschnitt von STRAND_WIDTH auf
ARROW_WIDTH (doppelter Querschnitt an derselben Stelle = Schulter des Pfeils),
dann linear bis zum letzten Rest auf Schleifenbreite — die Spitze zeigt zum
C-Terminus und geht nahtlos in die folgende Röhre über.

Alle Maße in Å.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HELIX_WIDTH = 2.4
HELIX_THICKNESS = 0.5
STRAND_WIDTH = 2.0
STRAND_THICKNESS = 0.5
ARROW_WIDTH = 3.2
LOOP_RADIUS = 0.3
MIN_HELIX = 4  # kürzere Helixstücke (DSSP-Reste an Schleifen) zeichnet niemand als Band
MIN_STRAND = 3  # Zwei-Rest-Stränge (Blattränder) wären nur Fähnchen statt Pfeile
SUBDIVIDE = 6

# Querschnitt je Code: (Breite, Dicke, Superellipsen-Exponent: 2 = Kreis, groß = Rechteck)
DIMS = {
    "H": (HELIX_WIDTH, HELIX_THICKNESS, 5.0),
    "E": (STRAND_WIDTH, STRAND_THICKNESS, 8.0),
    "C": (2 * LOOP_RADIUS, 2 * LOOP_RADIUS, 2.0),
}

# Kovalenzradien (Å, Cordero et al. 2008), für Ligandenbindungen per Abstand
COVALENT_RADIUS = {
    "H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "P": 1.07, "S": 1.05,
    "Cl": 1.02, "Br": 1.20, "I": 1.39, "B": 0.84, "Se": 1.20, "Fe": 1.32, "Zn": 1.22,
    "Cu": 1.32, "Mg": 1.41, "Mn": 1.39, "Co": 1.26, "Ni": 1.24, "Ca": 1.76, "Na": 1.66,
    "K": 2.03, "Mo": 1.54, "W": 1.62, "V": 1.53, "Cd": 1.44, "Hg": 1.32, "Pt": 1.36,
}
BOND_TOLERANCE = 0.4


def _runs(ss: str):
    """(Code, Start, Ende einschließlich) je zusammenhängendem Lauf."""
    i, out = 0, []
    while i < len(ss):
        j = i
        while j < len(ss) and ss[j] == ss[i]:
            j += 1
        out.append((ss[i], i, j - 1))
        i = j
    return out


def effective_ss(ss: str) -> str:
    """Zu kurze Helix-/Strangstücke werden Schleife — sie trügen kein Band und keinen Pfeil."""
    out = list(ss)
    for code, start, end in _runs(ss):
        n = end - start + 1
        if (code == "H" and n < MIN_HELIX) or (code == "E" and n < MIN_STRAND) or code not in "HE":
            out[start:end + 1] = "C" * n
    return "".join(out)


def control_points(ca: np.ndarray, ss: str) -> np.ndarray:
    """Kontrollpunkte des Splines: Cα; im Strang ohne das Zickzack der Faltung.

    Die Helix behält die echte Cα-Spirale (das Band windet sich darum), der
    Strang wird mit (¼, ½, ¼) zweimal geglättet. Die Enden jedes Laufs bleiben,
    damit Schleifen anschließen.
    """
    ca = np.asarray(ca, dtype=float)
    pts = ca.copy()
    eff = effective_ss(ss)
    for code, start, end in _runs(eff):
        if code != "E" or end - start < 2:
            continue
        for _ in range(2):
            inner = 0.25 * pts[start:end - 1] + 0.5 * pts[start + 1:end] + 0.25 * pts[start + 2:end + 1]
            pts[start + 1:end] = inner
    return pts


def _tangents(pts: np.ndarray) -> np.ndarray:
    t = np.empty_like(pts)
    if len(pts) == 1:
        return np.array([[1.0, 0.0, 0.0]])
    t[1:-1] = pts[2:] - pts[:-2]
    t[0] = pts[1] - pts[0]
    t[-1] = pts[-1] - pts[-2]
    return t / np.maximum(np.linalg.norm(t, axis=1), 1e-9)[:, None]


def _orthonormal(vec: np.ndarray, tan: np.ndarray) -> np.ndarray:
    v = vec - np.einsum("ij,ij->i", vec, tan)[:, None] * tan
    return v / np.maximum(np.linalg.norm(v, axis=1), 1e-12)[:, None]


def _any_perpendicular(t: np.ndarray) -> np.ndarray:
    ref = np.array([0.0, 0.0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    v = np.cross(t, ref)
    return v / np.linalg.norm(v)


def side_vectors(ca: np.ndarray, o: np.ndarray, ss: str) -> np.ndarray:
    """Breitenrichtung je Rest: Cα→O ⊥ Tangente, Vorzeichen ohne Umklappen.

    Fehlt das O (NaN: Chromophor, CA-only-Einträge), wird zwischen den
    Nachbarn gemittelt; fehlt es überall, nimmt die Krümmungsrichtung seinen Platz.
    """
    ca = np.asarray(ca, dtype=float)
    n = len(ca)
    pts = control_points(ca, ss)
    tan = _tangents(pts)
    o = np.asarray(o, dtype=float) if o is not None and len(o) == n else np.full((n, 3), np.nan)
    raw = o - ca
    raw = raw - np.einsum("ij,ij->i", np.nan_to_num(raw), tan)[:, None] * tan
    norm = np.linalg.norm(raw, axis=1)
    valid = np.isfinite(norm) & (norm > 0.3)
    sides = np.zeros((n, 3))
    sides[valid] = raw[valid] / norm[valid][:, None]
    idx = np.flatnonzero(valid)
    if len(idx) == 0:
        # keine Carbonyle: Krümmungsrichtung, sonst irgendeine Senkrechte
        for i in range(n):
            if 0 < i < n - 1:
                k = pts[i - 1] + pts[i + 1] - 2 * pts[i]
                k = k - (k @ tan[i]) * tan[i]
                if np.linalg.norm(k) > 1e-3:
                    sides[i] = k / np.linalg.norm(k)
                    continue
            sides[i] = _any_perpendicular(tan[i])
    else:
        for a, b in zip(idx[:-1], idx[1:]):
            if sides[b] @ sides[a] < 0:
                sides[b] = -sides[b]
        for i in range(n):
            if valid[i]:
                continue
            before = idx[idx < i]
            after = idx[idx > i]
            v = (sides[before[-1]] if len(before) else 0) + (sides[after[0]] if len(after) else 0)
            if np.linalg.norm(v) < 1e-6:
                v = sides[before[-1]] if len(before) else sides[after[0]]
            sides[i] = v
    sides = _orthonormal(sides, tan)
    eff = effective_ss(ss)
    for code, start, end in _runs(eff):
        if code != "E" or end - start < 2:
            continue
        smooth = sides.copy()
        smooth[start + 1:end] = sides[start:end - 1] + 2 * sides[start + 1:end] + sides[start + 2:end + 1]
        # Enden einseitig mitglätten — sonst verdreht sich das Band am ersten/letzten Rest
        smooth[start] = 2 * sides[start] + sides[start + 1]
        smooth[end] = sides[end - 1] + 2 * sides[end]
        sides = _orthonormal(smooth, tan)
    # Nach Glättung/Orthogonalisierung erneut kein Umklappen
    for i in range(1, n):
        if sides[i] @ sides[i - 1] < 0:
            sides[i] = -sides[i]
    return sides


@dataclass
class Tube:
    """Querschnittsfolge eines Segments (M Stützstellen)."""

    centers: np.ndarray  # M×3
    tangents: np.ndarray  # M×3, Einheitsvektoren
    sides: np.ndarray  # M×3, Breitenrichtung (⊥ Tangente)
    binormals: np.ndarray  # M×3, Dickenrichtung = Tangente × Seite
    width: np.ndarray  # M
    thickness: np.ndarray  # M
    exponent: np.ndarray  # M, Superellipse
    u: np.ndarray  # M, Lage in Resten (0 = erster Rest)
    residue: np.ndarray  # M, int — welcher Rest färbt die Stützstelle
    outer: np.ndarray  # M, +1/−1: Seite (+/− Binormale) außen an der Helix; 0 = egal
    ss: str  # wirksame Sekundärstruktur je Rest

    def rings(self, k: int = 8) -> np.ndarray:
        """Querschnittspunkte M×K×3, gegen den Uhrzeigersinn um die Tangente."""
        theta = 2 * np.pi * (np.arange(k) + 0.5) / k
        c, s = np.cos(theta), np.sin(theta)
        e = 2.0 / self.exponent[:, None]
        x = 0.5 * self.width[:, None] * np.sign(c) * np.abs(c)[None, :] ** e
        y = 0.5 * self.thickness[:, None] * np.sign(s) * np.abs(s)[None, :] ** e
        return (self.centers[:, None, :] + x[..., None] * self.sides[:, None, :]
                + y[..., None] * self.binormals[:, None, :])

    def profile_side(self, k: int = 8) -> np.ndarray:
        """Je Querschnittsfläche j (zwischen Punkt j und j+1): +1 oben (+Binormale), −1 unten."""
        theta = 2 * np.pi * (np.arange(k) + 1.0) / k  # Mitte der Fläche j
        s = np.sin(theta)
        return np.where(s > 1e-9, 1, np.where(s < -1e-9, -1, 0))


def _catmull_rom(pts: np.ndarray, seg: np.ndarray, t: np.ndarray):
    ext = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    p0, p1, p2, p3 = ext[seg], ext[seg + 1], ext[seg + 2], ext[seg + 3]
    t = t[:, None]
    t2, t3 = t * t, t * t * t
    pos = 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
    der = 0.5 * ((-p0 + p2) + 2 * (2 * p0 - 5 * p1 + 4 * p2 - p3) * t
                 + 3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t2)
    return pos, der


def _helix_outer(ca: np.ndarray, pts: np.ndarray, sides: np.ndarray, eff: str) -> np.ndarray:
    """Je Rest: welche Bandseite (+/− Binormale) zeigt von der Helixachse weg."""
    n = len(ca)
    out = np.zeros(n)
    tan = _tangents(pts)
    binorm = np.cross(tan, sides)
    for code, start, end in _runs(eff):
        if code != "H":
            continue
        score = 0.0
        for i in range(start, end + 1):
            lo, hi = max(start, i - 1), min(end + 1, i + 3)
            if hi - lo < 4:
                lo, hi = max(start, hi - 4), min(end + 1, lo + 4)
            axis_pt = ca[lo:hi].mean(axis=0)
            score += binorm[i] @ (ca[i] - axis_pt)
        out[start:end + 1] = 1.0 if score >= 0 else -1.0
    return out


def _transport(prev: np.ndarray, tangent: np.ndarray) -> np.ndarray:
    v = prev - (prev @ tangent) * tangent
    return v / max(np.linalg.norm(v), 1e-12)


def _untwist_round_runs(sides: np.ndarray, tangents: np.ndarray, round_: np.ndarray) -> np.ndarray:
    """Runde Röhrenstücke: Rahmen per Paralleltransport statt Schleifen-C=O.

    In Schleifen zeigen die Carbonyle kreuz und quer; der Kreisquerschnitt
    sieht das nicht, wohl aber die Schattierung der Facetten — sie verdrehen
    sich zu einem Schachbrett. Der Transport hält die Facetten gerade; den
    Winkel, der am Ende zum nächsten Band fehlt, verteilt er gleichmäßig.
    """
    sides = sides.copy()
    m_total = len(sides)
    m = 0
    while m < m_total:
        if not round_[m]:
            m += 1
            continue
        a = m
        while m < m_total and round_[m]:
            m += 1
        b = m - 1
        new = np.empty((b - a + 1, 3))
        new[0] = _transport(sides[a - 1], tangents[a]) if a > 0 else sides[a]
        for i in range(1, len(new)):
            new[i] = _transport(new[i - 1], tangents[a + i])
        if b + 1 < m_total:
            t = tangents[b + 1]
            got = _transport(new[-1], t)
            target = sides[b + 1]
            phi = np.arctan2(np.cross(got, target) @ t, got @ target)
            steps = len(new) + 1
            for i in range(len(new)):
                ti = tangents[a + i]
                ang = phi * (i + 1) / steps
                v = new[i]
                new[i] = v * np.cos(ang) + np.cross(ti, v) * np.sin(ang)
        sides[a:b + 1] = new
    return sides


def build_tube(ca: np.ndarray, o: np.ndarray, ss: str, sub: int = SUBDIVIDE) -> Tube:
    """Spline mit Querschnitten für ein lückenloses Segment (≥ 2 Reste)."""
    ca = np.asarray(ca, dtype=float)
    n = len(ca)
    if n < 2:
        raise ValueError("a tube needs at least two residues")
    eff = effective_ss(ss)
    pts = control_points(ca, ss)
    res_sides = side_vectors(ca, o, ss)
    outer_res = _helix_outer(ca, pts, res_sides, eff)

    def strand_end(i: int) -> bool:
        return eff[i] == "E" and (i + 1 >= n or eff[i + 1] != "E")

    loop = DIMS["C"]
    seg_idx, ts, dims, color_res = [], [], [], []
    for i in range(n - 1):
        a, b = eff[i], eff[i + 1]
        steps = [k / sub for k in range(sub)] + ([1.0] if i == n - 2 else [])
        arrow = a == "E" and b == "E" and strand_end(i + 1)
        start = loop if strand_end(i) else DIMS[a]
        end = DIMS[b]
        for t in steps:
            if arrow:
                if t == 0.0:  # Schulter: Schaftquerschnitt, dann Pfeilquerschnitt am selben Ort
                    seg_idx.append(i)
                    ts.append(0.0)
                    dims.append(DIMS["E"])
                    color_res.append(i)
                lin = t
                w = ARROW_WIDTH * (1 - lin) + loop[0] * lin
                th = STRAND_THICKNESS * (1 - lin) + loop[1] * lin
                p = DIMS["E"][2] * (1 - lin) + loop[2] * lin
                dims.append((w, th, p))
                color_res.append(i if t < 1.0 else i + 1)
            else:
                s = t * t * (3 - 2 * t)
                dims.append(tuple(start[j] * (1 - s) + end[j] * s for j in range(3)))
                if strand_end(i) and t > 0:
                    color_res.append(i + 1)  # nach der Pfeilspitze beginnt die Schleife
                else:
                    # Die Farbe folgt der Form: alles merklich Breitere als die Röhre
                    # trägt schon die Farbe von Helix/Strang, keine grauen Bandzipfel.
                    switch = 0.5
                    if start == loop and end != loop:
                        switch = 0.15
                    elif end == loop and start != loop:
                        switch = 0.85
                    color_res.append(i if s < switch else i + 1)
            seg_idx.append(i)
            ts.append(t)
    seg_idx = np.array(seg_idx)
    ts = np.array(ts)
    centers, der = _catmull_rom(pts, seg_idx, ts)
    tangents = der / np.maximum(np.linalg.norm(der, axis=1), 1e-9)[:, None]
    nxt = np.minimum(seg_idx + 1, n - 1)
    raw = res_sides[seg_idx] * (1 - ts)[:, None] + res_sides[nxt] * ts[:, None]
    sides = _orthonormal(raw, tangents)
    for m in range(1, len(sides)):
        if sides[m] @ sides[m - 1] < 0:  # Sicherheitsnetz; tritt bei Vorzeichenpflege nicht auf
            sides[m] = -sides[m]
    dims = np.array(dims, dtype=float)
    round_ = (dims[:, 2] == 2.0) & (dims[:, 0] == dims[:, 1])
    sides = _untwist_round_runs(sides, tangents, round_)
    binormals = np.cross(tangents, sides)
    res = np.array(color_res)
    outer = np.where(np.array([eff[r] for r in res]) == "H", outer_res[res], 0.0)
    return Tube(
        centers=centers, tangents=tangents, sides=sides, binormals=binormals,
        width=dims[:, 0], thickness=dims[:, 1], exponent=dims[:, 2],
        u=seg_idx + ts, residue=res, outer=outer, ss=eff,
    )


def cartoon_tubes(view, sub: int = SUBDIVIDE) -> list:
    """(Kettenindex, Segment, Tube) je Segment mit ≥ 2 Resten — kein Band über Lücken."""
    out = []
    for ci, chain in enumerate(view.chains):
        for seg in chain["segments"]:
            if len(seg.ca) >= 2:
                out.append((ci, seg, build_tube(seg.ca, seg.o, seg.ss, sub)))
    return out


def ligand_bonds(elements: list[str], xyz: np.ndarray) -> list[tuple[int, int]]:
    """Bindungen per Abstand: d < r₁ + r₂ + Toleranz (Kovalenzradien)."""
    xyz = np.asarray(xyz, dtype=float)
    if len(xyz) < 2:
        return []
    radii = np.array([COVALENT_RADIUS.get(e.capitalize(), 0.77) for e in elements])
    d = np.linalg.norm(xyz[:, None, :] - xyz[None, :, :], axis=2)
    limit = radii[:, None] + radii[None, :] + BOND_TOLERANCE
    i, j = np.nonzero(np.triu((d < limit) & (d > 0.4), k=1))
    return list(zip(i.tolist(), j.tolist()))
