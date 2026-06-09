#!/usr/bin/env python3
"""Generate complexometric titration reaction equations as CDXML.

Layout exakt nach handschriftlicher Vorlage:
- [His]₂ Cu²⁺  inline (Cu rechts neben Klammer)
- Gleichgewichtspfeile ⇌
- Produkt-His mit NH₃ (protoniert)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lxml import etree
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.cdxml_writer import SCALE, _create_cdxml_root, _create_fragment

OUTPUT = os.path.expanduser("~/ChemDraw-Output")
os.makedirs(OUTPUT, exist_ok=True)


def gen2d(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError(f"Bad SMILES: {smiles}")
    AllChem.Compute2DCoords(mol)
    return mol


def mol_w(mol):
    c = mol.GetConformer()
    xs = [c.GetAtomPosition(i).x * SCALE for i in range(mol.GetNumAtoms())]
    return max(xs) - min(xs) if xs else 0


def place(page, mol, fid, nid, cx, cy):
    frag, nid, bounds = _create_fragment(mol, fid, nid, cx, cy)
    page.append(frag)
    return nid, bounds


def txt(page, nid, x, y, parts, size="10", just="Center"):
    """parts: [(text, face|None), ...] — '32'=sub, '64'=super"""
    t = etree.SubElement(
        page, "t", id=str(nid), p=f"{x:.1f} {y:.1f}", Justification=just
    )
    for text, face in parts:
        a = {"font": "3", "size": size}
        if face:
            a["face"] = face
        s = etree.SubElement(t, "s", **a)
        s.text = text
    return nid + 1


def bracket(page, nid, x1, y1, x2, y2):
    etree.SubElement(
        page,
        "graphic",
        id=str(nid),
        GraphicType="Bracket",
        BracketType="SquarePair",
        BoundingBox=f"{x1:.1f} {y1:.1f} {x2:.1f} {y2:.1f}",
    )
    return nid + 1


def arrow_single(page, nid, tx, hx, y):
    etree.SubElement(
        page,
        "arrow",
        id=str(nid),
        FillType="None",
        ArrowheadHead="Full",
        ArrowheadType="Solid",
        Head3D=f"{hx:.1f} {y:.1f} 0",
        Tail3D=f"{tx:.1f} {y:.1f} 0",
    )
    return nid + 1


def arrow_equilibrium(page, nid, tx, hx, y, gap=3.5):
    """⇌ als zwei gegenläufige Halbpfeile."""
    for i, (t, h, dy) in enumerate(
        [
            (tx, hx, -gap),  # vorwärts oben →
            (hx, tx, gap),  # rückwärts unten ←
        ]
    ):
        etree.SubElement(
            page,
            "arrow",
            id=str(nid + i),
            FillType="None",
            ArrowheadHead="Full",
            ArrowheadType="Solid",
            ArrowheadCenterSize="3.5",
            ArrowheadWidth="5",
            Head3D=f"{h:.1f} {y + dy:.1f} 0",
            Tail3D=f"{t:.1f} {y + dy:.1f} 0",
        )
    return nid + 2


def save(root, name):
    path = f"{OUTPUT}/{name}.cdxml"
    with open(path, "w") as f:
        f.write(
            etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", pretty_print=True
            ).decode()
        )
    print(f"  ✓ {path}")


# ── Moleküle ──
# Histidin im Komplex (deprotoniertes Carboxylat)
his_complex = gen2d("N[C@@H](Cc1c[nH]cn1)C(=O)[O-]")
# Histidin protoniert (Produkt) — ohne Stereo, um ChemDraw-Valenzwarnung zu vermeiden
his_product = gen2d("[NH3+]C(Cc1c[nH]cn1)C(=O)O")
# EDTA (Y⁴⁻)
edta = gen2d("[O-]C(=O)CN(CCN(CC(=O)[O-])CC(=O)[O-])CC(=O)[O-]")

hw = mol_w(his_complex)
hpw = mol_w(his_product)
PAD = 10


# ═══════════════════════════════════════════════════════════
# Reaktion 1: Alkalimetrische Titration
# [His]₂ Cu²⁺ + 6 HCl  ⇌  2 His·H + Cu²⁺ + 6 Cl⁻
# ═══════════════════════════════════════════════════════════
print("Reaktion 1: Alkalimetrische Titration")

PW, PH = 1200, 400
root = _create_cdxml_root()
pg = etree.SubElement(
    root, "page", BoundingBox=f"0 0 {PW} {PH}", Width=str(PW), Height=str(PH)
)
cy = PH / 2 + 5
nid, fid = 10, 1

# Titel
nid = txt(pg, nid, PW / 2, 32, [("Alkalimetrische Titration", None)], size="14")

# ── [His]₂ Cu²⁺ (Komplex) ──
cx = 90
nid, bnd = place(pg, his_complex, fid, nid, cx + hw / 2, cy)
fid += 1

bx1, by1 = bnd[0] - PAD, bnd[1] - PAD
bx2, by2 = bnd[2] + PAD, bnd[3] + PAD
nid = bracket(pg, nid, bx1, by1, bx2, by2)

# ₂ subscript unten rechts an Klammer
nid = txt(pg, nid, bx2 + 7, by2 + 5, [("2", "32")], size="11")

# ²⁺ Ladung oben rechts an Klammer
nid = txt(pg, nid, bx2 + 14, by1 - 6, [("2+", None)], size="9")

# Cu²⁺ RECHTS neben Klammer, INLINE (gleiche y wie Reaktionszentrum)
nid = txt(pg, nid, bx2 + 38, cy, [("Cu", None), ("2+", "64")], size="11")
cx = bx2 + 65

# +
nid = txt(pg, nid, cx + 15, cy, [("+", None)], size="14")
cx += 40

# 6 HCl
nid = txt(pg, nid, cx + 25, cy, [("6 HCl", None)], size="11")
cx += 65

# ⇌ Gleichgewichtspfeile
nid = arrow_equilibrium(pg, nid, cx + 10, cx + 80, cy)
cx += 100

# 2 (Koeffizient)
nid = txt(pg, nid, cx + 5, cy, [("2", None)], size="13")
cx += 20

# Protoniertes Histidin
nid, bnd2 = place(pg, his_product, fid, nid, cx + hpw / 2, cy)
fid += 1
cx = bnd2[2] + 20

# + Cu²⁺
nid = txt(pg, nid, cx + 12, cy, [("+", None)], size="14")
cx += 35
nid = txt(pg, nid, cx + 15, cy, [("Cu", None), ("2+", "64")], size="11")
cx += 45

# + 6 Cl⁻
nid = txt(pg, nid, cx + 12, cy, [("+", None)], size="14")
cx += 35
nid = txt(pg, nid, cx + 18, cy, [("6 Cl", None), ("⁻", "64")], size="11")

save(root, "Alkalimetrische-Titration")


# ═══════════════════════════════════════════════════════════
# Reaktion 2: Komplexometrische Titration
# [His]₂ Cu²⁺ + H₂Y²⁻  ⇌  CuY²⁻ + 2 His
# Y⁴⁻ = EDTA
# ═══════════════════════════════════════════════════════════
print("Reaktion 2: Komplexometrische Titration")

PW2, PH2 = 770, 650
root2 = _create_cdxml_root()
pg2 = etree.SubElement(
    root2,
    "page",
    BoundingBox=f"0 0 {PW2} {PH2}",
    Width=str(PW2),
    Height=str(PH2),
    WidthPages="1",
    HeightPages="1",
)
ry = 135
nid, fid = 200, 10

nid = txt(pg2, nid, PW2 / 2, 32, [("Komplexometrische Titration", None)], size="14")

# ── [His]₂ Cu²⁺ ──
cx = 60
his2 = gen2d("N[C@@H](Cc1c[nH]cn1)C(=O)[O-]")
nid, bnd = place(pg2, his2, fid, nid, cx + hw / 2, ry)
fid += 1

bx1, by1 = bnd[0] - PAD, bnd[1] - PAD
bx2, by2 = bnd[2] + PAD, bnd[3] + PAD
nid = bracket(pg2, nid, bx1, by1, bx2, by2)
nid = txt(pg2, nid, bx2 + 7, by2 + 5, [("2", "32")], size="11")
nid = txt(pg2, nid, bx2 + 14, by1 - 6, [("2+", None)], size="9")
nid = txt(pg2, nid, bx2 + 35, ry, [("Cu", None), ("2+", "64")], size="11")
cx = bx2 + 55

# + H₂Y²⁻
nid = txt(pg2, nid, cx + 12, ry, [("+", None)], size="14")
cx += 30
nid = txt(
    pg2,
    nid,
    cx + 22,
    ry,
    [("H", None), ("2", "32"), ("Y", None), ("2−", "64")],
    size="11",
)
cx += 55

# ⇌
nid = arrow_equilibrium(pg2, nid, cx + 8, cx + 65, ry)
cx += 80

# CuY²⁻
nid = txt(pg2, nid, cx + 18, ry, [("CuY", None), ("2−", "64")], size="11")
cx += 48

# + 2 His
nid = txt(pg2, nid, cx + 10, ry, [("+", None)], size="14")
cx += 28
nid = txt(pg2, nid, cx + 5, ry, [("2", None)], size="13")
cx += 18

his3 = gen2d("N[C@@H](Cc1c[nH]cn1)C(=O)[O-]")
nid, _ = place(pg2, his3, fid, nid, cx + hw / 2, ry)
fid += 1

# Annotation
mid_eq = cx - 200
nid = txt(pg2, nid, mid_eq + 45, ry + 30, [("dominierend im sauren", None)], size="8")
nid = txt(pg2, nid, mid_eq + 45, ry + 42, [("bis neutralen Bereich", None)], size="8")

# ── Y⁴⁻ = EDTA ──
ey = 440
nid = txt(
    pg2, nid, 80, ey, [("Y", None), ("4−", "64"), ("  =", None)], size="13", just="Left"
)

frag, nid, _ = _create_fragment(edta, fid, nid, 380, ey)
pg2.append(frag)

save(root2, "Komplexometrische-Titration")

print("\nFertig!")
