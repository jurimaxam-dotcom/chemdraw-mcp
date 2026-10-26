"""Mehrdeutige Familiennamen (Etappe 2, 26.10.2026).

Vorher wählte OPSIN für "xylene", "Xylol", "cresol", "Kresol", "toluidine"
still das ortho-Isomer, und "Glucose" wurde die offenkettige Aldehydform —
gezeichnet, berechnet und beschriftet, als hätte der Nutzer genau das gemeint.
Jetzt löst ein Familienname gar kein Isomer auf: `resolve()` wirft
`kind="ambiguous"` mit den Kandidaten, `generate_molecule` zeigt sie als
Auswahl. Alles hier läuft ohne Netz: die Familien liegen fest im Code, und
jeder Weg in die Kaskade ist in diesen Tests ein Fehler.
"""

import asyncio
import json

import pytest
from mcp import Client
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchiKey
from rdkit.Chem.rdMolDescriptors import CalcNumRings

from chemdraw_tool import resolver
from chemdraw_tool import server as srv
from chemdraw_tool.payloads import AmbiguousPayload, MoleculePayload
from chemdraw_tool.resolver import NameResolutionError, resolve, resolve_name

# InChIKeys am 26.10.2026 bei PubChem nachgeschlagen (Name → CID → InChIKey),
# nicht aus dem Gedächtnis. Der offenkettige Glucose-Schlüssel ist derselbe,
# den tests/identity/stoffe.json vorher für "Glucose" festhielt.
PINNED = {
    "xylene": {
        "o-xylene": "CTQNGGLPUBDAKN-UHFFFAOYSA-N",
        "m-xylene": "IVSZLXZYQVIEFR-UHFFFAOYSA-N",
        "p-xylene": "URLKBWYHVLBVBO-UHFFFAOYSA-N",
    },
    "cresol": {
        "o-cresol": "QWVGKYWNOKOFNN-UHFFFAOYSA-N",
        "m-cresol": "RLSSMJSEOOYNOY-UHFFFAOYSA-N",
        "p-cresol": "IWDCLRJOBJJRNH-UHFFFAOYSA-N",
    },
    "toluidine": {
        "o-toluidine": "RNVCVTLRINQCPJ-UHFFFAOYSA-N",
        "m-toluidine": "JJYPMNFTHPTTDI-UHFFFAOYSA-N",
        "p-toluidine": "RZXMPPFPUUCRFN-UHFFFAOYSA-N",
    },
    "butanol": {
        "1-butanol": "LRHPLDYGYMQRHN-UHFFFAOYSA-N",
        "2-butanol": "BTANRVKWQNVYAZ-UHFFFAOYSA-N",
        "isobutanol": "ZXEKIIBDNHEJCQ-UHFFFAOYSA-N",
        "tert-butanol": "DKGAVHZHDRPRBM-UHFFFAOYSA-N",
    },
    "glucose": {
        "D-glucose (open chain)": "GZCGUPFRVQAUEE-SLPGGIOYSA-N",
        "α-D-glucopyranose": "WQZGKKKJIJFFOK-DVKNGEFBSA-N",
        "β-D-glucopyranose": "WQZGKKKJIJFFOK-VFUOTHLCSA-N",
    },
}

FAMILY_INPUTS = {
    "xylene": ["xylene", "Xylol", "XYLENE", " xylene ", "xylenes", "Xylole"],
    "cresol": ["cresol", "Kresol", "cresols", "Kresole"],
    "toluidine": ["toluidine", "Toluidin", "toluidines"],
    "butanol": ["butanol", "Butanol", "BUTANOL"],
    "glucose": ["glucose", "Glucose", "Glukose"],
}


@pytest.fixture(autouse=True)
def _no_cascade(monkeypatch):
    """Jeder Weg in OPSIN oder ins Netz ist hier ein Fehler — ein Familienname
    darf die Kaskade nicht einmal betreten."""

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Familienname ist in die Kaskade gelaufen")

    monkeypatch.setattr(resolver, "_opsin_lookup", forbidden)
    monkeypatch.setattr(resolver, "_pubchem_lookup", forbidden)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", forbidden)
    resolve_name.cache_clear()
    yield
    resolve_name.cache_clear()


def _all_inputs():
    return [(family, text) for family, texts in FAMILY_INPUTS.items() for text in texts]


# --- Resolver -----------------------------------------------------------------


@pytest.mark.parametrize("family,text", _all_inputs())
def test_family_name_is_ambiguous_not_an_isomer(family, text):
    with pytest.raises(NameResolutionError) as exc:
        resolve(text)
    assert exc.value.kind == "ambiguous"
    labels = [c.label for c in exc.value.candidates]
    assert labels == list(PINNED[family])


@pytest.mark.parametrize("family", list(PINNED))
def test_message_names_every_candidate(family):
    with pytest.raises(NameResolutionError) as exc:
        resolve(family)
    message = str(exc.value)
    for label in PINNED[family]:
        assert label in message, f"{label} fehlt in: {message}"
    assert "ambiguous" in message.lower()


def test_ambiguous_error_is_still_a_valueerror():
    """server._user_facing_errors fängt ValueError — sonst käme bei
    compare_molecules & Co. nur 'Error executing tool' an."""
    with pytest.raises(ValueError):
        resolve("xylene")


@pytest.mark.parametrize("family", list(PINNED))
def test_candidate_smiles_are_valid_and_pinned(family):
    candidates = resolver.ambiguous_candidates(family)
    assert candidates, f"keine Kandidaten für {family}"
    keys = {}
    for cand in candidates:
        mol = Chem.MolFromSmiles(cand.smiles)
        assert mol is not None, f"{cand.label}: ungültiges SMILES {cand.smiles}"
        keys[cand.label] = MolToInchiKey(mol)
        assert cand.name, f"{cand.label} ohne ausgeschriebenen Namen"
    assert keys == PINNED[family]


def test_glucose_candidates_are_ring_forms_not_positions():
    """Glucose ist keine o/m/p-Familie: offenkettig gegen α/β-Pyranose."""
    labels = [c.label for c in resolver.ambiguous_candidates("Glucose")]
    assert not any(label.startswith(("o-", "m-", "p-")) for label in labels)
    ring = [CalcNumRings(Chem.MolFromSmiles(c.smiles))
            for c in resolver.ambiguous_candidates("Glucose")]
    assert ring == [0, 1, 1]


@pytest.mark.parametrize(
    "text",
    [
        "o-Xylol", "m-xylene", "p-Xylene", "para-Xylene", "1,4-dimethylbenzene",
        "m-cresol", "o-Kresol", "4-methylphenol", "p-toluidine",
        "1-Butanol", "2-butanol", "tert-butanol", "butan-1-ol", "isobutanol",
        "D-Glucose", "alpha-D-glucopyranose", "xylene isomers",
    ],
)
def test_explicit_isomer_names_still_go_to_the_cascade(monkeypatch, text):
    asked = []

    def opsin(name):
        asked.append(name)
        return "C"

    monkeypatch.setattr(resolver, "_opsin_lookup", opsin)
    smiles, _ = resolve(text)
    assert smiles == "C"
    assert asked == [text]


def test_candidate_smiles_resolve_directly():
    """Der Klick im Panel schickt das SMILES — das muss ohne Kaskade zeichnen."""
    for cand in resolver.ambiguous_candidates("xylene"):
        smiles, mol = resolve(cand.smiles)
        assert mol is not None and smiles == cand.smiles


def test_lookup_is_case_insensitive_and_unknown_names_are_none():
    assert resolver.ambiguous_candidates("aspirin") is None
    assert resolver.ambiguous_candidates("KRESOL") == resolver.ambiguous_candidates("cresol")


# --- generate_molecule: Auswahl statt Zeichnung ----------------------------------


def _call(profile: str, tool: str, arguments: dict):
    async def run():
        async with Client(srv.create_server(profile)) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(run())


def _text(result) -> str:
    return "\n".join(getattr(block, "text", "") for block in result.content)


@pytest.fixture
def _isolated(tmp_path, monkeypatch):
    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())

    def no_network(_smiles):
        raise AssertionError("Mehrdeutiger Name hat PubChem gefragt")

    monkeypatch.setattr(srv, "_enrich_properties", no_network)
    return tmp_path


def test_generate_molecule_offers_the_candidates(_isolated):
    result = _call("mvp", "generate_molecule", {"name_or_smiles": "Xylol"})

    assert not result.is_error, _text(result)
    data = result.structured_content
    assert data["type"] == "ambiguous"
    assert data["name"] == "Xylol"
    assert [c["label"] for c in data["candidates"]] == list(PINNED["xylene"])
    for cand in data["candidates"]:
        assert "<svg" in cand["svg"], f"{cand['label']} ohne Vorschaubild"
        assert Chem.MolFromSmiles(cand["smiles"]) is not None
    # Nichts gezeichnet, nichts geschrieben.
    assert data["files"] == {}
    assert not any(_isolated.rglob("*.png")), "Dateien für einen mehrdeutigen Namen"


def test_ambiguous_answer_tells_the_model_to_ask(_isolated):
    """Claude Desktop strippt structuredContent — der Text muss allein reichen:
    für das Modell (Kandidaten + 'Nutzer fragen') und fürs Panel (JSON)."""
    result = _call("mvp", "generate_molecule", {"name_or_smiles": "cresol"})
    payload = json.loads(_text(result))
    assert payload["type"] == "ambiguous"
    message = payload["message"]
    for label in PINNED["cresol"]:
        assert label in message
    for cand in payload["candidates"]:
        assert cand["smiles"] in message, "Modell bekommt das SMILES nicht genannt"
    assert "ask the user" in message.lower()


def test_ambiguous_payload_is_a_molecule_payload_subclass():
    """Die Rückgabe bleibt als Annotation MoleculePayload (eine Union würde das
    SDK in {"result": …} wickeln, das Panel fände kein `type` mehr)."""
    assert issubclass(AmbiguousPayload, MoleculePayload)
    assert AmbiguousPayload().type == "ambiguous"
    assert "candidates" in MoleculePayload.model_fields


# --- Andere Aufrufer: klare Fehlermeldung, kein still gewähltes Isomer -----------


def _assert_ambiguous_error(result, family="xylene"):
    assert result.is_error
    text = _text(result)
    for label in PINNED[family]:
        assert label in text, text


def test_compare_molecules_refuses_a_family_name(_isolated):
    result = _call("mvp", "compare_molecules", {"structures": ["xylene", "CCO"]})
    _assert_ambiguous_error(result)


def test_generate_reaction_refuses_a_family_name(_isolated):
    result = _call(
        "mvp", "generate_reaction", {"reactants": ["Kresol"], "products": ["CCO"]}
    )
    _assert_ambiguous_error(result, "cresol")


def test_lookup_molecule_data_refuses_a_family_name(_isolated):
    result = _call("mvp", "lookup_molecule_data", {"name": "toluidine"})
    _assert_ambiguous_error(result, "toluidine")


def test_export_anki_deck_refuses_a_family_name(_isolated):
    card = {"front": {"text": "?", "structure": "Butanol"}, "back": {"text": "!"}}
    result = _call("mvp", "export_anki_deck", {"deck_name": "t", "cards": [card]})
    _assert_ambiguous_error(result, "butanol")


def test_batch_generate_lists_a_family_name_as_failed(_isolated, monkeypatch):
    monkeypatch.setattr(srv, "_enrich_properties", lambda _s: {})
    result = _call("mvp", "batch_generate", {"molecules": ["xylene", "CCO"]})
    assert not result.is_error, _text(result)
    data = result.structured_content
    assert [m["name"] for m in data["molecules"]] == ["CCO"]
    assert len(data["failed"]) == 1
    entry = data["failed"][0]
    assert entry.startswith("xylene")
    for label in PINNED["xylene"]:
        assert label in entry
