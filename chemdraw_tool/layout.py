from lxml import etree
from rdkit import Chem

from chemdraw_tool.cdxml_writer import (
    PAGE_HEIGHT,
    PAGE_WIDTH,
    SCALE,
    _create_cdxml_root,
    _create_fragment,
)
from chemdraw_tool.condition_text import formula_runs

MOL_GAP = 40.0
PLUS_WIDTH = 20.0
ARROW_LENGTH = 60.0
ARROW_GAP = 20.0
# Breite eines Koeffizienten („2“) samt Abstand zum Molekül.
COEF_WIDTH = 16.0
# Zeilenhöhe der Bedingungen (size 8 → ChemDraw "LineHeight auto" ≈ 1.25 × 8).
CONDITIONS_LINE = 10.0

# Pfeiltyp → <arrow>-Attribute. Belegt an ChemDraw-eigenen Dateien in RDKits
# Testdaten (Code/GraphMol/test_data/CDXML/): chemdraw_template6.cdxml, <arrow
# id="80152"> = Nachfolger von <graphic ArrowType="Equilibrium">;
# chemdraw_template1.cdxml, <arrow id="80117"> = Nachfolger von <graphic
# ArrowType="RetroSynthetic">. Die Attributnamen/-werte stehen auch als
# Enum-Strings in RDKits libRDKitChemDraw (ArrowheadHead/Tail: None, Full,
# HalfLeft, HalfRight; ArrowheadType: Solid, Hollow, Angle).
_ARROW_ATTRS = {
    "forward": {"ArrowheadHead": "Full", "ArrowheadType": "Solid"},
    "equilibrium": {
        "ArrowheadHead": "HalfLeft",
        "ArrowheadTail": "HalfLeft",
        "ArrowheadType": "Solid",
        "HeadSize": "1000",
        "ArrowheadCenterSize": "875",
        "ArrowheadWidth": "250",
        "ArrowShaftSpacing": "300",
    },
    "retro": {
        "ArrowheadHead": "Full",
        "ArrowheadType": "Angle",
        "HeadSize": "600",
        "ArrowheadCenterSize": "600",
        "ArrowheadWidth": "150",
        "ArrowShaftSpacing": "600",
    },
}


def _conditions_text(page, next_id: int, x: float, y: float, text: str) -> int:
    """Bedingungstext als <t>; Formelziffern als ChemDraw-Tiefstellung
    (face="32", wie in ChemDraws eigenem Ti(OiPr)<s face="32">4</s>)."""
    t = etree.SubElement(
        page,
        "t",
        id=str(next_id),
        p=f"{x:.2f} {y:.2f}",
        Justification="Center",
    )
    for chunk, sub in formula_runs(text):
        s = etree.SubElement(t, "s", font="3", size="8")
        if sub:
            s.set("face", "32")
        s.text = chunk
    return next_id + 1


def _coefficient_text(page, next_id: int, x: float, y: float, factor: int) -> int:
    """Stöchiometrischer Koeffizient vor einem Molekül, so groß wie das „+“."""
    t = etree.SubElement(
        page,
        "t",
        id=str(next_id),
        p=f"{x + COEF_WIDTH / 2:.2f} {y:.2f}",
        Justification="Center",
    )
    s = etree.SubElement(t, "s", font="3", size="10")
    s.text = str(factor)
    return next_id + 1


def _mol_width(mol: Chem.Mol) -> float:
    conf = mol.GetConformer()
    xs = [conf.GetAtomPosition(i).x * SCALE for i in range(mol.GetNumAtoms())]
    return max(xs) - min(xs) if xs else 0.0


def reaction_to_cdxml(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    conditions: str = "",
    name: str = "",
    reactant_names: list[str] | None = None,
    product_names: list[str] | None = None,
    arrow: str = "forward",
    conditions_below: str = "",
    coefficients: list[int] | None = None,
) -> str:
    if arrow not in _ARROW_ATTRS:
        raise ValueError(
            f"Unknown arrow {arrow!r}; use one of {', '.join(_ARROW_ATTRS)}."
        )
    root = _create_cdxml_root()

    page = etree.SubElement(
        root,
        "page",
        BoundingBox=f"0 0 {PAGE_WIDTH} {PAGE_HEIGHT}",
        Width=str(PAGE_WIDTH),
        Height=str(PAGE_HEIGHT),
    )

    widths_r = [_mol_width(m) for m in reactants]
    widths_p = [_mol_width(m) for m in products]

    n_plus_r = max(0, len(reactants) - 1)
    n_plus_p = max(0, len(products) - 1)

    # Koeffizient 1 schreibt niemand hin — dann bleibt die Datei bytegleich.
    factors = list(coefficients or [])
    factors += [1] * (len(reactants) + len(products) - len(factors))
    coef_r, coef_p = factors[: len(reactants)], factors[len(reactants) :]
    n_coef = sum(f != 1 for f in factors)

    total_width = (
        n_coef * COEF_WIDTH
        + sum(widths_r)
        + n_plus_r * (PLUS_WIDTH + 2 * MOL_GAP)
        + ARROW_GAP
        + ARROW_LENGTH
        + ARROW_GAP
        + sum(widths_p)
        + n_plus_p * (PLUS_WIDTH + 2 * MOL_GAP)
    )

    center_y = PAGE_HEIGHT / 2
    cursor_x = (PAGE_WIDTH - total_width) / 2

    next_id = 100
    fragment_id = 1

    r_names = reactant_names or []
    p_names = product_names or []

    for i, mol in enumerate(reactants):
        if coef_r[i] != 1:
            next_id = _coefficient_text(page, next_id, cursor_x, center_y, coef_r[i])
            cursor_x += COEF_WIDTH
        w = widths_r[i]
        cx = cursor_x + w / 2
        frag, next_id, bounds = _create_fragment(
            mol,
            fragment_id,
            next_id,
            cx,
            center_y,
        )
        page.append(frag)
        fragment_id += 1

        if i < len(r_names) and r_names[i]:
            label_y = bounds[3] + 18
            t = etree.SubElement(
                page,
                "t",
                id=str(next_id),
                p=f"{cx:.2f} {label_y:.2f}",
                Justification="Center",
            )
            s = etree.SubElement(t, "s", font="3", size="8")
            s.text = r_names[i]
            next_id += 1

        cursor_x += w

        if i < len(reactants) - 1:
            cursor_x += MOL_GAP
            t = etree.SubElement(
                page,
                "t",
                id=str(next_id),
                p=f"{cursor_x + PLUS_WIDTH / 2:.2f} {center_y:.2f}",
                Justification="Center",
            )
            s = etree.SubElement(t, "s", font="3", size="10")
            s.text = "+"
            next_id += 1
            cursor_x += PLUS_WIDTH + MOL_GAP

    arrow_tail_x = cursor_x + ARROW_GAP
    arrow_head_x = arrow_tail_x + ARROW_LENGTH
    cursor_x = arrow_head_x + ARROW_GAP

    etree.SubElement(
        page,
        "arrow",
        id=str(next_id),
        FillType="None",
        **_ARROW_ATTRS[arrow],
        Head3D=f"{arrow_head_x:.2f} {center_y:.2f} 0",
        Tail3D=f"{arrow_tail_x:.2f} {center_y:.2f} 0",
    )
    next_id += 1

    cond_x = (arrow_tail_x + arrow_head_x) / 2
    if conditions:
        # p ist die Grundlinie der ERSTEN Zeile: mehrzeilig höher ansetzen.
        extra_lines = conditions.count("\n")
        cond_y = center_y - 20 - extra_lines * CONDITIONS_LINE
        next_id = _conditions_text(page, next_id, cond_x, cond_y, conditions)
    if conditions_below:
        next_id = _conditions_text(
            page, next_id, cond_x, center_y + 18, conditions_below
        )

    for i, mol in enumerate(products):
        if coef_p[i] != 1:
            next_id = _coefficient_text(page, next_id, cursor_x, center_y, coef_p[i])
            cursor_x += COEF_WIDTH
        w = widths_p[i]
        cx = cursor_x + w / 2
        frag, next_id, bounds = _create_fragment(
            mol,
            fragment_id,
            next_id,
            cx,
            center_y,
        )
        page.append(frag)
        fragment_id += 1

        if i < len(p_names) and p_names[i]:
            label_y = bounds[3] + 18
            t = etree.SubElement(
                page,
                "t",
                id=str(next_id),
                p=f"{cx:.2f} {label_y:.2f}",
                Justification="Center",
            )
            s = etree.SubElement(t, "s", font="3", size="8")
            s.text = p_names[i]
            next_id += 1

        cursor_x += w

        if i < len(products) - 1:
            cursor_x += MOL_GAP
            t = etree.SubElement(
                page,
                "t",
                id=str(next_id),
                p=f"{cursor_x + PLUS_WIDTH / 2:.2f} {center_y:.2f}",
                Justification="Center",
            )
            s = etree.SubElement(t, "s", font="3", size="10")
            s.text = "+"
            next_id += 1
            cursor_x += PLUS_WIDTH + MOL_GAP

    if name:
        all_ys = []
        for frag in page.findall("fragment"):
            for n in frag.findall("n"):
                p = n.get("p").split()
                all_ys.append(float(p[1]))
        if all_ys:
            max_y = max(all_ys)
            t = etree.SubElement(
                page,
                "t",
                p=f"{PAGE_WIDTH / 2:.2f} {max_y + 35:.2f}",
                Justification="Center",
            )
            s = etree.SubElement(t, "s", font="3", size="10")
            s.text = name

    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode("utf-8")


def write_reaction_cdxml(
    reactants: list[Chem.Mol],
    products: list[Chem.Mol],
    filepath: str,
    conditions: str = "",
    name: str = "",
    reactant_names: list[str] | None = None,
    product_names: list[str] | None = None,
    arrow: str = "forward",
    conditions_below: str = "",
    coefficients: list[int] | None = None,
) -> None:
    content = reaction_to_cdxml(
        reactants,
        products,
        conditions,
        name,
        reactant_names=reactant_names,
        product_names=product_names,
        arrow=arrow,
        conditions_below=conditions_below,
        coefficients=coefficients,
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
