"""Wächter gegen den teuersten Testfehler dieses Projekts: falsch-grün.

Die Tool-Tests leiten ihre Ausgabepfade per `monkeypatch.setattr` auf ein
tmp_path um — 26-mal, verteilt über die Suite. Das funktioniert nur, solange
das Patch-Ziel und der Ort, an dem der Code die Konstante nachschlägt, dasselbe
Modul sind. Verschiebt ein Umbau die Konstanten in ein anderes Modul, zeigt
`setattr` ins Leere: Die Tests laufen weiter grün und schreiben dabei in das
echte `~/ChemDraw-Output` des Nutzers.

Genau das fängt dieser Wächter ab. Er ist bewusst kein Mock, sondern eine
Nachkontrolle am echten Ordner: Was am Ende der Suite dort neu liegt, hat kein
Test dorthin gelegt — er wollte in tmp_path schreiben.
"""

from pathlib import Path

import pytest

REAL_OUTPUT = Path.home() / "ChemDraw-Output"

# Der Server schreibt hier im Normalbetrieb hin; ein laufender Desktop-Server
# darf die Suite nicht rot machen. Log-Dateien sind kein Testergebnis.
IGNORED = {"server.log"}  # samt Rotation: server.log.1, server.log.2


def _snapshot() -> set[Path]:
    if not REAL_OUTPUT.exists():
        return set()
    return {
        p
        for p in REAL_OUTPUT.rglob("*")
        if p.is_file() and p.name.split(".log")[0] + ".log" not in IGNORED
    }


@pytest.fixture(scope="session", autouse=True)
def _no_writes_to_the_real_output_dir():
    """Kein Test darf im echten Ausgabeordner Spuren hinterlassen."""
    before = _snapshot()
    yield
    new = _snapshot() - before
    if new:
        listing = "\n".join(f"  - {p}" for p in sorted(new)[:10])
        pytest.fail(
            "Tests haben in den ECHTEN Ausgabeordner geschrieben — eine "
            "Umleitung per monkeypatch zeigt ins Leere:\n"
            f"{listing}\n"
            "Patch-Ziel und Fundort der Konstante müssen dasselbe Modul sein."
        )


# --- Kein Netz in den Mechanismus-Tests (Etappe E, 05.11.2026) ----------------------------
#
# generate_mechanism schlägt für SMILES-Eingaben den PubChem-Titel nach. Der Nachschlag fängt
# jeden Fehler still ab — ein Test, der ins Netz geht, bleibt also grün und hängt nur still am
# Netz (3 s Timeout je Stoff). Darum zwei Fixtures, die Testdateien per `pytestmark` einbinden:
# `kein_netz` sperrt Sockets UND merkt sich jeden Versuch (Teardown rot), `titel_offline` gibt
# dem Titel-Nachschlag eine feste Antwort.


@pytest.fixture
def kein_netz(monkeypatch):
    """Jeder Verbindungsversuch wird abgelehnt und am Testende als Fehler gemeldet."""
    import socket

    versuche: list[str] = []

    def ablehnen(*args, **kwargs):
        versuche.append(repr(args[1:] or kwargs))
        raise OSError("Netz im Test gesperrt (tests/conftest.py: kein_netz)")

    monkeypatch.setattr(socket.socket, "connect", ablehnen)
    monkeypatch.setattr(socket, "create_connection", ablehnen)
    yield versuche
    assert not versuche, f"Test ist ins Netz gegangen: {versuche[:3]}"


@pytest.fixture
def titel_offline(monkeypatch):
    """PubChem-Titel ohne Netz: unbekannt (None), Cache leer."""
    import chemdraw_tool.databases as databases
    import chemdraw_tool.server as server

    monkeypatch.setattr(databases, "pubchem_title_by_inchikey", lambda key: None)
    monkeypatch.setattr(server, "_TITLE_CACHE", {})


@pytest.fixture(autouse=True)
def _nci_ueber_requests_get(monkeypatch, request):
    """NCI-Abfragen laufen im Test über `requests.get`, wie alle anderen.

    Im Betrieb nimmt `resolver._nci_get` eine eigene IPv4-Session. Die
    Resolver-Tests ersetzen aber `resolver.requests.get` — ohne diese Umleitung
    ginge jeder NCI-Schritt an den Attrappen vorbei ins echte Netz.
    `tests/test_resolver_review.py` prüft `_nci_get` selbst (Marker `echtes_nci_get`).
    """
    if request.node.get_closest_marker("echtes_nci_get"):
        return
    from chemdraw_tool import resolver

    monkeypatch.setattr(
        resolver, "_nci_get", lambda url: resolver.requests.get(url, timeout=resolver._TIMEOUT)
    )


@pytest.fixture(autouse=True)
def _protein_lookup_offline(monkeypatch):
    """UniProt-Nachfrage des Resolvers (E6) ohne Netz: kein Protein bekannt.

    Der Resolver fragt UniProt, wenn alle Strukturquellen einen Namen nicht
    kennen, und bei Enzymnamen (-ase, -zyme). Ohne diese Attrappe ginge jeder
    not_found-Test einmal mehr ins Netz (unter `kein_netz` rot).
    `tests/test_proteins.py` setzt die Nachfrage je Test selbst.
    """
    from chemdraw_tool import resolver

    monkeypatch.setattr(resolver, "_protein_lookup", lambda name: None)


@pytest.fixture(autouse=True)
def _gene_lookup_offline(monkeypatch):
    """Genkürzel-Nachfrage des Resolvers (E8) ohne Netz: kein Gen bekannt.

    Der Resolver fragt UniProt vor der Kaskade, wenn die Eingabe wie ein
    bakterielles Genkürzel aussieht ("RecA"). Tests, die das prüfen, setzen
    `resolver._gene_lookup` selbst.
    """
    from chemdraw_tool import resolver

    monkeypatch.setattr(resolver, "_gene_lookup", lambda name: None)
