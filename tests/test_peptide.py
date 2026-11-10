"""Frei zusammengesetzte Peptide (E4, 09.11.2026).

PubChem kennt "Ala-Trp-Lys-Ser-Gly" nicht — vorher not_found. Jetzt baut
`chemdraw_tool.peptide` die Kette offline über RDKits HELM-Leser. Alles hier
läuft ohne Netz: die Kaskaden-Quellen werfen, wenn sie gefragt werden.

Referenz-InChIKeys stammen NICHT aus dem Code unter Test: entweder aus
PubChem (gemessen 09.11.2026 über die bisherige Kaskade, siehe Kommentar)
oder aus `Chem.MolFromSequence`/handgeschriebenem SMILES.
"""

import pytest
from rdkit import Chem

from chemdraw_tool import peptide, resolver
from chemdraw_tool.generator import generate_2d, is_linear_peptide
from chemdraw_tool.resolver import NameResolutionError, resolve


def _key(smiles_or_mol) -> str:
    mol = (
        Chem.MolFromSmiles(smiles_or_mol)
        if isinstance(smiles_or_mol, str)
        else smiles_or_mol
    )
    return Chem.MolToInchiKey(mol)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Die lokale Stufe darf keine Quelle fragen."""
    resolver.resolve_name.cache_clear()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Netzquelle gefragt")

    for source in ("_opsin_lookup", "_pubchem_lookup", "_nci_cir_lookup"):
        monkeypatch.setattr(resolver, source, forbidden)
    yield
    resolver.resolve_name.cache_clear()


# --- Dreibuchstabencode -----------------------------------------------------

# PubChem, 09.11.2026 über die alte Kaskade: lokal muss derselbe Stoff kommen.
PUBCHEM = {
    "Gly-Ala": "VPZXBVLAVMBEQI-VKHMYHEASA-N",
    "Ala-Gly-Ser": "NBTGEURICRTMGL-WHFBIAKZSA-N",
    "H-Ala-Gly-OH": "CXISPYVYMQWFLE-VKHMYHEASA-N",
    "ala-gly": "CXISPYVYMQWFLE-VKHMYHEASA-N",
    "D-Ala-Gly": "CXISPYVYMQWFLE-GSVOUGTGSA-N",
    "D-Ala-D-Ala": "DEFJQIDDEAULHB-QWWZWVQMSA-N",
    "Gly-Gly": "YMAWOPBAYDPSLA-UHFFFAOYSA-N",
    "Pro-Pro": "RWCOTTLHDJWHRS-YUMQZZPRSA-N",
    "Asp-Phe": "YZQCXOFQZKCETR-UWVGGRQHSA-N",
    "Glu-Cys-Gly": "ZZIFPJZQHRJERU-WDSKDSINSA-N",
    "Gly-His-Lys": "MVORZMQFXBLMHM-QWRGUYRKSA-N",
    "Lys-Lys": "NVGBPTNZLWRQSY-UWVGGRQHSA-N",
    "H-Tyr-Gly-Gly-Phe-Met-OH": "YFGBQHOOROIVKG-FKBYEOEOSA-N",
    "cyclo(Arg-Gly-Asp-D-Phe-Val)": "YYQUWEHEBOMRPH-NYUBLWNDSA-N",
    "cyclo(Pro-Gly)": "OWOHLURDBZHNGG-YFKPBYRVSA-N",
}


@pytest.mark.parametrize("name", sorted(PUBCHEM))
def test_local_sequence_matches_pubchem(name):
    smiles, mol = resolve(name)
    assert _key(mol) == PUBCHEM[name]


@pytest.mark.parametrize(
    "name, sequence",
    [
        ("Ala-Trp-Lys-Ser-Gly", "AWKSG"),
        ("Gly-Phe-Asp-Cys-Met-Arg", "GFDCMR"),
        ("GLY-PHE-ASP-CYS-MET-ARG", "GFDCMR"),
    ],
)
def test_sequences_pubchem_does_not_know_resolve_offline(name, sequence):
    """Die beiden Sequenzen, die vorher not_found waren."""
    smiles, mol = resolve(name)
    assert _key(mol) == _key(Chem.MolFromSequence(sequence))
    assert len(Chem.GetMolFrags(mol)) == 1


def test_stereo_is_now_explicit_where_pubchem_had_none():
    """PubChem lieferte 'Ser-Thr' ohne Stereo (LDEBVRIURYMKQS-UHFFFAOYSA-N).
    Lokal ist es L-Ser-L-Thr: gleiches Gerüst, jetzt mit Stereoblock."""
    _, mol = resolve("Ser-Thr")
    key = _key(mol)
    assert key.split("-")[0] == "LDEBVRIURYMKQS"
    assert key == _key(Chem.MolFromSequence("ST"))


def test_termini_acetyl_and_amide():
    _, mol = resolve("Ac-Ala-Gly-NH2")
    assert _key(mol) == _key("CC(=O)N[C@@H](C)C(=O)NCC(N)=O")


@pytest.mark.parametrize(
    "code, smiles",
    [
        ("Orn", "NCCC[C@H](N)C(=O)NCC(=O)O"),
        ("Nle", "CCCC[C@H](N)C(=O)NCC(=O)O"),
        ("Nva", "CCC[C@H](N)C(=O)NCC(=O)O"),
        ("Abu", "CC[C@H](N)C(=O)NCC(=O)O"),
        ("Sar", "CNCC(=O)NCC(=O)O"),
    ],
)
def test_extra_monomers(code, smiles):
    _, mol = resolve(f"{code}-Gly")
    assert _key(mol) == _key(smiles)


_L_SMILES = {
    "Ala": "C[C@H](N)C(=O)O",
    "Arg": "N=C(N)NCCC[C@H](N)C(=O)O",
    "Asn": "NC(=O)C[C@H](N)C(=O)O",
    "Asp": "OC(=O)C[C@H](N)C(=O)O",
    "Cys": "SC[C@H](N)C(=O)O",
    "Gln": "NC(=O)CC[C@H](N)C(=O)O",
    "Glu": "OC(=O)CC[C@H](N)C(=O)O",
    "His": "c1nc[nH]c1C[C@H](N)C(=O)O",
    "Ile": "CC[C@H](C)[C@H](N)C(=O)O",
    "Leu": "CC(C)C[C@H](N)C(=O)O",
    "Lys": "NCCCC[C@H](N)C(=O)O",
    "Met": "CSCC[C@H](N)C(=O)O",
    "Phe": "c1ccccc1C[C@H](N)C(=O)O",
    "Pro": "OC(=O)[C@@H]1CCCN1",
    "Ser": "OC[C@H](N)C(=O)O",
    "Thr": "C[C@@H](O)[C@H](N)C(=O)O",
    "Trp": "c1ccc2c(c1)c(c[nH]2)C[C@H](N)C(=O)O",
    "Tyr": "Oc1ccc(cc1)C[C@H](N)C(=O)O",
    "Val": "CC(C)[C@H](N)C(=O)O",
}


def _mirror(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    for atom in mol.GetAtoms():
        atom.InvertChirality()
    return Chem.MolToSmiles(mol)


@pytest.mark.parametrize("code", sorted(_L_SMILES))
def test_every_residue_and_its_d_form(code):
    """L-Rest gegen handgeschriebenes SMILES, D-Rest gegen das Spiegelbild
    (D-Ile ist (2R,3R), nicht allo; D-Thr (2R,3S))."""
    gly = "NCC(=O)O"
    l_dipeptide = _join(Chem.MolFromSmiles(_L_SMILES[code]), gly)
    d_dipeptide = _join(Chem.MolFromSmiles(_mirror(_L_SMILES[code])), gly)
    assert _key(resolve(f"{code}-Gly")[1]) == _key(l_dipeptide)
    assert _key(resolve(f"D-{code}-Gly")[1]) == _key(d_dipeptide)


def _join(residue: Chem.Mol, glycine_smiles: str) -> Chem.Mol:
    """Amidbindung Rest-COOH + Gly-NH2, per Reaktions-SMARTS (unabhängig von HELM)."""
    from rdkit.Chem import AllChem

    rxn = AllChem.ReactionFromSmarts(
        "[C:1](=[O:2])[OH1].[NH2:3][CH2:4]>>[C:1](=[O:2])[NH1:3][CH2:4]"
    )
    # Nur die α-Carboxylgruppe: die am Cα mit freier α-Aminogruppe.
    products = rxn.RunReactants((residue, Chem.MolFromSmiles(glycine_smiles)))
    alpha = Chem.MolFromSmarts("[NX3][CX4][CX3](=O)[NX3H1][CH2]C(=O)O")
    for (product,) in products:
        Chem.SanitizeMol(product)
        if product.HasSubstructMatch(alpha):
            return product
    raise AssertionError(f"keine α-Amidbindung für {Chem.MolToSmiles(residue)}")


# Kollisionskandidaten: alles, was nicht reine Sequenz ist, fragt weiter die
# Kaskade — Schutzgruppen, Ester, Trivialnamen, ein einzelner Rest.
COLLISIONS = [
    "Ala",
    "Phe",
    "H-Ala-OH",
    "Met-enkephalin",
    "Leu-enkephalin",
    "His-tag",
    "Val-Cit",
    "Boc-Ala-OH",
    "Fmoc-Gly-OH",
    "Z-Gly-OH",
    "Asp-Phe-OMe",
    "Ac-Ala-NH2",
    "AGS",
    "tert-Butanol",
    "N-acetyl-cysteine",
]


@pytest.mark.parametrize("name", COLLISIONS)
def test_not_a_plain_sequence_still_asks_the_cascade(monkeypatch, name):
    seen = []

    def pubchem(query, report):
        seen.append(query)
        return "CCO"

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda query: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", pubchem)
    monkeypatch.setattr(
        resolver, "_pubchem_checked", lambda query, smiles, report: (smiles, query)
    )
    smiles, _ = resolve(name)
    assert seen == [name]
    assert smiles == "CCO"


@pytest.mark.parametrize(
    "name, fragment",
    [
        ("Val-Cit", "Cit"),
        ("Ala-Xyz-Gly", "Xyz"),
        ("Boc-Ala-OH", "Boc"),
        ("Asp-Phe-OMe", "OMe"),
        ("Hyp-Gly", "Hyp"),
        ("D-Gly-Ala", "Gly"),
        ("D-Orn-Gly", "Orn"),
    ],
)
def test_sequence_with_unbuildable_residue_raises_a_named_fault(name, fragment):
    with pytest.raises(peptide.PeptideSequenceError) as exc:
        peptide.three_letter_smiles(name)
    assert fragment in str(exc.value)


def test_not_a_sequence_returns_none():
    for name in ["Ala", "Met-enkephalin", "Fmoc-Gly-OH", "Z-Gly-OH", "Ala Gly", "Foo-Bar"]:
        assert peptide.three_letter_smiles(name) is None, name


def test_unknown_residue_falls_back_to_the_cascade_first(monkeypatch):
    """'Val-Cit' kennt PubChem — die lokale Stufe darf es nicht abfangen."""
    seen = []

    def pubchem(name, report):
        seen.append(name)
        return "CC(C)[C@H](N)C(=O)N[C@@H](CCCNC(N)=O)C(=O)O"

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", pubchem)
    monkeypatch.setattr(
        resolver, "_pubchem_checked", lambda name, smiles, report: (smiles, name)
    )
    smiles, _ = resolve("Val-Cit")
    assert seen == ["Val-Cit"]
    assert "CCCNC(N)=O" in smiles


def test_unknown_residue_message_names_it_when_the_cascade_finds_nothing(monkeypatch):
    def nobody(name, report):
        report.append(resolver._Attempt("PubChem", resolver._NOT_FOUND, "name unknown"))
        return None

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", nobody)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", nobody)
    with pytest.raises(NameResolutionError) as exc:
        resolve("Ala-Xyz-Gly")
    assert exc.value.kind == "not_found"
    assert "'Xyz'" in str(exc.value)
    assert "peptide" in str(exc.value).lower()


def test_offline_cascade_keeps_its_offline_diagnosis(monkeypatch):
    """Nur not_found bekommt die Peptid-Meldung — ein Netzproblem bleibt eins."""

    def down(name, report):
        report.append(resolver._Attempt("PubChem", resolver._UNREACHABLE, "timeout"))
        return None

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", down)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", down)
    with pytest.raises(NameResolutionError) as exc:
        resolve("Ala-Xyz-Gly")
    assert exc.value.kind == "offline"


def test_length_limit_is_a_clear_error():
    long = "-".join(["Ala"] * (peptide.MAX_RESIDUES + 1))
    with pytest.raises(peptide.PeptideSequenceError) as exc:
        peptide.three_letter_smiles(long)
    assert str(peptide.MAX_RESIDUES) in str(exc.value)
    ok = "-".join(["Ala"] * peptide.MAX_RESIDUES)
    assert peptide.three_letter_smiles(ok)


def test_three_letter_sequences_never_parse_as_smiles():
    """Parse-first: wäre ein Code gültiges SMILES, gewönne der SMILES-Weg."""
    for code in peptide.THREE_LETTER:
        assert Chem.MolFromSmiles(f"{code}-Gly") is None, code


# --- Einbuchstabencode, nur mit Präfix ---------------------------------------


def test_one_letter_code_needs_the_prefix():
    _, mol = resolve("peptide:AGS")
    assert _key(mol) == PUBCHEM["Ala-Gly-Ser"]
    _, mol = resolve("Peptide: AGS")
    assert _key(mol) == PUBCHEM["Ala-Gly-Ser"]


def test_lowercase_one_letter_is_the_d_residue():
    _, mol = resolve("peptide:aG")
    assert _key(mol) == PUBCHEM["D-Ala-Gly"]


@pytest.mark.parametrize(
    "text, fragment",
    [("peptide:AGX", "X"), ("peptide:gA", "g"), ("peptide:A", "two"), ("peptide:", "two")],
)
def test_one_letter_faults_name_the_problem(text, fragment):
    with pytest.raises(NameResolutionError) as exc:
        resolve(text)
    assert exc.value.kind == "not_found"
    assert fragment in str(exc.value)


def test_one_letter_termini_and_cyclo():
    assert _key(resolve("peptide:Ac-AG-NH2")[1]) == _key("CC(=O)N[C@@H](C)C(=O)NCC(N)=O")
    assert _key(resolve("peptide:cyclo(RGDfV)")[1]) == PUBCHEM["cyclo(Arg-Gly-Asp-D-Phe-Val)"]


@pytest.mark.parametrize("smiles", ["CCC", "O", "CO", "CNC"])
def test_smiles_keep_their_old_meaning(smiles):
    """'CCC' bleibt Propan, 'O' Wasser — parse-first schlägt jede Peptidstufe."""
    resolved, _ = resolve(smiles)
    assert resolved == smiles


# --- Zeichnung --------------------------------------------------------------


def test_linear_peptides_from_five_residues_get_the_linear_layout():
    penta = Chem.MolFromSequence("AWKSG")
    assert is_linear_peptide(penta)
    assert not is_linear_peptide(Chem.MolFromSequence("YGGF"))  # vier: Standard
    assert not is_linear_peptide(Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O"))
    cyclic = Chem.MolFromHELM("PEPTIDE1{R.G.D.[dF].V}$PEPTIDE1,PEPTIDE1,5:R2-1:R1$$$")
    assert not is_linear_peptide(cyclic)


def _positions(mol):
    return [tuple(round(v, 4) for v in p) for p in mol.GetConformer().GetPositions()]


def test_layout_switch_hits_only_linear_peptides():
    """Pentapeptid: CoordGen; Tetrapeptid, Cyclopeptid, Aspirin: Standard-Layout
    unverändert. (Der frühere Spannweiten-Test war auch mit dem Standard-Layout
    grün — er unterschied nichts.)"""
    from rdkit.Chem import AllChem, rdCoordGen

    def expected(mol, use_coordgen):
        ref = Chem.Mol(mol)
        if use_coordgen:
            rdCoordGen.AddCoords(ref)
            conf = ref.GetConformer()
            for i in range(ref.GetNumAtoms()):
                p = conf.GetAtomPosition(i)
                conf.SetAtomPosition(i, (p.x * 1.5, p.y * 1.5, 0.0))
        else:
            AllChem.Compute2DCoords(ref)
        return _positions(ref)

    penta = Chem.MolFromSequence("AWKSG")
    assert _positions(generate_2d(penta)) == expected(penta, True)
    for mol in (
        Chem.MolFromSequence("YGGF"),
        Chem.MolFromHELM("PEPTIDE1{R.G.D.[dF].V}$PEPTIDE1,PEPTIDE1,5:R2-1:R1$$$"),
        Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O"),
    ):
        assert _positions(generate_2d(mol)) == expected(mol, False)


def test_peptide_layout_keeps_the_standard_bond_length():
    """CoordGen legt Bindungen auf 1,0, Compute2DCoords auf 1,5 — CDXML und
    Reaktions-/Vergleichsbilder mischen sonst zwei Maßstäbe."""
    mol = generate_2d(Chem.MolFromSequence("AWKSGFDCM"))
    conf = mol.GetConformer()
    lengths = sorted(
        (conf.GetAtomPosition(b.GetBeginAtomIdx()) - conf.GetAtomPosition(b.GetEndAtomIdx())).Length()
        for b in mol.GetBonds()
    )
    assert abs(lengths[len(lengths) // 2] - 1.5) < 0.05


# --- Anzeigename (E17, 10.11.2026) ------------------------------------------
# Legende und Dateiname zeigten das Eingabe-Präfix: „peptide:YGGFM“, Datei
# `peptideyggfm.png`. Bis acht Reste steht der Dreibuchstabencode da (lesbar,
# D-Reste als „D-Phe“ — der Einbuchstabencode unterscheidet sie nur über die
# Kleinschreibung, die der Dateiname verlöre), darüber die Sequenz ohne Präfix.


@pytest.mark.parametrize(
    "query, shown",
    [
        ("peptide:YGGFM", "Tyr-Gly-Gly-Phe-Met"),
        ("peptide:cyclo(RGDfV)", "cyclo(Arg-Gly-Asp-D-Phe-Val)"),
        ("peptide:Ac-aG-NH2", "Ac-D-Ala-Gly-NH2"),
        ("peptide:aG", "D-Ala-Gly"),
        ("peptide:ACDEFGHIKLMN", "ACDEFGHIKLMN"),
        ("Tyr-Gly-Gly-Phe-Met", None),
        ("aspirin", None),
        ("peptide:XZ", None),  # nicht baubar: die Fehlermeldung kommt woanders
    ],
)
def test_display_name_of_a_one_letter_peptide(query, shown):
    assert peptide.display_name(query) == shown


def test_legend_and_file_name_without_the_prefix(tmp_path, monkeypatch):
    from chemdraw_tool import server

    for const in [k for k in dir(server) if k.endswith("_DIR")]:
        monkeypatch.setattr(server, const, tmp_path / const)
    monkeypatch.setattr(server, "_enrich_properties", lambda smiles: {})
    shown = server.generate_molecule("peptide:YGGFM")
    assert shown.name == "Tyr-Gly-Gly-Phe-Met"
    assert all("peptide" not in path for path in shown.files.values())
    assert all(path.endswith(("tyr-gly-gly-phe-met.png", "tyr-gly-gly-phe-met.svg"))
               for path in shown.files.values())
    # D-Rest bleibt im Dateinamen unterscheidbar
    d_form = server.generate_molecule("peptide:yGGFM")
    assert set(d_form.files.values()).isdisjoint(shown.files.values())
    # das Label des Nutzers gewinnt weiter
    named = server.generate_molecule("peptide:YGGFM", label="Met-enkephalin")
    assert named.name == "Met-enkephalin"
    assert all(path.endswith(("met-enkephalin.png", "met-enkephalin.svg"))
               for path in named.files.values())
