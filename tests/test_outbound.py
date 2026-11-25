"""PubChem-Drossel (25.11.2026).

PubChem verlangt höchstens 5 Anfragen pro Sekunde je Absender
(https://pubchem.ncbi.nlm.nih.gov/docs/programmatic-access). Der gehostete
Server schickt die Namen aller Nutzer von einer Adresse — ohne Drossel hängt
die Einhaltung am Zufall. Geprüft wird die Mechanik (mit eigener Uhr, ohne
echtes Schlafen), der Fehlerweg und auf `Session.send`-Ebene, dass der Weg des
Remote-Werkzeugs keine PubChem-Anfrage an der Drossel vorbei schickt.
"""

import json
import socket

import pytest
import requests

from chempane import outbound, remote, resolver


class Uhr:
    def __init__(self):
        self.jetzt = 100.0
        self.geschlafen: list[float] = []

    def zeit(self) -> float:
        return self.jetzt

    def schlaf(self, sekunden: float) -> None:
        self.geschlafen.append(round(sekunden, 6))
        self.jetzt += sekunden


def _taktgeber(uhr: Uhr, abstand=0.2, max_warten=2.0) -> outbound.StartSpacer:
    return outbound.StartSpacer(abstand, max_warten, clock=uhr.zeit, sleep=uhr.schlaf)


def test_betriebswerte_halten_fuenf_pro_sekunde():
    assert outbound.PUBCHEM_MIN_INTERVAL >= 0.2
    assert 0 < outbound.PUBCHEM_MAX_WAIT <= 3.0


def test_erster_start_wartet_nicht_der_zweite_den_abstand():
    uhr = Uhr()
    takt = _taktgeber(uhr)
    takt.acquire()
    takt.acquire()
    takt.acquire()
    assert uhr.geschlafen == [0.2, 0.2]


def test_nach_einer_pause_wartet_niemand():
    uhr = Uhr()
    takt = _taktgeber(uhr)
    takt.acquire()
    uhr.jetzt += 5.0
    takt.acquire()
    assert uhr.geschlafen == []


def test_gleichzeitige_starts_bekommen_gestaffelte_plaetze():
    """Zehn Anfragen im selben Augenblick: Plätze im Abstand, nie zwei auf einem."""
    uhr = Uhr()
    takt = outbound.StartSpacer(0.2, 5.0, clock=lambda: 100.0, sleep=uhr.schlaf)
    for _ in range(10):
        takt.acquire()
    assert uhr.geschlafen == [round(0.2 * i, 6) for i in range(1, 10)]


def test_voller_stau_sagt_ab_statt_endlos_zu_warten():
    uhr = Uhr()
    takt = outbound.StartSpacer(0.2, 0.5, clock=lambda: 100.0, sleep=uhr.schlaf)
    for _ in range(3):  # Wartezeiten 0, 0.2, 0.4
        takt.acquire()
    with pytest.raises(outbound.OutboundBusy):
        takt.acquire()  # wäre 0.6 > 0.5
    # Die Absage belegt keinen Platz: nach kurzer Zeit geht es weiter.
    takt_später = outbound.StartSpacer(0.2, 0.5, clock=uhr.zeit, sleep=uhr.schlaf)
    takt_später.acquire()


def test_absage_ist_kein_netzausfall():
    """`unreachable` hieße für den Nutzer „Netzproblem“ — falsch, die Quelle lebt."""
    status, detail = resolver._classify_error(outbound.OutboundBusy("pubchem"))
    assert status == resolver._SOURCE_ERROR
    assert "busy" in detail


def test_pubchem_lookup_meldet_absage_als_quellenfehler(monkeypatch):
    class Voll:
        def acquire(self):
            raise outbound.OutboundBusy("pubchem")

    monkeypatch.setattr(outbound, "PUBCHEM", Voll())
    gesendet = []
    monkeypatch.setattr(
        requests.Session, "send", lambda self, req, **kw: gesendet.append(req.url)
    )
    report: list = []
    assert resolver._pubchem_lookup("caffeine", report) is None
    assert gesendet == [], "trotz Absage ging eine Anfrage an PubChem"
    assert [(a.source, a.status) for a in report] == [
        (resolver._PUBCHEM, resolver._SOURCE_ERROR)
    ]
    fehler = resolver._resolution_error("caffeine", report)
    assert fehler.kind == "sources_down"
    assert "network problem" not in str(fehler)


_KOFFEIN = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"


def test_remote_werkzeug_schickt_nichts_an_der_drossel_vorbei(monkeypatch):
    """Jede Anfrage an pubchem.ncbi.nlm.nih.gov hatte vorher einen Platz."""
    plaetze = 0
    anfragen: list[tuple[str, int]] = []

    class Zaehler:
        def acquire(self):
            nonlocal plaetze
            plaetze += 1

    def antwort(self, request, **kw):
        r = requests.Response()
        r.url = request.url
        r.request = request
        r.headers["Content-Type"] = "application/json"
        if "pubchem.ncbi.nlm.nih.gov" in request.url:
            anfragen.append((request.url, plaetze))
            r.status_code = 200
            r._content = json.dumps(
                {"PropertyTable": {"Properties": [{"CID": 2519, "SMILES": _KOFFEIN}]}}
            ).encode()
        else:
            r.status_code = 404
            r._content = b"{}"
        return r

    def kein_socket(*args, **kwargs):
        raise OSError("Socket im Drossel-Test gesperrt")

    monkeypatch.setattr(outbound, "PUBCHEM", Zaehler())
    monkeypatch.setattr(requests.Session, "send", antwort)
    monkeypatch.setattr(socket.socket, "connect", kein_socket)
    monkeypatch.setattr(socket, "create_connection", kein_socket)
    # OPSIN aus: der Name muss den Netzweg nehmen, sonst prüft der Test nichts.
    monkeypatch.setattr(resolver, "_opsin_lookup", lambda *a, **kw: None)
    # Eigener Namens-Cache: die Treffer dieses Tests dürfen keinem anderen Test antworten.
    monkeypatch.setattr(resolver, "_ROUTE_CACHE", {})

    for name in ("caffeine", "Koffein", "(+/-)-caffeine"):
        remote.remote_generate_molecule(name)

    assert anfragen, "kein Name ging an PubChem — der Test prüft nichts"
    ohne_platz = [url for i, (url, stand) in enumerate(anfragen, start=1) if stand < i]
    assert not ohne_platz, f"PubChem-Anfrage ohne Platz in der Drossel: {ohne_platz[:3]}"
