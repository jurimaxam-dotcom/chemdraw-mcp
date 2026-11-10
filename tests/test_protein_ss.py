"""Eigene Sekundärstruktur-Zuweisung (protein_ss, E13) gegen hinterlegte Angaben.

Gemessen 10.11.2026 (Q3 = Anteil gleicher Zustände H/E/C je Rest):
1LYZ 0,82 · 4INS 0,82 · 3I40 0,88 · 1GFL 0,98 · 2HHB 0,83 · 2PTN 0,88 ·
3OXC · 1HZH 0,97 · 1WLA 0,88 · 3KS3 0,96 · AF-P13518 (siehe Test).
Die PDB-Angaben stammen oft von den Autoren (Helices samt Kappen, 1LYZ mit
Geometrie von 1975); das AlphaFold-Modell trägt echte DSSP-Angaben — dort
liegt die Übereinstimmung bei 98 %, Helix-Reste 100 %.
"""

import gzip
from pathlib import Path

import pytest

from chemdraw_tool import protein_structure as ps
from chemdraw_tool.protein_ss import assign_segments

FIX = Path(__file__).parent / "__fixtures__" / "pdb"


def _bb(name, chains=None):
    text = gzip.decompress((FIX / f"{name}.cif.gz").read_bytes()).decode()
    return ps.backbone_from_mmcif(text, chains, source="alphafold" if name.startswith("AF") else "pdb")


def _compare(bb):
    deposited = "".join(s.ss for s in bb.segments)
    computed = "".join(assign_segments(bb.segments))
    q3 = sum(a == b for a, b in zip(deposited, computed)) / len(deposited)
    return deposited, computed, q3


@pytest.mark.parametrize("name,chains,q3_min", [
    ("1LYZ", ["A"], 0.8),
    ("4INS", ["A", "B", "C", "D"], 0.8),
    ("3I40", ["A", "B"], 0.85),
    ("1GFL", ["A"], 0.95),
    ("2HHB", None, 0.8),
    ("3OXC", None, 0.75),
    ("1HZH", None, 0.95),
])
def test_agreement_with_the_deposited_annotation(name, chains, q3_min):
    _, _, q3 = _compare(_bb(name, chains))
    assert q3 >= q3_min


def test_alphafold_dssp_is_reproduced():
    deposited, computed, q3 = _compare(_bb("AF-P13518-F1-model_v6"))
    assert q3 >= 0.97
    helix = [i for i, x in enumerate(deposited) if x == "H"]
    assert sum(computed[i] == "H" for i in helix) / len(helix) >= 0.98


def test_gfp_barrel_is_strands_and_hemoglobin_is_helices():
    _, gfp, _ = _compare(_bb("1GFL", ["A"]))
    assert gfp.count("E") > 100 and gfp.count("H") < 15
    _, hb, _ = _compare(_bb("2HHB"))
    assert hb.count("H") > 350 and hb.count("E") == 0


def test_backbone_without_n_c_o_is_left_alone():
    bb = _bb("1LYZ", ["A"])
    for seg in bb.segments:
        seg.n = [None] * len(seg.coords)
    assert assign_segments(bb.segments) is None


def test_old_entries_get_missing_helices_filled_in():
    # 2PTN (1981) hinterlegt nur zwei HELIX-Einträge; die C-terminale Helix
    # 235–245 („CONTIGUOUS WITH H3“, H3 selbst fehlt) stand als graue Spirale da.
    bb = _bb("2PTN", ["A"])
    seg = bb.segments[0]
    assert "HHHHHHHH" in seg.ss[-14:], seg.ss[-25:]
    assert bb.ss_source == "deposited+computed"
    # Lysozym 1LYZ: Helix D (109–115) fehlt in den Angaben
    lyz = _bb("1LYZ")
    assert "HHHHHH" in lyz.segments[0].ss[105:118]
    # Neuere Einträge mit vollständigen Angaben bleiben unverändert
    assert _bb("1GFL", ["A"]).ss_source == "deposited"
    assert _bb("2HHB").ss_source == "deposited"
