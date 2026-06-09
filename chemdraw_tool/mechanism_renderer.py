"""SVG Bezier arrow renderer for mechanism steps.

Takes pre-positioned RDKit Mol objects and CurvedArrow definitions,
renders the molecules to SVG, then overlays curved Bezier arrow paths and
partial-bond dashed lines.
"""

from __future__ import annotations

import math
import re

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep

STEP_WIDTH = 450
STEP_HEIGHT = 350


def _get_draw_coords(
    mol: Chem.Mol, drawer: rdMolDraw2D.MolDraw2DSVG
) -> dict[int, tuple[float, float]]:
    """Get atom-map-ID → pixel-space (x, y) from a finished drawer."""
    result = {}
    for atom in mol.GetAtoms():
        map_id = atom.GetAtomMapNum()
        if map_id != 0:
            pt = drawer.GetDrawCoords(atom.GetIdx())
            result[map_id] = (pt.x, pt.y)
    return result


def _render_mols_svg(
    mols: list[Chem.Mol], width: int = STEP_WIDTH, height: int = STEP_HEIGHT
) -> tuple[str, dict[int, tuple[float, float]]]:
    """Render molecules to SVG, return (svg_text, atom_map_coords)."""
    map_index: list[tuple[int, int]] = []
    offset = 0
    for m in mols:
        for atom in m.GetAtoms():
            map_id = atom.GetAtomMapNum()
            if map_id != 0:
                map_index.append((map_id, atom.GetIdx() + offset))
        offset += m.GetNumAtoms()

    if len(mols) == 1:
        mol = Chem.RWMol(mols[0])
    else:
        from rdkit.Chem import CombineMols

        combined = mols[0]
        for m in mols[1:]:
            combined = CombineMols(combined, m)
        mol = Chem.RWMol(combined)

    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.clearBackground = False
    opts.bondLineWidth = 2.5
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()

    coords = {}
    for map_id, atom_idx in map_index:
        pt = drawer.GetDrawCoords(atom_idx)
        coords[map_id] = (pt.x, pt.y)

    all_pts = []
    for i in range(mol.GetNumAtoms()):
        pt = drawer.GetDrawCoords(i)
        all_pts.append((pt.x, pt.y))

    svg = drawer.GetDrawingText()

    if all_pts:
        pad = 40
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        vx = max(0, min(xs) - pad)
        vy = max(0, min(ys) - pad)
        vw = max(xs) - min(xs) + 2 * pad
        vh = max(ys) - min(ys) + 2 * pad
        new_viewbox = f"viewBox='{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}'"
        # RDKit already emits a viewBox — replace it instead of adding a second
        # (duplicate attributes are invalid SVG).
        if re.search(r"viewBox='[^']*'", svg):
            svg = re.sub(r"viewBox='[^']*'", new_viewbox, svg, count=1)
        else:
            svg = re.sub(r"<svg\b", f"<svg {new_viewbox}", svg, count=1)

    svg = re.sub(r"\bwidth='[^']*'", "width='100%'", svg)
    svg = re.sub(r"\bheight='[^']*'", "", svg)
    return svg, coords


def _bezier_arrow_path(sx: float, sy: float, tx: float, ty: float, style: str) -> str:
    """Generate an SVG path element for a curved arrow.

    The control point is offset perpendicular to the source→target
    midpoint, creating the classic organic chemistry curved arrow.
    """
    mx, my = (sx + tx) / 2, (sy + ty) / 2
    dx, dy = tx - sx, ty - sy
    length = math.hypot(dx, dy) or 1.0

    perp_x, perp_y = -dy / length, dx / length
    bulge = min(length * 0.35, 40.0)
    cx, cy = mx + perp_x * bulge, my + perp_y * bulge

    stroke_width = 2.8 if style == "full" else 2.0
    color = "#e74c3c"

    arrow_head = ""
    if style == "full":
        angle = math.atan2(ty - cy, tx - cx)
        a1 = angle + 0.4
        a2 = angle - 0.4
        head_len = 11
        hx1 = tx - head_len * math.cos(a1)
        hy1 = ty - head_len * math.sin(a1)
        hx2 = tx - head_len * math.cos(a2)
        hy2 = ty - head_len * math.sin(a2)
        arrow_head = (
            f'<polygon points="{tx:.1f},{ty:.1f} {hx1:.1f},{hy1:.1f} '
            f'{hx2:.1f},{hy2:.1f}" fill="{color}" />'
        )
    elif style == "half":
        angle = math.atan2(ty - cy, tx - cx)
        a1 = angle + 0.5
        head_len = 9
        hx1 = tx - head_len * math.cos(a1)
        hy1 = ty - head_len * math.sin(a1)
        arrow_head = (
            f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{hx1:.1f}" y2="{hy1:.1f}" '
            f'stroke="{color}" stroke-width="{stroke_width}" />'
        )

    return (
        f'<path class="arrow" d="M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {tx:.1f} {ty:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" />'
        f"{arrow_head}"
    )


def _lone_pair_offset(
    atom_pos: tuple[float, float],
    all_coords: dict[int, tuple[float, float]],
    atom_map_id: int,
) -> tuple[float, float]:
    """Offset source position slightly away from nearest bonded atom."""
    ax, ay = atom_pos
    offset = 12.0

    nearest_dist = float("inf")
    nearest_dir = (0.0, -1.0)
    for mid, (ox, oy) in all_coords.items():
        if mid == atom_map_id:
            continue
        d = math.hypot(ox - ax, oy - ay)
        if d < nearest_dist:
            nearest_dist = d
            if d > 0:
                nearest_dir = ((ax - ox) / d, (ay - oy) / d)

    return (ax + nearest_dir[0] * offset, ay + nearest_dir[1] * offset)


def _resolve_arrow_coords(
    arrow: CurvedArrow,
    coords: dict[int, tuple[float, float]],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Resolve arrow source/target to pixel coordinates."""
    src_map_id = arrow.source[0]
    src_type = arrow.source[1]
    tgt_map_id = arrow.target[0]

    if src_map_id not in coords or tgt_map_id not in coords:
        return None

    if src_type == "lone_pair":
        sx, sy = _lone_pair_offset(coords[src_map_id], coords, src_map_id)
    elif src_type == "bond_to" and len(arrow.source) >= 3:
        other_id = arrow.source[2]
        if other_id in coords:
            bx = (coords[src_map_id][0] + coords[other_id][0]) / 2
            by = (coords[src_map_id][1] + coords[other_id][1]) / 2
            sx, sy = bx, by
        else:
            sx, sy = coords[src_map_id]
    else:
        sx, sy = coords[src_map_id]

    tx, ty = coords[tgt_map_id]
    return (sx, sy), (tx, ty)


def _dashed_bond_line(x1: float, y1: float, x2: float, y2: float) -> str:
    """SVG dashed line for partial bonds in transition states."""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="#999" stroke-width="2.0" stroke-dasharray="6,3" />'
    )


def render_step_svg(
    step: MechanismStep,
    mols: list[Chem.Mol],
    width: int = STEP_WIDTH,
    height: int = STEP_HEIGHT,
) -> str:
    """Render a mechanism step as SVG with arrow overlays."""
    base_svg, coords = _render_mols_svg(mols, width, height)

    overlay_elements = []

    for arrow in step.arrows:
        resolved = _resolve_arrow_coords(arrow, coords)
        if resolved:
            (sx, sy), (tx, ty) = resolved
            overlay_elements.append(_bezier_arrow_path(sx, sy, tx, ty, arrow.style))

    if step.is_transition_state:
        for map_a, map_b in step.partial_bonds:
            if map_a in coords and map_b in coords:
                x1, y1 = coords[map_a]
                x2, y2 = coords[map_b]
                overlay_elements.append(_dashed_bond_line(x1, y1, x2, y2))

    if not overlay_elements:
        return base_svg

    overlay_group = f'<g class="mechanism-overlay">{"".join(overlay_elements)}</g>'
    return base_svg.replace("</svg>", f"{overlay_group}</svg>")
