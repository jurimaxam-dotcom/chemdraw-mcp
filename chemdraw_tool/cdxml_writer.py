import logging

from lxml import etree
from rdkit import Chem

logger = logging.getLogger(__name__)

BOND_LENGTH_POINTS = 30.0
RDKIT_BOND_LENGTH = 1.5
SCALE = BOND_LENGTH_POINTS / RDKIT_BOND_LENGTH

PAGE_WIDTH = 540
PAGE_HEIGHT = 720

ACS_SETTINGS = {
    "BondLength": str(BOND_LENGTH_POINTS),
    "BondSpacing": "18",
    "LineWidth": "0.6",
    "BoldWidth": "2",
    "MarginWidth": "1.6",
    "HashSpacing": "2.5",
    "ChainAngle": "120",
    "LabelFont": "3",
    "LabelSize": "10",
    "CaptionFont": "3",
    "CaptionSize": "10",
}

COLOR_TABLE = [
    (1.0, 1.0, 1.0),  # 0: background (white)
    (0.0, 0.0, 0.0),  # 1: foreground (black)
    (1.0, 0.0, 0.0),  # 2: red (O)
    (0.0, 0.0, 1.0),  # 3: blue (N)
    (0.0, 0.502, 0.0),  # 4: dark green (F, Cl)
    (0.784, 0.784, 0.0),  # 5: dark yellow (S)
    (0.502, 0.0, 0.502),  # 6: purple (P)
    (0.647, 0.165, 0.165),  # 7: brown (Br)
    (0.58, 0.0, 0.58),  # 8: dark magenta (I)
]

ELEMENT_COLORS: dict[int, int] = {
    7: 3,  # N → blue
    8: 2,  # O → red
    9: 4,  # F → green
    15: 6,  # P → purple
    16: 5,  # S → yellow
    17: 4,  # Cl → green
    35: 7,  # Br → brown
    53: 8,  # I → magenta
}

BOND_DIR_TO_DISPLAY: dict[Chem.BondDir, str] = {
    Chem.BondDir.BEGINWEDGE: "WedgeBegin",
    Chem.BondDir.BEGINDASH: "WedgedHashBegin",
}


def _create_cdxml_root() -> etree.Element:
    root = etree.Element("CDXML", **ACS_SETTINGS)

    colortable = etree.SubElement(root, "colortable")
    for r, g, b in COLOR_TABLE:
        etree.SubElement(colortable, "color", r=str(r), g=str(g), b=str(b))

    fonttable = etree.SubElement(root, "fonttable")
    etree.SubElement(fonttable, "font", id="3", charset="iso-8859-1", name="Arial")

    return root


def _create_fragment(
    mol: Chem.Mol,
    fragment_id: int,
    node_id_start: int,
    center_x: float,
    center_y: float,
) -> tuple[etree.Element, int, tuple[float, float, float, float]]:
    conf = mol.GetConformer()
    fragment = etree.Element("fragment", id=str(fragment_id))

    bond_id_start = node_id_start + mol.GetNumAtoms()

    positions = []
    for i in range(mol.GetNumAtoms()):
        pos = conf.GetAtomPosition(i)
        positions.append((pos.x * SCALE, -pos.y * SCALE))

    if not positions:
        raise ValueError(
            "Molekül ohne Atome kann nicht zu einem CDXML-Fragment werden."
        )

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    raw_cx = (min(xs) + max(xs)) / 2
    raw_cy = (min(ys) + max(ys)) / 2
    offset_x = center_x - raw_cx
    offset_y = center_y - raw_cy

    final_positions = []
    for i, atom in enumerate(mol.GetAtoms()):
        node_id = node_id_start + i
        x = positions[i][0] + offset_x
        y = positions[i][1] + offset_y
        final_positions.append((x, y))

        attrs = {"id": str(node_id), "p": f"{x:.2f} {y:.2f}"}

        element = atom.GetAtomicNum()
        if element != 6:
            attrs["Element"] = str(element)

        num_hs = atom.GetTotalNumHs()
        if num_hs > 0 and element != 6:
            attrs["NumHydrogens"] = str(num_hs)

        charge = atom.GetFormalCharge()
        if charge != 0:
            attrs["Charge"] = str(charge)

        if element in ELEMENT_COLORS:
            attrs["color"] = str(ELEMENT_COLORS[element])

        etree.SubElement(fragment, "n", **attrs)

    Chem.Kekulize(mol, clearAromaticFlags=False)
    Chem.WedgeMolBonds(mol, conf)

    for i, bond in enumerate(mol.GetBonds()):
        bond_id = bond_id_start + i
        begin = node_id_start + bond.GetBeginAtomIdx()
        end = node_id_start + bond.GetEndAtomIdx()
        order = int(bond.GetBondTypeAsDouble())

        attrs = {"id": str(bond_id), "B": str(begin), "E": str(end)}
        if order != 1:
            attrs["Order"] = str(order)

        bond_dir = bond.GetBondDir()
        display = BOND_DIR_TO_DISPLAY.get(bond_dir)
        if display:
            attrs["Display"] = display
        elif bond_dir != Chem.BondDir.NONE:
            logger.warning(
                "Unhandled bond direction %s (bond %d) — stereo info may be lost",
                bond_dir,
                bond_id,
            )

        etree.SubElement(fragment, "b", **attrs)

    fxs = [p[0] for p in final_positions]
    fys = [p[1] for p in final_positions]
    bounds = (min(fxs), min(fys), max(fxs), max(fys))
    next_id = bond_id_start + mol.GetNumBonds()

    return fragment, next_id, bounds


def mol_to_cdxml(mol: Chem.Mol, name: str = "") -> str:
    root = _create_cdxml_root()

    page = etree.SubElement(
        root,
        "page",
        BoundingBox=f"0 0 {PAGE_WIDTH} {PAGE_HEIGHT}",
        Width=str(PAGE_WIDTH),
        Height=str(PAGE_HEIGHT),
    )

    fragment, _, bounds = _create_fragment(
        mol,
        fragment_id=1,
        node_id_start=2,
        center_x=PAGE_WIDTH / 2,
        center_y=PAGE_HEIGHT / 2,
    )
    page.append(fragment)

    if name:
        max_y = bounds[3]
        t = etree.SubElement(
            page,
            "t",
            p=f"{PAGE_WIDTH / 2:.2f} {max_y + 30:.2f}",
            Justification="Center",
        )
        s = etree.SubElement(t, "s", font="3", size="10")
        s.text = name

    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode("utf-8")


def write_cdxml(mol: Chem.Mol, filepath: str, name: str = "") -> str:
    content = mol_to_cdxml(mol, name)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return content
