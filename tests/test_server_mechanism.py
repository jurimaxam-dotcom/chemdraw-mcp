"""Tests for generate_mechanism MCP tool."""

import pytest
from rdkit import Chem

from chemdraw_tool.payloads import MechanismPayload
from chemdraw_tool.server import generate_mechanism

# PubChem-Titel je InChIKey — die Tests gehen nie ins Netz (autouse-Fixture unten).
_TITLES = {
    "C[C@@H](Br)CC": "2-Bromobutane",  # bewusst ohne Deskriptor: der kommt aus RDKit
    "C[C@H](Br)CC": "2-Bromobutane",
    "CCC(=O)O": "Propionic acid",
    "CCO": "Ethanol",
}
_LOOKUPS: list[str] = []

# Sockets gesperrt (tests/conftest.py) — der Titel-Fake unten deckt den einen bekannten Aufruf ab,
# die Sperre jeden unbekannten.
pytestmark = pytest.mark.usefixtures("kein_netz")


def _key(smiles: str) -> str:
    return Chem.MolToInchiKey(Chem.MolFromSmiles(smiles))


@pytest.fixture(autouse=True)
def _kein_netz(monkeypatch):
    """Titel-Nachschlag ohne Netz: feste Antworten, unbekannte Schlüssel → None."""
    import chemdraw_tool.databases as databases
    import chemdraw_tool.server as server

    table = {_key(smi): title for smi, title in _TITLES.items()}

    def fake(key):
        _LOOKUPS.append(key)
        return table.get(key)

    _LOOKUPS.clear()
    monkeypatch.setattr(databases, "pubchem_title_by_inchikey", fake)
    monkeypatch.setattr(server, "_TITLE_CACHE", {})


def test_generate_mechanism_sn2():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
    )
    assert isinstance(result, MechanismPayload)
    assert result.type == "mechanism"
    assert result.reaction_type == "sn2"
    assert result.current_step == 0
    assert len(result.steps) >= 3
    assert all("<svg" in s.svg.lower() for s in result.steps)


def test_generate_mechanism_specific_step():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
        current_step=2,
    )
    assert result.current_step == 2


def test_generate_mechanism_unknown_type():
    with pytest.raises(ValueError, match="Unknown mechanism 'nonexistent'.*fischer_ester, sn1, sn2"):
        generate_mechanism(
            reaction_type="nonexistent",
            substrates=["CCBr"],
        )


def test_generate_mechanism_sn1():
    result = generate_mechanism(
        reaction_type="sn1",
        substrates=["CC(C)(C)Br", "O"],
    )
    assert isinstance(result, MechanismPayload)
    assert result.reaction_type == "sn1"
    assert len(result.steps) >= 4


def test_generate_mechanism_all_steps_have_svg():
    result = generate_mechanism(
        reaction_type="sn2",
        substrates=["CCBr", "[OH-]"],
    )
    for step in result.steps:
        assert step.svg.strip() != ""
        assert "<svg" in step.svg.lower()


def test_generate_mechanism_wrong_substrates():
    with pytest.raises(ValueError, match="do not fit the sn2 mechanism"):
        generate_mechanism(
            reaction_type="sn2",
            substrates=["CC=O", "CC"],
        )


def test_title_names_the_textbook_example_when_it_falls_back(monkeypatch):
    """Befund 30.10.2026: über CH3Br + OH⁻ stand „SN2: CCCCBr + [SH-]“. Seit Etappe B zeichnet das
    Tool die Substrate; nur im Fallback ist das Bild die Vorlage — dann nennt der Titel sie."""
    import chemdraw_tool.mechanism_coords as coords

    def kaputt(steps):
        raise RuntimeError("layout exploded")

    monkeypatch.setattr(coords, "layout_anchored", kaputt)
    result = generate_mechanism("sn2", ["CCCCBr", "[SH-]"])
    assert result.name == "Nucleophilic Substitution (SN2) — textbook example: bromomethane + hydroxide"
    assert result.substrates_drawn is False
    assert "layout" in result.fallback_reason
    assert "CCCCBr" not in result.name


@pytest.mark.parametrize("reaction_type, example", [
    ("sn1", "2-bromo-2-methylpropane + water"),
    ("fischer_ester", "acetic acid + methanol"),
])
def test_every_template_names_its_drawn_example(reaction_type, example):
    from chemdraw_tool.templates import get_template
    assert get_template(reaction_type).example == example


def test_drawing_follows_the_substrates():
    """Umkehr von test_drawing_does_not_depend_on_the_substrates (Etappe B, 04.11.2026)."""
    a = generate_mechanism("sn2", ["CBr", "[OH-]"])
    b = generate_mechanism("sn2", ["CCCCBr", "[SH-]"])
    assert a.substrates_drawn and b.substrates_drawn
    assert [s.svg for s in a.steps] != [s.svg for s in b.steps]


def test_title_names_the_users_substances(monkeypatch):
    import chemdraw_tool.server as server
    from chemdraw_tool.resolver import validate_smiles

    names = {"2-bromobutane": "CCC(C)Br", "sodium cyanide": "[C-]#N.[Na+]"}
    monkeypatch.setattr(server, "resolve", lambda s: (names[s], validate_smiles(names[s])))
    result = generate_mechanism("sn2", ["2-bromobutane", "sodium cyanide"])
    assert result.name == "Nucleophilic Substitution (SN2) — 2-bromobutane + sodium cyanide"
    assert result.substrates_drawn is True and result.fallback_reason == ""


@pytest.mark.parametrize("reaction_type, substrates, n", [
    ("sn2", ["C[C@@H](Br)CC", "[C-]#N"], 3),
    ("sn1", ["CC(C)(C)Cl", "O"], 5),
    ("fischer_ester", ["CCC(=O)O", "CCO"], 6),
])
def test_three_families_draw_real_substrates(reaction_type, substrates, n):
    result = generate_mechanism(reaction_type, substrates)
    assert result.substrates_drawn is True
    assert len(result.steps) == n
    assert all("<svg" in s.svg for s in result.steps)
    assert result.substrates_drawn  # Titel zeigt Formeln, siehe test_title_shows_formulas_not_raw_smiles


def test_empty_substrates_draw_the_textbook_example():
    result = generate_mechanism("fischer_ester", [])
    assert result.substrates_drawn is False
    assert result.fallback_reason == "no substrates given"
    assert "textbook example: acetic acid + methanol" in result.name


def test_outside_the_limit_says_why():
    with pytest.raises(ValueError, match="do not fit the sn2 mechanism: tertiary halide"):
        generate_mechanism("sn2", ["CC(C)(C)Br", "[OH-]"])
    with pytest.raises(ValueError, match="use sn2"):
        generate_mechanism("sn1", ["CCCCBr", "O"])


def test_unresolvable_name_says_so(monkeypatch):
    import chemdraw_tool.server as server

    def nie(s):
        raise ValueError("not found")

    monkeypatch.setattr(server, "resolve", nie)
    with pytest.raises(ValueError, match="'foozane' could not be resolved"):
        generate_mechanism("sn2", ["foozane", "hydroxide"])


def test_payload_new_fields_have_defaults():
    p = MechanismPayload(name="x", reaction_type="sn2", steps=[])
    assert p.substrates_drawn is False and p.fallback_reason == ""


def test_reaction_type_lists_every_template_and_nothing_else():
    """Kein „e.g." mehr: das Schema nennt genau die vorhandenen Typen."""
    import inspect
    import typing

    from chemdraw_tool.templates import list_templates
    hint = inspect.signature(generate_mechanism).parameters["reaction_type"].annotation
    assert sorted(typing.get_args(hint)) == list_templates()


def test_description_names_the_limit_of_each_family():
    doc = generate_mechanism.__doc__
    assert "e.g." not in doc
    assert "primary or secondary" in doc and "tertiary, benzylic or allylic" in doc
    assert "they are not drawn" not in doc
    assert "Not this tool for" in doc


def test_title_names_smiles_input_with_stereodescriptor():
    """Desktop-Abnahme 05.11.: das Modell übergibt SMILES; der Titel zeigte erst die SMILES, dann
    die Summenformel (C₄H₉Br — trennt nicht einmal Konstitutionsisomere). Jetzt: Name + CIP."""
    r = generate_mechanism(reaction_type="sn2", substrates=["C[C@@H](Br)CC", "[C-]#N"])
    assert r.name == "Nucleophilic Substitution (SN2) — (R)-2-bromobutane + cyanide", r.name
    r2 = generate_mechanism(reaction_type="sn2", substrates=["C[C@H](Br)CC", "[OH-]"])
    assert r2.name.endswith("— (S)-2-bromobutane + hydroxide"), r2.name


def test_title_names_fischer_smiles_input():
    r = generate_mechanism("fischer_ester", ["CCC(=O)O", "CCO"])
    assert r.name == "Fischer esterification — propionic acid + ethanol", r.name


def test_title_keeps_a_descriptor_pubchem_already_gives(monkeypatch):
    import chemdraw_tool.databases as databases

    monkeypatch.setattr(databases, "pubchem_title_by_inchikey", lambda key: "(2R)-2-Bromobutane")
    r = generate_mechanism("sn2", ["C[C@@H](Br)CC", "[C-]#N"])
    assert r.name.endswith("— (2R)-2-bromobutane + cyanide"), r.name


@pytest.mark.parametrize("title, shown", [
    ("2-Bromobutane", "2-bromobutane"),
    ("Propionic acid", "propionic acid"),
    ("(R)-2-Bromobutane", "(R)-2-bromobutane"),
    ("N,N-Dimethylformamide", "N,N-dimethylformamide"),
    ("DMSO", "DMSO"),
    # Echte PubChem-Titel (Stichprobe 05.11.2026): CAS-Inversion und Title Case
    ("2-Bromobutane, (R)-", "(R)-2-bromobutane"),
    ("Propionic Acid", "propionic acid"),
])
def test_pubchem_title_is_lowercased_like_running_text(title, shown):
    from chemdraw_tool.server import _running_text_name

    assert _running_text_name(title) == shown


def test_title_falls_back_to_smiles_with_descriptor_when_offline(monkeypatch):
    """Ohne Netz: kanonisches SMILES mit CIP in Klammern — nie die Summenformel, nie ein Fehler."""
    import chemdraw_tool.databases as databases

    def offline(key):
        raise ConnectionError("no network")

    monkeypatch.setattr(databases, "pubchem_title_by_inchikey", offline)
    r = generate_mechanism("sn2", ["C[C@@H](Br)CC", "[C-]#N"])
    canon = Chem.MolToSmiles(Chem.MolFromSmiles("C[C@@H](Br)CC"))
    assert r.name == f"Nucleophilic Substitution (SN2) — {canon} (R) + cyanide", r.name
    assert r.substrates_drawn is True and r.fallback_reason == ""
    assert "C₄H₉Br" not in r.name


def test_title_lookup_is_cached_per_process_but_failures_are_not():
    generate_mechanism("fischer_ester", ["CCC(=O)O", "CCO"])
    generate_mechanism("fischer_ester", ["CCC(=O)O", "CCO"])
    assert _LOOKUPS.count(_key("CCC(=O)O")) == 1
    generate_mechanism("sn2", ["CCCCBr", "[SH-]"])  # 1-Brombutan: kein Titel im Fake
    generate_mechanism("sn2", ["CCCCBr", "[SH-]"])
    assert _LOOKUPS.count(_key("CCCCBr")) == 2


def test_smiles_detection_is_parse_first_not_string_equality(monkeypatch):
    """resolve() darf ein SMILES kanonisieren — es bleibt eine SMILES-Eingabe (wie im Resolver:
    was RDKit liest, ist SMILES)."""
    import chemdraw_tool.server as server
    from chemdraw_tool.resolver import validate_smiles

    def canonical(s):
        smi = Chem.MolToSmiles(Chem.MolFromSmiles(s))
        return smi, validate_smiles(smi)

    monkeypatch.setattr(server, "resolve", canonical)
    r = generate_mechanism("sn2", ["C[C@@H](Br)CC", "[C-]#N"])
    assert r.name.endswith("— (R)-2-bromobutane + cyanide"), r.name
