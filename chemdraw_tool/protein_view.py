"""Ansicht eines Proteins: gedrehte Koordinaten für Datei und Panel (E8, E13).

Die Koordinaten werden schwerpunktzentriert in eine feste Ansicht gedreht
(`choose_frame`, Grundlage: Hauptachsen — größte Ausdehnung waagrecht,
zweitgrößte senkrecht, die kleinste zeigt zum Betrachter). Das ist eine echte
Drehung (Determinante +1), keine Spiegelung: Helices bleiben rechtsgängig.
Die Panel-Daten tragen die bereits gedrehten Koordinaten — Ruhelage des
Panels = Identität, also zeigen Panel und Datei dieselbe Ausgangsansicht.

Panel-Format (E13): je Segment Cα als Base64 aus int16 (Little Endian) in
0,1 Å und das Carbonyl-O als Base64 aus int8-Abständen zum Cα in 0,1 Å
(0,0,0 = fehlt). 12 Zeichen je Rest statt ~15 für das alte Cα-Textformat —
mit O, das der Cartoon für die Bandorientierung braucht. Die Antwort trägt die
Daten zweimal (Text für das Modell + structuredContent), und über ~150 000
Zeichen bekommt das Panel sie in Claude gar nicht (Anthropic-Doku
„Troubleshooting“), darum zählt hier jedes Zeichen.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np

from chemdraw_tool.protein_structure import Backbone

# Okabe-Ito; schwere Kette blau, leichte orange wie im IgG-Schema (igg_scheme.py).
CHAIN_PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#7a5195", "#4d4d4d"]


class ViewSegment(NamedTuple):
    """Ein gedrehtes Segment: Cα (N×3), Sekundärstruktur, pLDDT, Carbonyl-O (N×3, NaN = fehlt)."""

    ca: np.ndarray
    ss: str
    plddt: list[float]
    o: np.ndarray


@dataclass
class ViewLigand:
    code: str
    name: str
    chain: str
    elements: list[str]
    xyz: np.ndarray  # gedreht, N×3


@dataclass
class View:
    """Gedrehte Struktur, je Kette: id, label, color, first, last, segments."""

    chains: list[dict]
    residues: int
    source: str
    identifier: str
    plddt_mean: float | None
    ligands: list[ViewLigand] = field(default_factory=list)
    ss_source: str = "deposited"


def principal_frame(points: np.ndarray, first: np.ndarray) -> np.ndarray:
    """Drehmatrix (Zeilen = neue Achsen x, y, z) in die Hauptachsen.

    x = größte Ausdehnung, y = zweitgrößte, z = x × y (rechtshändig). Das erste
    Cα (N-Terminus) liegt links; dafür wird um z gedreht, nie gespiegelt.
    """
    centered = points - points.mean(axis=0)
    _, vecs = np.linalg.eigh(centered.T @ centered)
    ex, ey = vecs[:, 2], vecs[:, 1]
    if (first - points.mean(axis=0)) @ ex > 0:
        ex, ey = -ex, -ey  # 180° um z
    ez = np.cross(ex, ey)
    return np.vstack([ex, ey, ez])


TILT_DEG = 30.0  # Kandidaten: Hauptachsen, ±30° um x und um y gekippt
OVERLAP_CELL = 1.5  # Å; Rasterweite der Überdeckungsmessung
TILT_PENALTY = 1.08  # gekippte Ansicht muss die Überdeckung um > 8 % senken


def _rot_x(deg: float) -> np.ndarray:
    a = np.radians(deg)
    return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])


def _rot_y(deg: float) -> np.ndarray:
    a = np.radians(deg)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def self_overlap(points: np.ndarray, rot: np.ndarray, cell: float = OVERLAP_CELL) -> float:
    """Selbstüberdeckung der projizierten Cα-Spur (kleiner = übersichtlicher).

    Die Spur wird dreifach verdichtet und auf ein Raster (cell Å) projiziert;
    gezählt wird je Zelle, wie viele verschiedene Kettenabschnitte (je 4 Reste)
    sie treffen, minus eins — Nachbarreste, die sich ohnehin eine Zelle teilen,
    zählen also nicht, übereinanderliegende Helices schon. Normiert auf die Restzahl.
    """
    pts = np.asarray(points, dtype=float) - np.asarray(points, dtype=float).mean(axis=0)
    n = len(pts)
    if n < 2:
        return 0.0
    frac = np.array([0.0, 1 / 3, 2 / 3])
    dense = (pts[:-1, None, :] * (1 - frac)[None, :, None]
             + pts[1:, None, :] * frac[None, :, None]).reshape(-1, 3)
    dense = np.vstack([dense, pts[-1:]])
    group = np.append(np.repeat(np.arange(n - 1), 3), n - 1) // 4
    xy = np.floor((dense @ rot.T)[:, :2] / cell).astype(np.int64)
    xy -= xy.min(axis=0)
    key = (xy[:, 0] * (xy[:, 1].max() + 1) + xy[:, 1]) * (group.max() + 1) + group
    pairs = np.unique(key) // (group.max() + 1)
    _, counts = np.unique(pairs, return_counts=True)
    return float((counts - 1).sum()) / n


def choose_frame(backbone: Backbone, points: np.ndarray) -> np.ndarray:
    """Ansicht für Datei und Panel: Hauptachsen oder leicht gekippt, je nach Überdeckung.

    Kandidaten sind die Hauptachsenansicht und vier Kippungen (±TILT_DEG um x
    und y); gewählt wird die mit der geringsten Selbstüberdeckung, die
    Hauptachsen gewinnen Gleichstände (TILT_PENALTY). Das Vorzeichen der
    zweiten Achse ist festgelegt (dritte Momente ≥ 0), sonst entschiede LAPACK
    über die Blickseite. Zum Schluss liegt der N-Terminus links (180° um z) —
    immer eine echte Drehung, nie eine Spiegelung.
    """
    pts = np.asarray(points, dtype=float)
    center = pts.mean(axis=0)
    base = principal_frame(pts, pts[0])
    if np.sum(((pts - center) @ base[1]) ** 3) < 0:
        base = np.diag([1.0, -1.0, -1.0]) @ base  # 180° um x: Blickseite festlegen
    candidates = [base] + [r @ base for r in (_rot_x(TILT_DEG), _rot_x(-TILT_DEG),
                                              _rot_y(TILT_DEG), _rot_y(-TILT_DEG))]
    scores = [self_overlap(pts, r) * (1.0 if i == 0 else TILT_PENALTY)
              for i, r in enumerate(candidates)]
    rot = candidates[int(np.argmin(scores))]
    if (pts[0] - center) @ rot[0] > 0:
        rot = np.diag([-1.0, -1.0, 1.0]) @ rot  # 180° um z: N-Terminus links
    return rot


def chain_color(i: int, label: str) -> str:
    lab = label.casefold()
    if "heavy" in lab:
        return "#0072B2" if not lab.endswith("2") else "#56B4E9"
    if "light" in lab:
        return "#E69F00" if not lab.endswith("2") else "#D55E00"
    if lab.startswith("α"):
        return "#0072B2" if lab.endswith("1") else "#56B4E9"
    if lab.startswith("β"):
        return "#D55E00" if lab.endswith("1") else "#E69F00"
    return CHAIN_PALETTE[i % len(CHAIN_PALETTE)]


def plddt_class(value: float) -> str:
    """AlphaFold-Konfidenzklassen: 4 >90, 3 70–90, 2 50–70, 1 <50."""
    return "4" if value > 90 else "3" if value > 70 else "2" if value > 50 else "1"


def _points(values) -> np.ndarray:
    return np.array([p if p is not None else (np.nan, np.nan, np.nan) for p in values], dtype=float)


def make_view(backbone: Backbone, chain_labels: dict[str, str] | None = None) -> View:
    chain_labels = chain_labels or {}
    allpts = np.array([p for s in backbone.segments for p in s.coords], dtype=float)
    center = allpts.mean(axis=0)
    rot = choose_frame(backbone, allpts)
    chains: dict[str, dict] = {}
    for seg in backbone.segments:
        ca = (np.asarray(seg.coords, dtype=float) - center) @ rot.T
        o = _points(seg.o or [None] * len(seg.coords))
        o = (o - center) @ rot.T  # NaN bleibt NaN
        entry = chains.setdefault(seg.chain, {"id": seg.chain, "segments": [], "first": seg.first})
        entry["segments"].append(ViewSegment(ca, seg.ss, list(seg.plddt), o))
        entry["last"] = seg.last
    ordered = list(chains.values())
    for i, c in enumerate(ordered):
        c["label"] = chain_labels.get(c["id"], f"chain {c['id']}")
        c["color"] = chain_color(i, c["label"])
    ligands = [
        ViewLigand(lig.code, lig.name, lig.chain, list(lig.elements),
                   (np.asarray(lig.coords, dtype=float) - center) @ rot.T)
        for lig in backbone.ligands
    ]
    plddt = [v for s in backbone.segments for v in s.plddt]
    return View(
        chains=ordered,
        residues=backbone.residue_count,
        source=backbone.source,
        identifier=backbone.identifier,
        plddt_mean=round(sum(plddt) / len(plddt), 1) if plddt else None,
        ligands=ligands,
        ss_source=backbone.ss_source,
    )


# --- Panel-Format ---------------------------------------------------------------


def encode_xyz(points: np.ndarray) -> str:
    """N×3 in Å → Base64 aus int16 LE in 0,1 Å."""
    ints = np.clip(np.rint(points * 10), -32767, 32767).astype("<i2")
    return base64.b64encode(ints.tobytes()).decode("ascii")


def decode_xyz(text: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(text), dtype="<i2").reshape(-1, 3).astype(float) / 10


def encode_offsets(ca: np.ndarray, o: np.ndarray) -> str:
    """O − Cα je Rest als int8 in 0,1 Å (C=O liegt 2,4 Å vom Cα); fehlendes O → 0,0,0."""
    ca_r = np.rint(ca * 10) / 10  # Bezug ist das gerundete Cα, das das Panel sieht
    delta = np.nan_to_num(o - ca_r, nan=0.0)
    ints = np.clip(np.rint(delta * 10), -127, 127).astype("i1")
    return base64.b64encode(ints.tobytes()).decode("ascii")


def decode_offsets(text: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(text), dtype="i1").reshape(-1, 3).astype(float) / 10


def panel_chains(view: View) -> list[dict]:
    """Ketten fürs Panel: je Segment `ca`, `o` (Base64), `ss`, ggf. `q` (pLDDT-Klasse)."""
    out = []
    for c in view.chains:
        segs = []
        for seg in c["segments"]:
            item = {"ca": encode_xyz(seg.ca), "o": encode_offsets(seg.ca, seg.o), "ss": seg.ss}
            if seg.plddt:
                item["q"] = "".join(plddt_class(v) for v in seg.plddt)
            segs.append(item)
        out.append({"id": c["id"], "label": c["label"], "color": c["color"],
                    "first": c.get("first", ""), "last": c.get("last", ""), "segments": segs})
    return out


def panel_ligands(view: View) -> list[dict]:
    """Liganden fürs Panel: Elemente als Text, Koordinaten wie `ca`."""
    return [{"code": lig.code, "name": lig.name, "chain": lig.chain,
             "e": " ".join(lig.elements), "xyz": encode_xyz(lig.xyz)} for lig in view.ligands]
