"""`chemdraw-doctor` — diagnose a chemdraw-mcp installation before it fails silently.

Every problem this project actually has in the field looks identical from the
chat window: "the server does nothing". This command makes the difference
visible — and, more importantly, keeps the *legitimate* states from looking
like breakage:

    ok       checked, works
    note     nothing to check here, and that is fine (e.g. no Claude Desktop)
    limited  works, but with a documented restriction (e.g. no Java → no OPSIN)
    error    genuinely broken — the exit code is non-zero only for these

Exit code: 0 as long as the server is usable (limitations included), non-zero
only when something is broken, so the command is scriptable.

Alle Prüfungen bekommen ihre Umgebung injiziert (Dateisystem, Netz, Java-Sonde,
Renderer) — die Tests laufen damit ohne Netz und ohne die echte Umgebung
anzufassen. Die Nutzerausgabe ist Englisch wie der Rest der Oberfläche.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import shutil
import sys
import textwrap
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import requests

from chemdraw_tool import resolver

# --- Einstufung ---------------------------------------------------------------

OK = "ok"
NOTE = "note"
LIMITED = "limited"
ERROR = "error"

# Marker statt Farbe: die Ausgabe soll unverändert in eine Datei oder ein
# GitHub-Issue kopierbar sein. Gleiche Breite ⇒ die Namen fluchten.
MARKERS = {OK: "[OK]", NOTE: "[NOTE]", LIMITED: "[LIMITED]", ERROR: "[FAIL]"}
_MARKER_WIDTH = 9
INDENT = " " * (_MARKER_WIDTH + 1)
_WIDTH = 88


@dataclass(frozen=True)
class CheckResult:
    """Ergebnis einer Prüfung: Einstufung, Befund, exakter Behebungsbefehl."""

    name: str
    status: str
    detail: str
    fix: str | None = None


# PNG-Signatur laut Spezifikation (kein Projekt-Wissen) — bewusst hier und nicht
# aus image_export importiert, damit dieses Modul ohne RDKit-Import ladbar bleibt.
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_PROBE_SMILES = "CCO"

# Wurzel der Ausgaben; server.py legt darunter einzelmolekuele/, spektren/ usw. an.
OUTPUT_ROOT = Path.home() / "ChemDraw-Output"

# Exakt die Toleranz des Resolvers: prüfte die Diagnose strenger, meldete sie eine
# Einschränkung, die der Server gar nicht hat (NCI CIR antwortet real oft erst nach
# >10 s). Damit die Diagnose trotzdem zügig fertig ist, laufen die Sonden parallel.
_NET_TIMEOUT = resolver._TIMEOUT

# Die Java-Sonde des Resolvers ist die einzige im Projekt — keine zweite Suche
# aufbauen, sonst diagnostiziert das Kommando etwas anderes als der Server tut.
_default_java_probe = resolver._java_runtime_available


# --- Zugriff auf die Installer-Helfer -----------------------------------------


@functools.cache
def _installer_helpers():
    """Die Config-Helfer — liegen im Paket und sind damit immer verfügbar.

    Früher lagen sie in scripts/ und fehlten im Wheel, sodass ausgerechnet
    PyPI-Nutzer die zwei wichtigsten Prüfungen (uv-Pfad, Desktop-Eintrag) nicht
    bekamen. Die Funktion bleibt als schmale Fuge, damit Tests sie ersetzen
    können.
    """
    from chemdraw_tool import desktop_config

    return desktop_config


def _runnable(path: str) -> bool:
    """Existiert die Datei und ist sie ausführbar?"""
    return _installer_helpers()._is_runnable(path)


def _short(path: str | Path, home: str | Path | None = None) -> str:
    """`/Users/x/ChemDraw-Output` → `~/ChemDraw-Output` für den Fließtext.

    Nur für die Prosa: kurze Pfade überleben den Zeilenumbruch. Die Fix-Befehle
    behalten absolute Pfade — ein Tilde in Anführungszeichen expandiert die Shell
    nicht, und genau diese Zeilen werden kopiert.
    """
    text = str(path)
    root = str(home if home is not None else Path.home())
    if root and (text == root or text.startswith(root + os.sep)):
        return "~" + text[len(root) :]
    return text


# --- Die einzelnen Prüfungen ---------------------------------------------------


def check_rendering(*, render: Callable[[str], bytes] | None = None) -> CheckResult:
    """Echter Mini-Render als Funktionsbeweis — nicht nur ein Import.

    Ein Import beweist nichts: der klassische Ausfall ist ein von Claude Desktop
    am Leben gehaltener Server-Prozess, der alte und neue Module mischt. Das
    zeigt sich erst beim Zeichnen, als Boost-Signaturfehler.
    """
    renderer = render or _default_render
    try:
        data = renderer(_PROBE_SMILES)
    except Exception as exc:  # noqa: BLE001 — jede Ausnahme ist hier der Befund
        return CheckResult(
            name="RDKit rendering",
            status=ERROR,
            detail=(
                f"Rendering the probe molecule '{_PROBE_SMILES}' failed: "
                f"{type(exc).__name__}: {exc}"
            ),
            fix="uv sync   (then quit and restart Claude Desktop completely)",
        )
    if not isinstance(data, bytes) or not data.startswith(_PNG_MAGIC):
        return CheckResult(
            name="RDKit rendering",
            status=ERROR,
            detail=(
                f"Rendering '{_PROBE_SMILES}' returned {len(data) if isinstance(data, bytes) else type(data).__name__} "
                "that is not a PNG — the RDKit drawing backend is not working."
            ),
            fix="uv sync   (then quit and restart Claude Desktop completely)",
        )
    return CheckResult(
        name="RDKit rendering",
        status=OK,
        detail=f"Drew '{_PROBE_SMILES}' to a {len(data)} byte PNG — the offline render path works.",
    )


def _default_render(smiles: str) -> bytes:
    # Spät importiert: so ist ein kaputtes RDKit ein Prüfbefund statt eines
    # Absturzes beim Start des Kommandos.
    from rdkit import Chem

    from chemdraw_tool.image_export import render_molecule_png

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("RDKit could not parse the probe SMILES")
    return render_molecule_png(mol)


def check_java(
    *,
    java_available: Callable[[], bool] | None = None,
    platform: str = sys.platform,
) -> CheckResult:
    """JRE vorhanden? Ohne sie fällt der Resolver still auf PubChem/NCI zurück."""
    probe = java_available or _default_java_probe
    if probe():
        # Die Sonde hängt das gefundene bin/ in den PATH — deshalb erst danach fragen.
        java = shutil.which("java") or "java"
        return CheckResult(
            name="Java runtime (OPSIN)",
            status=OK,
            detail=(
                f"Found {_short(java)} — systematic IUPAC names are parsed offline by OPSIN, "
                "no network needed."
            ),
        )
    fix = (
        "brew install openjdk"
        if platform == "darwin"
        else "sudo apt install default-jre   (or your distribution's JRE package)"
    )
    if platform == "darwin":
        fix += "   (keg-only is fine — the resolver probes /opt/homebrew/opt/openjdk/bin/java directly)"
    return CheckResult(
        name="Java runtime (OPSIN)",
        status=LIMITED,
        detail=(
            "No Java runtime found. Everything still works, but systematic IUPAC names "
            "are looked up online via PubChem/NCI instead of being parsed offline by "
            "OPSIN: slower, network-dependent, and names no database indexes will fail."
        ),
        fix=fix,
    )


def check_uv(*, resolve: Callable[[], str] | None = None) -> CheckResult:
    """Lässt sich uv zu einem absoluten Pfad auflösen?

    Claude Desktop startet MCP-Server mit dem minimalen GUI-PATH; ein blankes
    "uv" in der Config ist dort nicht auflösbar und der Server startet wortlos nicht.
    """
    if resolve is None:
        resolve = _installer_helpers().resolve_uv_command
    command = resolve()
    if os.path.isabs(command) and _runnable(command):
        return CheckResult(
            name="uv launcher",
            status=OK,
            detail=f"uv resolves to {_short(command)} — usable from Claude Desktop's minimal GUI PATH.",
        )
    return CheckResult(
        name="uv launcher",
        status=LIMITED,
        detail=(
            f"uv could not be resolved to an absolute path (best guess: {command!r}). "
            "Running the server by hand still works if uv is on your shell PATH, but a "
            "Claude Desktop entry using it would fail to start without a message."
        ),
        fix="curl -LsSf https://astral.sh/uv/install.sh | sh   (then re-run ./install.sh)",
    )


def _server_name() -> str:
    return _installer_helpers().SERVER_NAME


def check_desktop_config(*, config_path: Path | None = None) -> CheckResult:
    """Claude-Desktop-Config: vorhanden, gültig, Eintrag da, Startbefehl startbar?

    Wichtig: eine fehlende Config ist KEIN Fehler. Claude Code, die Web-App und
    andere MCP-Clients benutzen diese Datei nicht.
    """
    name = "Claude Desktop config"
    if config_path is None:
        config_path = _installer_helpers().claude_config_path()
    path = Path(config_path)

    if not path.exists():
        return CheckResult(
            name=name,
            status=NOTE,
            detail=(
                f"No config at {_short(path)} — Claude Desktop is not installed or has never been "
                "started on this machine. Nothing to fix: Claude Code, the web app and "
                "other MCP clients do not use this file."
            ),
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return CheckResult(
            name=name,
            status=ERROR,
            detail=(
                f"{_short(path)} is not valid JSON ({exc}). Claude Desktop ignores the whole file, "
                "so every configured MCP server is dead, not just this one."
            ),
            fix=f'python3 -m json.tool "{path}"   (shows the exact position; the installer keeps a backup at {path}.bak)',
        )

    servers = data.get("mcpServers") if isinstance(data, dict) else None
    entry = servers.get(_server_name()) if isinstance(servers, dict) else None
    if not isinstance(entry, dict):
        return CheckResult(
            name=name,
            status=LIMITED,
            detail=(
                f"{_short(path)} exists but has no '{_server_name()}' entry, so Claude Desktop does "
                "not know this server. Not a problem if you use another client."
            ),
            fix="./install.sh   (idempotent; leaves your other MCP servers untouched)",
        )

    command = entry.get("command") or ""
    if not (os.path.isabs(command) and _runnable(command)):
        return CheckResult(
            name=name,
            status=ERROR,
            detail=(
                f"The '{_server_name()}' entry starts {command!r}, which is not an executable "
                "file at an absolute path. Claude Desktop launches MCP servers with the "
                "minimal GUI PATH and will fail to start it without any message."
            ),
            fix="chemdraw-install   (rewrites the entry with the absolute launcher path)",
        )
    args = " ".join(str(a) for a in entry.get("args", []))
    return CheckResult(
        name=name,
        status=OK,
        detail=f"Registered in {_short(path)} and startable: {_short(command)} {args}".rstrip(),
    )


def _default_network_probe(url: str) -> None:
    response = requests.get(url, timeout=_NET_TIMEOUT)
    response.raise_for_status()


def check_network(*, probe: Callable[[str], None] | None = None) -> CheckResult:
    """Sind die Namens-Datenbanken erreichbar?

    Kein Netz ist ein Fehlen von Komfort, kein Defekt: SMILES (und mit Java auch
    systematische IUPAC-Namen) funktionieren offline weiter. Die Unterscheidung
    "nicht erreichbar" vs. "antwortet mit Fehler" ist dieselbe wie im Resolver.
    """
    ask = probe or _default_network_probe
    sources = (
        (resolver._PUBCHEM, resolver._PUBCHEM_URL.format(name="water")),
        (resolver._NCI, resolver._NCI_CIR_URL.format(name="water")),
    )
    # Parallel: eine hängende Quelle soll die andere nicht aufhalten — sonst
    # wartet der Nutzer bei Netzausfall zweimal das volle Timeout ab.
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = [pool.submit(ask, url) for _, url in sources]
        outcomes = [
            (source, future.exception())
            for (source, _), future in zip(sources, futures, strict=True)
        ]

    reachable: list[str] = []
    problems: list[str] = []
    statuses: list[str] = []
    for source, exc in outcomes:
        if exc is None:
            reachable.append(source)
            continue
        status, human = resolver._classify_error(exc)
        statuses.append(status)
        problems.append(f"{source}: {human}")

    if not problems:
        return CheckResult(
            name="Name databases",
            status=OK,
            detail=f"{' and '.join(reachable)} reachable — trivial and brand names resolve.",
        )

    summary = "; ".join(problems)
    if reachable:
        return CheckResult(
            name="Name databases",
            status=LIMITED,
            detail=(
                f"{' and '.join(reachable)} answered, but {summary}. Name lookups still work "
                "through the remaining source, with less coverage."
            ),
            fix=None,
        )
    if all(status == resolver._SOURCE_ERROR for status in statuses):
        return CheckResult(
            name="Name databases",
            status=LIMITED,
            detail=(
                f"Every name database was reachable but returned errors ({summary}). That is "
                "on their side — retry in a few minutes. "
                + resolver._offline_hint(lead="Independent of any database you can use")
            ),
            fix=None,
        )
    return CheckResult(
        name="Name databases",
        status=LIMITED,
        detail=(
            f"No name database could be reached ({summary}) — you are offline or behind a "
            "proxy. Only lookups by trivial or brand name are affected. "
            + resolver._offline_hint()
        ),
        fix=f'curl -sS -o /dev/null -w "%{{http_code}}\\n" "{sources[0][1]}"   (should print 200)',
    )


def check_output_dir(*, root: Path | None = None) -> CheckResult:
    """Ist ~/ChemDraw-Output/ da und beschreibbar? (Legt nichts an.)"""
    target = Path(root) if root is not None else OUTPUT_ROOT
    name = "Output directory"
    if target.exists():
        if not target.is_dir():
            return CheckResult(
                name=name,
                status=ERROR,
                detail=f"{_short(target)} exists but is not a directory — generated files cannot be saved.",
                fix=f'mv "{target}" "{target}.bak"',
            )
        if os.access(target, os.W_OK | os.X_OK):
            return CheckResult(
                name=name, status=OK, detail=f"{_short(target)} exists and is writable."
            )
        return CheckResult(
            name=name,
            status=ERROR,
            detail=f"{_short(target)} exists but is not writable — every generated file will fail to save.",
            fix=f'chmod u+rwx "{target}"',
        )

    ancestor = next((p for p in target.parents if p.exists()), Path(target.anchor))
    if os.access(ancestor, os.W_OK | os.X_OK):
        return CheckResult(
            name=name,
            status=OK,
            detail=f"{_short(target)} does not exist yet — it is created automatically on the first drawing.",
        )
    return CheckResult(
        name=name,
        status=ERROR,
        detail=f"{_short(target)} is missing and cannot be created: {_short(ancestor)} is not writable.",
        fix=f'chmod u+rwx "{ancestor}"',
    )


# Reihenfolge = Lesereihenfolge des Berichts: erst der Funktionsbeweis, dann die
# Umgebung, zuletzt das Optionale.
DEFAULT_CHECKS: tuple[Callable[[], CheckResult], ...] = (
    check_rendering,
    check_java,
    check_uv,
    check_desktop_config,
    check_network,
    check_output_dir,
)


# --- Ausführung, Einstufung, Bericht ------------------------------------------


def run_checks(
    checks: Iterable[Callable[[], CheckResult]] | None = None,
) -> list[CheckResult]:
    """Führt alle Prüfungen aus. Eine abstürzende Prüfung ist selbst ein Befund."""
    results: list[CheckResult] = []
    for check in checks if checks is not None else DEFAULT_CHECKS:
        try:
            results.append(check())
        except Exception as exc:  # noqa: BLE001 — nie mit Traceback aussteigen
            results.append(
                CheckResult(
                    name=getattr(check, "__name__", "check"),
                    status=ERROR,
                    detail=f"The check itself crashed: {type(exc).__name__}: {exc}",
                    fix="Please report this output at https://github.com/jurimaxam-dotcom/chemdraw-mcp/issues",
                )
            )
    return results


def exit_code(results: Sequence[CheckResult]) -> int:
    """0, solange der Server benutzbar ist — Einschränkungen zählen nicht."""
    return 1 if any(r.status == ERROR for r in results) else 0


def summarize(results: Sequence[CheckResult]) -> str:
    """Ein Satz: kann der Nutzer den Server jetzt benutzen oder nicht?"""
    errors = sum(1 for r in results if r.status == ERROR)
    limits = sum(1 for r in results if r.status == LIMITED)
    if errors:
        return (
            f"Summary: the server will not work as installed — {errors} "
            f"{'check' if errors == 1 else 'checks'} failed above, each with the command that fixes it."
        )
    if limits:
        return (
            f"Summary: the server is usable, with {limits} "
            f"{'limitation' if limits == 1 else 'limitations'} listed above."
        )
    return "Summary: the server is usable and every check passed."


def _environment_header() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        own = version("chemdraw-mcp")
    except PackageNotFoundError:
        own = "unknown version"
    try:
        from rdkit import rdBase

        rdkit_version = f"RDKit {rdBase.rdkitVersion}"
    except Exception:  # noqa: BLE001 — im Bericht ist das die Fehlermeldung
        rdkit_version = "RDKit unavailable"
    python_version = ".".join(str(p) for p in sys.version_info[:3])
    return (
        f"chemdraw-mcp doctor — {own} | Python {python_version} | {rdkit_version} | {sys.platform}"
    )


def format_report(results: Sequence[CheckResult], *, header: str | None = None) -> str:
    lines: list[str] = []
    if header:
        lines += [header, "=" * min(len(header), _WIDTH), ""]
    for result in results:
        lines.append(f"{MARKERS[result.status]:<{_MARKER_WIDTH}} {result.name}")
        lines.append(
            textwrap.fill(
                result.detail,
                width=_WIDTH,
                initial_indent=INDENT,
                subsequent_indent=INDENT,
            )
        )
        if result.fix:
            lines.append(f"{INDENT}Fix: {result.fix}")
        lines.append("")
    lines.append(summarize(results))
    return "\n".join(lines)


def main(
    argv: Sequence[str] | None = None,
    *,
    checks: Iterable[Callable[[], CheckResult]] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="chemdraw-doctor",
        description=(
            "Check a chemdraw-mcp installation and print, for every problem, the exact "
            "command that fixes it. Exit code 0 means usable (limitations included)."
        ),
    )
    parser.parse_args(argv)
    results = run_checks(checks=checks)
    print(format_report(results, header=_environment_header()))
    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
