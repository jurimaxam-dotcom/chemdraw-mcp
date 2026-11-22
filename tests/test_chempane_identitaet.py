"""Etappe 4 der Umbenennung: Identitäten nach außen (22.11.2026).

- Registry: neuer Eintrag io.github.chempane/chempane für das PyPI-Paket chempane; die
  mcp-name-Zeile im README (PyPI-Seite von chempane) muss exakt server.json `name` sein.
- Bundle: manifest `name` bleibt chemdraw-mcp (Entscheidung E3: gleiche Extension-ID
  local.mcpb.<author>.chemdraw-mcp, damit Desktop ein Update sieht statt einer zweiten
  Erweiterung), angezeigt wird chempane. Das Bundle installiert chempane, nicht die Hülle —
  sonst fehlten chempanes Hashes in requirements.lock.
- publish.yml baut chempane und die Hülle; der Registry-Job läuft nur aus dem Repo, dessen
  Owner den Namensraum stellt (Etappe 0, Befund 6) — vor dem Umzug nach chempane/chempane
  überspringt er mit Warnung statt rot zu werden.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_server_json_names_chempane():
    data = _json("server.json")
    assert data["name"] == "io.github.chempane/chempane"
    assert data["packages"][0]["identifier"] == "chempane"
    assert "chemdraw" not in data["title"].lower()


def test_readme_mcp_name_matches_server_json():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"<!-- mcp-name: {_json('server.json')['name']} -->" in readme


def _variant(profile: str) -> dict:
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "mcpb_manifest.py"), profile],
        capture_output=True, text=True, check=True, cwd=ROOT,
    )
    return json.loads(out.stdout)


def test_bundle_keeps_its_id_but_shows_chempane():
    for profile, ident in (("mvp", "chemdraw-mcp"), ("pharma", "chemdraw-mcp-pharma")):
        manifest = _variant(profile)
        assert manifest["name"] == ident, "Extension-ID bleibt (E3)"
        assert manifest["display_name"].startswith("chempane")
        for key in ("display_name", "description", "long_description"):
            assert "ChemDraw MCP" not in manifest[key], (profile, key)


def test_bundle_installs_chempane():
    build = (ROOT / "scripts" / "build-mcpb.sh").read_text(encoding="utf-8")
    run_sh = (ROOT / "mcpb" / "server" / "run.sh").read_text(encoding="utf-8")
    assert "printf 'chempane==%s %s\\n'" in build
    assert "pypi.org/pypi/chempane/$VERSION/json" in build
    assert 'SERVER="$UMGEBUNG/bin/chempane"' in run_sh
    assert "--refresh-package chempane" in run_sh


def test_publish_builds_both_packages_and_waits_for_chempane():
    wf = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "uv build --out-dir dist huelle/chemdraw-mcp" in wf
    assert "pypi.org/pypi/chempane/$VERSION/json" in wf


def test_registry_job_skips_outside_the_namespace_owner():
    wf = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    registry = wf[wf.index("\n  registry:"):]
    assert "github.repository_owner" in registry
    assert re.search(r"if: steps\.\w+\.outputs\.publish == 'true'", registry)
