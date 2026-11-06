"""Vorab-Prüfung eines Releases: Tag, Version und CHANGELOG passen zusammen.

Läuft als Job `check` in .github/workflows/publish.yml vor dem Build; ein Befund
macht den Release rot, bevor etwas auf PyPI landet. Lokal vor dem Release-Klick:

    uv run python scripts/release_check.py --tag v0.9.0

Die Doku-Inhalte prüfen tests/test_readme.py und tests/test_docs_consistency.py
(derselbe Job ruft sie auf); was nicht mechanisch geht, steht als Checkliste in
docs/registry-publish.md § Release-Reihenfolge im Ganzen.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _abschnitt(changelog: str, kopf: str) -> str | None:
    """Text nach der Überschrift, die mit `kopf` beginnt, bis zur nächsten „## “."""
    m = re.search(rf"^{re.escape(kopf)}.*$", changelog, flags=re.MULTILINE)
    if not m:
        return None
    rest = changelog[m.end() :]
    ende = re.search(r"^## ", rest, flags=re.MULTILINE)
    return rest[: ende.start() if ende else None]


def befunde(version: str, changelog: str, tag: str | None) -> list[str]:
    """Liste der Befunde; leer = Release darf laufen."""
    out = []
    if tag is not None and tag != f"v{version}":
        out.append(f"Tag {tag} passt nicht zur Version {version} in pyproject.toml (erwartet v{version})")

    kopf = f"## [{version}]"
    abschnitt = _abschnitt(changelog, kopf)
    if abschnitt is None:
        out.append(f"CHANGELOG.md hat keinen Abschnitt {kopf}")
    else:
        zeile = re.search(rf"^{re.escape(kopf)}.*$", changelog, flags=re.MULTILINE).group(0)
        if not re.fullmatch(rf"{re.escape(kopf)} — \d{{4}}-\d{{2}}-\d{{2}}", zeile):
            out.append(f"CHANGELOG-Überschrift ohne Datum: „{zeile}“ (erwartet „{kopf} — JJJJ-MM-TT“)")
        if not re.search(r"^\s*- ", abschnitt, flags=re.MULTILINE):
            out.append(f"CHANGELOG-Abschnitt {kopf} ist leer")

    offen = _abschnitt(changelog, "## [Unreleased]")
    if offen and re.search(r"^\s*- ", offen, flags=re.MULTILINE):
        out.append("CHANGELOG [Unreleased] hat noch Einträge — in den Versionsabschnitt verschieben")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", help="Release-Tag, z. B. v0.9.0 (ohne: Tag nicht prüfen)")
    args = parser.parse_args(argv)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    gefunden = befunde(version, changelog, args.tag or None)
    for b in gefunden:
        print(f"::error::{b}")
    if not gefunden:
        print(f"Release-Check {version} ({args.tag or 'ohne Tag'}): ok")
    return 1 if gefunden else 0


if __name__ == "__main__":
    sys.exit(main())
