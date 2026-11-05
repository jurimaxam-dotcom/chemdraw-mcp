"""Doppel-Pin Playwright: Python- und JS-Seite müssen exakt dieselbe Version haben.

Beide Pakete teilen sich den Browser-Cache (~/Library/Caches/ms-playwright) und
laden je Version eine andere Chromium-Build-Revision (Vorfall 14.08.2026, siehe
Kommentar in pyproject.toml). Bisher war das nur ein Kommentar — Dependabot-PR #7
(05.11.2026) hob die Python-Seite allein, weil `.github/dependabot.yml` kein
npm-Ökosystem überwacht. Dieser Test macht aus dem Kommentar eine Regel: ein
einseitiger Bump färbt den PR rot statt still zu driften.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def python_playwright_pin(pyproject_text: str) -> str:
    data = tomllib.loads(pyproject_text)
    for spec in data["dependency-groups"]["dev"]:
        if isinstance(spec, str) and re.match(r"playwright\s*==", spec):
            return spec.split("==", 1)[1].strip()
    raise AssertionError("pyproject.toml: kein exakter playwright==-Pin in der dev-Gruppe")


def js_playwright_pin(package_json_text: str) -> str:
    data = json.loads(package_json_text)
    return data["devDependencies"]["playwright"]


def test_playwright_is_pinned_to_the_same_version_on_both_sides():
    py = python_playwright_pin((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    js = js_playwright_pin(
        (ROOT / "chemdraw_tool" / "ui" / "package.json").read_text(encoding="utf-8")
    )
    assert re.fullmatch(r"\d+\.\d+\.\d+", js), (
        f"package.json pinnt playwright nicht exakt ({js!r}) — kein ^ oder ~"
    )
    assert py == js, (
        f"Playwright-Drift: pyproject.toml {py} ≠ package.json {js}. "
        "Beide Seiten auf dieselbe Version heben (npm install --save-exact "
        "--save-dev playwright@X im ui-Ordner bzw. pyproject + uv lock)."
    )
