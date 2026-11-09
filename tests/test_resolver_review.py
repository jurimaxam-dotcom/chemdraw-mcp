"""Resolver-Befunde aus dem Review 09.11.2026 (jeder Fall einmal rot gesehen)."""

from unittest.mock import Mock, patch

import pytest
import requests

from chemdraw_tool import resolver
from chemdraw_tool.resolver import NameResolutionError, resolve, resolve_name

METHYLDOPA = "C[C@](CC1=CC(=C(C=C1)O)O)(C(=O)O)N"
OPSIN_FEHLGRIFF = "CN[C@H](C(=O)O)CC1=CC=C(O)C(O)=C1"  # N-Methyl-DOPA


@pytest.fixture(autouse=True)
def _clear_resolution_cache():
    resolve_name.cache_clear()
    yield
    resolve_name.cache_clear()


def _pubchem_answer(smiles):
    resp = Mock(status_code=200)
    resp.raise_for_status = Mock()
    resp.json.return_value = {"PropertyTable": {"Properties": [{"SMILES": smiles}]}}
    return resp


def test_answer_from_an_outage_is_not_kept_once_the_network_is_back():
    """OPSIN liest den Trivialnamen falsch; PubChem korrigiert das — außer es ist gerade weg.

    Der Notbehelf während des Ausfalls ist in Ordnung. Ihn zu cachen nicht: der
    Desktop-Prozess lebt tagelang und zeichnete den falschen Stoff weiter.
    """
    with patch.object(resolver, "_opsin_lookup", return_value=OPSIN_FEHLGRIFF):
        with patch("chemdraw_tool.resolver.requests.get",
                   side_effect=requests.exceptions.ConnectionError("down")):
            assert resolve_name("methyldopa") == OPSIN_FEHLGRIFF
        with patch("chemdraw_tool.resolver.requests.get",
                   return_value=_pubchem_answer(METHYLDOPA)):
            assert resolve_name("methyldopa") == METHYLDOPA


def test_confirmed_answer_is_still_cached():
    with patch.object(resolver, "_opsin_lookup", return_value=None):
        with patch("chemdraw_tool.resolver.requests.get",
                   return_value=_pubchem_answer(METHYLDOPA)) as get:
            resolve_name("methyldopa")
            calls = get.call_count
            resolve_name("methyldopa")
            assert get.call_count == calls


def test_cache_does_not_grow_without_bound():
    with patch.object(resolver, "_opsin_lookup", return_value="CCO"):
        for i in range(resolver._ROUTE_CACHE_MAX + 50):
            resolve_name(f"1-ethanol-{i}")  # Lokant → keine PubChem-Gegenprobe
    assert len(resolver._ROUTE_CACHE) <= resolver._ROUTE_CACHE_MAX


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_input_is_not_a_molecule(text):
    with pytest.raises(NameResolutionError) as err:
        resolve(text)
    assert err.value.kind == "not_found"


def test_trailing_newline_does_not_change_the_lookup():
    with patch.object(resolver, "_opsin_lookup", return_value=None):
        with patch("chemdraw_tool.resolver.requests.get",
                   return_value=_pubchem_answer("CC(=O)OC1=CC=CC=C1C(=O)O")) as get:
            resolve("aspirin\n")
    assert "aspirin%0A" not in get.call_args_list[0].args[0]
    assert get.call_args_list[0].args[0].rstrip("/").split("/name/")[1].startswith("aspirin/")


@pytest.mark.parametrize("code", [400, 414])
def test_rejected_input_is_not_reported_as_an_outage(code):
    """HTTP 400/414 heißt: diese Eingabe taugt nicht — nicht „Quelle gestört, später nochmal“."""
    resp = Mock(status_code=code, text="")
    resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
    with patch.object(resolver, "_opsin_lookup", return_value=None):
        with patch("chemdraw_tool.resolver.requests.get", return_value=resp):
            with pytest.raises(NameResolutionError) as err:
                resolve_name("Xyzzolin-..")
    assert err.value.kind == "not_found"


@pytest.mark.echtes_nci_get
def test_nci_is_asked_over_ipv4_first():
    """Der tote AAAA-Eintrag von cactus.nci.nih.gov kostete 3 s je Aufruf."""
    seen = {}

    def fake_get(self, url, **kwargs):
        seen["adapter"] = self.get_adapter(url)
        return Mock(status_code=200, text="CCO")

    with patch.object(requests.Session, "get", fake_get):
        assert resolver._nci_get("https://cactus.nci.nih.gov/x").text == "CCO"
    assert isinstance(seen["adapter"], resolver._IPv4Adapter)
    assert seen["adapter"].poolmanager.connection_pool_kw["source_address"] == ("0.0.0.0", 0)


@pytest.mark.echtes_nci_get
def test_nci_falls_back_to_the_default_route_without_ipv4():
    with patch.object(requests.Session, "get",
                      side_effect=requests.exceptions.ConnectionError("no ipv4")):
        with patch("chemdraw_tool.resolver.requests.get",
                   return_value=Mock(status_code=200, text="CCO")) as get:
            assert resolver._nci_get("https://cactus.nci.nih.gov/x").text == "CCO"
    assert get.call_count == 1


def test_name_with_a_slash_is_sent_as_post_body():
    """`(+/-)-ibuprofen`: als `%2F` im GET-Pfad antwortet PubChem 404, per POST trifft es."""
    answer = _pubchem_answer("CC(C)CC1=CC=C(C=C1)C(C)C(=O)O")
    with patch.object(resolver, "_opsin_lookup", return_value=None):
        with patch("chemdraw_tool.resolver.requests.post", return_value=answer) as post:
            with patch("chemdraw_tool.resolver.requests.get",
                       side_effect=AssertionError("GET darf hier nicht laufen")):
                assert resolver._pubchem_lookup("(+/-)-ibuprofen") == "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"
    assert post.call_args.kwargs["data"] == {"name": "(+/-)-ibuprofen"}
    assert "/name/property/" in post.call_args.args[0]


def test_one_empty_pubchem_value_does_not_drop_the_other_properties():
    from chemdraw_tool.databases import _walk_sections

    section = {"Information": [
        {"Name": "Melting Point", "Value": {"StringWithMarkup": [{"String": "135 °C"}]}},
        {"Name": "Boiling Point", "Value": {"StringWithMarkup": []}},
        {"Name": "Density", "Value": {"Number": [], "Unit": "g/cm3"}},
        {"Name": "LogP", "Value": {"Number": [1.19]}},
    ]}
    results: list = []
    _walk_sections(section, results)
    assert [r["name"] for r in results] == ["Melting Point", "LogP"]


def test_vault_survives_a_non_utf8_note_and_an_empty_name(tmp_path, monkeypatch):
    from chemdraw_tool import vault

    (tmp_path / "Coffein.md").write_text("Coffein ist ok", encoding="utf-8")
    (tmp_path / "Alt.md").write_bytes("Säure ok".encode("latin-1"))
    monkeypatch.setattr(vault, "VAULT_PATH", tmp_path)
    monkeypatch.setattr(vault, "is_enabled", lambda: True)
    assert {r["name"] for r in vault.search("ok")} == {"Coffein", "Alt"}
    assert vault.read_entry("   ") == (None, None)


@pytest.mark.echtes_nci_get
def test_nci_timeout_is_not_paid_twice():
    """Antwortet NCI über IPv4 nicht, ist NCI weg — der zweite Versuch würde nur
    noch einmal dasselbe Timeout abwarten (und davor das der toten IPv6-Adresse)."""
    with patch.object(requests.Session, "get",
                      side_effect=requests.exceptions.ConnectTimeout("langsam")):
        with patch("chemdraw_tool.resolver.requests.get") as get:
            with pytest.raises(requests.exceptions.Timeout):
                resolver._nci_get("https://cactus.nci.nih.gov/x")
    assert get.call_count == 0


def test_route_cache_survives_concurrent_writers():
    import threading

    errors = []

    def work(k):
        try:
            with patch.object(resolver, "_opsin_lookup", return_value="CCO"):
                for i in range(400):
                    resolve_name(f"1-ethanol-{k}-{i}")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(k,)) for k in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors
    assert len(resolver._ROUTE_CACHE) <= resolver._ROUTE_CACHE_MAX
