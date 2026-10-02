import atexit
import functools
import glob
import importlib.util
import logging
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import warnings
from urllib.parse import quote

import requests
from rdkit import Chem, RDLogger

logger = logging.getLogger(__name__)

# resolve() now attempts a SMILES parse on every input (parse-first), so real
# names like "Aspirin" would emit a "SMILES Parse Error" to stderr on every
# lookup. We handle parse failures via None checks everywhere; silence RDKit's
# error stream to keep the MCP server logs readable.
RDLogger.DisableLog("rdApp.error")

_SMILES_CHARS = re.compile(r"[=()[\]#@/\\]")
_SMILES_RING = re.compile(r"[a-z]\d")
_STEREO_PREFIX = re.compile(r"^\([RSEZrsez±+\-]\)-")

_UMLAUT_MAP = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
    }
)


def is_smiles(input_str: str) -> bool:
    if " " in input_str:
        return False
    if _STEREO_PREFIX.match(input_str):
        return False
    return bool(_SMILES_CHARS.search(input_str) or _SMILES_RING.search(input_str))


def validate_smiles(smiles: str) -> Chem.Mol | None:
    return Chem.MolFromSmiles(smiles)


_PUBCHEM_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    "/{name}/property/IsomericSMILES/JSON"
)

_NCI_CIR_URL = "https://cactus.nci.nih.gov/chemical/structure/{name}/smiles"

_PUBCHEM = "PubChem"
_NCI = "NCI CIR"

# (connect, read): ein nicht erreichbarer Host scheitert nach 3 s statt nach 10.
# Die Kaskade kettet bis zu vier Requests — mit einem einzigen 10-s-Wert wartet
# der Nutzer bei hängendem Netz 40 s auf eine Fehlermeldung.
_TIMEOUT = (3, 10)

# Ausgang eines einzelnen Quellen-Versuchs. Der Unterschied ist die ganze
# Diagnose: NOT_FOUND heißt "Quelle hat geantwortet und kennt den Namen nicht"
# (Rat: Namen ändern), UNREACHABLE heißt "gar keine Antwort" (Rat: Netz prüfen).
_NOT_FOUND = "not_found"
_UNREACHABLE = "unreachable"
_SOURCE_ERROR = "source_error"


class NameResolutionError(ValueError):
    """Namensauflösung fehlgeschlagen — mit Ursache statt Pauschalmeldung.

    Bleibt eine ValueError: server.py und andere Aufrufer fangen darauf.
    `kind` ist einer von 'not_found' | 'offline' | 'sources_down' | 'partial'.
    """

    def __init__(self, message: str, *, name: str, kind: str, attempts: list):
        super().__init__(message)
        self.name = name
        self.kind = kind
        self.attempts = attempts


class _Attempt:
    """Was eine Quelle bei einem Versuch geantwortet hat."""

    __slots__ = ("source", "status", "detail")

    def __init__(self, source: str, status: str, detail: str):
        self.source = source
        self.status = status
        self.detail = detail


def _classify_error(exc: Exception) -> tuple[str, str]:
    """Netzwerk-Ausnahme → (Status, Klartext für die Fehlermeldung)."""
    # Reihenfolge zählt: ConnectTimeout erbt von Timeout UND ConnectionError.
    if isinstance(exc, requests.exceptions.Timeout):
        return _UNREACHABLE, "timed out"
    json_error = getattr(requests.exceptions, "JSONDecodeError", None)
    if json_error is not None and isinstance(exc, json_error):
        # Antwort kam an, war nur unlesbar → Quelle erreichbar, aber kaputt.
        return _SOURCE_ERROR, "unreadable answer"
    if isinstance(exc, requests.exceptions.HTTPError):
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if code == 404:
            return _NOT_FOUND, "name unknown (HTTP 404)"
        return _SOURCE_ERROR, f"HTTP {code}" if code else "HTTP error"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return _UNREACHABLE, "connection failed"
    if isinstance(exc, requests.exceptions.RequestException):
        return _UNREACHABLE, f"request failed ({type(exc).__name__})"
    return _SOURCE_ERROR, f"unexpected answer ({type(exc).__name__})"


def _record(report: list | None, source: str, status: str, detail: str) -> None:
    if report is not None:
        report.append(_Attempt(source, status, detail))


def _is_unreachable(report: list | None, source: str) -> bool:
    """Host in diesem Lauf schon als tot erkannt? Dann nicht erneut anwählen —
    das spart bei Netzausfall ein zweites Connect-Timeout pro Host."""
    if not report:
        return False
    return any(a.source == source and a.status == _UNREACHABLE for a in report)


def _pubchem_lookup(name: str, report: list | None = None) -> str | None:
    if _is_unreachable(report, _PUBCHEM):
        return None
    try:
        resp = requests.get(
            _PUBCHEM_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        props_list = resp.json().get("PropertyTable", {}).get("Properties", [])
    except Exception as exc:
        # Früher: bloßes `return None` — die Ursache ging verloren und oben
        # bekam jeder Ausfall denselben (bei Netzausfall falschen) Rat.
        _record(report, _PUBCHEM, *_classify_error(exc))
        return None
    if not props_list:
        _record(report, _PUBCHEM, _NOT_FOUND, "name unknown")
        return None
    props = props_list[0]
    smiles = props.get("SMILES") or props.get("IsomericSMILES")
    if not smiles:
        _record(report, _PUBCHEM, _NOT_FOUND, "answer without SMILES")
        return None
    return smiles


def _nci_cir_lookup(name: str, report: list | None = None) -> str | None:
    if _is_unreachable(report, _NCI):
        return None
    try:
        resp = requests.get(
            _NCI_CIR_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
    except Exception as exc:
        _record(report, _NCI, *_classify_error(exc))
        return None
    if resp.status_code != 200:
        status = _NOT_FOUND if resp.status_code == 404 else _SOURCE_ERROR
        detail = (
            "name unknown (HTTP 404)"
            if status == _NOT_FOUND
            else f"HTTP {resp.status_code}"
        )
        _record(report, _NCI, status, detail)
        return None
    smiles = resp.text.strip().split("\n")[0]
    if smiles and validate_smiles(smiles):
        return smiles
    _record(report, _NCI, _NOT_FOUND, "name unknown")
    return None


# macOS ships a /usr/bin/java stub that exists but fails without a JRE, and
# Homebrew's openjdk is keg-only (not on PATH). Probe known locations and, on
# success, prepend the bin dir to PATH so py2opsin's bare "java" call works —
# the MCP server is launched by Claude Desktop with a minimal GUI PATH.
_JAVA_CANDIDATES = (
    "/opt/homebrew/opt/openjdk/bin/java",
    "/usr/local/opt/openjdk/bin/java",
)


@functools.cache
def _java_runtime_available() -> bool:
    for java in (shutil.which("java"), *_JAVA_CANDIDATES):
        if not java or not os.path.exists(java):
            continue
        try:
            ok = (
                subprocess.run(
                    [java, "-version"], capture_output=True, timeout=10
                ).returncode
                == 0
            )
        except Exception:
            continue
        if ok:
            bin_dir = os.path.dirname(java)
            path = os.environ.get("PATH", "")
            if bin_dir not in path.split(os.pathsep):
                os.environ["PATH"] = bin_dir + os.pathsep + path
            return True
    return False


# --- OPSIN als Dauer-JVM -----------------------------------------------------
# py2opsin startet pro Name eine neue JVM (1,9–5,8 s gemessen). Weil OPSIN in
# der Kaskade VOR dem Netz steht, zahlte jeder Trivialname diese Zeit als
# Fehlschlag. Stattdessen läuft die OPSIN-CLI aus dem py2opsin-Paket einmal
# und bekommt die Namen zeilenweise. Protokoll (opsin-cli 2.9.0, gemessen):
# eine Zeile rein → genau eine Zeile raus, pro Zeile geflusht; mit `-n` lautet
# sie "SMILES\tName", bei unparsebarem Namen "\tName" (Grund auf stderr). Das
# Namens-Echo macht jede Antwort ihrer Frage zuordenbar — passt es nicht, ist
# der Strom verrutscht und die JVM wird verworfen. EOF auf stdin beendet sie.

_OPSIN_HANDSHAKE = ("methane", "C")
_OPSIN_START_TIMEOUT = 60.0  # Kaltstart unter Last gemessen bis 12 s
_OPSIN_TIMEOUT = 10.0  # warm < 30 ms; das hier fängt nur Hänger
_OPSIN_MAX_FAILURES = 3
_JVM_FLAGS = (
    "-XX:+IgnoreUnrecognizedVMOptions",  # fremde JVMs scheitern nicht an -XX
    "-XX:TieredStopAtLevel=1",  # nur C1: Kaltstart 2,2 → 1,4 s
    "-Dfile.encoding=UTF-8",  # stdin-Zeichensatz nicht vom (leeren) LANG abhängig
    "-Djava.awt.headless=true",
)


class _OpsinUnavailable(Exception):
    """Die Dauer-JVM ist nicht nutzbar — dieser Aufruf geht den py2opsin-Weg."""


class _OpsinTimeout(Exception):
    """Die JVM lebt, antwortet aber nicht."""


class _OpsinProcess:
    def __init__(self, java: str, jar: str):
        self._proc = subprocess.Popen(
            [java, *_JVM_FLAGS, "-jar", jar, "-osmi", "-n"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            # stderr nie als Pipe: läuft sie voll, blockiert die JVM.
            stderr=subprocess.DEVNULL,
            # Unter Claude Desktop ist die CWD "/" — nichts soll davon abhängen.
            cwd=tempfile.gettempdir(),
        )
        self._lines: queue.Queue[bytes] = queue.Queue()
        threading.Thread(
            target=self._pump, args=(self._proc.stdout, self._lines), daemon=True
        ).start()

    @staticmethod
    def _pump(stdout, lines: "queue.Queue[bytes]") -> None:
        # Leseschleife im eigenen Thread: so bekommt ask() einen portablen
        # Timeout per Queue, ohne select() auf Pipes (geht unter Windows nicht).
        try:
            for line in iter(stdout.readline, b""):
                lines.put(line)
        except (OSError, ValueError):
            pass
        finally:
            lines.put(b"")  # EOF-Marke

    def ask(self, name: str, timeout: float) -> str:
        """SMILES, oder "" wenn OPSIN den Namen nicht parsen kann."""
        try:
            self._proc.stdin.write(name.encode("utf-8") + b"\n")
            self._proc.stdin.flush()
        except (OSError, ValueError) as exc:
            raise _OpsinUnavailable(f"stdin: {exc}") from exc
        try:
            line = self._lines.get(timeout=timeout)
        except queue.Empty:
            raise _OpsinTimeout(name) from None
        # EOF (b"") vor dem Strippen prüfen — sonst sähe ein toter Prozess
        # aus wie "unparsebar" (b"\t…\n").
        if not line:
            raise _OpsinUnavailable("JVM beendet")
        smiles, sep, echoed = (
            line.decode("utf-8", "replace").rstrip("\r\n").partition("\t")
        )
        if not sep or echoed != name:
            raise _OpsinUnavailable(f"Antwort passt nicht zur Frage: {echoed!r}")
        return smiles

    def close(self) -> None:
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.kill()
            self._proc.wait(timeout=5)
        except Exception:
            pass


_opsin_lock = threading.Lock()
_opsin_proc: _OpsinProcess | None = None
_opsin_failures = 0


def _opsin_jar() -> str | None:
    """Das OPSIN-CLI-JAR aus dem py2opsin-Paket — ohne py2opsin zu importieren
    (dessen Import startet ein `java -version`)."""
    spec = importlib.util.find_spec("py2opsin")
    if spec is None or not spec.submodule_search_locations:
        return None
    for folder in spec.submodule_search_locations:
        jars = sorted(
            glob.glob(os.path.join(folder, "opsin-cli-*-jar-with-dependencies.jar"))
        )
        if jars:
            return jars[-1]
    return None


def _start_opsin_process() -> _OpsinProcess:
    # Nach _java_runtime_available() zeigt PATH auf eine funktionierende JRE;
    # trotzdem absolut starten, damit nichts mehr vom PATH abhängt.
    java = shutil.which("java")
    jar = _opsin_jar()
    if not java or not jar:
        raise _OpsinUnavailable("kein java oder kein OPSIN-JAR")
    try:
        proc = _OpsinProcess(java, jar)
    except OSError as exc:
        raise _OpsinUnavailable(f"Start: {exc}") from exc
    name, expected = _OPSIN_HANDSHAKE
    try:
        answer = proc.ask(name, _OPSIN_START_TIMEOUT)
    except (_OpsinTimeout, _OpsinUnavailable) as exc:
        proc.close()
        raise _OpsinUnavailable(f"Handshake: {exc}") from exc
    if answer != expected:
        proc.close()
        raise _OpsinUnavailable(f"Handshake: {answer!r} statt {expected!r}")
    return proc


def _discard_opsin_process() -> None:
    global _opsin_proc
    if _opsin_proc is not None:
        _opsin_proc.close()
        _opsin_proc = None


def _opsin_persistent(name: str) -> str:
    """SMILES oder "" (unparsebar / Hänger). Wirft _OpsinUnavailable, wenn
    dieser Aufruf über py2opsin laufen soll."""
    global _opsin_proc, _opsin_failures
    with _opsin_lock:
        if _opsin_failures >= _OPSIN_MAX_FAILURES:
            raise _OpsinUnavailable("Dauer-JVM aufgegeben")
        try:
            if _opsin_proc is None:
                _opsin_proc = _start_opsin_process()
            smiles = _opsin_proc.ask(name, _OPSIN_TIMEOUT)
        except _OpsinTimeout:
            # Nicht über py2opsin wiederholen — derselbe Name hinge erneut.
            logger.warning(
                "OPSIN answered nothing for %r within %ss", name, _OPSIN_TIMEOUT
            )
            _discard_opsin_process()
            _opsin_failures += 1
            return ""
        except _OpsinUnavailable as exc:
            logger.info("Persistent OPSIN unavailable (%s), using py2opsin", exc)
            _discard_opsin_process()
            _opsin_failures += 1
            raise
        _opsin_failures = 0
        return smiles


def _opsin_reset() -> None:
    """Dauer-JVM beenden und Fehlerzähler zurücksetzen (atexit, Tests)."""
    global _opsin_failures
    with _opsin_lock:
        _discard_opsin_process()
        _opsin_failures = 0


atexit.register(_opsin_reset)


def _opsin_oneshot(name: str) -> str | None:
    """Der alte Weg: py2opsin, eine JVM pro Name. Fallback, wenn die
    Dauer-JVM nicht startet."""
    # Import after the PATH fix in _java_runtime_available(); py2opsin probes
    # `java -version` at import time and warns on every unparseable name.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from py2opsin import py2opsin

        # py2opsin writes its input file to CWD by default; the server's CWD
        # under Claude Desktop is / (not writable).
        tmp_fpath = os.path.join(
            tempfile.gettempdir(), f"py2opsin_input_{os.getpid()}.txt"
        )
        try:
            smiles = py2opsin(name, output_format="SMILES", tmp_fpath=tmp_fpath)
        except Exception:
            # py2opsin's error path is buggy (str + Exception raises TypeError)
            return None
    return smiles if isinstance(smiles, str) else None


def _opsin_lookup(name: str) -> str | None:
    """Parse systematic IUPAC nomenclature offline via OPSIN (rule-based).

    Returns None when no JRE is reachable (graceful degradation to the
    network cascade) or when OPSIN can't parse the name (trivial names).
    """
    if not _java_runtime_available():
        return None
    # Das Zeilenprotokoll verträgt keinen Zeilenumbruch im Namen (er würde
    # jede spätere Antwort verschieben) und keinen leeren Namen.
    if not name.strip() or "\n" in name or "\r" in name:
        return None
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return None
    try:
        smiles = _opsin_persistent(name)
    except _OpsinUnavailable:
        smiles = _opsin_oneshot(name)
    if not smiles:
        return None
    if validate_smiles(smiles) is None:
        return None
    return smiles


def _transliterate(name: str) -> str | None:
    """Replace umlauts with ASCII equivalents. Returns None if no change."""
    result = name.translate(_UMLAUT_MAP)
    return result if result != name else None


def _offline_hint(lead: str = "Offline you can still use") -> str:
    """Was ohne Netz noch funktioniert — OPSIN nur versprechen, wenn Java da ist."""
    if _java_runtime_available():
        return (
            f"{lead} a SMILES string (e.g. 'CC(=O)Oc1ccccc1C(=O)O') or a systematic "
            f"IUPAC name (e.g. '2-methylbutan-2-ol') — OPSIN parses those locally, "
            f"no network needed. Trivial and brand names ('Aspirin') need a database."
        )
    return (
        f"{lead} a SMILES string (e.g. 'CC(=O)Oc1ccccc1C(=O)O'). Systematic IUPAC "
        f"names would work without network too via OPSIN, but that needs a Java "
        f"runtime (macOS: 'brew install openjdk')."
    )


def _name_hint() -> str:
    if _java_runtime_available():
        return (
            "Use the English or IUPAC name (brand names and German trivial names "
            "are often not indexed), a systematic IUPAC name — OPSIN parses those "
            "offline — or pass the SMILES directly."
        )
    return (
        "Use the English or IUPAC name (brand names and German trivial names are "
        "often not indexed) or pass the SMILES directly."
    )


# Bei Umlaut-Namen wird jede Quelle zweimal gefragt (original + transliteriert).
# Für die Meldung zählt pro Quelle nur das schwerwiegendste Ergebnis.
_SEVERITY = {_NOT_FOUND: 0, _SOURCE_ERROR: 1, _UNREACHABLE: 2}


def _summarize(attempts: list) -> str:
    worst: dict[str, _Attempt] = {}
    for attempt in attempts:
        known = worst.get(attempt.source)
        if known is None or _SEVERITY[attempt.status] > _SEVERITY[known.status]:
            worst[attempt.source] = attempt
    return "; ".join(f"{a.source}: {a.detail}" for a in worst.values())


def _resolution_error(name: str, attempts: list) -> NameResolutionError:
    """Aus den Quellen-Ergebnissen die passende Diagnose bauen.

    Vorher bekam jeder Ausfall denselben Rat ("nimm einen anderen Namen") —
    bei Netzausfall ist das eine Fehlersuche, die nie zum Ziel führt.
    """
    summary = _summarize(attempts)
    answered = any(a.status == _NOT_FOUND for a in attempts)
    unreachable = any(a.status == _UNREACHABLE for a in attempts)
    degraded = any(a.status == _SOURCE_ERROR for a in attempts)

    if answered and not (unreachable or degraded):
        kind = "not_found"
        message = (
            f"Could not resolve '{name}' to a structure. Every source answered and "
            f"none knows this name ({summary}). {_name_hint()}"
        )
    elif not answered and unreachable:
        kind = "offline"
        message = (
            f"Could not resolve '{name}': no structure database could be reached "
            f"({summary}). This is a network problem, not a problem with the name — "
            f"renaming will not help. {_offline_hint()}"
        )
    elif not answered and degraded:
        kind = "sources_down"
        message = (
            f"Could not resolve '{name}': the structure databases were reachable but "
            f"returned errors ({summary}). That is on their side, not your input — "
            f"retry in a few minutes. "
            f"{_offline_hint(lead='Independent of any database you can use')}"
        )
    elif attempts:
        kind = "partial"
        hint = _name_hint()
        message = (
            f"Could not resolve '{name}': some sources answered, others did not "
            f"({summary}). The name may well be correct — retry once the connection "
            f"is stable. If it keeps failing: {hint[0].lower()}{hint[1:]}"
        )
    else:
        # Kein Netz-Versuch protokolliert (z.B. alle Lookups gemockt).
        kind = "not_found"
        message = f"Could not resolve '{name}' to a structure. {_name_hint()}"

    return NameResolutionError(message, name=name, kind=kind, attempts=attempts)


@functools.lru_cache(maxsize=512)
def resolve_name(name: str) -> str:
    """Resolve a compound name to SMILES via fallback cascade.

    1. OPSIN (offline, rule-based — systematic IUPAC names, no DB index needed)
    2. PubChem direct (handles English names + many synonyms)
    3. PubChem with umlaut transliteration (ä→ae etc.)
    4. NCI CIR with transliteration
    5. NCI CIR with the original name

    Cached via lru_cache: identische Namen gehen nur einmal ins Netz.
    Wichtig — lru_cache speichert KEINE Ausnahmen: ein Fehlschlag (offline!)
    wird nicht festgeschrieben, sobald das Netz zurück ist greift der nächste
    Versuch wieder. `resolve_name.cache_clear()` leert den Cache.
    """
    report: list[_Attempt] = []

    if smiles := _opsin_lookup(name):
        return smiles

    if smiles := _pubchem_lookup(name, report):
        return smiles

    transliterated = _transliterate(name)
    if transliterated:
        logger.info("Retrying with transliterated name: %r → %r", name, transliterated)
        if smiles := _pubchem_lookup(transliterated, report):
            return smiles
        if smiles := _nci_cir_lookup(transliterated, report):
            return smiles

    if smiles := _nci_cir_lookup(name, report):
        return smiles

    logger.info(
        "Resolution failed for %r: %s",
        name,
        "; ".join(f"{a.source}={a.status}({a.detail})" for a in report)
        or "no attempts",
    )
    raise _resolution_error(name, report)


def resolve(input_str: str) -> tuple[str, Chem.Mol]:
    # Parse-first: anything that RDKit accepts as SMILES IS treated as SMILES.
    # The character heuristic (is_smiles) misses short valid SMILES without
    # special characters — "O" (water) and "CO" (methanol) went down the NAME
    # path, where PubChem's index resolves them to molecular oxygen and COBALT
    # respectively. The tool docstrings promise "SMILES strings are always
    # safe", so SMILES must win for ambiguous short inputs. Real names
    # ("Aspirin") don't parse as SMILES and still take the name path.
    candidate = input_str.strip()
    if " " not in candidate and not _STEREO_PREFIX.match(candidate):
        mol = validate_smiles(candidate)
        if mol is not None:
            return candidate, mol
        if is_smiles(candidate):
            logger.info(
                "Looked like SMILES but failed to parse, trying name resolution: %r",
                input_str,
            )

    smiles = resolve_name(input_str)
    mol = validate_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return smiles, mol
