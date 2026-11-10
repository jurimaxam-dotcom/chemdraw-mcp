"""Protein als Cartoon (Bänderdiagramm) im Bild — PNG und Vektor-SVG (E8, E13).

Ansicht: `protein_view.choose_frame` (Hauptachsen, ggf. leicht gekippt), echte
Drehung, orthografische Projektion; z zeigt zum Betrachter.

Geometrie: `protein_cartoon` — ein Spline je Segment, Querschnitt je Stützstelle
(Helixband, Strangpfeil, Schleifenröhre). Hier wird daraus ein Polygonnetz:

  - Vierecke zwischen benachbarten Querschnitten, Rückseiten verworfen
    (geschlossene Röhre), Maleralgorithmus nach Flächenschwerpunkt-Tiefe;
  - Schattierung je Fläche: Umgebungslicht + Lambert + Blinn-Glanz, Licht von
    links oben vorn; Innenseite der Helixbänder dunkler;
  - Konturen nur an Silhouetten (Vorder-/Rückseite wechseln) und scharfen
    Kanten (> 50°) — nie an den Quernähten; als kurze Strecken in derselben
    Tiefensortierung, direkt hinter ihrer Fläche;
  - Tiefennebel: hinten bis FOG Weiß beigemischt;
  - jede Fläche mit dünnem Rand in der eigenen Farbe — sonst zeigt das
    Antialiasing Haarrisse zwischen Nachbarflächen.

Liganden als Kugel-Stab-Modell (Elementfarben, C grau), Ionen als Kugeln, in
derselben Tiefensortierung. Das SVG ist reiner Vektor (Polygone),
deterministisch (`svg.hashsalt`), Koordinaten auf 0,1 pt gerundet.
"""

from __future__ import annotations

import io
import math
import re
import textwrap

import matplotlib
import numpy as np

matplotlib.use("Agg")

from matplotlib import rc_context  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from chemdraw_tool import protein_cartoon as pc  # noqa: E402
from chemdraw_tool.ph_plots import safe_text  # noqa: E402
from chemdraw_tool.protein_view import (  # noqa: E402,F401 — Wiederexport für Aufrufer
    CHAIN_PALETTE,
    View,
    ViewSegment,
    chain_color,
    choose_frame,
    make_view,
    panel_chains,
    panel_ligands,
    plddt_class,
    principal_frame,
    self_overlap,
)

# --- Palette (das Panel übernimmt dieselben Werte) ---------------------------------
SS_COLOR = {"H": "#c8423b", "E": "#d99a00", "C": "#9da3ab"}
SS_NAME = {"H": "α-helix", "E": "β-strand", "C": "loop"}
ELEMENT_COLOR = {
    "C": "#8c8c8c", "N": "#3050f8", "O": "#e8212b", "S": "#e6c619", "P": "#ff8000",
    "Fe": "#e06633", "Zn": "#7d80b0", "Cu": "#c88033", "Mg": "#4fb83a", "Ca": "#3dbf3d",
    "Mn": "#9c7ac7", "Co": "#f090a0", "Ni": "#50d050", "Na": "#ab5cf2", "K": "#8f40d4",
    "Cl": "#1fbf1f", "Br": "#a62929", "I": "#940094", "F": "#7fc94a", "Se": "#ffa100",
    "Mo": "#54b5b5", "Cd": "#ffd98f", "Hg": "#b8b8d0", "Pt": "#d0d0e0",
}
ELEMENT_DEFAULT = "#ff1493"
INNER_SHADE = 0.78  # Innenseite der Helixbänder
PLDDT_FADE = ((50.0, 0.25), (70.0, 0.6))  # unter 50 sehr blass, unter 70 blass

# --- Licht ---------------------------------------------------------------------------
LIGHT = np.array([-0.35, 0.55, 1.0]) / np.linalg.norm([-0.35, 0.55, 1.0])
HALF = (LIGHT + np.array([0.0, 0.0, 1.0])) / np.linalg.norm(LIGHT + np.array([0.0, 0.0, 1.0]))
AMBIENT, DIFFUSE, SPECULAR, SHININESS = 0.40, 0.62, 0.22, 24.0
FOG = 0.45  # hinterster Teil: so viel Weiß beigemischt
CREASE_COS = math.cos(math.radians(65))

# --- Maßstab -------------------------------------------------------------------------
MAX_PTS_PER_A = 14.0  # Deckel: kleine Proteine (Insulin) nicht als Würste
SEAM_PT = 0.3  # Rand in Flächenfarbe gegen Haarrisse
ATOM_RADIUS = 0.30  # Å, Kugel im Kugel-Stab-Modell
STICK_RADIUS = 0.13
ION_RADIUS = 0.95
SPHERE_SIDES = 20


def catmull_rom(points: np.ndarray, sub: int = pc.SUBDIVIDE) -> np.ndarray:
    """Glatte Kurve durch alle Punkte (uniformes Catmull-Rom, wie pv/geom.js)."""
    n = len(points)
    if n < 2:
        return points.copy()
    seg = np.repeat(np.arange(n - 1), sub)
    t = np.tile(np.arange(sub) / sub, n - 1)
    pos, _ = pc._catmull_rom(np.asarray(points, dtype=float), seg, t)
    return np.vstack([pos, points[-1:]])


# --- Farben --------------------------------------------------------------------------


def _rgb(color: str) -> np.ndarray:
    return np.array(matplotlib.colors.to_rgb(color))


def _fade(plddt: list[float], i: int) -> float:
    if plddt:
        for limit, alpha in PLDDT_FADE:
            if plddt[i] < limit:
                return alpha
    return 1.0


def _shade(base: np.ndarray, normals: np.ndarray) -> np.ndarray:
    """Umgebungslicht + Lambert + Blinn-Glanz; normals sind Einheitsvektoren (N×3)."""
    diff = np.clip(normals @ LIGHT, 0, 1)
    spec = np.clip(normals @ HALF, 0, 1) ** SHININESS
    out = base * (AMBIENT + DIFFUSE * diff)[:, None] + SPECULAR * spec[:, None]
    return np.clip(out, 0, 1)


class _Items:
    """Sammelt Polygone für die eine Tiefensortierung."""

    def __init__(self):
        self.verts: list[np.ndarray] = []
        self.keys: list[np.ndarray] = []
        self.face: list[np.ndarray] = []
        self.edge: list[np.ndarray] = []
        self.width: list[np.ndarray] = []

    def add(self, verts, keys, face, edge, width):
        verts = list(verts)
        if not verts:
            return
        self.verts.extend(verts)
        self.keys.append(np.asarray(keys, dtype=float).reshape(-1))
        self.face.append(np.asarray(face, dtype=float).reshape(-1, 4))
        self.edge.append(np.asarray(edge, dtype=float).reshape(-1, 4))
        self.width.append(np.broadcast_to(np.asarray(width, dtype=float), (len(verts),)).copy())

    def collection(self) -> PolyCollection:
        keys = np.concatenate(self.keys)
        order = np.argsort(keys, kind="stable")
        verts = [self.verts[i] for i in order]
        coll = PolyCollection(
            verts, facecolors=np.concatenate(self.face)[order],
            edgecolors=np.concatenate(self.edge)[order],
            linewidths=np.concatenate(self.width)[order], closed=True,
        )
        coll.set_joinstyle("round")
        coll.set_capstyle("round")
        coll.set_clip_on(False)
        return coll


def _fog(rgb: np.ndarray, z: np.ndarray, zmin: float, span: float) -> np.ndarray:
    depth = np.clip((z - zmin) / span, 0, 1)  # 0 hinten … 1 vorn
    white = FOG * (1 - depth)
    return rgb + (1 - rgb) * white[:, None]


def _rgba(rgb: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    return np.hstack([rgb, np.full((len(rgb), 1), alpha)])


SMOOTH_COS = math.cos(math.radians(40))  # Nachbarn dahinter sind eine Kante, keine Wölbung
SMOOTH_PASSES = 2


def _smooth_normals(unit: np.ndarray, real: np.ndarray) -> np.ndarray:
    """Flächennormalen mit ihren vier Nachbarn mitteln — weicher Verlauf statt Kacheln.

    Über scharfe Kanten (Bandrand, Pfeilschulter) wird nicht gemittelt.
    """
    cur = unit
    for _ in range(SMOOTH_PASSES):
        acc = cur.copy()
        for shift, axis in ((1, 1), (-1, 1), (1, 0), (-1, 0)):
            nb = np.roll(cur, shift, axis=axis)
            ok = real & np.roll(real, shift, axis=axis)
            if axis == 0:  # nicht über die Enden der Röhre hinweg
                ok[0 if shift == 1 else -1] = False
            # Kante oder Wölbung entscheidet die rohe Normale, nicht die schon gemittelte
            w = (ok & (np.einsum("...i,...i->...", unit, np.roll(unit, shift, axis=axis))
                       > SMOOTH_COS)) * 0.6
            acc = acc + w[..., None] * nb
        cur = acc / np.maximum(np.linalg.norm(acc, axis=-1), 1e-12)[..., None]
    return cur


def _tube_items(items: _Items, tube: pc.Tube, base_rgb: np.ndarray, fade: np.ndarray,
                k: int, zmin: float, span: float, outline_pt: float):
    """Flächen, Silhouetten und Endkappen einer Röhre."""
    rings = tube.rings(k)  # M×K×3
    p0 = rings[:-1]
    p1 = np.roll(rings[:-1], -1, axis=1)
    p2 = np.roll(rings[1:], -1, axis=1)
    p3 = rings[1:]
    normal = np.cross(p2 - p0, p3 - p1)  # (M−1)×K×3
    length = np.linalg.norm(normal, axis=2)
    real = length > 1e-10
    unit = np.where(real[..., None], normal / np.maximum(length, 1e-12)[..., None], 0.0)
    front = real & (unit[..., 2] > 0)
    zc = (p0[..., 2] + p1[..., 2] + p2[..., 2] + p3[..., 2]) / 4

    res = tube.residue[:-1]  # Farbe der Fläche: Rest an ihrem Anfang
    base = base_rgb[res]  # (M−1)×3
    side = tube.profile_side(k)  # K
    inner = (tube.outer[:-1, None] != 0) & (side[None, :] == -tube.outer[:-1, None])

    smooth = _smooth_normals(unit, real)
    mi, ji = np.nonzero(front)
    if len(mi):
        n = smooth[mi, ji]
        rgb = _shade(base[mi], n)
        rgb = np.where(inner[mi, ji][:, None], rgb * INNER_SHADE, rgb)
        f = fade[res[mi]][:, None]
        rgb = 1 - (1 - rgb) * f
        rgb = _fog(rgb, zc[mi, ji], zmin, span)
        quads = np.stack([p0[mi, ji], p1[mi, ji], p2[mi, ji], p3[mi, ji]], axis=1)[..., :2]
        col = _rgba(rgb)
        items.add(quads, zc[mi, ji], col, col, SEAM_PT)

    # Konturen: Silhouette (vorn/hinten wechselt) oder scharfe Kante zwischen zwei Vorderflächen
    def contour(fa, fb, ua, ub, za, zb, offset, p, q, ok, silhouette):
        """Strecke p–q, wo Fläche a und Nachbar b Silhouette oder scharfe Kante bilden.

        Quer zur Röhre zählt nur die scharfe Kante (Pfeilschulter, Kappe): ein
        Vorder-/Rückseitenwechsel zwischen zwei Querschnitten liegt auf einer fast
        streifend gesehenen Fläche und gäbe nur Striche quer über die Bandkante.
        """
        crease = (fa | fb) & (np.einsum("...i,...i->...", ua, ub) < CREASE_COS)
        mask = (fa != fb) | crease if silhouette else crease
        mm, jj = np.nonzero(mask & ok)
        if not len(mm):
            return
        use_a = fa[mm, jj]
        key = np.where(use_a, za[mm, jj], zb[mm, jj]) + 1e-4  # direkt hinter ihrer Vorderfläche
        res_m = np.where(use_a, res[mm], res[np.minimum(mm + offset, len(res) - 1)])
        dark = 1 - (1 - base_rgb[res_m] * 0.38) * fade[res_m][:, None]
        a, b = p[mm, jj], q[mm, jj]
        dark = _fog(dark, (a[:, 2] + b[:, 2]) / 2, zmin, span)
        segs = np.stack([a, b], axis=1)[..., :2]
        items.add(segs, key, np.zeros((len(mm), 4)), _rgba(dark), outline_pt)

    # längs: Fläche j gegen j+1 im selben Abschnitt, gemeinsame Kante p1–p2
    nb = np.roll(np.arange(k), -1)
    contour(front, front[:, nb], unit, unit[:, nb], zc, zc[:, nb], 0, p1, p2, real & real[:, nb],
            True)
    # quer: Abschnitt m gegen m+1, gemeinsame Kante p3–p2 (Ring m+1)
    if len(front) > 1:
        contour(front[:-1], front[1:], unit[:-1], unit[1:], zc[:-1], zc[1:], 1,
                p3[:-1], p2[:-1], real[:-1] & real[1:], False)

    # Endkappen
    for end, sign in ((0, -1.0), (-1, 1.0)):
        ring = rings[end]
        nrm = tube.tangents[end] * sign
        if nrm[2] <= 0:
            continue
        r = int(tube.residue[end])
        rgb = _shade(base_rgb[r][None], nrm[None])[0]
        rgb = 1 - (1 - rgb) * fade[r]
        z = float(ring[:, 2].mean())
        rgb = _fog(rgb[None], np.array([z]), zmin, span)
        dark = _fog((1 - (1 - base_rgb[r] * 0.38) * fade[r])[None], np.array([z]), zmin, span)
        items.add([ring[:, :2]], [z + 2e-4], _rgba(rgb), _rgba(dark), outline_pt)


def _circle(center: np.ndarray, radius: float, sides: int = SPHERE_SIDES) -> np.ndarray:
    a = 2 * np.pi * np.arange(sides) / sides
    return center[None, :] + radius * np.stack([np.cos(a), np.sin(a)], axis=1)


def _sphere_items(items: _Items, xyz: np.ndarray, radius: float, color: str,
                  zmin: float, span: float, outline_pt: float):
    """Kugel als konzentrische, zum Licht versetzte Scheiben (Vektor statt Verlauf)."""
    base = _rgb(color)
    z = float(xyz[2])
    layers = ((1.0, 0.0, 0.62), (0.78, 0.12, 0.82), (0.55, 0.24, 1.0), (0.3, 0.36, None))
    verts, faces, edges = [], [], []
    for scale, shift, light in layers:
        c = xyz[:2] + shift * radius * LIGHT[:2] / np.linalg.norm(LIGHT[:2])
        if light is None:
            rgb = base + (1 - base) * 0.55
        else:
            rgb = base * light
        rgb = _fog(np.clip(rgb, 0, 1)[None], np.array([z]), zmin, span)[0]
        verts.append(_circle(c, radius * scale))
        faces.append(np.append(rgb, 1.0))
        edges.append(np.append(rgb, 1.0))
    dark = _fog((base * 0.4)[None], np.array([z]), zmin, span)[0]
    edges[0] = np.append(dark, 1.0)
    widths = [outline_pt] + [SEAM_PT * 0.5] * (len(layers) - 1)
    keys = z + radius + np.arange(len(layers)) * 1e-5
    for v, k_, f, e, w in zip(verts, keys, faces, edges, widths):
        items.add([v], [k_], f, e, w)


def _ligand_items(items: _Items, view: View, zmin: float, span: float, outline_pt: float):
    for lig in view.ligands:
        xyz = np.asarray(lig.xyz, dtype=float)
        els = [e.capitalize() for e in lig.elements]
        if len(xyz) == 1:
            _sphere_items(items, xyz[0], ION_RADIUS, ELEMENT_COLOR.get(els[0], ELEMENT_DEFAULT),
                          zmin, span, outline_pt)
            continue
        for i, j in pc.ligand_bonds(els, xyz):
            a, b = xyz[i], xyz[j]
            mid = (a + b) / 2
            d2 = b[:2] - a[:2]
            ln = np.linalg.norm(d2)
            if ln < 1e-6:
                continue
            perp = np.array([-d2[1], d2[0]]) / ln
            for p, q, el in ((a, mid, els[i]), (mid, b, els[j])):
                base = _rgb(ELEMENT_COLOR.get(el, ELEMENT_DEFAULT))
                z = (p[2] + q[2]) / 2
                for width, shift, light in ((1.0, 0.0, 0.7), (0.45, 0.3, 1.0)):
                    off = perp * STICK_RADIUS * width
                    sh = perp * STICK_RADIUS * shift * np.sign(perp @ LIGHT[:2] or 1)
                    quad = np.array([p[:2] + off + sh, q[:2] + off + sh, q[:2] - off + sh,
                                     p[:2] - off + sh])
                    rgb = _fog(np.clip(base * light, 0, 1)[None], np.array([z]), zmin, span)[0]
                    edge = rgb if width < 1 else _fog((base * 0.4)[None], np.array([z]), zmin, span)[0]
                    items.add([quad], [z + (0 if width == 1.0 else 1e-5)], np.append(rgb, 1),
                              np.append(edge, 1), outline_pt * 0.7 if width == 1.0 else SEAM_PT * 0.5)
        for p, el in zip(xyz, els):
            _sphere_items(items, p, ATOM_RADIUS, ELEMENT_COLOR.get(el, ELEMENT_DEFAULT),
                          zmin, span, outline_pt * 0.7)


# --- Bild ----------------------------------------------------------------------------


POLYGON_BUDGET = 30000  # SVG: ≈ 3,5 MB; gemessen ~115 Byte je Polygon nach _compact_svg
PNG_POLYGON_BUDGET = 120000  # PNG: nur Rechenzeit (~1 s je 50 000 Polygone), feinere Verläufe


def _detail(pts_per_a: float, residues: int, budget: int = POLYGON_BUDGET) -> tuple[int, int]:
    """Stützstellen je Rest und Querschnittsecken: nach Bildmaßstab, gedeckelt vom Budget.

    Geschätzt werden ~0,55·K sichtbare Flächen plus ~1,5 Konturstücke je
    Querschnitt. Zuerst fallen die Querschnittsecken auf 12, dann die
    Stützstellen auf 5, dann die Ecken auf 8, zuletzt die Stützstellen auf 3.
    """
    sub = int(np.clip(round(3.8 * pts_per_a / 3.0), 3, 14))
    k = 16 if pts_per_a >= 8 else 12 if pts_per_a >= 4 else 8

    def cost(s, kk):
        return residues * s * (0.55 * kk + 1.5)

    while cost(sub, k) > budget:
        if k > 12:
            k = 12
        elif sub > 5:
            sub -= 1
        elif k > 8:
            k = 8
        elif sub > 3:
            sub -= 1
        else:
            break
    return sub, k


def _ligand_legend(view: View) -> list[tuple[str, str]]:
    seen, out = set(), []
    for lig in view.ligands:
        if lig.code in seen:
            continue
        seen.add(lig.code)
        els = [e.capitalize() for e in lig.elements]
        if len(els) == 1:
            out.append((lig.name or lig.code, ELEMENT_COLOR.get(els[0], ELEMENT_DEFAULT)))
            continue
        # Organische Gruppe (auch Häm mit Fe): grau wie ihre C-Stäbe — eine
        # Metallfarbe läse sich in der Legende wie eine Kettenfarbe
        color = ELEMENT_COLOR["C"]
        label = f"{lig.name} ({lig.code})" if lig.name and lig.name != lig.code else lig.code
        out.append((label, color))
    return out


def _label_boxes(view: View, cloud: np.ndarray, pts_per_a: float):
    """N-/C-Marken außerhalb der Struktur: entlang der Richtung vom Zentrum weg schieben,
    bis die Textbox keinen Teil der Struktur mehr verdeckt. Liefert (Text, Ankerpunkt, Mitte, Halbmaße)."""
    multi = len(view.chains) > 1
    labels = []
    placed: list[tuple[np.ndarray, np.ndarray]] = []
    center = cloud.mean(axis=0)
    pad = 1.6  # Å Abstand zur Struktur
    for c in view.chains:
        ends = (("N", c["segments"][0].ca[0]), ("C", c["segments"][-1].ca[-1]))
        for name, point in ends:
            text = f"{name} ({c['id']})" if multi else name
            # Textbreite grob: 0,62 em je Zeichen bei 9 pt, plus Rand
            half = np.array([(0.62 * 9 * len(text) + 6) / 2, (9 * 1.25 + 4) / 2]) / pts_per_a
            direction = point[:2] - center
            norm = np.linalg.norm(direction)
            direction = direction / norm if norm > 1e-6 else np.array([-1.0, 0.0])
            best = None
            outward = math.atan2(direction[1], direction[0])
            for dist in np.arange(1.0, 70.0, 1.0):
                for step in range(24):
                    # zuerst nach außen, dann abwechselnd links/rechts herum
                    turn = (step + 1) // 2 * (1 if step % 2 else -1) * math.radians(15)
                    d = np.array([math.cos(outward + turn), math.sin(outward + turn)])
                    mid = point[:2] + d * (dist + abs(d[0]) * half[0] + abs(d[1]) * half[1])
                    lo, hi = mid - half - pad, mid + half + pad
                    if np.any(np.all((cloud >= lo) & (cloud <= hi), axis=1)):
                        continue
                    if any(np.all(np.abs(mid - m) < h + half + 0.5) for m, h in placed):
                        continue
                    best = (dist, mid)
                    break
                if best is not None:
                    break
            if best is None:
                best = (0, point[:2] + direction * 10)
            placed.append((best[1], half))
            labels.append((text, point[:2], best[1], half))
    return labels


def build_protein_figure(
    view: View,
    title: str,
    subtitle: str = "",
    citation: str = "",
    color_by: str = "",
    *,
    polygon_budget: int = POLYGON_BUDGET,
) -> Figure:
    color_by = color_by or ("chain" if len(view.chains) > 1 else "ss")
    ca_all = np.vstack([seg.ca for c in view.chains for seg in c["segments"]])
    lig_all = [np.asarray(lig.xyz) for lig in view.ligands]
    cloud3 = np.vstack([ca_all] + lig_all) if lig_all else ca_all
    width_in = 8.0
    plot_w = width_in * 0.96

    def scale_for(lo, hi):
        s = plot_w / (hi[0] - lo[0])
        if (hi[1] - lo[1]) * s > 8.0:  # sehr hohe Moleküle: Breite statt Höhe opfern
            s = 8.0 / (hi[1] - lo[1])
        return min(s, MAX_PTS_PER_A / 72)

    margin = 3.0  # > halbe Pfeilbreite
    lo, hi = cloud3[:, :2].min(axis=0) - margin, cloud3[:, :2].max(axis=0) + margin
    scale = scale_for(lo, hi)
    pts_per_a = scale * 72
    sub, k = _detail(pts_per_a, view.residues, polygon_budget)
    tubes = pc.cartoon_tubes(view, sub)

    # Termini-Marken neben die Struktur; danach ggf. Rahmen erweitern und einmal nachrechnen
    cloud2 = np.vstack([t.centers[:, :2] for _, _, t in tubes] + [x[:, :2] for x in lig_all]) \
        if tubes else cloud3[:, :2]
    for _ in range(2):
        labels = _label_boxes(view, cloud2, pts_per_a * 0.92)
        boxes = [np.vstack([mid - half, mid + half]) for _, _, mid, half in labels]
        lo = np.min([lo] + [b[0] - 0.5 for b in boxes], axis=0)
        hi = np.max([hi] + [b[1] + 0.5 for b in boxes], axis=0)
        new = scale_for(lo, hi)
        if new >= scale * 0.999:
            break
        scale = new
        pts_per_a = scale * 72
    xmin, ymin = lo
    xmax, ymax = hi
    plot_w_used = (xmax - xmin) * scale
    plot_h = (ymax - ymin) * scale

    # Feste Umbrüche statt wrap=True: die Höhe des Kopfs muss vor der Figur feststehen.
    title_lines = textwrap.wrap(title, 62) or [""]
    sub_lines = textwrap.wrap(subtitle, 92)
    cite_lines = textwrap.wrap(citation, 120)
    present = {code for _, _, t in tubes for code in t.ss}
    handles = []
    if color_by == "ss":
        for code in "HEC":
            if code in present:
                handles.append(Patch(facecolor=SS_COLOR[code], edgecolor=_dark_hex(SS_COLOR[code]),
                                     linewidth=0.6, label=SS_NAME[code]))
    else:
        for c in view.chains:
            handles.append(Patch(facecolor=c["color"], edgecolor=_dark_hex(c["color"]), linewidth=0.6,
                                 label=f"{c['label']} ({c['id']})" if c["label"] != f"chain {c['id']}"
                                 else c["label"]))
    for label, color in _ligand_legend(view):
        handles.append(Line2D([], [], linestyle="none", marker="o", markersize=8,
                              markerfacecolor=color, markeredgecolor=_dark_hex(color), label=label))
    if view.plddt_mean is not None:
        handles.append(Patch(facecolor=_mix_hex("#8a8f98", 0.6), edgecolor="none",
                             label="pale: low confidence (pLDDT < 70)"))
    ncol = min(4, max(1, len(handles)))
    legend_rows = max(1, math.ceil(len(handles) / ncol))
    top = 0.32 + 0.24 * len(title_lines) + 0.19 * len(sub_lines) + 0.22
    bottom = 0.3 + 0.27 * legend_rows + 0.15 * len(cite_lines) + 0.12
    fig_h = plot_h + top + bottom
    fig = Figure(figsize=(width_in, fig_h), facecolor="white")
    ax = fig.add_axes(((width_in - plot_w_used) / 2 / width_in, bottom / fig_h,
                       plot_w_used / width_in, plot_h / fig_h))
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")

    outline_pt = float(np.clip(0.085 * pts_per_a, 0.3, 1.0))
    zs = np.concatenate([t.centers[:, 2] for _, _, t in tubes] + [x[:, 2] for x in lig_all]) \
        if tubes else cloud3[:, 2]
    zmin, zmax = float(zs.min()), float(zs.max())
    span = max(zmax - zmin, 1e-6)
    items = _Items()
    for ci, seg, tube in tubes:
        chain = view.chains[ci]
        if color_by == "ss":
            base = np.array([_rgb(SS_COLOR[code]) for code in tube.ss])
        else:
            base = np.tile(_rgb(chain["color"]), (len(tube.ss), 1))
        fade = np.array([_fade(seg.plddt, i) for i in range(len(seg.ss))])
        _tube_items(items, tube, base, fade, k, zmin, span, outline_pt)
    _ligand_items(items, view, zmin, span, outline_pt)
    if items.verts:
        ax.add_collection(items.collection())

    for text, anchor, mid, half in labels:
        d = anchor - mid  # Leitlinie vom Terminus bis zum Boxrand
        tscale = np.min(np.where(np.abs(d) > 1e-9, half / np.maximum(np.abs(d), 1e-9), np.inf))
        edge = mid + d * min(1.0, tscale)
        # Leitlinie hinter dem Cartoon (kreuzt sie ihn, taucht sie darunter durch),
        # der Punkt am Terminus davor
        ax.plot([anchor[0], edge[0]], [anchor[1], edge[1]], color="#555555", lw=0.6,
                solid_capstyle="round", zorder=0.5)
        ax.plot([anchor[0]], [anchor[1]], marker="o", markersize=3.2, color="#333333",
                markeredgecolor="white", markeredgewidth=0.6, zorder=3)
        ax.text(mid[0], mid[1], text, ha="center", va="center", fontsize=9, fontweight="bold",
                color="#222222", zorder=4,
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#bbbbbb", "lw": 0.5})

    fig.text(0.5, 1 - 0.32 / fig_h, safe_text("\n".join(title_lines)), ha="center", va="top",
             fontsize=12.5, fontweight="bold", linespacing=1.15)
    if sub_lines:
        y = 0.32 + 0.24 * len(title_lines) + 0.08
        fig.text(0.5, 1 - y / fig_h, safe_text("\n".join(sub_lines)), ha="center", va="top",
                 fontsize=9.5, color="#444444", linespacing=1.2)
    if handles:
        fig.legend(handles=handles, loc="lower left",
                   bbox_to_anchor=(0.02, (0.12 + 0.15 * len(cite_lines) + 0.1) / fig_h),
                   ncol=ncol, frameon=False, fontsize=9, handlelength=1.6)
    if cite_lines:
        fig.text(0.98, 0.12 / fig_h, safe_text("\n".join(cite_lines)), ha="right", va="bottom",
                 fontsize=7.5, color="#666666", linespacing=1.2)
    return fig


def _dark_hex(color: str, f: float = 0.6) -> str:
    return matplotlib.colors.to_hex(_rgb(color) * f)


def _mix_hex(color: str, white: float) -> str:
    rgb = _rgb(color)
    return matplotlib.colors.to_hex(rgb + (1 - rgb) * white)


def _rc():
    return rc_context({"svg.hashsalt": "chemdraw-protein", "svg.fonttype": "path",
                       "font.family": "DejaVu Sans"})


_NUM = re.compile(r"-?\d+\.\d+")
_SEGMENT = re.compile(r"^M (\S+ \S+) L (\S+ \S+) L \1 z$")


def _compact_svg(text: str) -> str:
    """Gezeichnete Pfade (d als erstes Attribut, also keine Glyphen) verdichten.

    Koordinaten auf 0,1 pt, Konturstrecken ohne Rückweg, Stil ohne Leerzeichen
    und ohne Linienende bei Flächen. Ändert nichts am Bild, nur an der Größe
    (1HZH: Ziel < 5 MB).
    """
    def path(m: re.Match) -> str:
        d = " ".join(_NUM.sub(lambda n: f"{float(n.group()):.1f}", m.group(1)).split())
        d = _SEGMENT.sub(r"M \1 L \2", d)
        style = m.group(2).replace(": ", ":").replace("; ", ";")
        if not style.startswith("fill:none"):
            style = style.replace(";stroke-linecap:round", "")
        return f'<path d="{d}" style="{style}"'
    return re.sub(r'<path d="([^"]*)" style="([^"]*)"', path, text)


def render_protein_png(view: View, title: str, subtitle: str = "", citation: str = "",
                       color_by: str = "", dpi: int = 200) -> bytes:
    with _rc():
        fig = build_protein_figure(view, title, subtitle, citation, color_by,
                                   polygon_budget=PNG_POLYGON_BUDGET)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    return buf.getvalue()


def render_protein_svg(view: View, title: str, subtitle: str = "", citation: str = "",
                       color_by: str = "") -> str:
    with _rc():
        fig = build_protein_figure(view, title, subtitle, citation, color_by)
        buf = io.StringIO()
        fig.savefig(buf, format="svg", facecolor="white", metadata={"Date": None})
    return _compact_svg(buf.getvalue())


def residue_summary(view: View) -> dict[str, int]:
    counts = {"H": 0, "E": 0, "C": 0}
    for c in view.chains:
        for seg in c["segments"]:
            for code in seg.ss:
                counts[code] += 1
    return counts


def extent(view: View) -> float:
    pts = np.vstack([seg.ca for c in view.chains for seg in c["segments"]])
    return float(math.dist(pts.min(axis=0), pts.max(axis=0)))
