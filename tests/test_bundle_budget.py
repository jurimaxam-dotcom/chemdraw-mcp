"""Größenbudget für das Panel-Bundle (Plan Phase 0, neu angesetzt 12.11.2026).

Das Panel ist eine einzige Datei, aber zwei Lasten: der Teil, den jedes Panel beim
Start parst, und die 3D-Engine (Mol*), die als `text/plain` eingebettet ist und erst
bei einem Protein ausgeführt wird. Gemessen 12.11.2026: Start-Teil 519.911 B,
Engine 2.476.772 B. Ein gemeinsames Budget würde ein Anwachsen des Start-Teils
hinter der großen Engine verstecken — deshalb zwei Grenzen.

Rot heißt nicht „Grenze anheben“: erst nachsehen, was dazugekommen ist. Angehoben
wird nur bewusst, mit dem Grund im selben Commit.
"""

import re
from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "chemdraw_tool" / "ui" / "dist" / "index.html"
ENGINE = re.compile(rb'<script type="text/plain" id="chem-cartoon-engine">(.*?)</script>', re.S)

START_BUDGET = 650_000      # jedes Panel parst das beim Start
ENGINE_BUDGET = 2_700_000   # nur bei Proteinen ausgeführt


def split_sizes(html: bytes) -> tuple[int, int]:
    """(Start-Teil, Engine) in Bytes; ohne Engine-Block zählt alles zum Start-Teil."""
    match = ENGINE.search(html)
    engine = len(match.group(1)) if match else 0
    return len(html) - engine, engine


def test_engine_block_wird_gefunden():
    _, engine = split_sizes(DIST.read_bytes())
    assert engine > 0, "Engine-Block nicht gefunden — das Budget würde sonst alles dem Start-Teil anlasten"


def test_start_teil_bleibt_im_budget():
    start, _ = split_sizes(DIST.read_bytes())
    assert start <= START_BUDGET, f"Start-Teil des Panels {start} B > {START_BUDGET} B"


def test_engine_bleibt_im_budget():
    _, engine = split_sizes(DIST.read_bytes())
    assert engine <= ENGINE_BUDGET, f"3D-Engine {engine} B > {ENGINE_BUDGET} B"


def test_ohne_engine_block_zaehlt_alles_zum_start():
    assert split_sizes(b"<html>abc</html>") == (16, 0)
