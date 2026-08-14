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
import os
import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

SERVER_NAME = "chemdraw-tool"

# Claude Desktop startet MCP-Server nicht in einer Login-Shell, sondern mit dem
# minimalen GUI-/launchd-PATH. Ein blankes "uv" als command ist dort nicht
# auflösbar — der Server startet dann kommentarlos nicht. Deshalb wird uv zum
# Absolutpfad aufgelöst; wenn es nicht im PATH steht (Homebrew, frisch nach
# ~/.local/bin installiert), werden die bekannten Installationsorte probiert.
UV_CANDIDATES: tuple[Path, ...] = (
    Path.home() / ".local" / "bin" / "uv",
    Path.home() / ".cargo" / "bin" / "uv",
    Path("/opt/homebrew/bin/uv"),
    Path("/usr/local/bin/uv"),
)


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


def _is_runnable(path: str) -> bool:
    """Existiert die Datei und ist sie ausführbar? (Verzeichnisse zählen nicht.)"""
    return os.path.isfile(path) and os.access(path, os.X_OK)


def resolve_uv_command(
    explicit: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
    candidates: Iterable[Path | str] = UV_CANDIDATES,
) -> str:
    """Löst uv zu einem absoluten, ausführbaren Pfad auf.

    Reihenfolge: explizit übergebener Pfad (install.sh kennt das uv, das es
    gerade benutzt hat) → PATH dieser Shell → bekannte Installationsorte.
    Findet sich nichts, bleibt es beim blanken "uv" — der Installer soll daran
    nicht scheitern, meldet den Fall aber (siehe verify_entry).

    Symlinks werden bewusst NICHT aufgelöst: /opt/homebrew/bin/uv bleibt über
    Versions-Upgrades hinweg gültig, das Cellar-Ziel dahinter nicht.
    """
    probes: list[str] = []
    if explicit:
        probes.append(explicit)
    from_path = which("uv")
    if from_path:
        probes.append(from_path)
    probes.extend(str(candidate) for candidate in candidates)

    for probe in probes:
        resolved = os.path.abspath(os.path.expanduser(probe))
        if _is_runnable(resolved):
            return resolved
    return "uv"


def build_server_entry(project_dir: str, uv_command: str | None = None) -> dict:
    """Baut den mcpServers-Eintrag, der den Server via uv startet."""
    if not Path(project_dir).is_absolute():
        raise ValueError(f"project_dir muss absolut sein, war: {project_dir!r}")
    return {
        "command": resolve_uv_command(uv_command),
        "args": ["--directory", project_dir, "run", "chemdraw-tool-server"],
    }


def verify_entry(entry: dict) -> str:
    """Prüft, ob der geschriebene Eintrag wirklich startfähig ist.

    Gibt die Zeile zurück, die der Installer ausgibt — Erfolg mit dem konkreten
    Startbefehl, sonst eine Warnung, die den späteren stillen Fehlschlag
    ("Server startet nicht") sofort sichtbar macht.
    """
    command = entry.get("command", "")
    if _is_runnable(command) and os.path.isabs(command):
        return f"✓ Startet mit: {command}"
    return (
        f"⚠ uv nicht als Absolutpfad auflösbar (Eintrag: {command!r}). "
        "Claude Desktop startet MCP-Server mit minimalem GUI-PATH und findet "
        "uv dort evtl. nicht. Bitte 'command' in der Config von Hand auf die "
        "Ausgabe von 'which uv' setzen."
    )


def merge_server_config(existing: dict, name: str, entry: dict) -> dict:
    """Gibt eine neue Config zurück mit name→entry unter mcpServers.

    Mutiert `existing` nicht. Bestehende Server und Top-Level-Keys bleiben.
    """
    result = copy.deepcopy(existing)
    servers = result.setdefault("mcpServers", {})
    servers[name] = entry
    return result


def install(
    project_dir: str, config_path: Path | None = None, uv_command: str | None = None
) -> Path:
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

    entry = build_server_entry(project_dir, uv_command=uv_command)
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
    ap.add_argument(
        "--uv-command",
        default=None,
        help="Pfad zum uv-Binary (Default: Auflösung über PATH bzw. bekannte "
        "Installationsorte). install.sh reicht hier das uv durch, das es "
        "gerade benutzt hat.",
    )
    args = ap.parse_args()
    project_dir = str(Path(args.project_dir).resolve())
    path = install(project_dir, uv_command=args.uv_command)
    print(f"✓ chemdraw-tool in {path} registriert.")
    print(verify_entry(build_server_entry(project_dir, uv_command=args.uv_command)))
    print("→ Claude Desktop neu starten, damit der Server geladen wird.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
