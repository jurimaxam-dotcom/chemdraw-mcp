"""Rückgrat aus mmCIF (E8, E13) — Leser, Kettenfilter, Liganden, Abrufe ohne Netz.

Die Dateien unter tests/__fixtures__/pdb/ sind echte Antworten vom 10.11.2026:
RCSB ModelServer `/full` (Modell 1) für 1LYZ, 2PTN, 3I40, 4INS, 1N8Z, 1HZH,
2PRK, 1GFL, 2HHB, 3OXC, 1WLA, 3KS3 und die AlphaFold-Modelle AF-P13518 (CsrD,
E. coli) und AF-P60716 (LipA, E. coli; beide ohne PDB-Eintrag),
mit scripts/protein_fixtures.py auf Rückgratatome N/CA/C/O + HETATM ohne
Wasser gekürzt; PDBe best_structures für P00698 auf drei Einträge gekürzt, für
P60716 die 404-Antwort (best_P60716_404.json).
"""

import gzip
import json
import math
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from chemdraw_tool import protein_structure as ps

FIX = Path(__file__).parent / "__fixtures__" / "pdb"


def cif(name: str) -> str:
    return gzip.decompress((FIX / f"{name}.cif.gz").read_bytes()).decode()


def test_lysozyme_is_one_segment_of_129_residues():
    bb = ps.backbone_from_mmcif(cif("1LYZ"), ["A"], identifier="1LYZ")
    assert len(bb.segments) == 1
    seg = bb.segments[0]
    assert len(seg.coords) == 129 == len(seg.ss)
    assert set(seg.ss) <= {"H", "E", "C"}
    # 1LYZ annotiert drei α-Helices (5–15, 25–35, 89–96 = 30 Reste; 80–84 ist
    # eine 3₁₀-Helix, Klasse 5) und ein kleines β-Faltblatt
    # 30 hinterlegte Helix-Reste + Helix D (109–114), die 1LYZ nicht führt
    assert seg.ss.count("H") == 36 and seg.ss.count("E") >= 6
    assert (seg.first, seg.last) == ("1", "129")


def test_insulin_has_two_chains():
    bb = ps.backbone_from_mmcif(cif("3I40"), ["A", "B"])
    assert bb.chains == ["A", "B"] or sorted(bb.chains) == ["A", "B"]
    lengths = {s.chain: len(s.coords) for s in bb.segments}
    assert lengths == {"A": 21, "B": 30}


def test_chain_filter_keeps_only_the_fab_of_1n8z():
    everything = ps.backbone_from_mmcif(cif("1N8Z"))
    assert "C" in everything.chains  # HER2 steckt mit in der Datei
    fab = ps.backbone_from_mmcif(cif("1N8Z"), ["A", "B"])
    assert sorted(fab.chains) == ["A", "B"]
    assert all(s.chain in ("A", "B") for s in fab.segments)
    assert fab.residue_count < everything.residue_count - 400


def test_calcium_ions_are_not_read_as_c_alpha():
    text = cif("2PRK")
    assert "HETATM" in text and " CA CA CA " in text  # die Falle liegt wirklich in der Datei
    bb = ps.backbone_from_mmcif(text, ["A"])
    assert bb.residue_count == 279  # Proteinase K, reif 279 aa; ohne die Ca²⁺-Ionen


def test_chain_break_is_not_bridged():
    bb = ps.backbone_from_mmcif(cif("1N8Z"), ["C"])
    assert len(bb.segments) > 1  # HER2 hat ungeordnete Schleifen
    for seg in bb.segments:
        for p, q in zip(seg.coords, seg.coords[1:]):
            assert math.dist(p, q) <= ps.BREAK_DISTANCE
    # und zwischen zwei Segmenten derselben Kette klafft wirklich eine Lücke
    same = [s for s in bb.segments if s.chain == "C"]
    assert math.dist(same[0].coords[-1], same[1].coords[0]) > ps.BREAK_DISTANCE


def test_intact_igg_has_four_chains():
    bb = ps.backbone_from_mmcif(cif("1HZH"), ["H", "K", "L", "M"])
    assert sorted(bb.chains) == ["H", "K", "L", "M"]
    assert 1250 < bb.residue_count <= 1331
    # Ein Antikörper ist β-Faltblatt (Immunglobulin-Domänen), kaum Helix
    ss = "".join(s.ss for s in bb.segments)
    assert ss.count("E") > 5 * ss.count("H")


def test_alphafold_model_reads_strands_from_struct_conf_and_plddt():
    bb = ps.backbone_from_mmcif(cif("AF-P60716-F1-model_v6"), source="alphafold")
    assert bb.residue_count == 321 and len(bb.segments) == 1
    ss = "".join(s.ss for s in bb.segments)
    assert ss.count("E") == 47 and ss.count("H") == 112  # Radikal-SAM-(β/α)-Fass
    plddt = [v for s in bb.segments for v in s.plddt]
    assert len(plddt) == 321 and 40 < min(plddt) <= max(plddt) < 99


def test_single_row_categories_are_read():
    text = """data_x
_struct_conf.conf_type_id HELX_P
_struct_conf.beg_label_asym_id A
_struct_conf.beg_label_seq_id 2
_struct_conf.end_label_asym_id A
_struct_conf.end_label_seq_id 3
#
loop_
_atom_site.group_PDB
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_seq_id
_atom_site.auth_asym_id
_atom_site.pdbx_PDB_model_num
ATOM C CA . A 1 0.0 0.0 0.0 1 A 1
ATOM C CA A A 2 3.8 0.0 0.0 2 A 1
ATOM C CA B A 2 3.9 0.0 0.0 2 A 1
ATOM C CA . A 3 7.6 0.0 0.0 3 A 1
ATOM C CA . A 4 7.6 3.8 0.0 4 A 2
#
"""
    bb = ps.backbone_from_mmcif(text)
    assert len(bb.segments) == 1
    seg = bb.segments[0]
    assert seg.ss == "CHH"  # Einzeleintrag gelesen; Altloc B und Modell 2 nicht
    assert seg.coords[1] == (3.8, 0.0, 0.0)


def test_upper_limit_gives_a_clear_message(monkeypatch):
    monkeypatch.setattr(ps, "MAX_RESIDUES", 100)
    with pytest.raises(ps.TooLarge, match="limited to 100"):
        ps.backbone_from_mmcif(cif("1LYZ"))


def test_every_residue_carries_its_backbone_atoms():
    bb = ps.backbone_from_mmcif(cif("1LYZ"), ["A"])
    seg = bb.segments[0]
    assert len(seg.n) == len(seg.c) == len(seg.o) == 129
    assert all(p is not None for p in seg.o)  # das C-terminale O heißt O, nicht OXT
    assert seg.seq.startswith("KVFGRCELAAAMKRHGL")  # Hühnereiweiß-Lysozym
    # Geometrie an einer modernen Struktur prüfen (3KS3, 0,9 Å) — 1LYZ (1975)
    # hat C=O-Abstände von 0,7 bis 1,6 Å. C=O 1,23 Å, Cα–C 1,52 Å: dieselben
    # Reste, nichts verrutscht
    fine = ps.backbone_from_mmcif(cif("3KS3"), ["A"])
    for s in fine.segments:
        assert all(1.15 < math.dist(c, o) < 1.3 for c, o in zip(s.c, s.o))
        assert all(1.45 < math.dist(a, c) < 1.6 for a, c in zip(s.coords, s.c))


def test_alphafold_model_carries_backbone_atoms_too():
    bb = ps.backbone_from_mmcif(cif("AF-P13518-F1-model_v6"), source="alphafold")
    assert all(p is not None for s in bb.segments for p in s.o)


def test_selenomethionine_is_a_residue_not_a_ligand_or_a_break():
    text = cif("1LYZ")
    rows = [r for r in text.splitlines() if r.startswith("ATOM") and " MET " in r]
    assert rows  # Met 105
    mse = text
    for r in rows:
        mse = mse.replace(r, r.replace("ATOM", "HETATM", 1).replace(" MET ", " MSE "))
    bb = ps.backbone_from_mmcif(mse, ["A"])
    assert len(bb.segments) == 1 and bb.residue_count == 129
    assert bb.ligands == []


def test_hemoglobin_brings_its_four_hemes_and_drops_the_phosphate():
    bb = ps.backbone_from_mmcif(cif("2HHB"))
    codes = sorted(lig.code for lig in bb.ligands)
    assert codes == ["HEM"] * 4  # PO4 ist Puffer
    heme = bb.ligands[0]
    assert heme.name == "heme b" and len(heme.coords) == 43 and "Fe" in heme.elements
    assert {lig.chain for lig in bb.ligands} == {"A", "B", "C", "D"}


def test_hiv_protease_shows_its_inhibitor_once():
    # 3OXC: HIV-1-Protease-Dimer mit Saquinavir (ROC) zwischen den Ketten
    bb = ps.backbone_from_mmcif(cif("3OXC"))
    names = {lig.code: lig.name for lig in bb.ligands}
    assert names == {"ROC": "saquinavir"}
    assert len(bb.ligands[0].elements) == 49 and not bb.ligands[0].is_ion
    zinc = ps.backbone_from_mmcif(cif("3KS3"), ["A"]).ligands[0]
    assert zinc.is_ion and zinc.elements == ["Zn"]


def test_ligands_of_other_chains_stay_out():
    # 1N8Z: die NAG-Zucker sitzen an HER2 (Kette C) — beim Fab (A/B) nichts
    assert ps.backbone_from_mmcif(cif("1N8Z"), ["A", "B"]).ligands == []
    # Carboanhydrase: Zn²⁺ im aktiven Zentrum, Glycerin (Kryoschutz) nicht
    assert [lig.code for lig in ps.backbone_from_mmcif(cif("3KS3"), ["A"]).ligands] == ["ZN"]
    # Trypsin: das strukturelle Ca²⁺ bleibt und wird nicht zum Cα
    trypsin = ps.backbone_from_mmcif(cif("2PTN"), ["A"])
    assert [lig.name for lig in trypsin.ligands] == ["Ca²⁺"]


def test_entry_without_annotation_gets_its_secondary_structure_computed():
    bare = ps.backbone_from_mmcif(_without_ss(cif("1LYZ")), ["A"])
    assert bare.ss_source == "computed"
    ss = bare.segments[0].ss
    assert ss.count("H") >= 25 and ss.count("E") >= 4
    assert ps.backbone_from_mmcif(cif("1GFL"), ["A"]).ss_source == "deposited"


def _without_ss(text: str) -> str:
    """Die beiden Sekundärstruktur-Kategorien samt Zeilen entfernen."""
    out, skip = [], False
    for row in text.splitlines():
        if row.strip() == "loop_":
            skip = False
        if row.startswith(("_struct_conf.", "_struct_sheet_range.")):
            skip = True
            if out and out[-1].strip() == "loop_":
                out.pop()
            continue
        if skip and not row.startswith("#"):
            continue
        skip = False
        out.append(row)
    return "\n".join(out)


# --- Abrufe (requests.get als Attrappe) ---------------------------------------


def _resp(status: int, *, text: str = "", payload=None) -> Mock:
    m = Mock()
    m.status_code = status
    m.text = text
    m.json = Mock(return_value=payload)
    return m


@pytest.fixture
def fake_net(monkeypatch, kein_netz):
    calls: list[str] = []
    ps._CACHE.clear()

    def install(answers: dict[str, Mock]):
        def fake_get(url, timeout=None, **kw):
            calls.append(url)
            for needle, resp in answers.items():
                if needle in url:
                    return resp
            raise AssertionError(f"unerwartete URL {url}")

        monkeypatch.setattr(ps.requests, "get", fake_get)
        return calls

    yield install
    ps._CACHE.clear()


def test_best_structure_then_modelserver(fake_net):
    best = json.loads((FIX / "best_P00698.json").read_text())
    calls = fake_net({
        "best_structures/P00698": _resp(200, payload=best),
        "models.rcsb.org/v1/2VB1": _resp(200, text=cif("1LYZ")),
    })
    bb, chain = ps.structure_for_accession("P00698")
    assert chain == "A" and bb.identifier == "2VB1"
    assert bb.residue_count == 129
    assert "/full?" in calls[1] and "model_nums=1" in calls[1]


def test_no_pdb_entry_falls_back_to_alphafold(fake_net):
    af = json.loads((FIX / "af_P60716.json").read_text())
    fake_net({
        "best_structures/P60716": _resp(404, payload=json.loads((FIX / "best_P60716_404.json").read_text())),
        "api/prediction/P60716": _resp(200, payload=af),
        "AF-P60716-F1-model_v6.cif": _resp(200, text=cif("AF-P60716-F1-model_v6")),
    })
    bb, chain = ps.structure_for_accession("P60716")
    assert bb.source == "alphafold" and chain == ""
    assert bb.identifier == "AF-P60716-F1-model_v6"


def test_network_down_raises_structure_unavailable(monkeypatch, kein_netz):
    ps._CACHE.clear()

    def down(url, timeout=None, **kw):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(ps.requests, "get", down)
    with pytest.raises(ps.StructureUnavailable):
        ps.pdb_backbone("1LYZ", ["A"])
    with pytest.raises(ps.StructureUnavailable):
        ps.structure_for_accession("P00698")


def test_pdbe_timeout_falls_back_to_alphafold(fake_net, monkeypatch):
    """Gemessen 10.11.: PDBe läuft zeitweise in den 15-s-Timeout (best_structures
    für A0ACF8QHC8: 36 s) — das Protein blieb dann ungezeichnet."""
    af = json.loads((FIX / "af_P60716.json").read_text())
    fake_net({
        "api/prediction/P60716": _resp(200, payload=af),
        "AF-P60716-F1-model_v6.cif": _resp(200, text=cif("AF-P60716-F1-model_v6")),
    })
    inner = ps.requests.get

    def slow_pdbe(url, timeout=None, **kw):
        if "best_structures" in url:
            raise requests.ReadTimeout("read timed out")
        return inner(url, timeout=timeout, **kw)

    monkeypatch.setattr(ps.requests, "get", slow_pdbe)
    bb, chain = ps.structure_for_accession("P60716")
    assert bb.source == "alphafold" and chain == ""


def test_no_pdb_and_no_alphafold_is_not_a_network_problem(fake_net):
    """A0ABX6SKX1 (TrEMBL, Pseudomonas sediminis): weder PDB noch AlphaFold — gemessen 10.11."""
    fake_net({
        "best_structures/A0ABX6SKX1": _resp(404, payload={}),
        "api/prediction/A0ABX6SKX1": _resp(404, payload={}),
    })
    with pytest.raises(ps.NoStructure):
        ps.structure_for_accession("A0ABX6SKX1")
