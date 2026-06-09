#!/usr/bin/env python3
"""Registriert den chemdraw-tool MCP-Server in der Claude-Desktop-Config.

Idempotenter Merge: fügt den Server-Eintrag hinzu bzw. aktualisiert ihn,
OHNE andere bereits konfigurierte MCP-Server oder Top-Level-Einstellungen
anzufassen. Schreibt vor dem Überschreiben ein .bak-Backup.

Wird von install.sh aufgerufen, ist aber auch direkt nutzbar:
    uv run python scripts/install_claude_config.py [--project-dir PFAD]
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

SERVER_NAME = "chemdraw-tool"


def claude_config_path() -> Path:
    """Plattformabhängiger Pfad zur claude_desktop_config.json."""
    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if sys.platform.startswith("win"):
        import os

        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "Claude" / "claude_desktop_config.json"
    # Linux / sonstige: XDG-Konvention
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def build_server_entry(project_dir: str) -> dict:
    """Baut den mcpServers-Eintrag, der den Server via uv startet."""
    if not Path(project_dir).is_absolute():
        raise ValueError(f"project_dir muss absolut sein, war: {project_dir!r}")
    return {
        "command": "uv",
        "args": ["--directory", project_dir, "run", "chemdraw-tool-server"],
    }


def merge_server_config(existing: dict, name: str, entry: dict) -> dict:
    """Gibt eine neue Config zurück mit name→entry unter mcpServers.

    Mutiert `existing` nicht. Bestehende Server und Top-Level-Keys bleiben.
    """
    result = copy.deepcopy(existing)
    servers = result.setdefault("mcpServers", {})
    servers[name] = entry
    return result


def install(project_dir: str, config_path: Path | None = None) -> Path:
    """Liest die Config (falls vorhanden), merged den Eintrag, schreibt zurück.

    Returns den geschriebenen Pfad. Legt ein <pfad>.bak-Backup an, wenn die
    Datei schon existierte.
    """
    path = config_path or claude_config_path()
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Claude-Config ist kein gültiges JSON: {path} ({exc}). "
                "Datei wurde NICHT verändert — bitte erst reparieren "
                "(oder löschen, dann legt der Installer sie neu an)."
            ) from exc
        path.with_suffix(path.suffix + ".bak").write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    entry = build_server_entry(project_dir)
    merged = merge_server_config(existing, SERVER_NAME, entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--project-dir",
        default=str(Path(__file__).resolve().parent.parent),
        help="Absoluter Pfad zum Projekt (Default: dieses Repo).",
    )
    args = ap.parse_args()
    path = install(str(Path(args.project_dir).resolve()))
    print(f"✓ chemdraw-tool in {path} registriert.")
    print("→ Claude Desktop neu starten, damit der Server geladen wird.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
