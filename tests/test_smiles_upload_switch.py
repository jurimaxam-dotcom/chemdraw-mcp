"""CHEMDRAW_NO_SMILES_UPLOAD: der SMILES-Rückfall an PubChem ist abschaltbar.

Jede SMILES-Eingabe fragt PubChem per InChIKey (lokal gerechnet) nach
Stammdaten. Kennt PubChem den Schlüssel nicht, geht heute das SMILES selbst
per POST hinaus. Wer eine unveröffentlichte Struktur zeichnet, will genau das
verhindern können — ohne die Zeichnung zu verlieren. Der Standard bleibt wie er
ist; der Schalter stoppt nur den POST mit dem SMILES. Kein Netz in diesen Tests.
"""

from pathlib import Path

import pytest

from chemdraw_tool import server as srv

_UNBEKANNT = "CC(C)(C)c1ccc(cc1)C(=O)NC1CC1"  # beliebig: der Schlüssel "fehlt" bei PubChem
_DOCS = Path(__file__).resolve().parents[1] / "docs" / "tools.md"


@pytest.fixture
def calls(monkeypatch, tmp_path):
    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    seen: list[str] = []
    monkeypatch.setattr(srv, "pubchem_properties_by_inchikey", lambda key: seen.append("key") or None)
    monkeypatch.setattr(srv, "pubchem_synonyms_by_inchikey", lambda key: (None, []))

    def by_smiles_props(smiles):
        seen.append("smiles-post")
        return {"CID": 1, "Title": "from SMILES"}

    def by_smiles_syn(smiles):
        seen.append("smiles-post")
        return ("1-1-1", [])

    monkeypatch.setattr(srv, "pubchem_properties_by_smiles", by_smiles_props)
    monkeypatch.setattr(srv, "pubchem_synonyms_by_smiles", by_smiles_syn)
    monkeypatch.delenv("CHEMDRAW_NO_SMILES_UPLOAD", raising=False)
    return seen


def test_default_still_falls_back_to_the_smiles(calls):
    props, cas = srv._pubchem_record(_UNBEKANNT)
    assert calls == ["key", "smiles-post", "smiles-post"]
    assert props["Title"] == "from SMILES"
    assert cas == "1-1-1"


def test_switch_stops_the_smiles_post_but_keeps_the_inchikey_query(calls, monkeypatch):
    monkeypatch.setenv("CHEMDRAW_NO_SMILES_UPLOAD", "1")
    props, cas = srv._pubchem_record(_UNBEKANNT)
    assert "smiles-post" not in calls
    assert calls == ["key"]
    assert (props, cas) == ({}, None)


def test_switch_still_draws_the_structure(calls, monkeypatch):
    monkeypatch.setenv("CHEMDRAW_NO_SMILES_UPLOAD", "1")
    payload = srv.generate_molecule(_UNBEKANNT)
    assert "smiles-post" not in calls
    assert "<svg" in payload.svg
    assert Path(payload.files["png"]).exists()


@pytest.mark.parametrize("value", ["", "0", "false", "no"])
def test_switch_off_values_keep_the_default(calls, monkeypatch, value):
    monkeypatch.setenv("CHEMDRAW_NO_SMILES_UPLOAD", value)
    srv._pubchem_record(_UNBEKANNT)
    assert "smiles-post" in calls


def test_switch_is_documented_with_the_network_behaviour():
    text = _DOCS.read_text(encoding="utf-8")
    assert "CHEMDRAW_NO_SMILES_UPLOAD=1" in text
