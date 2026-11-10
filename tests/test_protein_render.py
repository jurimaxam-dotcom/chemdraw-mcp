"""Rückgratbild und Panel-Daten (E8): Hauptachsen-Ansicht, Glättung, Datei."""

import gzip
from pathlib import Path

import numpy as np

from chemdraw_tool import protein_render as pr
from chemdraw_tool import protein_structure as ps
from chemdraw_tool import protein_view as pv

FIX = Path(__file__).parent / "__fixtures__" / "pdb"


def _bb(name, chains=None, source="pdb"):
    text = gzip.decompress((FIX / f"{name}.cif.gz").read_bytes()).decode()
    return ps.backbone_from_mmcif(text, chains, source=source, identifier=name)


def test_principal_frame_is_a_rotation_not_a_mirror():
    view_pts = np.array([p for s in _bb("1LYZ", ["A"]).segments for p in s.coords])
    rot = pr.principal_frame(view_pts, view_pts[0])
    assert np.allclose(rot @ rot.T, np.eye(3), atol=1e-9)
    assert np.isclose(np.linalg.det(rot), 1.0)  # Helices bleiben rechtsgängig


def test_view_puts_the_largest_extent_horizontal_and_n_terminus_left():
    view = pr.make_view(_bb("1HZH", ["H", "K", "L", "M"]))
    pts = np.vstack([seg.ca for c in view.chains for seg in c["segments"]])
    spread = pts.max(axis=0) - pts.min(axis=0)
    assert spread[0] >= spread[1] >= spread[2] * 0.9
    assert np.allclose(pts.mean(axis=0), 0, atol=1e-6)
    first = view.chains[0]["segments"][0].ca[0]
    assert first[0] < 0


def test_panel_chains_carry_c_alpha_and_carbonyl_as_base64():
    view = pr.make_view(_bb("3I40", ["A", "B"]), {"A": "A chain", "B": "B chain"})
    chains = pr.panel_chains(view)
    assert [c["label"] for c in chains] == ["A chain", "B chain"]
    seg = chains[0]["segments"][0]
    ca = pv.decode_xyz(seg["ca"])
    assert ca.shape == (21, 3) == (len(seg["ss"]), 3)
    assert np.allclose(ca, view.chains[0]["segments"][0].ca, atol=0.051)
    # O − Cα: 2,4 Å; zurückgerechnet auf 0,1 Å genau
    o = ca + pv.decode_offsets(seg["o"])
    assert np.allclose(o, view.chains[0]["segments"][0].o, atol=0.11)
    assert len(seg["ca"]) == 8 * 21 and len(seg["o"]) == 4 * 21  # 12 Zeichen je Rest


def test_panel_ligands_are_rotated_with_the_protein():
    bb = _bb("2HHB")
    view = pr.make_view(bb)
    ligs = pr.panel_ligands(view)
    assert [lig["code"] for lig in ligs] == ["HEM"] * 4
    xyz = pv.decode_xyz(ligs[0]["xyz"])
    assert xyz.shape == (43, 3) and ligs[0]["e"].split().count("Fe") == 1
    # Fe sitzt im selben Rahmen wie die Kette: nächstes Cα wenige Å entfernt
    fe = xyz[ligs[0]["e"].split().index("Fe")]
    ca = np.vstack([seg.ca for c in view.chains for seg in c["segments"]])
    assert np.min(np.linalg.norm(ca - fe, axis=1)) < 9


def test_alphafold_confidence_travels_as_classes():
    view = pr.make_view(_bb("AF-P60716-F1-model_v6", source="alphafold"))
    seg = pr.panel_chains(view)[0]["segments"][0]
    assert set(seg["q"]) <= set("1234") and len(seg["q"]) == len(seg["ss"])
    assert view.plddt_mean is not None and 91 < view.plddt_mean < 92


def test_catmull_rom_passes_through_every_point():
    pts = np.array([[0, 0, 0], [3.8, 0, 0], [5, 3, 1], [8, 4, 0]], dtype=float)
    curve = pr.catmull_rom(pts, sub=4)
    assert len(curve) == 3 * 4 + 1
    for i, p in enumerate(pts):
        assert np.allclose(curve[min(i * 4, len(curve) - 1)], p)


def test_chain_colors_follow_the_igg_scheme():
    view = pr.make_view(_bb("1N8Z", ["A", "B"]), {"A": "light chain", "B": "heavy chain"})
    colors = {c["label"]: c["color"] for c in view.chains}
    assert colors == {"light chain": "#E69F00", "heavy chain": "#0072B2"}


def test_figure_has_title_legend_and_termini():
    view = pr.make_view(_bb("1LYZ", ["A"]))
    fig = pr.build_protein_figure(view, "Lysozyme C, Gallus gallus — PDB 1LYZ, chain A",
                                  "Cα backbone trace", "PDB 1LYZ")
    texts = [t.get_text() for t in fig.texts] + [t.get_text() for ax in fig.axes for t in ax.texts]
    assert "Lysozyme C, Gallus gallus — PDB 1LYZ, chain A" in texts
    assert "N" in texts and "C" in texts
    legend = [t.get_text() for t in fig.legends[0].get_texts()]
    assert legend == ["α-helix", "β-strand", "loop"]


def test_multi_chain_figure_colors_by_chain():
    view = pr.make_view(_bb("3I40", ["A", "B"]), {"A": "A chain", "B": "B chain"})
    fig = pr.build_protein_figure(view, "Insulin")
    legend = [t.get_text() for t in fig.legends[0].get_texts()]
    assert legend == ["A chain (A)", "B chain (B)"]


def test_png_and_deterministic_svg():
    view = pr.make_view(_bb("3I40", ["A", "B"]))
    assert pr.render_protein_png(view, "Insulin", dpi=60).startswith(b"\x89PNG")
    a = pr.render_protein_svg(view, "Insulin")
    assert a == pr.render_protein_svg(view, "Insulin") and a.startswith("<?xml")


def test_long_texts_wrap_without_overlap_and_stay_inside():
    """Gemessen 10.11.: lange Titel liefen in den Untertitel, lange Unterzeilen über den Rand."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    view = pr.make_view(_bb("1LYZ", ["A"]))
    title = ("Tryptophan synthase alpha chain (TrpA), Pseudomonas sediminis (bacterium) — "
             "UniProt unreviewed (TrEMBL)")
    subtitle = ("PDB 1GFL, chain A · smoothed Cα trace · 230 residues · Q80R, the common "
                "cloned variant; one of two copies in the crystal")
    citation = ("Model: AlphaFold DB AF-A0A4R5G325-F1-model_v6 (CC BY 4.0) — Jumper et al. 2021, "
                "Nature 596:583; Varadi et al. 2024, Nucleic Acids Res. 52:D368 · UniProt A0A4R5G325 (CC BY 4.0)")
    fig = pr.build_protein_figure(view, title, subtitle, citation)
    renderer = FigureCanvasAgg(fig).get_renderer()
    boxes = [t.get_window_extent(renderer) for t in fig.texts]
    width, height = fig.bbox.width, fig.bbox.height
    for b in boxes:
        assert b.x0 >= 0 and b.x1 <= width and b.y0 >= 0 and b.y1 <= height, b
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert not a.overlaps(b), (a, b)


def test_small_proteins_do_not_turn_into_sausages():
    """Insulin (51 Reste) bekam 65 pt breite Helices — der Maßstab ist gedeckelt."""
    view = pr.make_view(_bb("3I40", ["A", "B"]))
    fig = pr.build_protein_figure(view, "Insulin")
    ax = fig.axes[0]
    pts_per_a = ax.get_position().width * fig.get_figwidth() * 72 / np.ptp(ax.get_xlim())
    assert pts_per_a <= pr.MAX_PTS_PER_A + 1e-6


def test_cartoon_is_drawn_as_shaded_polygons_not_lines():
    from matplotlib.collections import LineCollection, PolyCollection

    view = pr.make_view(_bb("1LYZ", ["A"]))
    fig = pr.build_protein_figure(view, "Lysozyme")
    colls = fig.axes[0].collections
    assert not any(isinstance(c, LineCollection) for c in colls)
    polys = [c for c in colls if isinstance(c, PolyCollection)]
    assert len(polys) == 1 and len(polys[0].get_paths()) > 3000
    # schattiert: viele verschiedene Flächenfarben, nicht drei SS-Farben
    faces = polys[0].get_facecolors()
    assert len(np.unique(np.round(faces[faces[:, 3] > 0], 3), axis=0)) > 200
    svg = pr.render_protein_svg(view, "Lysozyme")
    assert svg.count(" z\"") > 3000  # geschlossene Polygone im Vektor-SVG


def test_legend_names_each_ligand_once():
    view = pr.make_view(_bb("2HHB"))
    fig = pr.build_protein_figure(view, "Hemoglobin")
    legend = [t.get_text() for t in fig.legends[0].get_texts()]
    assert legend.count("heme b (HEM)") == 1
    # Häm-Symbol grau wie seine C-Stäbe: Fe-Orange läse sich wie die Farbe der β1-Kette
    colors = dict(pr._ligand_legend(view))
    assert colors["heme b (HEM)"] == pr.ELEMENT_COLOR["C"]
    view = pr.make_view(_bb("3KS3"))
    legend = [t.get_text() for t in pr.build_protein_figure(view, "CA II").legends[0].get_texts()]
    assert "Zn²⁺" in legend and legend[:3] == ["α-helix", "β-strand", "loop"]


def test_termini_labels_sit_beside_the_structure():
    """N-/C-Marken verdecken keinen Teil des Cartoons und einander nicht."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from chemdraw_tool import protein_cartoon as pc

    for name, chains in (("2HHB", None), ("1HZH", ["H", "K", "L", "M"])):
        view = pr.make_view(_bb(name, chains))
        fig = pr.build_protein_figure(view, name)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()  # erst dann haben die Textboxen ihre Lage
        renderer = canvas.get_renderer()
        ax = fig.axes[0]
        labels = [t for t in ax.texts if t.get_text()[0] in "NC"]
        assert len(labels) == 2 * len(view.chains)
        pts = np.vstack([t.centers[:, :2] for _, _, t in pc.cartoon_tubes(view, 2)])
        disp = ax.transData.transform(pts)
        boxes = [t.get_bbox_patch().get_window_extent(renderer) for t in labels]
        for b in boxes:
            inside = ((disp[:, 0] > b.x0) & (disp[:, 0] < b.x1)
                      & (disp[:, 1] > b.y0) & (disp[:, 1] < b.y1))
            assert not inside.any(), name
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                assert not a.overlaps(b)


def test_large_antibody_stays_within_svg_budget():
    """1HZH (1331 Reste): Vektor-SVG unter 5 MB."""
    view = pr.make_view(_bb("1HZH", ["H", "K", "L", "M"]))
    svg = pr.render_protein_svg(view, "IgG")
    assert len(svg.encode()) < 5_000_000
