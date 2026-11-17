"""Lizenzhinweise: Was im Panel steckt, steht auch in THIRD_PARTY_LICENSES.

Das Panel (`chemdraw_tool/ui/dist/index.html`) enthält fremden Code. MIT und
Apache-2.0 verlangen, dass Urheberhinweis und Lizenztext mitgehen — die Datei
wandert dafür ins sdist, ins Wheel und als Kopfkommentar in das Panel selbst.
Ohne diesen Test veraltet sie beim nächsten Paket-Update still.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "chemdraw_tool" / "ui"
HINWEISE = (ROOT / "THIRD_PARTY_LICENSES").read_text(encoding="utf-8")

# Gemessen am 17.11.2026 aus dem Rollup-Modulgraphen (Panel) und der
# esbuild-Metadatei (3D-Engine). Eine neue Laufzeit-Abhängigkeit in
# package.json macht den ersten Test rot, bis sie hier und in der Datei steht.
IM_PANEL = {
    "react", "react-dom", "scheduler", "zod",
    "@modelcontextprotocol/client", "@modelcontextprotocol/core", "@modelcontextprotocol/ext-apps",
    "molstar", "rxjs", "immutable", "mutative", "tslib",
}


def _lock_version(name: str) -> str:
    lock = json.loads((UI / "package-lock.json").read_text(encoding="utf-8"))
    return lock["packages"][f"node_modules/{name}"]["version"]


def test_jede_laufzeit_abhaengigkeit_ist_erfasst():
    direkt = set(json.loads((UI / "package.json").read_text(encoding="utf-8"))["dependencies"])
    assert direkt <= IM_PANEL, f"neu in package.json, Lizenzhinweis fehlt: {sorted(direkt - IM_PANEL)}"


def test_jedes_paket_steht_mit_der_gebauten_version_in_der_datei():
    fehlt = []
    for name in sorted(IM_PANEL):
        version = _lock_version(name)
        # Listenzeile: "- Anzeigename (paket) 1.2.3 — Lizenz" oder "- paket 1.2.3 — Lizenz"
        zeile = re.compile(rf"^- .*{re.escape(name)}\)? {re.escape(version)} — ", re.M)
        if not zeile.search(HINWEISE):
            fehlt.append(f"{name} {version}")
    assert not fehlt, f"nicht (oder mit anderer Version) in THIRD_PARTY_LICENSES: {fehlt}"


def test_urheberhinweise_der_mit_lizenzen_stehen_drin():
    for hinweis in (
        "Copyright (c) Facebook, Inc. and its affiliates.",  # react, react-dom, scheduler
        "Copyright (c) 2025 Colin McDonnell",                # zod
        "The MCP project is undergoing a licensing transition",  # MCP-Pakete
    ):
        assert hinweis in HINWEISE, hinweis


def test_notice_nennt_den_inhaber_und_geht_ins_sdist():
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Copyright 2026 jurimaxam-dotcom" in notice
    assert "Revvity" in notice, "der Markenhinweis gehört in die NOTICE"
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    einschluss = re.search(r"^only-include = \[(.*)\]$", pyproject, re.M).group(1)
    assert '"NOTICE"' in einschluss
