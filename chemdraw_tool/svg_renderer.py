"""SVG rendering module using RDKit MolDraw2DSVG."""

from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.render_style import apply_style

SVG_WIDTH = 900
SVG_HEIGHT = 700
FIXED_BOND_LENGTH = 25
SVG_PADDING = 22
# Strichstärke der Bindungen — feiner, ACS-naher Stil. Single source of truth:
# image_export.py importiert diesen Wert, damit Export-Datei und UI-Vorschau nie
# auseinanderdriften (Review-Finding 2026-06-10).
# Stil-Presets (render_style.py) definieren diese Konstante NICHT um: sie
# überschreiben die Strichstärke pro Zeichenvorgang, nachdem beide Pfade sie
# hier gesetzt haben. Die Parität gilt dadurch je Stil statt nur im Default.
BOND_LINE_WIDTH = 1.5


def _crop_svg_to_content(
    svg: str,
    drawer: rdMolDraw2D.MolDraw2DSVG,
    num_atoms: int,
    fill_container: bool = False,
) -> str:
    """Crop viewBox to atom bounds. Set sizing per `fill_container` mode.

    - fill_container=False (default): intrinsic pixel size matching atom extent.
      Use for reactions where consistent bond scale across molecules matters.
    - fill_container=True: width/height=100%, SVG scales to wrapper.
      Use for single-molecule cards where the SVG should fill its container.
    """
    if num_atoms == 0:
        return svg
    pts = [drawer.GetDrawCoords(i) for i in range(num_atoms)]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    vx = min(xs) - SVG_PADDING
    vy = min(ys) - SVG_PADDING
    vw = max(xs) - min(xs) + 2 * SVG_PADDING
    vh = max(ys) - min(ys) + 2 * SVG_PADDING

    svg = re.sub(
        r"viewBox='[^']*'",
        f"viewBox='{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}'",
        svg,
        count=1,
    )
    if fill_container:
        svg = re.sub(r"\bwidth='[^']*'", "width='100%'", svg, count=1)
        svg = re.sub(r"\bheight='[^']*'", "height='100%'", svg, count=1)
        svg = re.sub(
            r"<svg\b",
            "<svg style='width:100%;height:100%;display:block'",
            svg,
            count=1,
        )
    else:
        svg = re.sub(r"\bwidth='[^']*'", f"width='{vw:.0f}'", svg, count=1)
        svg = re.sub(r"\bheight='[^']*'", f"height='{vh:.0f}'", svg, count=1)
        svg = re.sub(
            r"<svg\b",
            f"<svg style='width:{vw:.0f}px;height:{vh:.0f}px;display:block'",
            svg,
            count=1,
        )
    return svg


def render_svg(
    mol: Chem.Mol,
    width: int = SVG_WIDTH,
    height: int = SVG_HEIGHT,
    fill_container: bool = False,
    annotate_stereo: bool = False,
    style: str = "",
) -> str:
    """Render a molecule to an SVG string with consistent pixel bond length.

    Uses fixedBondLength so all molecules share a chemical scale.

    fill_container=False (default): SVG has intrinsic pixel size — use for
    reactions/mechanism layouts where relative molecule sizes matter.
    fill_container=True: SVG scales to wrapper via width/height=100% +
    viewBox aspect — use for single-molecule cards where the SVG should fill
    its container responsively.

    style: named preset from render_style.STYLES; "" keeps today's look.
    """
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.fixedBondLength = FIXED_BOND_LENGTH
    opts.clearBackground = False
    opts.bondLineWidth = BOND_LINE_WIDTH
    opts.useDefaultAtomPalette()
    if annotate_stereo:
        opts.addStereoAnnotation = True
    apply_style(opts, style)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    return _crop_svg_to_content(
        svg, drawer, mol.GetNumAtoms(), fill_container=fill_container
    )


def extract_atom_data(
    mol: Chem.Mol, width: int = SVG_WIDTH, height: int = SVG_HEIGHT
) -> list[dict]:
    """Return per-atom data including SVG-space coordinates.

    Uses MolDraw2DSVG + GetDrawCoords so coordinates are in SVG pixel space.
    """
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.fixedBondLength = FIXED_BOND_LENGTH
    opts.clearBackground = False
    opts.bondLineWidth = BOND_LINE_WIDTH
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()

    atoms = []
    for atom in mol.GetAtoms():
        idx = atom.GetIdx()
        pt = drawer.GetDrawCoords(idx)
        atoms.append(
            {
                "idx": idx,
                "el": atom.GetSymbol(),
                "x": pt.x,
                "y": pt.y,
                "hCount": atom.GetTotalNumHs(),
                "charge": atom.GetFormalCharge(),
            }
        )
    return atoms


_FUNCTIONAL_GROUPS: list[tuple[str, str, str]] = [
    # (name, SMARTS, color)
    # Colors follow pharmacophore conventions:
    #   Donor → green, Acceptor → red/orange, Aromatic → blue, Hydrophobic → yellow
    # --- Acceptors (red/orange family) ---
    ("Carbonsäure", "[CX3](=O)[OX2H1]", "#e74c3c"),
    ("Ester", "[#6][CX3](=O)[OX2][#6]", "#d35400"),
    ("Keton", "[#6][CX3](=O)[#6]", "#c0392b"),
    ("Aldehyd", "[CX3H1](=O)", "#e67e22"),
    ("Nitro", "[NX3+](=O)[O-]", "#922b21"),
    ("Ether", "[#6][OX2][#6]", "#eb8c6f"),
    # --- Donor/Acceptor (purple) ---
    ("Amid", "[CX3](=O)[NX3]", "#8e44ad"),
    ("Sulfonamid", "S(=O)(=O)[NX3]", "#7d3c98"),
    # --- Donors (green family) ---
    ("Prim. Amin", "[NX3H2][#6]", "#2ecc71"),
    ("Sek. Amin", "[NX3H1]([#6])[#6]", "#27ae60"),
    ("Tert. Amin", "[NX3]([#6])([#6])[#6]", "#1e8449"),
    ("Hydroxyl", "[OX2H1][CX4]", "#52be80"),
    ("Phenol", "[OX2H1]c", "#1abc9c"),
    ("Thiol", "[SX2H1]", "#82e0aa"),
    # --- Other ---
    ("Halogenid", "[#6][F,Cl,Br,I]", "#f4d03f"),
    ("Phosphat", "P(=O)([OH])([OH])", "#e67e22"),
]

_COMPILED_GROUPS = [
    (name, Chem.MolFromSmarts(smarts), color)
    for name, smarts, color in _FUNCTIONAL_GROUPS
]


def extract_functional_groups(mol: Chem.Mol) -> list[dict]:
    """Detect functional groups via SMARTS matching."""
    groups = []
    seen_atoms: set[int] = set()

    for name, pattern, color in _COMPILED_GROUPS:
        if pattern is None:
            continue
        matches = mol.GetSubstructMatches(pattern)
        if not matches:
            continue
        atom_indices = sorted({idx for match in matches for idx in match})
        new_atoms = [i for i in atom_indices if i not in seen_atoms]
        if not new_atoms:
            continue
        seen_atoms.update(atom_indices)
        groups.append(
            {
                "name": name,
                "atomIndices": atom_indices,
                "color": color,
            }
        )

    ri = mol.GetRingInfo()
    aromatic_atoms = []
    for ring in ri.AtomRings():
        if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            aromatic_atoms.extend(ring)
    if aromatic_atoms:
        groups.append(
            {
                "name": "Aromat",
                "atomIndices": sorted(set(aromatic_atoms)),
                "color": "#2980b9",
            }
        )

    return groups


def molecule_payload(
    mol: Chem.Mol,
    name: str,
    subtitle: str = "",
    properties: dict | None = None,
) -> dict:
    """Build a molecule payload dict for the MCP App UI."""
    return {
        "type": "molecule",
        "svg": render_svg(mol, fill_container=True),
        "atoms": extract_atom_data(mol),
        "name": name,
        "subtitle": subtitle,
        "properties": properties if properties is not None else {},
    }


def reaction_payload(
    reactants: list[tuple[Chem.Mol, str]],
    products: list[tuple[Chem.Mol, str]],
    conditions: str = "",
    name: str = "",
) -> dict:
    """Build a reaction payload dict. Each entry in reactants/products is (mol, label)."""
    r_width, r_height = 250, 200

    def _mol_entry(mol: Chem.Mol, label: str) -> dict:
        return {
            "svg": render_svg(mol, width=r_width, height=r_height),
            "name": label,
        }

    return {
        "type": "reaction",
        "name": name,
        "conditions": conditions,
        "reactants": [_mol_entry(m, n) for m, n in reactants],
        "products": [_mol_entry(m, n) for m, n in products],
    }


def database_payload(mol: Chem.Mol, sources: list[dict]) -> dict:
    """Build a database lookup payload dict with a mini SVG thumbnail."""
    return {
        "type": "database",
        "molecule_svg": render_svg(mol, width=150, height=120, fill_container=True),
        "sources": sources,
    }
