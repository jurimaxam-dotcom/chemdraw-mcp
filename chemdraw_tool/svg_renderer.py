"""SVG rendering module using RDKit MolDraw2DSVG."""

from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.generator import coordination_drawing
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


_LABEL_MARGIN = 4
_GLYPH_PATH = re.compile(r"<path class='atom-\d+' d='([^']*)' fill='#[0-9A-Fa-f]{6}'")
_POINT = re.compile(r"(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)")


def _label_glyph_points(svg: str):
    """Alle Stützpunkte der Label-Glyphen (RDKit: <path class='atom-N' … fill=…>)."""
    for m in _GLYPH_PATH.finditer(svg):
        for x, y in _POINT.findall(m.group(1)):
            yield float(x), float(y)


def _has_abbreviation(mol: Chem.Mol) -> bool:
    return any(a.HasProp("_displayLabel") for a in mol.GetAtoms())


def _crop_svg_to_content(
    svg: str,
    drawer: rdMolDraw2D.MolDraw2DSVG,
    num_atoms: int,
    fill_container: bool = False,
    include_labels: bool = False,
) -> str:
    """Crop viewBox to atom bounds. Set sizing per `fill_container` mode.

    include_labels=True widens the box to every label glyph — needed for
    abbreviation labels (CO₂H, Boc), which reach beyond SVG_PADDING.

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
    x0, x1 = min(xs) - SVG_PADDING, max(xs) + SVG_PADDING
    y0, y1 = min(ys) - SVG_PADDING, max(ys) + SVG_PADDING
    if include_labels:
        # Kürzel ragen über die Atommitte ± SVG_PADDING hinaus („CO₂H“ am
        # Rand verlor sein H, Bildschau E16). Nur dann aufziehen — ohne
        # Kürzel bleibt der Zuschnitt byte-gleich (goldene SVGs).
        for gx, gy in _label_glyph_points(svg):
            x0, x1 = min(x0, gx - _LABEL_MARGIN), max(x1, gx + _LABEL_MARGIN)
            y0, y1 = min(y0, gy - _LABEL_MARGIN), max(y1, gy + _LABEL_MARGIN)
    vx, vy, vw, vh = x0, y0, x1 - x0, y1 - y0

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
    drawer, mol = _draw(mol, width, height, annotate_stereo, style)
    return _crop_svg_to_content(
        drawer.GetDrawingText(), drawer, mol.GetNumAtoms(), fill_container=fill_container,
        include_labels=_has_abbreviation(mol),
    )


def _draw(
    mol: Chem.Mol, width: int, height: int, annotate_stereo: bool, style: str
) -> tuple[rdMolDraw2D.MolDraw2DSVG, Chem.Mol]:
    """Zeichnet `mol` auf eine width×height-Fläche; gibt Drawer und Zeichen-Mol zurück."""
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.fixedBondLength = FIXED_BOND_LENGTH
    opts.clearBackground = False
    opts.bondLineWidth = BOND_LINE_WIDTH
    opts.useDefaultAtomPalette()
    if annotate_stereo:
        opts.addStereoAnnotation = True
    apply_style(opts, style)
    # Metall-Tetrapyrrole: N–Metall-Bindungen nur in der Zeichnung (generator.py).
    mol = coordination_drawing(mol)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return drawer, mol


# Zeichenfläche je Stoff im Reaktions-Panel. Passt ein Molekül bei
# FIXED_BOND_LENGTH nicht darauf, verwirft RDKit fixedBondLength und
# verkleinert es — ein Porphyrin auf ~0,5, N-Labels 4,5 px (E16, 10.11.2026).
REACTION_ENTRY_WIDTH = 250
REACTION_ENTRY_HEIGHT = 200
# Obergrenze fürs Vergrößern: ein Stoff, der selbst darauf nicht passt, ist
# kein Reaktionsteilnehmer mehr, den man im Panel liest.
_REACTION_ENTRY_MAX = 4000


def _drawn_bond_length(drawer: rdMolDraw2D.MolDraw2DSVG, mol: Chem.Mol) -> float | None:
    """Längste gezeichnete Bindung in Pixeln — None ohne Bindung."""
    lengths = []
    for bond in mol.GetBonds():
        a = drawer.GetDrawCoords(bond.GetBeginAtomIdx())
        b = drawer.GetDrawCoords(bond.GetEndAtomIdx())
        lengths.append(((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5)
    return max(lengths, default=None)


def _fits_fixed_scale(drawer: rdMolDraw2D.MolDraw2DSVG, mol: Chem.Mol) -> bool:
    """True, wenn RDKit im festen Maßstab gezeichnet hat (nichts verkleinert)."""
    drawn = _drawn_bond_length(drawer, mol)
    if drawn is None:
        return True
    # Die längste Bindung im 2D-Layout ist ≈ 1 Å, gezeichnet also ≈ FIXED_BOND_LENGTH;
    # verkleinert RDKit, liegt sie deutlich darunter (Porphyrin: ~0,5).
    conf = mol.GetConformer()
    longest = max(
        (conf.GetAtomPosition(b.GetBeginAtomIdx()) - conf.GetAtomPosition(b.GetEndAtomIdx())).Length()
        for b in mol.GetBonds()
    )
    return drawn >= 0.98 * FIXED_BOND_LENGTH * longest


def render_reaction_entry(mol: Chem.Mol, style: str = "") -> str:
    """SVG eines Reaktionsteilnehmers fürs Panel, immer im festen Bindungsmaßstab.

    Passt der Stoff auf REACTION_ENTRY_WIDTH×HEIGHT, ist das Ergebnis byte-
    gleich zu `render_svg(mol, 250, 200)`; sonst wird die Fläche verdoppelt,
    bis er passt. Das SVG ist ohnehin auf die Atome zugeschnitten — die
    Fläche bestimmt nur, ob RDKit verkleinern muss.
    """
    width, height = REACTION_ENTRY_WIDTH, REACTION_ENTRY_HEIGHT
    while True:
        drawer, drawn = _draw(mol, width, height, False, style)
        if _fits_fixed_scale(drawer, drawn) or width * 2 > _REACTION_ENTRY_MAX:
            return _crop_svg_to_content(
                drawer.GetDrawingText(), drawer, drawn.GetNumAtoms(),
                include_labels=_has_abbreviation(drawn),
            )
        width, height = width * 2, height * 2


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
    # Dasselbe Zeichen-Mol wie render_svg, sonst säßen die Tooltips woanders
    # als die Atome. Ladung/H im Tooltip kommen aus `mol`, der Quelle.
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, coordination_drawing(mol))
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
                # includeNeighbors: bei expliziten H (AddHs) zählen die
                # Nachbaratome mit, sonst stünde im Tooltip „0 H".
                "hCount": atom.GetTotalNumHs(includeNeighbors=True),
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
        # Gezaehlt werden Treffer, nicht Atome: "Ester 2" heisst zwei
        # Estergruppen. Treffer, deren Atome schon einer frueheren (spezielleren)
        # Gruppe gehoeren, zaehlen nicht mit — der Ether im Ester ist keiner.
        kept = [m for m in matches if any(i not in seen_atoms for i in m)]
        if not kept:
            continue
        atom_indices = sorted({idx for match in kept for idx in match})
        seen_atoms.update(idx for match in matches for idx in match)
        groups.append(
            {
                "name": name,
                "atomIndices": atom_indices,
                "count": len(kept),
                "color": color,
            }
        )

    ri = mol.GetRingInfo()
    aromatic_rings = [
        ring
        for ring in ri.AtomRings()
        if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring)
    ]
    if aromatic_rings:
        groups.append(
            {
                "name": "Aromat",
                "atomIndices": sorted({i for ring in aromatic_rings for i in ring}),
                # Naphthalin sind zwei Ringe, nicht zehn Atome.
                "count": len(aromatic_rings),
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
    def _mol_entry(mol: Chem.Mol, label: str) -> dict:
        return {
            "svg": render_reaction_entry(mol),
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
