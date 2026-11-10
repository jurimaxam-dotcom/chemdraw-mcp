"""Proteine zeichnen (E8): generate_molecule und generate_3d liefern die Rückgratspur.

Kein Netz: ModelServer-, PDBe- und AlphaFold-Antworten kommen aus
tests/__fixtures__/pdb/ (echte Antworten vom 10.11.2026), Dateien landen in tmp_path.
"""

import asyncio
import gzip
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from mcp.client import Client

from chemdraw_tool import protein_structure as ps
from chemdraw_tool import resolver
from chemdraw_tool import server as srv
from chemdraw_tool.resolver import NameResolutionError

FIX = Path(__file__).parent / "__fixtures__" / "pdb"


def _cif(name: str) -> str:
    return gzip.decompress((FIX / f"{name}.cif.gz").read_bytes()).decode()


def _resp(status=200, text="", payload=None):
    m = Mock()
    m.status_code = status
    m.text = text
    m.json = Mock(return_value=payload)
    return m


ROUTES = {
    "models.rcsb.org/v1/1LYZ/": lambda: _resp(text=_cif("1LYZ")),
    "models.rcsb.org/v1/2PTN/": lambda: _resp(text=_cif("2PTN")),
    "models.rcsb.org/v1/3I40/": lambda: _resp(text=_cif("3I40")),
    "models.rcsb.org/v1/1N8Z/": lambda: _resp(text=_cif("1N8Z")),
    "models.rcsb.org/v1/1HZH/": lambda: _resp(text=_cif("1HZH")),
    "models.rcsb.org/v1/2HHB/": lambda: _resp(text=_cif("2HHB")),
    "models.rcsb.org/v1/3KS3/": lambda: _resp(text=_cif("3KS3")),
    "models.rcsb.org/v1/1GFL/": lambda: _resp(text=_cif("1GFL")),
    "best_structures/P60716": lambda: _resp(404, payload=json.loads((FIX / "best_P60716_404.json").read_text())),
    "api/prediction/P60716": lambda: _resp(payload=json.loads((FIX / "af_P60716.json").read_text())),
    "AF-P60716-F1-model_v6.cif": lambda: _resp(text=_cif("AF-P60716-F1-model_v6")),
}


@pytest.fixture
def structures(monkeypatch, tmp_path, kein_netz):
    """Strukturabrufe aus Fixtures, Ausgabe nach tmp_path, Caches leer."""
    calls: list[str] = []

    def fake_get(url, timeout=None, **kw):
        calls.append(url)
        for needle, answer in ROUTES.items():
            if needle in url:
                return answer()
        raise AssertionError(f"unerwartete URL {url}")

    monkeypatch.setattr(ps.requests, "get", fake_get)
    for const in ("OUTPUT_DIR", "PROTEIN_DIR", "THREED_DIR", "PLOT_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    ps._CACHE.clear()
    resolver.resolve_name.cache_clear()
    yield calls
    ps._CACHE.clear()
    resolver.resolve_name.cache_clear()


def _residues(payload) -> dict[str, int]:
    return {
        c["id"]: sum(len(s["ss"]) for s in c["segments"]) for c in payload.protein.chains
    }


def test_draw_lysozyme_is_the_hen_enzyme_as_backbone(structures):
    payload = srv.generate_molecule("lysozyme")
    assert payload.type == "protein"
    assert payload.protein.title == "Lysozyme C, Gallus gallus (hen egg white)"
    assert payload.protein.subtitle.startswith("PDB 1LYZ, chain A · cartoon · 129 residues")
    assert _residues(payload) == {"A": 129}
    assert payload.protein.colorBy == "ss"
    assert "drawn as a cartoon (ribbon diagram: helices as spirals, strands as arrows), not a skeletal formula" in payload.message
    assert "human lysozyme (UniProt P61626)" in payload.message
    # 1LYZ führt Helix D nicht — ergänzt und gesagt
    assert payload.protein.ssSource == "deposited+computed"
    assert "Helices the entry's annotation omits were added" in payload.message
    assert "CC0" in payload.protein.citation and "P00698" in payload.protein.citation
    for fmt in ("png", "svg"):
        assert Path(payload.files[fmt]).exists()
    assert Path(payload.files["png"]).read_bytes().startswith(b"\x89PNG")


def test_3d_structure_of_trypsin(structures):
    payload = srv.generate_3d("trypsin")
    assert payload.type == "protein"
    assert "Bos taurus" in payload.protein.title
    assert payload.protein.subtitle.startswith("PDB 2PTN, chain A")
    assert sum(_residues(payload).values()) > 200


def test_insulin_shows_two_chains_colored_by_chain(structures):
    payload = srv.generate_molecule("insulin")
    assert _residues(payload) == {"A": 21, "B": 30}
    assert payload.protein.colorBy == "chain"
    assert [c["label"] for c in payload.protein.chains] == ["A chain", "B chain"]
    assert "porcine insulin (PDB 4INS" in payload.message


def test_trastuzumab_is_its_fab_with_the_scheme(structures):
    payload = srv.generate_molecule("trastuzumab")
    assert set(_residues(payload)) == {"A", "B"}  # HER2 (Kette C) nicht dabei
    assert payload.protein.title.startswith("Trastuzumab Fab fragment")
    assert "antigen is not shown" in payload.protein.subtitle
    assert Path(payload.files["scheme_png"]).exists() and Path(payload.files["scheme_svg"]).exists()
    assert "IgG domain scheme" in payload.message
    # Panel: eigene Struktur zuerst, im Schema ist ein Fab-Arm markiert
    assert payload.protein.scheme == {
        "start": "structure", "highlight": "fab",
        "caption": "The structure shown (PDB 1N8Z) is one Fab arm of the IgG.",
    }


def test_lysozyme_has_no_antibody_scheme(structures):
    assert srv.generate_molecule("lysozyme").protein.scheme is None


def test_unknown_antibody_gets_the_general_architecture(structures):
    payload = srv.generate_molecule("anti-GFP")
    assert payload.protein.title.startswith("Architecture of an intact IgG, not anti-GFP")
    assert set(_residues(payload)) == {"H", "K", "L", "M"}
    assert "No structure of this particular antibody is shown" in payload.message
    assert "scheme_png" in payload.files
    # Kein eigener Eintrag: das Panel öffnet auf dem Schema
    assert payload.protein.scheme["start"] == "scheme"
    assert payload.protein.scheme["highlight"] == ""


def test_gene_symbol_without_pdb_entry_shows_the_alphafold_model(structures, monkeypatch):
    # LipA (E. coli K-12, P60716): geprüft, kein PDB-Eintrag (PDBe 404), AlphaFold v6
    record = {
        "accession": "P60716", "name": "Lipoyl synthase", "gene": "lipA",
        "organism": "Escherichia coli (strain K12)", "domain": "bacterium",
        "reviewed": True, "length": 321, "mass": 36072,
        "others": ["Mycobacterium tuberculosis", "Bacillus subtilis", "Saccharolobus solfataricus"],
    }
    monkeypatch.setattr(resolver, "_gene_lookup", lambda name: record)
    payload = srv.generate_molecule("LipA")
    assert payload.protein.title == "Lipoyl synthase (LipA), Escherichia coli (bacterium)"
    assert payload.protein.subtitle.startswith("AlphaFold model, predicted · cartoon")
    assert payload.protein.source == "alphafold"
    assert "CC BY 4.0" in payload.protein.citation and "Jumper" in payload.protein.citation
    assert payload.protein.plddtMean and payload.protein.plddtMean > 90
    assert all("q" in s for c in payload.protein.chains for s in c["segments"])
    assert '"LipA Mycobacterium tuberculosis"' in payload.message
    assert "('LIPA')" in payload.message
    assert "predicted model" in payload.message


def test_network_down_keeps_the_protein_message(structures, monkeypatch):
    def down(url, timeout=None, **kw):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(ps.requests, "get", down)
    with pytest.raises(NameResolutionError) as info:
        srv.generate_molecule("lysozyme")
    assert info.value.kind == "protein"
    message = str(info.value)
    assert "Lysozyme C, Gallus gallus" in message
    assert "could not be fetched right now" in message
    assert not any((Path(srv.PROTEIN_DIR)).rglob("*.png")) if Path(srv.PROTEIN_DIR).exists() else True


def test_batch_generate_still_lists_proteins_as_not_drawn(structures):
    result = srv.batch_generate(["lysozyme", "CCO"])
    assert len(result.molecules) == 1
    assert result.failed[0].startswith("lysozyme (protein")


# --- Über den echten SDK-Client: Validierung gegen das Ausgabeschema ------------


def _call(tool: str, arguments: dict):
    async def run():
        async with Client(srv.create_server("mvp")) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(run())


@pytest.mark.parametrize("tool", ["generate_molecule", "generate_3d"])
def test_protein_payload_passes_the_sdk_output_validation(structures, tool):
    result = _call(tool, {"name_or_smiles": "insulin"})
    assert not result.is_error, result.content
    data = result.structured_content
    assert data["type"] == "protein"
    assert [c["id"] for c in data["protein"]["chains"]] == ["A", "B"]
    text = "\n".join(getattr(b, "text", "") for b in result.content)
    # Die Koordinaten stehen als eine Zeichenkette je Segment, nicht Zahl für Zahl
    assert len(text) < 15_000


def test_hemoglobin_shows_its_four_hemes(structures):
    payload = srv.generate_molecule("hemoglobin")
    assert [lig["code"] for lig in payload.protein.ligands] == ["HEM"] * 4
    assert "Bound groups drawn as sticks/spheres: heme b (HEM) ×4." in payload.message
    assert "with its four hemes" in payload.protein.subtitle


def test_carbonic_anhydrase_shows_its_zinc(structures):
    payload = srv.generate_molecule("carbonic anhydrase")
    assert [lig["code"] for lig in payload.protein.ligands] == ["ZN"]
    assert "Zn²⁺" in payload.message


def _answer_size(name):
    result = _call("generate_3d", {"name_or_smiles": name})
    text = "\n".join(getattr(b, "text", "") for b in result.content)
    residues = sum(len(s["ss"]) for c in result.structured_content["protein"]["chains"]
                   for s in c["segments"])
    return len(text) + len(json.dumps(result.structured_content)), residues


def test_answer_stays_far_below_the_hosts_limit(structures):
    """Claude reicht über ~150 000 Zeichen das Ergebnis nicht ans Panel weiter.

    Die Daten stehen zweimal in der Antwort (Text + structuredContent). Je Rest
    unter 33 Zeichen; dazu höchstens MAX_LIGAND_ATOMS × 2 × 8 Zeichen Liganden
    und ~3 000 Zeichen Text — bei MAX_RESIDUES also unter 115 000.
    """
    total, residues = _answer_size("IgG")
    assert residues > 1300 and total / residues < 33, total
    worst = ps.MAX_RESIDUES * total / residues + ps.MAX_LIGAND_ATOMS * 2 * 8 + 3_000
    assert worst < 115_000
    hemo, _ = _answer_size("hemoglobin")  # 574 Reste + vier Häm
    assert hemo < 30_000


# --- Datenblatt (lookup biochem): dieselbe Wahl wie das Bild -------------------

ENTRY_FIX = Path(__file__).parent / "__fixtures__" / "uniprot" / "e8"


@pytest.fixture
def entries(monkeypatch):
    """UniProt-Einträge aus Fixtures; PDBe kennt P60716 nicht (echte 404).

    databases und protein_structure teilen dasselbe requests-Modul — eine Attrappe.
    """
    def fake_get(url, timeout=None, **kw):
        if "best_structures" in url:
            return _resp(404, payload={"message": "no data"})
        for acc in ("P60716", "P00698"):
            if f"uniprotkb/{acc}" in url:
                return _resp(payload=json.loads((ENTRY_FIX / f"entry-{acc}-0.json").read_text()))
        raise AssertionError(f"unerwartete URL {url}")

    monkeypatch.setattr(ps.requests, "get", fake_get)
    ps._CACHE.clear()


def test_sheet_for_lysozyme_names_the_drawn_structure(entries):
    sheet = srv._lookup_biochem("lysozyme")
    assert "Gallus gallus (hen egg white)" in sheet
    assert "P00698" in sheet and "3.2.1.17" in sheet
    assert "129 amino acids (mature chain)" in sheet
    assert "**Drawn structure:** PDB 1LYZ, chain A" in sheet
    assert "human lysozyme (UniProt P61626)" in sheet


def test_sheet_for_gene_symbol_has_reaction_cofactor_and_the_alphafold_model(entries, monkeypatch):
    record = {
        "accession": "P60716", "name": "Lipoyl synthase", "gene": "lipA",
        "organism": "Escherichia coli (strain K12)", "domain": "bacterium",
        "reviewed": True, "length": 321, "mass": 36072,
        "others": ["Mycobacterium tuberculosis"],
    }
    monkeypatch.setattr(resolver, "_gene_lookup", lambda name: record)
    sheet = srv._lookup_biochem("LipA")
    assert "Escherichia coli (bacterium)" in sheet
    assert "RHEA:16585" in sheet and "dihydrolipoyl" in sheet and "2.8.1.8" in sheet
    assert "[4Fe-4S] cluster" in sheet
    assert "S-adenosyl-L-methionine (SAM) is a co-substrate" in sheet
    assert "AlphaFold model AF-P60716-F1 (predicted; no PDB structure)" in sheet
    assert "Mycobacterium tuberculosis" in sheet


def test_entry_without_any_structure_says_so(structures, monkeypatch):
    def none(accession):
        raise ps.NoStructure(f"no PDB structure and no AlphaFold model for {accession}")

    monkeypatch.setattr(ps, "structure_for_accession", none)
    record = {"accession": "A0ABX6SKX1", "name": "Tryptophan synthase alpha chain", "gene": "trpA",
              "organism": "Pseudomonas sediminis", "domain": "bacterium",
              "reviewed": False, "length": 269, "mass": 28648, "found_by": "gene", "others": []}
    monkeypatch.setattr(resolver, "_gene_lookup", lambda name: record)
    with pytest.raises(NameResolutionError) as info:
        srv.generate_molecule("TrpA Pseudomonas sediminis")
    message = str(info.value)
    assert "neither an experimental structure (PDB) nor an AlphaFold model" in message
    assert "right now" not in message


def test_too_large_name_that_is_a_protein_is_drawn(structures, monkeypatch):
    """Calcitonin: PubChem-Struktur mit 239 Schweratomen, UniProt kennt es als Protein."""
    from rdkit import Chem

    big = ".".join(["CCCCCCCCCC"] * 25)  # 250 Schweratome, als Name aufgelöst
    assert Chem.MolFromSmiles(big).GetNumHeavyAtoms() > srv.MAX_NAMED_HEAVY_ATOMS
    monkeypatch.setattr(resolver, "resolve_name_route",
                        lambda n: resolver.Resolution(big) if n == "calcitonin" else None)
    monkeypatch.setattr(resolver, "_protein_lookup", lambda n: {
        "accession": "P00698", "name": "Lysozyme C", "matched": "Lysozyme C",
        "organism": "Gallus gallus", "length": 147, "mass": 16239})
    monkeypatch.setattr(ps, "best_pdb_chain", lambda acc: ("1LYZ", "A"))
    payload = srv.generate_molecule("calcitonin")
    assert payload.type == "protein"
    assert payload.protein.subtitle.startswith("PDB 1LYZ, chain A")


# --- generate_protein_or_antibody: eigener Eingang mit „protein" im Namen (10.11.2026) -----
# Desktop zeigt dem Modell vor der Tool-Suche nur Toolnamen (Messung 10.11.2026,
# docs/evidence/desktop-routing-2026-11-10.md: 0 von 8 Protein-Aufträgen kamen
# hier an). Dasselbe Ergebnis wie generate_molecule, nur ein erkennbarer Name.


def test_generate_protein_draws_lysozyme(structures):
    payload = srv.generate_protein_or_antibody("lysozyme")
    assert payload.type == "protein"
    assert payload.protein.title == "Lysozyme C, Gallus gallus (hen egg white)"
    assert payload.protein.subtitle.startswith("PDB 1LYZ, chain A · cartoon · 129 residues")
    assert payload.protein.scheme is None
    for fmt in ("png", "svg"):
        assert Path(payload.files[fmt]).exists()


def test_generate_protein_draws_trastuzumab_with_the_scheme(structures):
    payload = srv.generate_protein_or_antibody("trastuzumab")
    assert payload.type == "protein"
    assert payload.protein.title.startswith("Trastuzumab Fab fragment")
    assert payload.protein.scheme["highlight"] == "fab"
    assert Path(payload.files["scheme_png"]).exists() and Path(payload.files["scheme_svg"]).exists()


def test_generate_protein_antibody_is_the_general_igg_architecture(structures):
    payload = srv.generate_protein_or_antibody("antibody")
    assert payload.type == "protein"
    assert payload.protein.title.startswith("Architecture of an intact IgG")
    assert payload.protein.scheme["start"] == "scheme"
    assert "No structure of this particular antibody is shown" in payload.message


def test_generate_protein_too_large_name_that_is_a_protein(structures, monkeypatch):
    big = ".".join(["CCCCCCCCCC"] * 25)
    monkeypatch.setattr(resolver, "resolve_name_route",
                        lambda n: resolver.Resolution(big) if n == "calcitonin" else None)
    monkeypatch.setattr(resolver, "_protein_lookup", lambda n: {
        "accession": "P00698", "name": "Lysozyme C", "matched": "Lysozyme C",
        "organism": "Gallus gallus", "length": 147, "mass": 16239})
    monkeypatch.setattr(ps, "best_pdb_chain", lambda acc: ("1LYZ", "A"))
    assert srv.generate_protein_or_antibody("calcitonin").type == "protein"


CAFFEINE = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"


def test_generate_protein_refuses_a_small_molecule_by_name(structures, monkeypatch):
    monkeypatch.setattr(resolver, "resolve_name_route",
                        lambda n: resolver.Resolution(CAFFEINE) if n == "caffeine" else None)
    monkeypatch.setattr(resolver, "_protein_lookup", lambda n: None)
    with pytest.raises(ValueError) as info:
        srv.generate_protein_or_antibody("caffeine")
    message = str(info.value)
    assert "'caffeine' was read as the compound C8H10N4O2" in message
    assert "UniProt lists no protein under this name" in message
    assert "generate_molecule" in message
    assert not Path(srv.OUTPUT_DIR).exists() and not Path(srv.PROTEIN_DIR).exists()


def test_generate_protein_prefers_the_protein_when_pubchem_misreads_the_name(structures, monkeypatch):
    """Gemessen 10.11.2026: PubChem liest „ubiquitin" als C6H8O7, „calmodulin" als
    C7H15N3O2. Wer generate_protein_or_antibody ruft, meint das Protein — UniProt entscheidet."""
    monkeypatch.setattr(resolver, "resolve_name_route",
                        lambda n: resolver.Resolution("OC(=O)CC(O)(C(=O)O)CC(=O)O"))
    monkeypatch.setattr(resolver, "_protein_lookup", lambda n: {
        "accession": "P00698", "name": "Lysozyme C", "matched": "Lysozyme C",
        "organism": "Gallus gallus", "length": 147, "mass": 16239})
    monkeypatch.setattr(ps, "best_pdb_chain", lambda acc: ("1LYZ", "A"))
    payload = srv.generate_protein_or_antibody("ubiquitin")
    assert payload.type == "protein"
    assert payload.protein.subtitle.startswith("PDB 1LYZ, chain A")


def test_generate_protein_refuses_a_smiles(structures):
    with pytest.raises(ValueError) as info:
        srv.generate_protein_or_antibody(CAFFEINE)
    assert "not a protein" in str(info.value) and "generate_molecule" in str(info.value)


def test_generate_protein_writes_only_the_requested_format(structures):
    payload = srv.generate_protein_or_antibody("lysozyme", formats=["png"])
    assert set(payload.files) == {"png"}
    assert not list(Path(srv.PROTEIN_DIR).rglob("*.svg"))


def test_generate_protein_has_no_cdxml(structures):
    with pytest.raises(ValueError) as info:
        srv.generate_protein_or_antibody("lysozyme", formats=["cdxml"])
    assert "CDXML" in str(info.value)


@pytest.mark.parametrize("profile", ["mvp", "full"])
def test_generate_protein_is_a_panel_tool_in_both_profiles(profile):
    tools = {t.name: t for t in asyncio.run(srv.create_server(profile).list_tools())}
    assert "generate_protein_or_antibody" in tools
    assert (tools["generate_protein_or_antibody"].meta or {}).get("ui") == srv._UI_META["ui"]


def test_generate_protein_through_the_sdk_client(structures):
    result = _call("generate_protein_or_antibody", {"name": "insulin"})
    assert not result.is_error, result.content
    assert result.structured_content["type"] == "protein"


def test_generate_protein_error_through_the_sdk_client_names_generate_molecule(structures):
    result = _call("generate_protein_or_antibody", {"name": CAFFEINE})
    assert result.is_error
    text = "\n".join(getattr(b, "text", "") for b in result.content)
    assert "generate_molecule" in text
