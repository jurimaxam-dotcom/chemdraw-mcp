"""Eintragswahl für Proteine (E8, 10.11.2026): Laborstandards, Antikörper, Genkürzel.

UniProt-Antworten unter tests/__fixtures__/uniprot/e8/ sind echte Antworten vom
10.11.2026 (PDB-Querverweise auf fünf gekürzt). Kein Test geht ins Netz.
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from chemdraw_tool import databases
from chemdraw_tool import protein_catalog as pc

E8 = Path(__file__).parent / "__fixtures__" / "uniprot" / "e8"


# --- Laborstandards -------------------------------------------------------------


@pytest.mark.parametrize(
    "name, accession, pdb, chains, organism",
    [
        ("lysozyme", ("P00698",), "1LYZ", ("A",), "Gallus gallus"),
        ("Lysozym", ("P00698",), "1LYZ", ("A",), "Gallus gallus"),
        ("hen egg-white lysozyme", ("P00698",), "1LYZ", ("A",), "Gallus gallus"),
        ("chicken lysozyme", ("P00698",), "1LYZ", ("A",), "Gallus gallus"),
        ("Lysozym Huhn", ("P00698",), "1LYZ", ("A",), "Gallus gallus"),
        ("trypsin", ("P00760",), "2PTN", ("A",), "Bos taurus"),
        ("bovine trypsin", ("P00760",), "2PTN", ("A",), "Bos taurus"),
        ("Rindertrypsin", ("P00760",), "2PTN", ("A",), "Bos taurus"),
        ("insulin", ("P01308",), "3I40", ("A", "B"), "Homo sapiens"),
        ("porcine insulin", ("P01315",), "4INS", ("A", "B"), "Sus scrofa"),
        ("hemoglobin", ("P69905", "P68871"), "2HHB", ("A", "B", "C", "D"), "Homo sapiens"),
        ("Hämoglobin", ("P69905", "P68871"), "2HHB", ("A", "B", "C", "D"), "Homo sapiens"),
        ("Alkoholdehydrogenase", ("P00330",), "4W6Z", ("A",), "Saccharomyces cerevisiae"),
        ("horse liver alcohol dehydrogenase", ("P00327",), "8ADH", ("A",), "Equus caballus"),
        ("GFP", ("P42212",), "1GFL", ("A",), "Aequorea victoria"),
        ("RNase A", ("P61823",), "7RSA", ("A",), "Bos taurus"),
        ("BSA", ("P02769",), "4F5S", ("A",), "Bos taurus"),
        ("Taq polymerase", ("P19821",), "1TAU", ("A",), "Thermus aquaticus"),
        ("angiotensin-converting enzyme", ("P12821",), "1UZE", ("A",), "Homo sapiens"),
        ("thrombin", ("P00734",), "1PPB", ("H", "L"), "Homo sapiens"),
        ("horseradish peroxidase", ("P00433",), "1ATJ", ("A",), "Armoracia rusticana"),
    ],
)
def test_lab_standards_pick_the_lab_entry(name, accession, pdb, chains, organism):
    choice = pc.curated_choice(name)
    assert choice is not None and choice.kind == "curated"
    assert choice.accession == accession
    assert (choice.structure.pdb, choice.structure.chains) == (pdb, chains)
    assert choice.organism.startswith(organism)


def test_every_curated_row_is_complete():
    keys = set()
    for row in pc.CURATED:
        assert row.uniprot and row.pdb and row.chains and row.mature_length and row.mass_da
        assert "(" in row.organism_label  # Organismus samt Klartext
        keys.add((row.key, row.default))
    # je Name genau ein Standard
    defaults = [row.key for row in pc.CURATED if row.default]
    assert len(defaults) == len(set(defaults))


def test_headline_names_organism_and_source():
    choice = pc.curated_choice("lysozyme")
    assert choice.headline == "Lysozyme C, Gallus gallus (hen egg white) — PDB 1LYZ, chain A"


def test_organism_without_a_table_row_goes_to_uniprot():
    # "human lysozyme" steht nicht in der Tabelle → UniProt mit Filter
    assert pc.curated_choice("human lysozyme") is None
    assert pc.organism_hint("human lysozyme") == ("lysozyme", "Homo sapiens")
    assert pc.organism_hint("lysozyme") == ("lysozyme", "")


def test_bsa_names_the_other_reading():
    assert "bis(trimethylsilyl)acetamide" in pc.curated_choice("BSA").other_reading


def test_ordinary_names_are_not_curated():
    for name in ("aspirin", "caffeine", "horseradish", "glucose", "humanin"):
        assert pc.curated_choice(name) is None


# --- Antikörper -------------------------------------------------------------------


def test_trastuzumab_is_its_fab_without_the_antigen():
    choice = pc.curated_choice("trastuzumab")
    assert choice.kind == "antibody" and choice.scheme
    assert (choice.structure.pdb, choice.structure.chains) == ("1N8Z", ("A", "B"))
    assert "Fab fragment" in choice.title
    assert "HER2" in choice.organism
    assert "antigen is not shown" in choice.structure.note


@pytest.mark.parametrize("name", ["Trastuzumab", "pembrolizumab", "rituximab", "adalimumab"])
def test_table_antibodies(name):
    assert pc.curated_choice(name).kind == "antibody"


@pytest.mark.parametrize(
    "name", ["antibody", "Antikörper", "IgG", "IgG1", "anti-GFP", "anti-CD20 antibody",
             "monoclonal antibody", "bevacizumab", "fantasimab"],
)
def test_other_antibody_names_get_the_general_architecture(name):
    choice = pc.curated_choice(name)
    assert choice.kind == "antibody_generic" and choice.scheme
    assert choice.structure.pdb == "1HZH"
    if name in ("bevacizumab", "fantasimab", "anti-GFP", "anti-CD20 antibody"):
        assert choice.title == f"Architecture of an intact IgG, not {name}"
    else:
        assert choice.title == "Architecture of an intact IgG antibody"


# --- Genkürzel: Form ---------------------------------------------------------------


@pytest.mark.parametrize("name", ["LipA", "PabA", "TrpA", "HemA", "LacY", "LacZ", "RecA",
                                  "GroEL", "recA", "RecA Bacillus subtilis"])
def test_gene_symbol_shape(name):
    assert pc.is_gene_symbol(name)


@pytest.mark.parametrize(
    "name",
    ["ATP", "NADH", "NADPH", "DMSO", "EDTA", "THF", "PABA", "DMF", "TFA", "HEPES", "Tris",
     "NaCl", "EtOH", "MeOH", "AcOH", "cAMP", "dNTP", "FeCl3", "CoA", "AcCoA", "LiAlH4",
     "Boc", "Fmoc", "aspirin", "caffeine", "MgSO4", "KMnO4", "NaOH", "HCl", "SDS", "BSTFA",
     "PhOH", "TBAF", "DCM", "DIPEA", "TEMED", "Glycin", "AMP"],
)
def test_small_molecule_abbreviations_are_not_gene_symbols(name):
    assert not pc.is_gene_symbol(name)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("RecA", ("RecA", "")),
        ("RecA Bacillus subtilis", ("RecA", "Bacillus subtilis")),
        ("RecA from B. subtilis", ("RecA", "subtilis")),
        ("RecA aus Bacillus", ("RecA", "Bacillus")),
        ("RecA (Bacillus subtilis)", ("RecA", "Bacillus subtilis")),
    ],
)
def test_split_gene_symbol(name, expected):
    assert pc.split_gene_symbol(name) == expected


# --- Genkürzel: UniProt -------------------------------------------------------------


def _resp(payload):
    m = Mock()
    m.raise_for_status = Mock()
    m.json = Mock(return_value=payload)
    return m


def _fx(name):
    return json.loads((E8 / f"{name}.json").read_text())


@pytest.fixture
def uniprot(monkeypatch, kein_netz):
    calls: list[str] = []

    def install(routes: list[tuple[str, str]]):
        def fake_get(url, timeout=None, **kw):
            calls.append(url)
            for needle, fixture in routes:
                if needle in url:
                    return _resp(_fx(fixture))
            return _resp({"results": []})

        monkeypatch.setattr(databases.requests, "get", fake_get)
        return calls

    return install


def test_lipa_is_the_majority_name_in_e_coli_not_the_first_hit(uniprot):
    # Gemessen 10.11.2026: erster Treffer mit Gen lipA ist "Lipase EstA" (B. subtilis);
    # die Mehrheit heißt "Lipoyl synthase", darin gewinnt E. coli K-12.
    calls = uniprot([("reviewed%3Atrue", "gene-LipA-0")])
    record = databases.uniprot_gene("LipA")
    assert record["accession"] == "P60716"
    assert record["name"] == "Lipoyl synthase"
    assert record["domain"] == "bacterium" and record["reviewed"] and not record["pdb"]
    assert record["others"] == ["Mycobacterium tuberculosis", "Bacillus subtilis", "Saccharolobus solfataricus"]
    assert "gene_exact%3A%22lipA%22" in calls[0] and len(calls) == 1
    choice = pc.from_gene_record(record, "LipA")
    assert choice.headline.startswith("Lipoyl synthase (LipA), Escherichia coli (bacterium)")


def test_single_reviewed_organism_names_the_others_from_trembl(uniprot):
    # TmoA: ein geprüfter Eintrag (Ectopseudomonas mendocina) — die anderen
    # Organismen stehen nur in TrEMBL.
    calls = uniprot([("reviewed%3Atrue", "gene-TmoA-0"), ("reviewed%3Afalse", "gene-TmoA-1")])
    record = databases.uniprot_gene("TmoA")
    assert record["accession"] == "Q00456" and record["reviewed"]
    assert record["organism"] == "Ectopseudomonas mendocina"
    assert record["others"] == ["Cupriavidus neocaledonicus", "Brevundimonas vancanneytii", "Mycobacterium kansasii 662"]
    assert any("reviewed%3Afalse" in c for c in calls)


def test_gene_with_organism_finds_the_unreviewed_entry_by_protein_name(uniprot):
    # Streptococcus vicugnae: kein Eintrag mit Genname lacY, wohl aber ein
    # TrEMBL-Eintrag "Lactose permease" (gemessen 10.11.2026)
    calls = uniprot([
        ("organism_name%3A%22Streptococcus%20vicugnae%22&size=25", "gene-LacY-Svicugnae-0"),
        ("query=%28protein_name", "gene-LacY-Svicugnae-2"),
        ("gene_exact%3A%22lacY%22&size=25", "gene-LacY-Svicugnae-1"),
    ])
    record = databases.uniprot_gene("LacY", "Streptococcus vicugnae")
    assert record["accession"] == "A0A4R5G325"
    assert record["reviewed"] is False and record["found_by"] == "name"
    # die zweite Suche fragt nur den häufigsten und den geprüften Namen
    name_query = next(c for c in calls if "query=%28protein_name" in c)
    assert "Galactoside" not in name_query
    choice = pc.from_gene_record(record, "LacY Streptococcus vicugnae")
    assert "unreviewed (TrEMBL)" in choice.organism
    assert "Streptococcus vicugnae (bacterium)" in choice.organism


def test_peta_without_e_coli_prefers_the_entry_with_a_pdb_structure(uniprot):
    # Gemessen 10.11.2026: Mehrheit "Cytochrome f" (15) vor der Rieske-Untereinheit (10);
    # erster Treffer der Gruppe P56771 (Arabidopsis) ohne PDB, P23577 mit PDB.
    uniprot([("reviewed%3Atrue", "gene-PetA-0")])
    record = databases.uniprot_gene("PetA")
    assert (record["accession"], record["name"]) == ("P23577", "Cytochrome f")
    assert record["organism"] == "Chlamydomonas reinhardtii" and record["pdb"]


def test_reca_is_e_coli_not_human_rad51(uniprot):
    uniprot([("reviewed%3Atrue", "gene-RecA-0")])
    record = databases.uniprot_gene("RecA")
    assert (record["accession"], record["name"]) == ("P0A7G6", "Protein RecA")


def test_paba_gene_is_the_aminodeoxychorismate_synthase(uniprot):
    uniprot([("reviewed%3Atrue", "gene-PabA-0")])
    record = databases.uniprot_gene("PabA")
    assert (record["accession"], record["name"]) == ("P00903", "Aminodeoxychorismate synthase component 2")


def test_gene_lookup_network_error_is_none(monkeypatch, kein_netz):
    def down(url, timeout=None, **kw):
        raise databases.requests.ConnectionError("offline")

    monkeypatch.setattr(databases.requests, "get", down)
    assert databases.uniprot_gene("RecA") is None
    assert databases.uniprot_entry("P60716") is None


# --- Eintrag per Zugangsnummer --------------------------------------------------------


def test_entry_has_reaction_cofactor_and_no_mature_split(uniprot):
    uniprot([("P60716.json", "entry-P60716-0")])
    record = databases.uniprot_entry("P60716")
    assert record["reactions"][0]["rhea"] == "RHEA:16585"
    assert "S-adenosyl-L-methionine" in record["reactions"][0]["equation"]
    assert record["cofactors"] == ["[4Fe-4S] cluster"]
    assert record["mature_length"] is None  # ganze Sequenz = reife Kette


def test_entry_mature_chain_of_lysozyme(uniprot):
    uniprot([("P00698.json", "entry-P00698-0")])
    record = databases.uniprot_entry("P00698")
    assert (record["mature_length"], record["mature_mass"]) == (129, 14313)
    assert record["ec"] == ["3.2.1.17"]


def test_mature_chains_rules():
    trypsin = {"features": [
        {"type": "Chain", "description": "Serine protease 1", "location": {"start": {"value": 24}, "end": {"value": 246}}},
        {"type": "Chain", "description": "Alpha-trypsin chain 1", "location": {"start": {"value": 24}, "end": {"value": 148}}},
        {"type": "Chain", "description": "Alpha-trypsin chain 2", "location": {"start": {"value": 149}, "end": {"value": 246}}},
    ]}
    assert databases.mature_chains(trypsin) == [("Serine protease 1", 24, 246)]
    insulin = {"features": [
        {"type": "Peptide", "description": "Insulin B chain", "location": {"start": {"value": 25}, "end": {"value": 54}}},
        {"type": "Peptide", "description": "C peptide", "location": {"start": {"value": 57}, "end": {"value": 87}}},
        {"type": "Peptide", "description": "Insulin A chain", "location": {"start": {"value": 90}, "end": {"value": 110}}},
    ]}
    assert [c[0] for c in databases.mature_chains(insulin)] == ["Insulin B chain", "Insulin A chain"]


# --- Resolver: Tabelle und Genkürzel vor der Kaskade --------------------------------

from chemdraw_tool import resolver  # noqa: E402
from chemdraw_tool.resolver import NameResolutionError  # noqa: E402


@pytest.fixture
def quiet_sources(monkeypatch):
    """Strukturquellen als Attrappe; merkt sich, wer gefragt wurde."""
    resolver.resolve_name.cache_clear()
    calls: list[str] = []
    hits: dict[str, str] = {}

    def source(label):
        def lookup(name, report=None):
            calls.append(name)
            if name in hits:
                return hits[name]
            resolver._record(report, label, resolver._NOT_FOUND, "name unknown")
            return None

        return lookup

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", source(resolver._PUBCHEM))
    monkeypatch.setattr(resolver, "_nci_cir_lookup", source(resolver._NCI))
    yield type("Q", (), {"calls": calls, "hits": hits})
    resolver.resolve_name.cache_clear()


@pytest.mark.parametrize("name", ["Lysozym", "GFP", "myoglobin", "Trastuzumab", "IgG", "BSA"])
def test_table_names_are_proteins_before_any_source(quiet_sources, kein_netz, name):
    # Gemessen 10.11.2026: GFP, BSA, HRP, ACE, myoglobin lösten als fremde
    # kleine Moleküle auf (z. B. BSA → Bis(trimethylsilyl)acetamid).
    quiet_sources.hits[name] = "CCO"
    with pytest.raises(NameResolutionError) as info:
        resolver.resolve(name)
    assert info.value.kind == "protein"
    assert info.value.protein is not None
    assert quiet_sources.calls == []


def test_lysozyme_message_names_the_hen_entry_and_the_alternative(quiet_sources):
    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("Lysozym")
    message = str(info.value)
    assert "Lysozyme C, Gallus gallus (hen egg white) — PDB 1LYZ, chain A" in message
    assert "UniProt P00698; 129 amino acids; 14.3 kDa" in message
    assert "human lysozyme (UniProt P61626)" in message
    assert "cartoon" in message and 'lookup with topic "biochem"' in message


def test_gene_symbol_is_asked_before_the_cascade(quiet_sources, monkeypatch):
    record = {
        "accession": "P00903", "name": "Aminodeoxychorismate synthase component 2", "gene": "pabA",
        "organism": "Escherichia coli (strain K12)", "domain": "bacterium",
        "reviewed": True, "length": 187, "mass": 20772,
        "others": ["Serratia marcescens", "Salmonella typhimurium", "Klebsiella aerogenes"],
    }
    asked = []
    monkeypatch.setattr(resolver, "_gene_lookup", lambda n: asked.append(n) or record)
    quiet_sources.hits["PabA"] = "Nc1ccc(cc1)C(=O)O"  # PubChem: PABA
    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("PabA")
    message = str(info.value)
    assert info.value.kind == "protein" and asked == ["PabA"]
    assert "Aminodeoxychorismate synthase component 2 (PabA), Escherichia coli (bacterium)" in message
    assert "written in capitals ('PABA')" in message
    assert '"PabA Serratia marcescens"' in message
    assert quiet_sources.calls == []


def test_capital_abbreviation_never_asks_the_gene_route(quiet_sources, monkeypatch):
    asked = []
    monkeypatch.setattr(resolver, "_gene_lookup", lambda n: asked.append(n))
    quiet_sources.hits["PABA"] = "Nc1ccc(cc1)C(=O)O"
    assert resolver.resolve("PABA")[0] == "Nc1ccc(cc1)C(=O)O"
    assert asked == []


def test_gene_symbol_unknown_to_uniprot_takes_the_cascade(quiet_sources, monkeypatch):
    monkeypatch.setattr(resolver, "_gene_lookup", lambda n: None)
    quiet_sources.hits["TrpA"] = "CCO"
    assert resolver.resolve("TrpA")[0] == "CCO"


def test_entry_found_by_protein_name_says_so_and_drops_the_gene_from_the_title():
    """S. vicugnae hat keinen Eintrag mit Genname lacY — A0A4R5G325 kam über den Proteinnamen."""
    record = {
        "accession": "A0A4R5G325", "name": "Lactose permease", "gene": "lacY",
        "organism": "Streptococcus vicugnae",
        "domain": "bacterium", "reviewed": False, "length": 524, "mass": 56702,
        "found_by": "name", "others": [],
    }
    choice = pc.from_gene_record(record, "LacY Streptococcus vicugnae")
    assert choice.figure_title == (
        "Lactose permease, Streptococcus vicugnae (bacterium) — UniProt unreviewed (TrEMBL)"
    )
    message = resolver.protein_choice_message("LacY Streptococcus vicugnae", choice)
    assert "no entry with the gene name lacY" in message
    assert "found by its protein name" in message


# --- Zusammenspiel mit E11/E12 (Struktur-Schreibweisen, Metall-Tetrapyrrole) ---


@pytest.mark.parametrize("name", [
    "RecA Bacillus subtilis", "RecA from B. subtilis", "RecA aus Bacillus",
    "hen egg-white lysozyme", "Lysozym Huhn", "RecA", "human insulin", "anti-GFP",
    "alcohol dehydrogenase", "Taq polymerase", "carbonic anhydrase II",
])
def test_protein_inputs_are_no_structure_notation(name):
    assert resolver.structure_notation(name) is None


def test_label_before_a_smiles_is_a_structure_not_a_gene_query():
    """E8-Fund: "<Genkürzel> <SMILES>" schickte das SMILES als Organismusfilter an UniProt."""
    kind, mol = resolver.structure_notation("RecA N#Cc1ccc(nc1)C1(CBr)CC2(C1)OCC(F)(F)CO2")
    assert kind == "SMILES" and mol.GetNumHeavyAtoms() == 21


@pytest.mark.parametrize("name", ["heme", "heme b", "protoheme", "hemin", "heme d1"])
def test_metal_tetrapyrroles_stay_small_molecules(name):
    assert pc.curated_choice(name) is None
    assert not pc.is_gene_symbol(name)
    smiles, mol = resolver.resolve(name)
    assert mol.GetNumHeavyAtoms() <= 49  # Häm d1 C34H30FeN4O10, kein Proteinumweg


def test_hemoglobin_stays_a_protein():
    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("hemoglobin")
    assert info.value.kind == "protein"
    assert info.value.protein.structure.pdb == "2HHB"


# --- Genkürzel + Organismus an neutralen Fällen (E17, 10.11.2026) -------------
# Antworten live von rest.uniprot.org (10.11.2026), auf die gelesenen Felder
# gekürzt. Thermus thermophilus hat keinen Eintrag mit Genname lacZ; der
# geprüfte O69315 „Beta-galactosidase“ (GH42, ohne Gennamen) kommt über den
# Proteinnamen und die Meldung sagt das. Klebsiella oxytoca hat nur
# ungeprüfte Einträge — der mit Genname lacZ gewinnt.
E17 = Path(__file__).parent / "__fixtures__" / "uniprot" / "e17"


def _fx17(name):
    return json.loads((E17 / f"{name}.json").read_text())


@pytest.fixture
def uniprot17(monkeypatch, kein_netz):
    def install(routes):
        def fake_get(url, timeout=None, **kw):
            for needle, fixture in routes:
                if needle in url:
                    return _resp(_fx17(fixture))
            return _resp({"results": []})

        monkeypatch.setattr(databases.requests, "get", fake_get)

    return install


def test_gene_symbol_without_such_gene_in_the_organism_says_what_is_shown(uniprot17):
    uniprot17([
        ("organism_name%3A%22Thermus%20thermophilus%22&size=25", "lacZ-Tthermophilus-0"),
        ("query=%28protein_name", "lacZ-Tthermophilus-2"),
        ("gene_exact%3A%22lacZ%22&size=25", "lacZ-Tthermophilus-1"),
    ])
    record = databases.uniprot_gene("LacZ", "Thermus thermophilus")
    assert record["accession"] == "O69315" and record["found_by"] == "name"
    choice = pc.from_gene_record(record, "LacZ Thermus thermophilus")
    message = resolver.protein_choice_message("LacZ Thermus thermophilus", choice)
    assert "no entry with the gene name lacZ" in message
    assert "found by its protein name ('Beta-galactosidase'" in message


def test_gene_symbol_prefers_the_entry_that_carries_the_gene_name(uniprot17):
    uniprot17([("organism_name%3A%22Klebsiella%20oxytoca%22&size=25", "lacZ-Koxytoca-0")])
    record = databases.uniprot_gene("LacZ", "Klebsiella oxytoca")
    assert record["accession"] == "A0AAP2BNC7"
    assert record["found_by"] == "gene" and record["reviewed"] is False
    choice = pc.from_gene_record(record, "LacZ Klebsiella oxytoca")
    assert "no entry with the gene name" not in resolver.protein_choice_message(
        "LacZ Klebsiella oxytoca", choice)
