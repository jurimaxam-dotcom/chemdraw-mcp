from lxml import etree
from rdkit import Chem

from chemdraw_tool.cdxml_writer import (
    PAGE_HEIGHT,
    PAGE_WIDTH,
    SCALE,
    _create_cdxml_root,
    _create_fragment,
)

MOL_GAP = 40.0
PLUS_WIDTH = 20.0
ARROW_LENGTH = 60.0
ARROW_GAP = 20.0


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
) -> str:
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

    total_width = (
        sum(widths_r)
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
        ArrowheadHead="Full",
        ArrowheadType="Solid",
        Head3D=f"{arrow_head_x:.2f} {center_y:.2f} 0",
        Tail3D=f"{arrow_tail_x:.2f} {center_y:.2f} 0",
    )
    next_id += 1

    if conditions:
        cond_x = (arrow_tail_x + arrow_head_x) / 2
        cond_y = center_y - 20
        t = etree.SubElement(
            page,
            "t",
            id=str(next_id),
            p=f"{cond_x:.2f} {cond_y:.2f}",
            Justification="Center",
        )
        s = etree.SubElement(t, "s", font="3", size="8")
        s.text = conditions
        next_id += 1

    for i, mol in enumerate(products):
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
) -> None:
    content = reaction_to_cdxml(
        reactants,
        products,
        conditions,
        name,
        reactant_names=reactant_names,
        product_names=product_names,
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
