"""Ohne Titel darf eine Datei nicht die vorige überschreiben.

Gefunden im Desktop-Chat 03.10.2026: `pk-pharmacokinetics.png` wurde bei jeder Kurve ohne Namen
neu geschrieben. Dasselbe Muster steckte in TLC, Scope, Spektrum, Kalibrierkurve und Reaktion
(feste Vorgabe wie „tlc-plate“). Regel: ohne Titel trägt der Dateiname einen kurzen Fingerabdruck
der Eingaben — andere Eingaben → andere Datei, gleiche Eingaben → dieselbe Datei (keine Dateiflut).
"""

import copy

import pytest

from chemdraw_tool import server as s
from tests.test_server_calibration import SIGNALS, STANDARDS
from tests.test_server_scope import ENTRIES
from tests.test_server_spectrum import IR_PEAKS
from tests.test_server_tlc import ESTER_LANES


def _andere_lanes():
    lanes = copy.deepcopy(ESTER_LANES)
    lanes[0]["spots"][0]["rf"] = 0.55
    return lanes


FAELLE = {
    "tlc": (
        "TLC_DIR",
        lambda: s.generate_tlc(ESTER_LANES),
        lambda: s.generate_tlc(_andere_lanes()),
    ),
    "scope": (
        "SCOPE_DIR",
        lambda: s.generate_scope_table(ENTRIES),
        lambda: s.generate_scope_table(ENTRIES[:2]),
    ),
    "spectrum": (
        "SPECTRUM_DIR",
        lambda: s.generate_spectrum("ir", IR_PEAKS),
        lambda: s.generate_spectrum("ir", IR_PEAKS[:-1]),
    ),
    "calibration": (
        "PLOT_DIR",
        lambda: s.generate_calibration_curve(STANDARDS, SIGNALS),
        lambda: s.generate_calibration_curve(STANDARDS, [x * 2 for x in SIGNALS]),
    ),
    "reaction": (
        "REACTION_DIR",
        lambda: s.generate_reaction(["CCO", "CC(=O)O"], ["CCOC(C)=O", "O"]),
        lambda: s.generate_reaction(["CCCO", "CC(=O)O"], ["CCCOC(C)=O", "O"]),
    ),
}


def _datei(payload) -> str:
    files = payload.files
    return files.get("png") or files.get("svg") or next(iter(files.values()))


@pytest.mark.parametrize("fall", sorted(FAELLE))
def test_verschiedene_eingaben_ohne_titel_ueberschreiben_sich_nicht(fall, tmp_path, monkeypatch):
    verzeichnis, a, b = FAELLE[fall]
    monkeypatch.setattr(f"chemdraw_tool.server.{verzeichnis}", tmp_path / "out")
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    erste, zweite = _datei(a()), _datei(b())
    assert erste != zweite, f"{fall}: zwei verschiedene Eingaben schreiben dieselbe Datei {erste}"


@pytest.mark.parametrize("fall", sorted(FAELLE))
def test_gleiche_eingaben_ohne_titel_geben_dieselbe_datei(fall, tmp_path, monkeypatch):
    verzeichnis, a, _ = FAELLE[fall]
    monkeypatch.setattr(f"chemdraw_tool.server.{verzeichnis}", tmp_path / "out")
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    assert _datei(a()) == _datei(a())


@pytest.mark.parametrize("fall", ["tlc", "scope", "spectrum"])
def test_mit_titel_bleibt_der_name_lesbar_und_unveraendert(fall, tmp_path, monkeypatch):
    """Ein gegebener Titel bleibt der Dateiname — kein Fingerabdruck, keine Überraschung."""
    kwargs = {
        "tlc": lambda: s.generate_tlc(ESTER_LANES, title="Veresterung"),
        "scope": lambda: s.generate_scope_table(ENTRIES, title="Suzuki scope"),
        "spectrum": lambda: s.generate_spectrum("ir", IR_PEAKS, title="Aspirin"),
    }[fall]
    verzeichnis = FAELLE[fall][0]
    monkeypatch.setattr(f"chemdraw_tool.server.{verzeichnis}", tmp_path / "out")
    name = _datei(kwargs()).rsplit("/", 1)[1]
    assert name.split(".")[0] in {"veresterung", "suzuki-scope", "aspirin"}
