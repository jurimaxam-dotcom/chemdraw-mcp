"""SVG Bezier arrow renderer for mechanism steps.

Takes pre-positioned RDKit Mol objects and CurvedArrow definitions,
renders the molecules to SVG, then overlays curved Bezier arrow paths and
partial-bond dashed lines.

Pfeil-Geometrie (Etappe E, 05.11.2026, docs/mechanismus-substrate-design.md „Pfeil-Geometrie“):
Pfeilenden sitzen am Rand der Atombeschriftung, nicht am Atommittelpunkt; der Pfeilkörper meidet
jede Beschriftung. Jedes SVG trägt einen Geometrie-Datensatz (`data-geometry`, `geometry_of`),
gegen den tests/test_mechanism_geometry.py prüft.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point2D

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep

STEP_WIDTH = 450
STEP_HEIGHT = 350
# Feste Bindungslänge: ohne sie fittet RDKit jeden Schritt in dieselbe Leinwand, und ein breites
# Bild (Produkt + weit entferntes Br⁻) bekommt winzige Atome (Galerie 02.10.2026). RDKit liest den
# Wert als Pixel je Koordinateneinheit; eine Bindung ist 1,5 Einheiten → 57 px.
BOND_PX = 38
# Die Leinwand muss größer sein als das größte Bild: passt die Zeichnung nicht hinein, verkleinert
# RDKit sie trotz fixedBondLength (Stearinsäure ist über 1000 px breit). Den leeren Rand schneidet
# die viewBox ab.
CANVAS_W = 2400
CANVAS_H = 1600
# Abstand zwischen Pfeilende und Beschriftungsrand
_LABEL_GAP = 3.5
# Pfeilende an einem unbeschrifteten Gerüst-C: so weit vor dem Knick
_BARE_ATOM_GAP = 4.0
# Mindestwölbung, damit ein kurzer Pfeil als Bogen erkennbar bleibt
_MIN_BULGE = 18.0
_MAX_BULGE = 40.0
# Seite × Wölbungsfaktor in Probierreihenfolge: erst die gewohnte Seite, dann die andere, dann weiter
_BULGE_TRIALS = [(s, f) for f in (1.0, 1.6, 2.3, 3.2) for s in (1, -1)]
_ARROW_COLOR = "#e74c3c"


Box = list[float]  # [x0, y0, x1, y1] in Pixeln


@dataclass
class _Drawing:
    svg: str  # RDKit-SVG, viewBox noch die ganze Leinwand
    coords: dict[int, tuple[float, float]]  # Map-ID → Atommittelpunkt
    boxes: dict[int, Box]  # Map-ID → Beschriftung (nur beschriftete Atome)
    obstacles: list[Box]  # alle Beschriftungen, auch ungemappter Atome und (R)/(S)
    atom_pts: list[tuple[float, float]]
    bond_px: float
    # Neutrale Kohlenstoffe ohne Isotop, die trotzdem ein „C“ bekommen haben (Map-ID, 0 = ohne
    # Map). RDKit beschriftet ein Gerüst-C nur, wenn seine zwei Bindungen auf einer Linie liegen —
    # im Ring ist das ein Layout-Fehler (Kontaktbogen 05.11.2026, 1-Methylcyclohexyl).
    labelled_carbons: list[int]
    # Gezeichnete Bindungen als Strecken (Pixel) — Pfeile sollen nicht auf ihnen landen
    bond_segments: list[tuple[tuple[float, float], tuple[float, float]]]
    # Jedes Glyph einer Beschriftung einzeln (Symbol, H, Ladung): Map-ID → Boxen
    glyphs: dict[int, list[Box]]


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


_LABEL_PATH = re.compile(r"<path class='(atom-(\d+)|CIP_Code)' d='([^']*)'")
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _glyph_boxes(svg: str) -> dict[int, list[Box]]:
    """Atomindex → Box je Glyph (ein Pfad je Zeichen; eine Ladung „⁻“ ist ein flacher Strich)."""
    out: dict[int, list[Box]] = {}
    for m in _LABEL_PATH.finditer(svg):
        if m.group(2) is None:
            continue
        nums = [float(v) for v in _NUM.findall(m.group(3))]
        xs, ys = nums[0::2], nums[1::2]
        if xs:
            out.setdefault(int(m.group(2)), []).append([min(xs), min(ys), max(xs), max(ys)])
    return out


def _label_boxes(svg: str) -> tuple[dict[int, Box], list[Box]]:
    """Beschriftungs-Rechtecke aus dem RDKit-SVG: {Atomindex: [x0, y0, x1, y1]} und Stereo-Notizen.

    RDKit zeichnet Atomsymbole als Glyphenpfade mit genau einer Klasse `atom-N`; Bindungen tragen
    `bond-k atom-i atom-j` und fallen deshalb heraus. Ein unbeschrifteter Gerüst-Kohlenstoff hat
    keinen Pfad und keine Box. `CIP_Code` sind die (R)/(S)-Notizen — Hindernisse ohne Atom.
    """
    boxes: dict[int, Box] = {}
    notes: list[Box] = []
    for m in _LABEL_PATH.finditer(svg):
        nums = [float(v) for v in _NUM.findall(m.group(3))]
        xs, ys = nums[0::2], nums[1::2]
        if not xs:
            continue
        box = [min(xs), min(ys), max(xs), max(ys)]
        if m.group(2) is None:
            notes.append(box)
            continue
        idx = int(m.group(2))
        if idx in boxes:
            b = boxes[idx]
            box = [min(b[0], box[0]), min(b[1], box[1]), max(b[2], box[2]), max(b[3], box[3])]
        boxes[idx] = box
    return boxes, notes


def _charge_left_where_bond_goes_right(mol: Chem.RWMol) -> None:
    """Ladung links vom Symbol, wenn die Bindungen des Atoms nach rechts gehen.

    RDKit setzt die Ladung eines Atoms ohne H immer oben rechts — auch wenn dort die Bindung
    abgeht. Im Azid lag das „⁻“ des endständigen N dann unter der Doppelbindung, der Leser sah
    N=N⁺=N⁻ statt ⁻N=N⁺=N⁻ (Sichtung 05.11.2026, R1). `_displayLabel` ersetzt die ganze
    Beschriftung; Atome mit H behalten RDKits eigene Ausrichtung (HO⁻/OH⁻).
    """
    if not mol.GetNumConformers():
        return
    conf = mol.GetConformer()
    for atom in mol.GetAtoms():
        charge = atom.GetFormalCharge()
        if not charge or atom.GetTotalNumHs() or atom.GetIsotope() or not atom.GetDegree():
            continue
        here = conf.GetAtomPosition(atom.GetIdx())
        if all(conf.GetAtomPosition(n.GetIdx()).x - here.x > 0.1 for n in atom.GetNeighbors()):
            sign = "+" if charge > 0 else "-"
            amount = f"{abs(charge)}" if abs(charge) > 1 else ""
            atom.SetProp("_displayLabel", f"<sup>{amount}{sign}</sup>{atom.GetSymbol()}")


def _show_carbon_h(mol: Chem.RWMol, glyphs: dict[int, list[Box]]) -> bool:
    """Beschriftetem Kohlenstoff mit H das H in die Beschriftung schreiben (CH⁺, HC⁺, CH).

    RDKit beschriftet ein Kation-C oder das freistehende Zentrum des Übergangszustands, lässt
    dessen H aber weg — „C⁺“ im 1-Phenylethyl-Kation sah aus wie ein Kation ohne H (Sichtung
    05.11.2026). Das H steht auf der Seite ohne Bindung: links, wenn ein Nachbar rechts liegt.
    True, wenn neu gezeichnet werden muss.
    """
    changed = False
    conf = mol.GetConformer() if mol.GetNumConformers() else None
    for atom in mol.GetAtoms():
        n_h, charge = atom.GetTotalNumHs(), atom.GetFormalCharge()
        if atom.GetAtomicNum() != 6 or not n_h or atom.HasProp("_displayLabel"):
            continue
        if len(glyphs.get(atom.GetIdx(), ())) != 1 + (1 if charge else 0):
            continue
        h = "H" + (f"<sub>{n_h}</sub>" if n_h > 1 else "")
        sup = f"<sup>{abs(charge) if abs(charge) > 1 else ''}{'+' if charge > 0 else '-'}</sup>" if charge else ""
        right = conf is not None and any(
            conf.GetAtomPosition(n.GetIdx()).x - conf.GetAtomPosition(atom.GetIdx()).x > 0.3
            for n in atom.GetNeighbors())
        atom.SetProp("_displayLabel", f"{h}C{sup}" if right else f"C{h}{sup}")
        changed = True
    return changed


# Ab so vielen Kohlenstoffen wird eine unverzweigte Alkylkette als CₙH₂ₙ₊₁ beschriftet (Gutachter
# GELB, Etappe E2): Stearinsäure (C₁₇) machte den Rahmen 1147 px breit, das Reaktionszentrum winzig.
# Butyl bleibt gezeichnet — kurze Ketten liest man als Gerüst schneller als als Formel.
CHAIN_MIN = 5
# Map-IDs ab hier sind Atome außerhalb des Reaktionszentrums (mechanism_substrate.FIRST_FREE_MAP)
_FIRST_FREE_MAP = 100


def abbreviate_chains(mol: Chem.RWMol, keep: set[int]) -> set[int]:
    """Unverzweigte, gesättigte, endständige Alkylketten ab CHAIN_MIN C zu einem Etikett-Atom kürzen.

    Das C, das an den Rest des Moleküls bindet, bleibt (Lage, Bindung, Stereo-Nachbarschaft) und
    trägt „C₁₇H₃₅“ bzw. nach links „H₃₅C₁₇“; die übrigen Kettenatome gehen. Nie gekürzt: Atome in
    `keep`, Ringatome, Aromaten, geladene Atome, Stereozentren, Mehrfachbindungen. Nur fürs Bild —
    die Schritt-SMILES behalten alle Atome. Gibt die Indizes der Etikett-Atome zurück (nach dem Kürzen).
    """
    def eligible(atom: Chem.Atom) -> bool:
        return (atom.GetAtomicNum() == 6 and not atom.GetIsAromatic() and not atom.IsInRing()
                and atom.GetFormalCharge() == 0 and atom.GetIsotope() == 0 and atom.GetIdx() not in keep
                and atom.GetDegree() <= 2 and atom.GetChiralTag() == Chem.ChiralType.CHI_UNSPECIFIED
                and all(b.GetBondType() == Chem.BondType.SINGLE for b in atom.GetBonds()))

    remove: set[int] = set()
    for end in mol.GetAtoms():
        if end.GetDegree() != 1 or not eligible(end) or end.GetIdx() in remove:
            continue
        path, prev, cur = [end.GetIdx()], -1, end
        while True:
            nxt = [n for n in cur.GetNeighbors() if n.GetIdx() != prev]
            if not nxt:  # das ganze Molekül ist eine Kette (kein Anknüpfungspunkt): nicht kürzen
                path = []
                break
            if eligible(nxt[0]) and nxt[0].GetDegree() == 2:
                prev, cur = cur.GetIdx(), nxt[0]
                path.append(cur.GetIdx())
                continue
            break
        if len(path) < CHAIN_MIN:
            continue
        n = len(path)
        label = mol.GetAtomWithIdx(path[-1])
        label.SetProp("_displayLabel", f"C<sub>{n}</sub>H<sub>{2 * n + 1}</sub>")
        label.SetProp("_displayLabelW", f"H<sub>{2 * n + 1}</sub>C<sub>{n}</sub>")
        label.SetIntProp("_chain", n)
        label.SetNoImplicit(True)
        label.SetNumExplicitHs(0)
        remove.update(path[:-1])
    for idx in sorted(remove, reverse=True):
        mol.RemoveAtom(idx)
    return {a.GetIdx() for a in mol.GetAtoms() if a.HasProp("_chain")}


def _draw(mols: list[Chem.Mol], width: int = STEP_WIDTH, height: int = STEP_HEIGHT,
          partial: tuple[int, ...] = ()) -> _Drawing:
    """Moleküle zeichnen; Koordinaten, Beschriftungen und gemessene Bindungslänge zurückgeben.

    partial: Map-IDs mit Teilladung (δ⁻) — sie behalten ihr Symbol, auch ein endständiges C.
    """
    combined = mols[0]
    for m in mols[1:]:
        combined = Chem.CombineMols(combined, m)
    mol = Chem.RWMol(combined)
    for atom in mol.GetAtoms():
        atom.SetIntProp("_map", atom.GetAtomMapNum())
        atom.SetAtomMapNum(0)

    # CIP ausdrücklich zuweisen (neuer Labeler), damit die Stereo-Notiz (R)/(S) zeigt — SN2-Produkt
    # von (R)-2-Brombutan + CN⁻ ist (S). Am vollen Molekül, vor dem Kürzen der Ketten: gekürzt sieht
    # eine Hexylkette aus wie ein Methyl. Bruchstücke eines Übergangszustands können den Labeler
    # stolpern lassen; dann bleibt das Bild ohne Notiz statt ohne Bild.
    try:
        from rdkit.Chem import rdCIPLabeler

        rdCIPLabeler.AssignCIPLabels(mol)
    except Exception:  # noqa: BLE001
        pass
    # Reaktionszentrum (Map < 100) und Teilladungen sind nie Teil einer Abkürzung
    abbreviate_chains(mol, keep={a.GetIdx() for a in mol.GetAtoms()
                                 if 0 < a.GetIntProp("_map") < _FIRST_FREE_MAP or a.GetIntProp("_map") in partial})
    idx_to_map = {a.GetIdx(): a.GetIntProp("_map") for a in mol.GetAtoms() if a.GetIntProp("_map")}
    abbreviated = {a.GetIdx() for a in mol.GetAtoms() if a.HasProp("_chain")}
    _charge_left_where_bond_goes_right(mol)
    partial_idx = {i for i, m in idx_to_map.items() if m in partial}
    for i in partial_idx:
        atom = mol.GetAtomWithIdx(i)
        if atom.GetAtomicNum() == 6:  # Nitril-C ohne Ladung bliebe ein unbeschriftetes Linienende
            # Zentrum mit H (ÜZ, primär/sekundär): „CH₂“/„CH“, H auf der bindungsfreien Seite
            n_h = atom.GetTotalNumHs()
            h = ("H" + (f"<sub>{n_h}</sub>" if n_h > 1 else "")) if n_h else ""
            conf = mol.GetConformer() if mol.GetNumConformers() else None
            right = conf is not None and any(
                conf.GetAtomPosition(n.GetIdx()).x - conf.GetAtomPosition(i).x > 0.3 for n in atom.GetNeighbors())
            atom.SetProp("_displayLabel", f"{h}C" if right else f"C{h}")

    def render() -> rdMolDraw2D.MolDraw2DSVG:
        drawer = rdMolDraw2D.MolDraw2DSVG(max(width, CANVAS_W), max(height, CANVAS_H))
        opts = drawer.drawOptions()
        opts.clearBackground = False
        opts.bondLineWidth = 2.5
        opts.fixedBondLength = BOND_PX
        opts.addStereoAnnotation = True
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        return drawer

    drawer = render()
    if _show_carbon_h(mol, _glyph_boxes(drawer.GetDrawingText())):
        drawer = render()

    atom_pts = []
    for i in range(mol.GetNumAtoms()):
        pt = drawer.GetDrawCoords(i)
        atom_pts.append((pt.x, pt.y))
    coords = {map_id: atom_pts[i] for i, map_id in idx_to_map.items()}

    # Bindungslänge gemessen, nicht angenommen: Median der gezeichneten Bindungen. Ohne Bindung
    # (Übergangszustand aus drei Einzelatomen) der Maßstab der Leinwand × RDKit-Bindung 1,5.
    lens = [math.dist(atom_pts[b.GetBeginAtomIdx()], atom_pts[b.GetEndAtomIdx()]) for b in mol.GetBonds()]
    if lens:
        bond_px = statistics.median(lens)
    else:
        p0, p1 = drawer.GetDrawCoords(Point2D(0, 0)), drawer.GetDrawCoords(Point2D(1.5, 0))
        bond_px = math.hypot(p1.x - p0.x, p1.y - p0.y)

    svg = drawer.GetDrawingText()
    raw_boxes, notes = _label_boxes(svg)
    boxes = {idx_to_map[i]: b for i, b in raw_boxes.items() if i in idx_to_map}
    labelled_carbons = sorted(
        idx_to_map.get(i, 0)
        for i in raw_boxes
        if (a := mol.GetAtomWithIdx(i)).GetAtomicNum() == 6 and a.GetFormalCharge() == 0 and a.GetIsotope() == 0
        and i not in partial_idx and i not in abbreviated
    )
    glyphs = {idx_to_map[i]: g for i, g in _glyph_boxes(svg).items() if i in idx_to_map}
    segments = [(atom_pts[b.GetBeginAtomIdx()], atom_pts[b.GetEndAtomIdx()]) for b in mol.GetBonds()]
    return _Drawing(svg, coords, boxes, list(raw_boxes.values()) + notes, atom_pts, bond_px, labelled_carbons,
                    segments, glyphs)


def _set_frame(svg: str, frame: tuple[float, float, float, float]) -> str:
    """viewBox auf frame setzen; Breite folgt dem Container (Overview skaliert per viewBox-Breite)."""
    vx, vy, vw, vh = frame
    new_viewbox = f"viewBox='{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}'"
    # RDKit already emits a viewBox — replace it instead of adding a second
    # (duplicate attributes are invalid SVG).
    if re.search(r"viewBox='[^']*'", svg):
        svg = re.sub(r"viewBox='[^']*'", new_viewbox, svg, count=1)
    else:
        svg = re.sub(r"<svg\b", f"<svg {new_viewbox}", svg, count=1)
    svg = re.sub(r"\bwidth='[^']*'", "width='100%'", svg, count=1)
    svg = re.sub(r"\s\bheight='[^']*'", "", svg, count=1)
    return svg


def _frame_of(points: list, boxes: list[Box], pad: float) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points] + [b[0] for b in boxes] + [b[2] for b in boxes]
    ys = [p[1] for p in points] + [b[1] for b in boxes] + [b[3] for b in boxes]
    return (min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad)


def _render_mols_svg(
    mols: list[Chem.Mol], width: int = STEP_WIDTH, height: int = STEP_HEIGHT
) -> tuple[str, dict[int, tuple[float, float]]]:
    """Render molecules to SVG, return (svg_text, atom_map_coords)."""
    d = _draw(mols, width, height)
    return _set_frame(d.svg, _frame_of(d.atom_pts, d.obstacles, 30)), d.coords


def unify_frames(svgs: list[str]) -> list[str]:
    """Alle Schritte eines Mechanismus auf dieselbe viewBox bringen.

    Jeder Schritt wird mittig auf derselben Leinwand mit fester Bindungslänge gezeichnet — in
    viewBox-Einheiten sind die Bindungen überall gleich lang. Ein Betrachter, der jedes SVG auf
    dieselbe Breite zieht (Einzelschritt-Ansicht im Panel, `rsvg-convert -w`), verkleinert aber den
    Schritt mit der breiteren viewBox: Fischer-Schritt 3 (Säure + Alkohol nebeneinander) wirkte
    kleiner als Schritt 2 (Säure allein). Die Vereinigung aller viewBoxen gibt allen Schritten
    denselben Maßstab.
    """
    frames = []
    for svg in svgs:
        m = re.search(r"viewBox='([^']*)'", svg)
        frames.append(tuple(float(v) for v in m.group(1).split()) if m else None)
    known = [f for f in frames if f]
    if not known:
        return list(svgs)
    x0 = min(f[0] for f in known)
    y0 = min(f[1] for f in known)
    x1 = max(f[0] + f[2] for f in known)
    y1 = max(f[1] + f[3] for f in known)
    return [_set_frame(svg, (x0, y0, x1 - x0, y1 - y0)) if f else svg for svg, f in zip(svgs, frames)]


def geometry_of(svg: str) -> dict:
    """Geometrie-Datensatz, den render_step_svg ins SVG legt (Pfeile, Beschriftungen, Bindungslänge)."""
    m = re.search(r"data-geometry='([^']*)'", svg)
    if m is None:
        raise ValueError("SVG enthält keinen Geometrie-Datensatz (data-geometry)")
    return json.loads(m.group(1))


# --- Pfeil-Geometrie ---------------------------------------------------------------------------


def _unit(dx: float, dy: float) -> tuple[float, float]:
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n > 1e-9 else (0.0, -1.0)


def _exit_distance(p, d, box: Box, gap: float) -> float:
    """Wie weit ein Strahl von p in Richtung d läuft, bis er die um gap vergrößerte Box verlässt."""
    x0, y0, x1, y1 = box[0] - gap, box[1] - gap, box[2] + gap, box[3] + gap
    if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1):
        return 0.0
    ts = []
    if d[0] > 1e-9:
        ts.append((x1 - p[0]) / d[0])
    elif d[0] < -1e-9:
        ts.append((x0 - p[0]) / d[0])
    if d[1] > 1e-9:
        ts.append((y1 - p[1]) / d[1])
    elif d[1] < -1e-9:
        ts.append((y0 - p[1]) / d[1])
    return min(ts) if ts else 0.0


def _control(s, t, side: int, factor: float) -> tuple[float, float]:
    """Kontrollpunkt des quadratischen Bogens: Normale (-dy, dx) × Wölbung, side wählt die Seite."""
    dx, dy = t[0] - s[0], t[1] - s[1]
    length = math.hypot(dx, dy) or 1.0
    bulge = max(min(length * 0.35, _MAX_BULGE), _MIN_BULGE) * factor * side
    return ((s[0] + t[0]) / 2 - dy / length * bulge, (s[1] + t[1]) / 2 + dx / length * bulge)


def _bezier_points(s, c, t, n: int = 40) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        u = i / n
        v = 1 - u
        pts.append((v * v * s[0] + 2 * v * u * c[0] + u * u * t[0], v * v * s[1] + 2 * v * u * c[1] + u * u * t[1]))
    return pts


def _collisions(s, c, t, obstacles: list[Box], ends: float = 4.0, margin: float = 1.5) -> int:
    """Zahl der Bogenpunkte (ohne die Enden), die in einer Beschriftung liegen."""
    hits = 0
    for p in _bezier_points(s, c, t):
        if math.dist(p, s) <= ends or math.dist(p, t) <= ends:
            continue
        for b in obstacles:
            if b[0] - margin < p[0] < b[2] + margin and b[1] - margin < p[1] < b[3] + margin:
                hits += 1
                break
    return hits


def _seg_dist(p, a, b) -> float:
    """Abstand eines Punktes zur Strecke a–b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n2 = dx * dx + dy * dy
    t = 0.0 if n2 < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def _place_arrow(
    arrow: CurvedArrow,
    coords: dict[int, tuple[float, float]],
    boxes: dict[int, Box],
    obstacles: list[Box],
    atom_pts: list[tuple[float, float]] | None = None,
    bond_px: float = 0.0,
    segments: list | None = None,
    glyphs: dict[int, list[Box]] | None = None,
) -> dict | None:
    """Start, Kontrollpunkt und Spitze eines Pfeils — Enden am Beschriftungsrand, Körper frei.

    Zweites Kriterium nach den Beschriftungen: der Bogen soll nicht über fremde Atome laufen
    (Wasserabspaltung: die Spitze landete am H des OH₂⁺ statt auf der freien Seite).
    """
    src_id, src_type = arrow.source[0], arrow.source[1]
    tgt_id = arrow.target[0]
    if src_id not in coords or tgt_id not in coords:
        return None
    partner = arrow.source[2] if src_type == "bond_to" and len(arrow.source) >= 3 else None
    if partner is not None and partner not in coords:
        partner = None
    kind = "lone_pair" if src_type == "lone_pair" else ("bond" if partner is not None else "atom")
    leaving = kind == "bond" and partner == tgt_id
    # Ziel Bindung (target = (a, "bond_to", b)): Spitze an die Mitte der entstehenden Bindung
    tgt_bond = None
    if len(arrow.target) >= 3 and arrow.target[1] == "bond_to" and arrow.target[2] in coords:
        tgt_bond = (tgt_id, arrow.target[2])

    if kind == "bond":
        a, b = coords[src_id], coords[partner]
        s0 = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    else:
        s0 = coords[src_id]
    if tgt_bond:
        a, b = coords[tgt_bond[0]], coords[tgt_bond[1]]
        t0 = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    else:
        t0 = coords[tgt_id]
    src_box, tgt_box = boxes.get(src_id), (None if tgt_bond else boxes.get(tgt_id))
    push_back = kind == "lone_pair" and tgt_bond is not None and src_id in tgt_bond

    def clip_tip(ctrl):
        d = _unit(t0[0] - ctrl[0], t0[1] - ctrl[1])
        r = _exit_distance(t0, (-d[0], -d[1]), tgt_box, _LABEL_GAP) if tgt_box else _BARE_ATOM_GAP
        return (t0[0] - d[0] * r, t0[1] - d[1] * r)

    def candidate(side: int, factor: float, lean: float = 1.0):
        if leaving:
            # Bindung → eigenes Ende (Abgangsgruppe): die Spitze landet neben der Beschriftung, auf
            # der Seite, zu der sich der Bogen wölbt — nicht im „Br“, nicht eine halbe Bindung kurz.
            # Schräg nach außen (Seite + ein Stück über das Atom hinaus): der Bogen wird so lang wie
            # eine Bindung statt ein Haken von einer halben (Kontaktbogen 05.11.2026, „Loss of water“).
            dx, dy = t0[0] - s0[0], t0[1] - s0[1]
            n = _unit(-dy * side, dx * side)
            u = _unit(dx, dy)
            d = _unit(0.6 * n[0] + lean * u[0], 0.6 * n[1] + lean * u[1])
            r = _exit_distance(t0, d, tgt_box, _LABEL_GAP) if tgt_box else 10.0
            tip = (t0[0] + d[0] * r, t0[1] + d[1] * r)
            return s0, _control(s0, tip, side, factor), tip
        if push_back:
            # Freies Paar → Bindung zum eigenen Nachbarn (C=O⁺H bildet sich zurück): Schwanz außen an
            # der Beschriftung, Bogen um sie herum, Spitze an der Bindungsmitte.
            dx, dy = t0[0] - s0[0], t0[1] - s0[1]
            u = _unit(dx, dy)
            n = _unit(-dy * side, dx * side)
            d = _unit(n[0] - 0.6 * u[0], n[1] - 0.6 * u[1])
            r = _exit_distance(s0, d, src_box, _LABEL_GAP) if src_box else _BARE_ATOM_GAP
            start = (s0[0] + d[0] * r, s0[1] + d[1] * r)
            tip = (t0[0] + n[0] * 3.0, t0[1] + n[1] * 3.0)
            bulge = _MIN_BULGE * factor
            ctrl = ((start[0] + tip[0]) / 2 + n[0] * bulge, (start[1] + tip[1]) / 2 + n[1] * bulge)
            return start, ctrl, tip
        ctrl = _control(s0, t0, side, factor)
        start = s0
        if kind == "lone_pair":
            # Freies Paar: Schwanz am Rand der eigenen Beschriftung, auf der Seite, zu der der Bogen
            # aufbricht — nicht auf „HO“, nicht hinter dem Atom.
            d = _unit(ctrl[0] - s0[0], ctrl[1] - s0[1])
            if len((glyphs or {}).get(src_id, ())) > 1:
                # Beschriftung mit H/Ladung („HO“, „H₂O“): das Paar gehört dem Atomsymbol — Schwanz
                # senkrecht über bzw. unter dem Symbol, nicht am Rand neben dem H (Sichtung 05.11.)
                d = (0.0, 1.0 if ctrl[1] > s0[1] else -1.0)
            r = _exit_distance(s0, d, src_box, _LABEL_GAP) if src_box else _BARE_ATOM_GAP
            start = (s0[0] + d[0] * r, s0[1] + d[1] * r)
        tip = clip_tip(ctrl)
        ctrl = _control(start, tip, side, factor)
        # Nach dem Kürzen den Rand entlang der neuen Anflugrichtung noch einmal bestimmen
        return start, ctrl, clip_tip(ctrl)

    own = [coords[m] for m in (src_id, tgt_id, partner, *(tgt_bond or ())) if m is not None and m in coords]

    def is_own(p) -> bool:
        return any(math.dist(p, q) < 1.0 for q in own)

    others = [p for p in (atom_pts or []) if not is_own(p)]
    # Bindungen zwischen zwei eigenen Atomen (die Quellbindung, die entstehende Bindung) zählen nicht
    foreign = [(a, b) for a, b in (segments or []) if not (is_own(a) and is_own(b))]
    near = 0.4 * bond_px

    def crowding(s, c, t) -> int:
        if near <= 0:
            return 0
        pts = _bezier_points(s, c, t, 20)
        hits = sum(1 for p in pts for q in others if math.dist(p, q) < near)
        # Die letzten Punkte (Spitze) dürfen keine fremde Bindung berühren
        # Weder Körper noch Spitze über eine fremde Bindung (Protonentransfer: der Bogen kreuzte C–O⁺)
        hits += sum(1 for p in pts[3:] for a, b in foreign if _seg_dist(p, a, b) < 0.12 * bond_px)
        return hits

    # Abgangsgruppe: erst schräg über das Atom hinaus (langer Bogen), dann seitlich (kurzer Haken in
    # eine freie Lücke zwischen zwei Bindungen)
    leans = (1.0, 0.0) if leaving else (1.0,)
    best = None
    for (side, factor), lean in ((t, le) for le in leans for t in _BULGE_TRIALS):
        s, c, t = candidate(side, factor, lean)
        score = _collisions(s, c, t, obstacles) + crowding(s, c, t)
        if best is None or score < best[0]:
            best = (score, s, c, t)
        if score == 0:
            break
    _, s, c, t = best
    return {
        "kind": kind,
        "src": [round(s[0], 2), round(s[1], 2)],
        "ctrl": [round(c[0], 2), round(c[1], 2)],
        "tip": [round(t[0], 2), round(t[1], 2)],
        "src_map": src_id,
        "tgt_map": tgt_id,
        "bond": [src_id, partner] if kind == "bond" else None,
        "tgt_bond": list(tgt_bond) if tgt_bond else None,
        "style": arrow.style,
    }


def _arrow_svg(s, c, t, style: str) -> str:
    """SVG für einen Bogenpfeil (volle Spitze = 2 e⁻, halbe = 1 e⁻)."""
    (sx, sy), (cx, cy), (tx, ty) = s, c, t
    stroke_width = 2.8 if style == "full" else 2.0
    color = _ARROW_COLOR
    angle = math.atan2(ty - cy, tx - cx)
    arrow_head = ""
    if style == "full":
        a1, a2 = angle + 0.4, angle - 0.4
        head_len = 11
        hx1, hy1 = tx - head_len * math.cos(a1), ty - head_len * math.sin(a1)
        hx2, hy2 = tx - head_len * math.cos(a2), ty - head_len * math.sin(a2)
        arrow_head = (
            f'<polygon points="{tx:.1f},{ty:.1f} {hx1:.1f},{hy1:.1f} '
            f'{hx2:.1f},{hy2:.1f}" fill="{color}" />'
        )
    elif style == "half":
        a1 = angle + 0.5
        head_len = 9
        hx1, hy1 = tx - head_len * math.cos(a1), ty - head_len * math.sin(a1)
        arrow_head = (
            f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{hx1:.1f}" y2="{hy1:.1f}" '
            f'stroke="{color}" stroke-width="{stroke_width}" />'
        )
    return (
        f'<path class="arrow" d="M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {tx:.1f} {ty:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" />'
        f"{arrow_head}"
    )


def _bezier_arrow_path(sx: float, sy: float, tx: float, ty: float, style: str) -> str:
    """Generate an SVG path element for a curved arrow between two points (no label clipping)."""
    s, t = (sx, sy), (tx, ty)
    return _arrow_svg(s, _control(s, t, 1, 1.0), t, style)


def _dashed_bond_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    trim: float = 14.0,
    box1: Box | None = None,
    box2: Box | None = None,
) -> str:
    """SVG dashed line for partial bonds in transition states.

    Beide Enden werden um `trim` Pixel gekürzt, bei beschrifteten Atomen mindestens bis vor die
    Beschriftung: die Koordinaten sind Atommittelpunkte, und der Strich lief sonst mitten durch
    „O⁻“, „CH₃“, „Br⁻“.
    """
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length > 3 * trim:
        ux, uy = dx / length, dy / length
        t1 = max(trim, _exit_distance((x1, y1), (ux, uy), box1, _LABEL_GAP) if box1 else 0.0)
        t2 = max(trim, _exit_distance((x2, y2), (-ux, -uy), box2, _LABEL_GAP) if box2 else 0.0)
        if t1 + t2 > length - 6:
            t1 = t2 = trim
        x1, y1, x2, y2 = x1 + ux * t1, y1 + uy * t1, x2 - ux * t2, y2 - uy * t2
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="#999" stroke-width="2.0" stroke-dasharray="6,3" />'
    )


def _partial_charge(text: str, box: Box | None, centre: tuple[float, float]) -> tuple[str, Box]:
    """Teilladung („δ−“) oben rechts an der Beschriftung — dort, wo RDKit eine Ladung setzt."""
    if box is None:
        box = [centre[0] - 4, centre[1] - 4, centre[0] + 4, centre[1] + 4]
    # Als Zeichenreferenz: RDKit deklariert das SVG als iso-8859-1, ein rohes „δ“ würde dort
    # zu Zeichensalat (wie das ‡ in _ts_brackets)
    delta, sign = (f"&#{ord(ch)};" for ch in (text[0], text[1:]))
    x, y = box[2] + 1.0, box[1] + 3.0
    svg = (
        f"<text class='partial-charge' x='{x:.1f}' y='{y:.1f}' font-size='15' "
        f"font-family='sans-serif' fill='#000000'>{delta}"
        f"<tspan dy='-5' font-size='12'>{sign}</tspan></text>"
    )
    return svg, [x - 1.0, y - 16.0, x + 18.0, y + 3.0]


def _ts_brackets(content: tuple[float, float, float, float]) -> tuple[str, Box]:
    """Eckige Klammern um den Übergangszustand, ‡ oben rechts (Lehrbuchkonvention)."""
    x, y, w, h = content
    margin, arm = 10.0, 9.0
    x0, y0, x1, y1 = x - margin, y - margin, x + w + margin, y + h + margin
    style = 'fill="none" stroke="#000000" stroke-width="2.0"'
    left = f"M {x0 + arm:.1f} {y0:.1f} L {x0:.1f} {y0:.1f} L {x0:.1f} {y1:.1f} L {x0 + arm:.1f} {y1:.1f}"
    right = f"M {x1 - arm:.1f} {y0:.1f} L {x1:.1f} {y0:.1f} L {x1:.1f} {y1:.1f} L {x1 - arm:.1f} {y1:.1f}"
    svg = (
        f"<path class='ts-bracket' d='{left}' {style} />"
        f"<path class='ts-bracket' d='{right}' {style} />"
        f"<text class='ts-dagger' x='{x1 + 3:.1f}' y='{y0 + 12:.1f}' font-size='20' "
        f"font-family='serif' fill='#000000'>&#8225;</text>"
    )
    return svg, [x0, y0 - 6, x1 + 16, y1]


def render_step(
    step: MechanismStep,
    mols: list[Chem.Mol],
    width: int = STEP_WIDTH,
    height: int = STEP_HEIGHT,
) -> tuple[str, dict]:
    """Einen Mechanismus-Schritt zeichnen: (SVG, Geometrie-Datensatz).

    Der Datensatz steht zusätzlich im SVG (`data-geometry` an der Overlay-Gruppe), damit ihn
    der Geometrie-Test auch hinter `generate_mechanism` erreicht.
    """
    # Atome an Teilbindungen behalten ihr Symbol: das primäre ÜZ-Zentrum war sonst ein
    # unbeschriftetes Strichende zwischen zwei Teilbindungen (Gutachter E2) — so steht „CH₂“ da
    marked = tuple(dict.fromkeys([*step.partial_charges, *(m for b in step.partial_bonds for m in b)]))
    d = _draw(mols, width, height, partial=marked)
    overlay: list[str] = []
    arrows = []
    extent_pts = list(d.atom_pts)
    # Teilladungen zuerst: ihre Boxen sind Hindernisse für die Pfeile und gehören in den Rahmen
    for map_id, text in step.partial_charges.items():
        if map_id not in d.coords:
            continue
        svg_text, box = _partial_charge(text, d.boxes.get(map_id), d.coords[map_id])
        overlay.append(svg_text)
        d.obstacles.append(box)
    for arrow in step.arrows:
        placed = _place_arrow(arrow, d.coords, d.boxes, d.obstacles, d.atom_pts, d.bond_px, d.bond_segments,
                              d.glyphs)
        if placed is None:
            continue
        arrows.append(placed)
        s, c, t = placed["src"], placed["ctrl"], placed["tip"]
        overlay.append(_arrow_svg(s, c, t, arrow.style))
        extent_pts.extend(_bezier_points(s, c, t, 20))

    if step.is_transition_state:
        for map_a, map_b in step.partial_bonds:
            if map_a in d.coords and map_b in d.coords:
                (x1, y1), (x2, y2) = d.coords[map_a], d.coords[map_b]
                overlay.append(_dashed_bond_line(x1, y1, x2, y2, box1=d.boxes.get(map_a), box2=d.boxes.get(map_b)))

    frame_boxes = list(d.obstacles)
    bracket = None
    if step.is_transition_state:
        bracket_svg, bracket = _ts_brackets(_frame_of(extent_pts, d.obstacles, 4))
        overlay.append(bracket_svg)
        frame_boxes.append(bracket)
    frame = _frame_of(extent_pts, frame_boxes, 24)

    geo = {
        "bond_px": round(d.bond_px, 3),
        "boxes": {str(k): [round(v, 2) for v in b] for k, b in d.boxes.items()},
        "centres": {str(k): [round(v, 2) for v in p] for k, p in d.coords.items()},
        "obstacles": [[round(v, 2) for v in b] for b in d.obstacles],
        "arrows": arrows,
        "arrows_defined": len(step.arrows),
        "ts_bracket": bracket is not None,
        "labelled_carbons": d.labelled_carbons,
        "frame": [round(v, 1) for v in frame],
        "glyphs": {str(k): [[round(v, 2) for v in b] for b in g] for k, g in d.glyphs.items()},
    }
    data = json.dumps(geo, separators=(",", ":"))
    overlay_group = f"<g class='mechanism-overlay' data-geometry='{data}'>{''.join(overlay)}</g>"
    svg = _set_frame(d.svg, frame).replace("</svg>", f"{overlay_group}</svg>")
    return svg, geo


def render_step_svg(
    step: MechanismStep,
    mols: list[Chem.Mol],
    width: int = STEP_WIDTH,
    height: int = STEP_HEIGHT,
) -> str:
    """Render a mechanism step as SVG with arrow overlays."""
    return render_step(step, mols, width, height)[0]
