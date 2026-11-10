"""Cartoon-Geometrie (E13): Spline, Bandnormalen, Strangpfeile, Kettenbrüche, Ansicht."""

import gzip
from pathlib import Path

import numpy as np
import pytest

from chemdraw_tool import protein_cartoon as pc
from chemdraw_tool import protein_structure as ps
from chemdraw_tool import protein_view as pv

FIX = Path(__file__).parent / "__fixtures__" / "pdb"


def _bb(name, chains=None, source="pdb"):
    text = gzip.decompress((FIX / f"{name}.cif.gz").read_bytes()).decode()
    return ps.backbone_from_mmcif(text, chains, source=source, identifier=name)


def _runs(ss, code):
    i, out = 0, []
    while i < len(ss):
        if ss[i] != code:
            i += 1
            continue
        j = i
        while j < len(ss) and ss[j] == code:
            j += 1
        out.append((i, j - 1))
        i = j
    return out


def _segments(name, chains=None, source="pdb"):
    view = pv.make_view(_bb(name, chains, source))
    return [seg for c in view.chains for seg in c["segments"]]


def test_strand_arrowheads_point_to_the_c_terminus():
    """Breiteste Stelle am vorletzten Rest, Spitze am letzten — Richtung = Kettenrichtung."""
    checked = 0
    for name in ("2PTN", "1GFL"):
        for seg in _segments(name, ["A"]):
            tube = pc.build_tube(seg.ca, seg.o, seg.ss)
            for start, end in _runs(tube.ss, "E"):
                inside = (tube.u >= start - 1e-9) & (tube.u <= end + 1e-9)
                w = tube.width[inside]
                u = tube.u[inside]
                widest = u[np.argmax(w)]
                assert widest == pytest.approx(end - 1), (name, start, end)
                assert w.max() == pytest.approx(pc.ARROW_WIDTH)
                head = (u >= end - 1) & (np.arange(len(u)) > np.argmax(w))
                assert np.all(np.diff(w[head]) <= 1e-9)  # Spitze verjüngt sich nach vorn
                tip = tube.centers[inside][-1]
                back = tube.centers[inside][np.argmax(w)]
                assert (tip - back) @ (seg.ca[end] - seg.ca[start]) > 0
                # Strangschaft schmal, Spitze breiter als der Schaft
                shaft = (u > start + 0.6) & (u < end - 1 - 1e-9)
                if shaft.any():
                    assert np.allclose(w[shaft], pc.STRAND_WIDTH)
                checked += 1
    assert checked > 20


def test_ribbon_normals_never_flip_between_neighbours():
    for name, chains, source in (("2PTN", ["A"], "pdb"), ("1GFL", ["A"], "pdb"),
                                 ("1WLA", None, "pdb"),
                                 ("AF-P13518-F1-model_v6", None, "alphafold")):
        for seg in _segments(name, chains, source):
            sides = pc.side_vectors(seg.ca, seg.o, seg.ss)
            assert np.allclose(np.linalg.norm(sides, axis=1), 1)
            dots = np.einsum("ij,ij->i", sides[:-1], sides[1:])
            assert np.all(dots > 0), (name, np.argmin(dots), dots.min())
            tube = pc.build_tube(seg.ca, seg.o, seg.ss)
            along = np.einsum("ij,ij->i", tube.sides[:-1], tube.sides[1:])
            assert np.all(along > 0)
            assert np.allclose(np.einsum("ij,ij->i", tube.sides, tube.tangents), 0, atol=1e-9)


def test_band_lies_in_the_peptide_plane():
    """Strang: Bandbreite entlang C=O (Faltblattebene). Helix: entlang der Achse."""
    seg = _segments("2PTN", ["A"])[0]
    sides = pc.side_vectors(seg.ca, seg.o, seg.ss)
    co = seg.o - seg.ca
    co /= np.linalg.norm(co, axis=1)[:, None]
    strand = [i for i, s in enumerate(seg.ss) if s == "E"]
    assert np.median(np.abs(np.einsum("ij,ij->i", sides[strand], co[strand]))) > 0.8
    seg = _segments("1WLA")[0]
    sides = pc.side_vectors(seg.ca, seg.o, seg.ss)
    dots = []
    for start, end in _runs(seg.ss, "H"):
        if end - start < 8:
            continue
        axis = seg.ca[end - 1:end + 1].mean(0) - seg.ca[start:start + 2].mean(0)
        axis /= np.linalg.norm(axis)
        dots += list(np.abs(sides[start + 2:end - 2] @ axis))
    assert np.median(dots) > 0.7


def test_missing_carbonyl_does_not_break_the_band():
    """GFP: am Chromophor fehlt ein O (NaN) — Ersatzrichtung statt NaN im Netz."""
    seg = _segments("1GFL", ["A"])[0]
    assert np.isnan(seg.o).any()
    tube = pc.build_tube(seg.ca, seg.o, seg.ss)
    assert np.isfinite(tube.rings(8)).all()


def test_chain_break_draws_no_band_across_the_gap():
    view = pv.make_view(_bb("1N8Z"))
    segs = [seg for c in view.chains for seg in c["segments"]]
    tubes = pc.cartoon_tubes(view)
    assert len(tubes) == sum(len(s.ca) >= 2 for s in segs) > 3
    for (ci, seg, tube) in tubes:
        step = np.linalg.norm(np.diff(tube.centers, axis=0), axis=1)
        assert step.max() < 2.5
        assert np.linalg.norm(tube.centers[0] - seg.ca[0]) < 0.01
        assert np.linalg.norm(tube.centers[-1] - seg.ca[-1]) < 0.01


def test_view_is_a_deterministic_rotation_with_less_overlap():
    for name in ("1GFL", "AF-P13518-F1-model_v6", "2HHB"):
        bb = _bb(name, ["A"] if name == "1GFL" else None,
                 "alphafold" if name.startswith("AF") else "pdb")
        pts = np.array([p for s in bb.segments for p in s.coords], dtype=float)
        rot = pv.choose_frame(bb, pts)
        assert np.array_equal(rot, pv.choose_frame(bb, pts))
        assert np.allclose(rot @ rot.T, np.eye(3), atol=1e-9)
        assert np.isclose(np.linalg.det(rot), 1.0)
        base = pv.principal_frame(pts, pts[0])
        assert pv.self_overlap(pts, rot) <= pv.self_overlap(pts, base)
        assert ((pts[0] - pts.mean(0)) @ rot.T)[0] < 0  # N-Terminus links


def test_ligand_bonds_follow_covalent_radii():
    view = pv.make_view(_bb("1WLA"))
    heme = view.ligands[0]
    bonds = pc.ligand_bonds(heme.elements, heme.xyz)
    fe = heme.elements.index("Fe")
    assert sum(fe in b for b in bonds) == 4  # Fe–N4 der Porphyrinebene
    assert 44 <= len(bonds) <= 52


def test_ca_only_entry_still_gets_a_band():
    """CA-only-Einträge (kein O): Krümmungsrichtung statt NaN, Band bleibt ohne Umklappen."""
    seg = _segments("1WLA")[0]
    tube = pc.build_tube(seg.ca, np.full_like(seg.o, np.nan), seg.ss)
    assert np.isfinite(tube.rings(8)).all()
    assert np.all(np.einsum("ij,ij->i", tube.sides[:-1], tube.sides[1:]) > 0)


def test_single_residue_segments_are_skipped_not_drawn_across():
    from chemdraw_tool import protein_render as pr

    view = pv.make_view(_bb("3I40", ["A", "B"]))
    lone = view.chains[0]["segments"][0]
    view.chains[0]["segments"].append(pv.ViewSegment(lone.ca[:1] + 30, "C", [], lone.o[:1] + 30))
    assert len(pc.cartoon_tubes(view)) == 2
    assert pr.render_protein_png(view, "Insulin", dpi=40).startswith(b"\x89PNG")
