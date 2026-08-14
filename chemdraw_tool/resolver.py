import functools
import logging
import os
import re
import shutil
import subprocess
import tempfile
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


def _opsin_lookup(name: str) -> str | None:
    """Parse systematic IUPAC nomenclature offline via OPSIN (rule-based).

    Returns None when no JRE is reachable (graceful degradation to the
    network cascade) or when OPSIN can't parse the name (trivial names).
    """
    if not _java_runtime_available():
        return None
    # Import after the PATH fix above; py2opsin probes `java -version` at
    # import time and warns on every unparseable name — keep logs clean.
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
    if not isinstance(smiles, str) or not smiles:
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
