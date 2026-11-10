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
from typing import NamedTuple
from urllib.parse import quote

import requests
import requests.adapters
from rdkit import Chem, RDLogger

from chemdraw_tool import peptide
from chemdraw_tool.de_names import english_variant, form_variant, salt_variant

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
    `kind` ist einer von 'not_found' | 'offline' | 'sources_down' | 'partial'
    | 'invalid_smiles' (Eingabe ist kaputtes SMILES, die Kaskade wurde nie
    betreten — `attempts` ist dann leer) | 'ambiguous' (Familienname wie
    "xylene": mehrere Isomere, keins gewählt — `candidates` nennt sie).
    """

    def __init__(
        self,
        message: str,
        *,
        name: str,
        kind: str,
        attempts: list,
        candidates: tuple = (),
    ):
        super().__init__(message)
        self.name = name
        self.kind = kind
        self.attempts = attempts
        self.candidates = list(candidates)


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
        if _input_rejected(code):
            return _NOT_FOUND, f"input rejected (HTTP {code})"
        return _SOURCE_ERROR, f"HTTP {code}" if code else "HTTP error"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return _UNREACHABLE, "connection failed"
    if isinstance(exc, requests.exceptions.RequestException):
        return _UNREACHABLE, f"request failed ({type(exc).__name__})"
    return _SOURCE_ERROR, f"unexpected answer ({type(exc).__name__})"


def _input_rejected(code: int | None) -> bool:
    """4xx außer Drosselung/Timeout: die Quelle lehnt DIESE Eingabe ab (zu lang,
    kaputt). Das ist eine Antwort, kein Ausfall — „später nochmal“ wäre falsch."""
    return code is not None and 400 <= code < 500 and code not in (404, 408, 429)


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
        if "/" in name:
            # "(+/-)-ibuprofen": als %2F im Pfad antwortet PubChem 404, im
            # POST-Body trifft derselbe Name (gemessen 09.11.2026).
            resp = requests.post(
                _PUBCHEM_URL.replace("/{name}", ""), data={"name": name}, timeout=_TIMEOUT
            )
        else:
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


class _IPv4Adapter(requests.adapters.HTTPAdapter):
    """Verbindet nur über IPv4: eine IPv4-Quelladresse lässt IPv6-Ziele sofort ausscheiden."""

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = ("0.0.0.0", 0)
        return super().init_poolmanager(*args, **kwargs)


def _nci_get(url: str) -> requests.Response:
    """NCI CIR abfragen, IPv4 zuerst.

    cactus.nci.nih.gov trägt einen AAAA-Eintrag, der nicht antwortet. requests
    kennt kein Happy Eyeballs und wartete bei jedem Aufruf das volle
    Connect-Timeout ab, bevor es auf IPv4 auswich (gemessen 09.11.2026: 3,4 s
    statt 0,35 s; deutsche Namen fragen NCI zweimal). Kommt über IPv4 keine
    Verbindung zustande (reines IPv6-Netz), folgt der normale Weg.
    """
    try:
        with requests.Session() as session:
            session.mount("https://", _IPv4Adapter())
            return session.get(url, timeout=_TIMEOUT)
    except requests.exceptions.Timeout:
        # IPv4 war wählbar, NCI antwortet nur nicht: ein zweiter Versuch würde
        # dasselbe Timeout (und davor das der toten IPv6-Adresse) noch einmal abwarten.
        raise
    except requests.exceptions.ConnectionError:
        return requests.get(url, timeout=_TIMEOUT)


def _nci_cir_lookup(name: str, report: list | None = None) -> str | None:
    if _is_unreachable(report, _NCI):
        return None
    try:
        resp = _nci_get(_NCI_CIR_URL.format(name=quote(name, safe="")))
    except Exception as exc:
        _record(report, _NCI, *_classify_error(exc))
        return None
    if resp.status_code != 200:
        # CIR meldet einen unbekannten Namen als HTTP 500 mit dem Body
        # "Page not found (404)" (belegt 04.11.2026, Masse-Evaluation). Das ist
        # eine Antwort, kein Ausfall — sonst wird jeder deutsche Trivialname,
        # den PubChem nicht kennt, zu "partial" samt falschem Rat "retry".
        unknown = resp.status_code == 404 or (
            resp.status_code == 500 and "page not found" in (resp.text or "").lower()
        )
        rejected = _input_rejected(resp.status_code)
        status = _NOT_FOUND if unknown or rejected else _SOURCE_ERROR
        detail = (
            f"name unknown (HTTP {resp.status_code})"
            if unknown
            else f"input rejected (HTTP {resp.status_code})"
            if rejected
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
            raise _OpsinUnavailable("JVM exited")
        smiles, sep, echoed = (
            line.decode("utf-8", "replace").rstrip("\r\n").partition("\t")
        )
        if not sep or echoed != name:
            raise _OpsinUnavailable(f"answer does not match the query: {echoed!r}")
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
        raise _OpsinUnavailable("no java or no OPSIN JAR")
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


# Lokanten, Klammern, Stereodeskriptoren: der Name ist systematisch gebaut und
# bleibt offline — er geht NIE ins Netz. "N,N-", "O-", "p-" zählen als Lokant.
_SYSTEMATIC_MARK = re.compile(r"\d|[(\[]|(?:^|[\s,-])[NOSPomp]'?(?:,[NOSP]'?)*-")


def _skeleton(smiles: str | None) -> str | None:
    """Erster InChIKey-Block ohne Kristallwasser; Stereo und Ladung zählen nicht.

    Wasser-Komponenten fallen vorher weg: "potassium citrate" baut OPSIN
    wasserfrei, PubChem führt das Monohydrat — ein Formkonflikt, keine
    Gerüstkorrektur. Gegenionen bleiben drin, denn dort hat PubChem gemessen
    recht (Edetat Na2Ca statt NaCa, Goldthiomalat Au/Na statt Au2-Dimer).
    """
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    parts = [f for f in frags if Chem.MolToSmiles(f) != "O"]
    if parts and len(parts) < len(frags):  # reines Wasser bleibt Wasser
        mol = parts[0]
        for frag in parts[1:]:
            mol = Chem.CombineMols(mol, frag)
    return Chem.MolToInchiKey(mol).split("-")[0]


def _opsin_checked(name: str, opsin_smiles: str, report: list) -> str:
    """OPSIN-Treffer für einen Namen ohne Lokanten gegen PubChem prüfen.

    Masse-Eval-Befund 2 (06.11.2026): OPSIN zerlegt Trivialnamen systematisch
    ("tropic-amide", "methyl-dopa", "chloro-xylen-ol") und gewann vor PubChem.
    Gemessen über 233 OPSIN-Treffer: 225 tragen keine Lokanten, darunter alle
    Fehlgriffe; OPSIN und PubChem uneinig bei 7, PubChem richtig bei 6. Der
    siebte ist 'Glycin' — PubChems deutsches Synonym zeigt auf den Fotoentwickler;
    die englische Schreibweise bestätigt OPSIN. Kennt PubChem den Namen nicht
    oder ist es nicht erreichbar, bleibt OPSINs Antwort.

    Salze (Nachbesserung nach Codex-Abnahme, gemessen an 22 Fällen): PubChem
    führt "sodium phosphate" als Na⁺ + PO₄³⁻ (Nettoladung −2) und
    Silikate in anderer Stöchiometrie; jede dieser Kippen war kohlenstofffrei,
    jeder Gewinn organisch. Darum: ohne Kohlenstoff keine Gegenfrage — OPSIN
    baut die Zusammensetzung aus dem Namen, wie vor Befund 2, und das spart den
    Netzaufruf. Eine Ladungsregel (geladene PubChem-Antwort → OPSIN) wurde
    gemessen und verworfen: sie deckt nichts über die Kohlenstoffregel hinaus ab
    und kippt "diiodo-L-tyrosine" (PubChem: richtiges Gerüst als Anion, OPSIN:
    N,N-Diiod) zurück auf den falschen Stoff.
    """
    if _SYSTEMATIC_MARK.search(name):
        return opsin_smiles
    opsin_mol = Chem.MolFromSmiles(opsin_smiles)
    if opsin_mol is None or not any(a.GetAtomicNum() == 6 for a in opsin_mol.GetAtoms()):
        return opsin_smiles
    pubchem = _pubchem_lookup(name, report)
    opsin_key = _skeleton(opsin_smiles)
    if pubchem is None or _skeleton(pubchem) in (None, opsin_key):
        return opsin_smiles
    english = None if form_variant(name) else english_variant(name)
    if english and english != name:
        if _skeleton(_pubchem_lookup(english, report)) == opsin_key:
            return opsin_smiles
    logger.info("OPSIN read %r as %s, PubChem disagrees — using PubChem", name, opsin_smiles)
    return pubchem


# Stereo-Klammerpräfixe "(−)-", "(+)-", "(S)-", "(RS)-", "(E)-", auch gekettet
# ("(S)-(−)-timolol"). Sie legen die Form fest, nie das Gerüst.
_STEREO_PREFIX = re.compile(r"^(?:\((?:[+\-−±]|RS|rs|[RS](?:,\s?[RS])*|[EZ])\)-)+")


def _spelling_variant(name: str) -> str | None:
    """Derselbe Stoff anders geschrieben: englisch und ohne Stereopräfix, oder None."""
    if form_variant(name):
        return None  # Form erst kürzen, wenn alle Quellen das Original verwerfen.
    core = _STEREO_PREFIX.sub("", name)
    variant = english_variant(core) or core
    return variant if variant != name else None


# Drehsinn-Gruppen "(+)-", "(−)-", "(-)-", "(±)-" innerhalb der Präfixkette.
_ROTATION_GROUP = re.compile(r"\((?:[+\-−±])\)-")
_DESCRIPTOR_GROUP = re.compile(r"\((?:RS|rs|[RS](?:,\s?[RS])*)\)-")


def _rotation_variant(name: str) -> str | None:
    """'(S)-(−)-timolol' → '(S)-timolol': Drehsinn weg, nur neben R/S.

    Lauf 9 (06.11.2026): Die Kette aus Deskriptor und Drehsinn kennt weder
    PubChem noch NCI, "(S)-timolol" trifft. Neben R/S ist der Drehsinn
    redundant. Ohne R/S ist er die einzige Stereoangabe und bleibt — und R/S
    bleibt immer, denn das nackte "timolol" ist bei PubChem das S-Enantiomer.
    """
    match = _STEREO_PREFIX.match(name)
    if not match or not _DESCRIPTOR_GROUP.search(match.group()):
        return None
    prefix = _ROTATION_GROUP.sub("", match.group())
    return prefix + name[match.end():] if prefix != match.group() else None


def _parent_skeleton(smiles: str | None) -> str | None:
    """Erster InChIKey-Block der größten organischen Komponente (Stammmolekül).

    Anders als _skeleton fallen hier Gegenionen weg: Dort steht OPSINs Bau aus
    dem Namen gegen PubChem, und die Gegenionen tragen Information (Edetat
    Na2Ca, Goldthiomalat). Hier stehen zwei PubChem-Records für denselben Namen
    gegeneinander, und ob einer als HCl-Salz oder freie Base hinterlegt ist,
    ist Depositor-Form, kein anderer Stoff. Ohne Kohlenstoff → _skeleton.
    """
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    organic = [
        f for f in Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
        if any(a.GetAtomicNum() == 6 for a in f.GetAtoms())
    ]
    if not organic:
        return _skeleton(smiles)
    parent = max(organic, key=lambda f: f.GetNumHeavyAtoms())
    return Chem.MolToInchiKey(parent).split("-")[0]


# Wörter, mit denen ein Name selbst ein Gegenion oder eine Salzform nennt —
# auch angehängt ("Bendamustinhydrochlorid"). Dann ist das Salz gemeint.
_SALT_WORD = re.compile(
    r"(?i)hydro(?:chlorid|bromid|iodid)|chlorid|bromid|[ij]odid|sulfat|sulphat"
    r"|mesy?lat|mesilat|besy?lat|besilat|tosylat|maleat|fumarat|tartrat|citrat"
    r"|acetat|phosphat|nitrat|succinat|lactat|gluconat|natrium|sodium|kalium"
    r"|potassium|calcium|kalzium|magnesium|lithium|ammonium|zink|\beisen"
    r"|ferr|meglumin|salz|hydrat|\b(?:iron|zinc|salt)\b"  # Buspiron ≠ iron, Ameisensäure ≠ Eisen
)


def _same_tautomer(a: str, b: str) -> bool:
    """Gleiches Stammmolekül, nur anders tautomer geschrieben?

    rifabutin (Lauf 9, 06.11.2026): PubChem liefert für "rifabutin" und
    "rifabutine" zwei Tautomere, die die Standard-InChI nicht zusammenführt
    (erster Key-Block verschieden, Formel und /c-Schicht gleich). Ohne diesen
    Vergleich kippte die Gegenprobe auf die Variante. RDKits Kanontautomer kostet
    bei rifabutin ~0,5 s — deshalb nur, wenn die Gerüste schon abweichen.
    """
    from rdkit.Chem.MolStandardize import rdMolStandardize

    keys = []
    for smiles in (a, b):
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        if mol is None:
            return False
        try:
            parent = rdMolStandardize.LargestFragmentChooser().choose(mol)
            canonical = rdMolStandardize.TautomerEnumerator().Canonicalize(parent)
        except Exception:  # RDKit-Randfall: im Zweifel verschieden
            return False
        keys.append(Chem.MolToInchiKey(canonical).split("-")[0])
    return keys[0] == keys[1]


# "D-", "L-", "DL-" am Namensanfang: Form steht im Namen (Groß/klein egal).
_DL_PREFIX = re.compile(r"(?i)^(?:DL|D|L)-")


def _parent_key25(smiles: str | None) -> str | None:
    """Block 1+2 des InChIKeys (Gerüst + Stereo) der Komponente aus _parent_skeleton."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    organic = [
        f for f in Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
        if any(a.GetAtomicNum() == 6 for a in f.GetAtoms())
    ]
    if not organic:
        return _water_free_key25(mol)
    parent = max(organic, key=lambda f: f.GetNumHeavyAtoms())
    return Chem.MolToInchiKey(parent)[:25]


def _water_free_key25(mol) -> str:
    """Block 1+2 desselben Moleküls, das _skeleton verwendet (ohne Kristallwasser)."""
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    parts = [f for f in frags if Chem.MolToSmiles(f) != "O"]
    if parts and len(parts) < len(frags):
        mol = parts[0]
        for frag in parts[1:]:
            mol = Chem.CombineMols(mol, frag)
    return Chem.MolToInchiKey(mol)[:25]


def _n_defined_stereo(smiles: str | None) -> int:
    """Zahl der definierten Stereozentren plus Doppelbindungen (E/Z) im ganzen SMILES."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return 0
    centres = Chem.FindMolChiralCenters(mol, includeUnassigned=False, useLegacyImplementation=False)
    bonds = sum(
        b.GetStereo() not in (Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY)
        for b in mol.GetBonds()
    )
    return len(centres) + bonds


def _components(smiles: str) -> int:
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return len(Chem.GetMolFrags(mol)) if mol is not None else 0


def _pubchem_checked(name: str, smiles: str, report: list) -> tuple[str, str]:
    """PubChem-Direkttreffer gegen die Schreibvariante desselben Namens prüfen.

    Masse-Eval-Befund 3 (06.11.2026): PubChem führt verirrte Depositor-Synonyme.
    "(−)-Ephedrin" trifft genau einen Record, 1-Bromo-3-methyl-5-nitrobenzene
    (CID 104213); "Risperidon" trifft nur CID 44402564, ein Dihydro-Analogon mit
    5 Synonymen. Eine Schreibweise ändert kein Stammmolekül — weicht es zwischen
    Name und Variante ab, ist einer der beiden ein Synonymfehler, und die
    Variante gewinnt (Lauf 5: nie hatte der Originalname recht; Holdout: 3
    behoben, 0 gekippt). Verglichen wird ohne Gegenionen (_parent_skeleton):
    mit ihnen kippte der Holdout Centrophenoxin auf das HCl-Salz der Variante.
    Kennt PubChem die Variante nicht oder ist das Netz weg, bleibt der
    Direkttreffer. Preis: ein Aufruf mehr, nur für Namen mit Variante.

    Salzform-Befund (06.11.2026): Gleiches Stammmolekül, aber der Direkttreffer
    ist ein Salz und die Variante der freie Stoff ("Bendamustin" → HCl,
    "Phenelzin" → Sulfat) → die freie Form, denn ein INN ohne Salzwort meint
    den Stoff selbst. Nennt der Name ein Gegenion (_SALT_WORD), bleibt das Salz.
    Umgekehrt (Centrophenoxin: direkt frei, Variante HCl) bleibt der
    Direkttreffer — die Regel wählt nur die Form ohne Gegenion.

    Stereoform-Befund (Schnitt 3, 07.11.2026): Gleiches Stammmolekül, aber
    Block 1+2 des InChIKeys weichen ab ("Naloxon" ohne C14, "Vareniclin"
    flach) → die Variante, wenn sie mindestens so viele definierte
    Stereoelemente trägt. Nie bei Stereo-/D-/L-Präfix im Namen (die Form steht
    dort im Namen), nie zu mehr Komponenten. Kippmessung über Masse 711 +
    Holdout 684: 0 gekippt, 4 + 6 behoben; ≥ statt > hält Isosorbiddinitrat
    und Vinorelbin, die Zählung schützt Lincomycin/Prostacyclin (direkt
    definiert, Variante flach). Preis: Mefloquin bleibt definiert.

    Rückgabe: (SMILES, Suchname, der es geliefert hat) — für „found as".
    """
    variant = _spelling_variant(name)
    if variant is None:
        return smiles, name
    other = _pubchem_lookup(variant, report)
    other_parent = _parent_skeleton(other)
    if other_parent is None:
        return smiles, name
    same_parent = other_parent == _parent_skeleton(smiles)
    if not same_parent and not _same_tautomer(other, smiles):
        logger.info("PubChem reads %r and %r as different compounds — using %r", name, variant, variant)
        return other, variant
    if (
        same_parent
        and _parent_key25(other) != _parent_key25(smiles)
        and not (_STEREO_PREFIX.match(name) or _DL_PREFIX.match(name))
        and _components(other) <= _components(smiles)
        and _n_defined_stereo(other) >= _n_defined_stereo(smiles)
    ):
        logger.info("PubChem gives %r with at least as much defined stereo as %r — using %r",
                    variant, name, variant)
        return other, variant
    if _components(other) == 1 < _components(smiles) and not _SALT_WORD.search(name):
        logger.info("PubChem gives %r as a salt, %r as the free form — using the free form", name, variant)
        return other, variant
    return smiles, name


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


# --- Kaputtes SMILES erkennen (Etappe 1, 26.10.2026) -------------------------
# Früher ging eine Eingabe, die wie SMILES aussah, aber nicht parste, in die
# Namenskaskade: "c1cccc1" machte NCI still zu Cyclopentan, "C1CCC" bekam einen
# Netz-Rat. Jetzt entscheidet _smiles_fault(), ob die Eingabe SMILES-Schreibweise
# ist. Die Grenze ist eng gezogen, weil ein falsches invalid_smiles einen
# auflösbaren Namen blockiert:
#   - die Eingabe muss vollständig aus SMILES-Token bestehen (Fe, NaCl, Coffein,
#     2-Propanol scheitern daran und bleiben Namen),
#   - sie muss ein eindeutiges SMILES-Merkmal tragen (Klammer, Bindungszeichen,
#     Ringziffer) — "Co"/"Cs" parsen unsanitisiert als C + aromatisches o/s,
#     sind aber Cobalt/Caesium,
#   - Summenformeln ohne H (CO2, N2O, SO2, PCl5) haben eine "offene Ringziffer"
#     wie C1CCC; sie unterscheiden sich durch lauter verschiedene Elemente.

_SMILES_TOKEN = re.compile(
    r"\[[^\[\]]*\]|Cl|Br|[BCNOPSFI]|[bcnops]|\*|%\d\d|\d|[-=#$:/\\.~]|[()]"
)
_SMILES_MARKER = re.compile(r"[()\[\]=#$%/\\\d]")
_FORMULA = re.compile(r"(?:[A-Z][a-z]?\d*)+")
_FORMULA_ELEMENT = re.compile(r"([A-Z][a-z]?)\d*")
_VALENCE_COUNT = re.compile(r", (\d+), is greater than permitted")
# Häufigste Valenzfehler mit eindeutiger geladener Schreibweise.
_CHARGED_FORM = {("N", 4): "[N+]", ("O", 3): "[O+]", ("S", 3): "[S+]"}


def _smiles_tokens(text: str) -> list[tuple[str, int]] | None:
    """(Token, Startindex) — oder None, wenn etwas kein SMILES-Token ist."""
    tokens, pos = [], 0
    while pos < len(text):
        match = _SMILES_TOKEN.match(text, pos)
        if not match:
            return None
        tokens.append((match.group(), pos))
        pos = match.end()
    return tokens


def _is_atom_token(token: str) -> bool:
    return token[0] in "[*" or token[0].isalpha()


def _looks_like_formula(text: str) -> bool:
    """CO2, N2O, PCl5: Summenformel mit Ziffer und jedem Element nur einmal."""
    if not _FORMULA.fullmatch(text) or not any(ch.isdigit() for ch in text):
        return False
    elements = _FORMULA_ELEMENT.findall(text)
    return len(elements) == len(set(elements))


def _replace_token(tokens, index: int, new: str) -> str:
    return "".join(new if i == index else tok for i, (tok, _) in enumerate(tokens))


def _aliphatic(tokens) -> str:
    """Aromatische Kleinbuchstaben außerhalb eckiger Klammern groß schreiben."""
    return "".join(
        tok.upper() if tok in ("b", "c", "n", "o", "p", "s") else tok
        for tok, _ in tokens
    )


def _structure_faults(tokens) -> tuple[list[str], str | None]:
    """Offene Ringe und unbalancierte Klammern — mit Stelle und Vorschlag."""
    paren_faults: list[str] = []
    open_rings: dict[str, int] = {}
    stack: list[int] = []
    for tok, pos in tokens:
        if tok.isdigit() or tok.startswith("%"):
            if tok in open_rings:
                del open_rings[tok]
            else:
                open_rings[tok] = pos
        elif tok == "(":
            stack.append(pos)
        elif tok == ")":
            if stack:
                stack.pop()
            else:
                paren_faults.append(
                    f"unbalanced parenthesis: ')' at character {pos + 1} has no "
                    f"matching '('"
                )
    for pos in stack:
        paren_faults.append(
            f"unbalanced parenthesis: '(' at character {pos + 1} is never closed"
        )
    ring_faults = [
        f"ring bond {digit} opened at character {pos + 1} is never closed"
        for digit, pos in open_rings.items()
    ]
    faults = paren_faults + ring_faults
    suggestion = None
    # Nur bei genau einem offenen Ring ist "Ziffer anhängen" eindeutig — bei
    # zweien ergäbe das Anhängen beider Ziffern eine Bindung mit sich selbst.
    if len(ring_faults) == 1 and not paren_faults:
        text = "".join(tok for tok, _ in tokens)
        (digit,) = open_rings
        suggestion = f"if you meant a ring, close it with the same digit: {text}{digit}"
    return faults, suggestion


def _chemistry_fault(mol, tokens) -> tuple[str, str | None]:
    """Sanitize-Fehler von RDKit in Klartext: Ursache, Stelle, Vorschlag."""
    atoms = [(tok, pos, i) for i, (tok, pos) in enumerate(tokens) if _is_atom_token(tok)]
    problem = Chem.DetectChemistryProblems(mol)[0]
    kind, rdkit_message = problem.GetType(), problem.Message().replace("  ", " ")

    if kind == "AtomValenceException":
        idx = problem.GetAtomIdx()
        tok, pos, tok_index = atoms[idx]
        symbol = mol.GetAtomWithIdx(idx).GetSymbol()
        count = _VALENCE_COUNT.search(rdkit_message)
        bonds = int(count.group(1)) if count else None
        cause = (
            f"valence error at atom {idx + 1} ({symbol}) at character {pos + 1}"
            + (f": {bonds} bonds, more than {symbol} allows" if bonds else "")
            + f" (RDKit: {rdkit_message})"
        )
        charged = _CHARGED_FORM.get((symbol, bonds))
        if charged and not tok.startswith("["):
            return cause, (
                f"if a charged atom is meant, write it in brackets: "
                f"{_replace_token(tokens, tok_index, charged)}"
            )
        return cause, f"check the bonds and branches around atom {idx + 1} ({symbol})"

    if kind == "KekulizeException":
        indices = list(problem.GetAtomIndices())
        symbols = " ".join(mol.GetAtomWithIdx(i).GetSymbol().lower() for i in indices)
        cause = (
            f"the aromatic ring (atoms {', '.join(str(i + 1) for i in indices)}: "
            f"{symbols}) has no valid alternating double-bond pattern "
            f"(RDKit: {rdkit_message})"
        )
        hints = ["benzene is c1ccccc1 (six aromatic atoms)"]
        if any(mol.GetAtomWithIdx(i).GetSymbol() == "N" for i in indices):
            hints.append("an aromatic nitrogen carrying H is written [nH], as in c1cc[nH]c1")
        hints.append(f"for the saturated ring write uppercase: {_aliphatic(tokens)}")
        return cause, "; ".join(hints)

    if kind == "AtomKekulizeException":
        idx = problem.GetAtomIdx()
        _, pos, _ = atoms[idx]
        cause = (
            f"atom {idx + 1} (character {pos + 1}) is written aromatic (lowercase) "
            f"outside a ring (RDKit: {rdkit_message})"
        )
        return cause, f"write it uppercase: {_aliphatic(tokens)}"

    return f"RDKit: {rdkit_message}", None


def _smiles_fault(text: str) -> str | None:
    """Klartext-Diagnose, wenn `text` kaputtes SMILES ist — sonst None (Name).

    Wird nur für Eingaben aufgerufen, die als SMILES schon gescheitert sind.
    """
    tokens = _smiles_tokens(text)
    if tokens is None or not _SMILES_MARKER.search(text) or _looks_like_formula(text):
        return None

    mol = Chem.MolFromSmiles(text, sanitize=False)
    suggestion = None
    if mol is not None and Chem.DetectChemistryProblems(mol):
        cause, suggestion = _chemistry_fault(mol, tokens)
    else:
        faults, suggestion = _structure_faults(tokens)
        cause = "; ".join(faults) if faults else "RDKit reports a SMILES syntax error"

    message = (
        f"Could not read '{text}' as SMILES: {cause}. It was not looked up as a "
        f"compound name because it is written in SMILES notation."
    )
    if suggestion:
        message += f" Suggestion (nothing was drawn): {suggestion}."
    return message + " To search by name instead, type the compound name."


# --- Mehrdeutige Familiennamen (Etappe 2, 26.10.2026) -------------------------
# "xylene", "Kresol", "toluidine" nennen keinen Stoff, sondern eine Familie.
# OPSIN wählte dafür still das ortho-Isomer, "Glucose" wurde die offenkettige
# Aldehydform — Zeichnung, Formel und Datenblatt passten dann perfekt zum
# falschen Stoff. Deshalb stehen die Familien hier fest, geprüft NACH dem
# SMILES-Weg und VOR OPSIN, mit fertigem SMILES je Kandidat (am 26.10.2026 bei
# PubChem nachgeschlagen, InChIKeys in tests/test_ambiguous_names.py gepinnt).
# Verglichen wird der ganze Name (strip + casefold), nie ein Teilstring:
# "o-Xylol", "m-cresol", "1-Butanol", "D-Glucose" lösen weiter normal auf.


class IsomerCandidate:
    """Ein Stoff, den ein Familienname meinen kann."""

    __slots__ = ("label", "name", "smiles")

    def __init__(self, label: str, name: str, smiles: str):
        self.label = label  # kurz, wie im Hörsaal: "o-xylene"
        self.name = name  # ausgeschrieben (IUPAC): "1,2-dimethylbenzene"
        self.smiles = smiles

    def __repr__(self) -> str:
        return f"IsomerCandidate({self.label!r}, {self.smiles!r})"

    def __eq__(self, other) -> bool:
        return isinstance(other, IsomerCandidate) and (
            self.label, self.name, self.smiles
        ) == (other.label, other.name, other.smiles)


def _family(*members: tuple[str, str, str]) -> tuple[IsomerCandidate, ...]:
    return tuple(IsomerCandidate(*m) for m in members)


_XYLENE = _family(
    ("o-xylene", "1,2-dimethylbenzene", "Cc1ccccc1C"),
    ("m-xylene", "1,3-dimethylbenzene", "Cc1cccc(C)c1"),
    ("p-xylene", "1,4-dimethylbenzene", "Cc1ccc(C)cc1"),
)
_CRESOL = _family(
    ("o-cresol", "2-methylphenol", "Cc1ccccc1O"),
    ("m-cresol", "3-methylphenol", "Cc1cccc(O)c1"),
    ("p-cresol", "4-methylphenol", "Cc1ccc(O)cc1"),
)
_TOLUIDINE = _family(
    ("o-toluidine", "2-methylaniline", "Cc1ccccc1N"),
    ("m-toluidine", "3-methylaniline", "Cc1cccc(N)c1"),
    ("p-toluidine", "4-methylaniline", "Cc1ccc(N)cc1"),
)
_BUTANOL = _family(
    ("1-butanol", "butan-1-ol", "CCCCO"),
    # Ohne Stereo-Angabe: "2-Butanol" meint das Racemat.
    ("2-butanol", "butan-2-ol", "CCC(C)O"),
    ("isobutanol", "2-methylpropan-1-ol", "CC(C)CO"),
    ("tert-butanol", "2-methylpropan-2-ol", "CC(C)(C)O"),
)
# Glucose ist keine Stellungsfamilie: offenkettig gegen die beiden Anomere.
_GLUCOSE = _family(
    (
        "D-glucose (open chain)",
        "(2R,3S,4R,5R)-2,3,4,5,6-pentahydroxyhexanal",
        "O=C[C@H](O)[C@@H](O)[C@H](O)[C@H](O)CO",
    ),
    (
        "α-D-glucopyranose",
        "alpha-D-glucopyranose",
        "OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@@H]1O",
    ),
    (
        "β-D-glucopyranose",
        "beta-D-glucopyranose",
        "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O",
    ),
)

_AMBIGUOUS_FAMILIES: dict[str, tuple[IsomerCandidate, ...]] = {
    **dict.fromkeys(("xylene", "xylenes", "xylol", "xylole"), _XYLENE),
    **dict.fromkeys(("cresol", "cresols", "kresol", "kresole"), _CRESOL),
    **dict.fromkeys(("toluidine", "toluidines", "toluidin"), _TOLUIDINE),
    **dict.fromkeys(("butanol", "butanols", "butanole"), _BUTANOL),
    **dict.fromkeys(("glucose", "glukose"), _GLUCOSE),
}

# Die sieben zweiatomigen Elemente: Wer "oxygen" schreibt, meint O₂ — gemessen
# 09.11.2026 lag jede Quelle anders daneben. OPSIN liest die englischen Namen
# als Atom ([O], [Cl] …) und wird für kohlenstofffreie Treffer nicht gegen
# PubChem geprüft (_opsin_checked); PubChem führt "Stickstoff" als [NH]
# (CID 5460607); "Iod" kennt PubChem nicht, NCI liefert Iodid [I-]. Nur exakte
# ganze Namen — "oxygen atom", "Natrium", "ozone" gehen weiter in die Kaskade.
_DIATOMIC_ELEMENTS: dict[str, str] = {
    **dict.fromkeys(("hydrogen", "wasserstoff"), "[HH]"),
    **dict.fromkeys(("nitrogen", "stickstoff"), "N#N"),
    **dict.fromkeys(("oxygen", "sauerstoff"), "O=O"),
    **dict.fromkeys(("fluorine", "fluor"), "FF"),
    **dict.fromkeys(("chlorine", "chlor"), "ClCl"),
    **dict.fromkeys(("bromine", "brom"), "BrBr"),
    **dict.fromkeys(("iodine", "iod", "jod"), "II"),
}

# Das Einzelatom derselben Elemente: "oxygen atom" / "atomic oxygen". PubChem
# führt "oxygen atom" als Synonym von Wasser (CID 962) und "hydrogen atom" als
# [1HH]; OPSIN kennt beide Wendungen nicht (gemessen 10.11.2026). Nur Englisch
# und nur genau diese zwei Formen — alles andere geht durch die Kaskade.
_ATOMIC_ELEMENTS: dict[str, str] = {
    "hydrogen": "[H]", "nitrogen": "[N]", "oxygen": "[O]", "fluorine": "[F]",
    "chlorine": "[Cl]", "bromine": "[Br]", "iodine": "[I]",
}


def _atom_phrase_key(name: str) -> str | None:
    """Element aus "<element> atom" bzw. "atomic <element>", sonst None."""
    words = name.casefold().split()
    if len(words) == 2 and words[1] == "atom":
        return words[0]
    if len(words) == 2 and words[0] == "atomic":
        return words[1]
    return None


def ambiguous_candidates(name: str) -> list[IsomerCandidate] | None:
    """Die Kandidaten, wenn `name` ein bekannter Familienname ist — sonst None."""
    family = _AMBIGUOUS_FAMILIES.get(name.strip().casefold())
    return list(family) if family else None


def _ambiguous_error(name: str, candidates: list[IsomerCandidate]) -> NameResolutionError:
    listing = ", ".join(f"{c.label} ({c.smiles})" for c in candidates)
    message = (
        f"'{name.strip()}' is ambiguous: it names {len(candidates)} different "
        f"compounds — {listing}. Nothing was drawn for it. Pass the specific "
        f"isomer by name or by its SMILES."
    )
    return NameResolutionError(
        message, name=name, kind="ambiguous", attempts=[], candidates=candidates
    )


# „X zwitterion“ (E4, 09.11.2026): PubChem führt „alanine zwitterion“ beim
# Racemat, „Alanin Zwitterion“ kennt keine Quelle, „Ala zwitterion“ wird bei
# PubChem das Tripeptid Ala-Leu-Ala. Darum: Grundname durch die Kaskade, dann
# genau EIN α-Aminosäure-Motiv umladen (α-NH → NH3+, α-COOH → COO-). Kein oder
# mehr als ein Motiv (Cystin) → die alte Kaskade mit dem ganzen Namen.
_ZWITTERION = re.compile(r"(.+?)[\s-]+zwitterion", re.IGNORECASE)
_ALPHA_AMINO_ACID = Chem.MolFromSmarts(
    "[NX3;H2,H1;+0;!$(N[C,S]=[O,S,N])][CX4][CX3](=O)[OX2H1]"
)


def _zwitterion(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    matches = mol.GetSubstructMatches(_ALPHA_AMINO_ACID) if mol else ()
    if len(matches) != 1:
        return None
    nitrogen, _, _, _, oxygen = matches[0]
    mol = Chem.RWMol(mol)
    mol.GetAtomWithIdx(nitrogen).SetFormalCharge(1)
    mol.GetAtomWithIdx(oxygen).SetFormalCharge(-1)
    for idx in (nitrogen, oxygen):
        atom = mol.GetAtomWithIdx(idx)
        atom.SetNumExplicitHs(0)
        atom.SetNoImplicit(False)
    Chem.SanitizeMol(mol)
    return Chem.MolToSmiles(mol)


class Resolution(NamedTuple):
    """Ergebnis der Namenskaskade.

    found_as: die Schreibweise, unter der der Stoff tatsächlich gefunden wurde,
    wenn sie nicht die Eingabe ist (englische Variante, Transliteration,
    Salzform-/Synonymregel) — sonst "". Damit sieht der Nutzer einen Umweg und
    kann einen falschen Treffer erkennen ("found as Dexamethasone").
    """

    smiles: str
    found_as: str = ""


def _found_as(name: str, query: str) -> str:
    """Suchname als Hinweis — leer, wenn er nur in Groß/Kleinschreibung abweicht."""
    return "" if query.strip().casefold() == name.strip().casefold() else query


def resolve_name(name: str) -> str:
    """Resolve a compound name to SMILES (see resolve_name_route)."""
    return resolve_name_route(name).smiles


_ROUTE_CACHE_MAX = 512
_ROUTE_CACHE: dict[str, Resolution] = {}
# Sync-Tools laufen in Worker-Threads (anyio.to_thread): Einfügen und Verdrängen
# müssen zusammen passieren, lru_cache brachte diese Sperre selbst mit.
_ROUTE_CACHE_LOCK = threading.Lock()


def resolve_name_route(name: str) -> Resolution:
    """Kaskade mit Cache: identische Namen gehen nur einmal ins Netz.

    Gecacht wird nur, was alle befragten Quellen beantwortet haben. War eine
    Quelle nicht erreichbar oder gestört, ist das Ergebnis ein Notbehelf (OPSIN
    ohne PubChem-Gegenprobe liest "methyldopa" als N-Methyl-DOPA) — er darf im
    tagelang laufenden Desktop-Prozess nicht stehen bleiben, wenn das Netz
    zurück ist (Befund 09.11.2026; lru_cache hielt ihn bis zum Prozessende).
    Ausnahmen werden wie zuvor nie gecacht.
    """
    cached = _ROUTE_CACHE.get(name)
    if cached is not None:
        return cached
    report: list[_Attempt] = []
    result = _resolve_name_route(name, report)
    if not any(a.status in (_UNREACHABLE, _SOURCE_ERROR) for a in report):
        with _ROUTE_CACHE_LOCK:
            while len(_ROUTE_CACHE) >= _ROUTE_CACHE_MAX:
                _ROUTE_CACHE.pop(next(iter(_ROUTE_CACHE)), None)  # ältester Eintrag
            _ROUTE_CACHE[name] = result
    return result


def _resolve_name_route(name: str, report: list) -> Resolution:
    """Resolve a compound name to SMILES via fallback cascade.

    0. Known family names ("xylene", "Glucose") raise kind="ambiguous";
       names of the seven diatomic elements ("oxygen", "Stickstoff") → X₂;
       peptides: "peptide:AGS" (one-letter) and "Ala-Gly-Ser" (three-letter)
       are built offline (chemdraw_tool.peptide)
    1. OPSIN (offline, rule-based — systematic IUPAC names, no DB index needed)
    2. PubChem direct (handles English names + many synonyms)
    3. PubChem with umlaut transliteration (ä→ae etc.)
    4. NCI CIR with transliteration
    5. NCI CIR with the original name
    6. Full cascade for a measured form suffix (Anhydrat / freie Säure / A+B)
    7. PubChem with the English spelling (de_names.english_variant)
    8. PubChem with only the counter-ion in English (de_names.salt_variant)
    9. PubChem without the rotation sign beside R/S ("(S)-(−)-x" → "(S)-x")

    Der Cache sitzt in resolve_name_route; `report` sammelt, was jede Quelle
    geantwortet hat. `resolve_name.cache_clear()` leert den Cache.
    """
    # Familienname zuerst: OPSIN würde ihn still zum ortho-Isomer machen.
    if candidates := ambiguous_candidates(name):
        raise _ambiguous_error(name, candidates)

    # Elementname eines zweiatomigen Elements: das Molekül, offline.
    if smiles := _DIATOMIC_ELEMENTS.get(name.strip().casefold()):
        return Resolution(smiles)
    if smiles := _ATOMIC_ELEMENTS.get(_atom_phrase_key(name) or ""):
        return Resolution(smiles)

    # Peptide (E4): Einbuchstabencode nur hinter "peptide:", Dreibuchstaben-
    # Sequenzen offline. Eine Sequenz mit unbaubarem Rest ("Val-Cit") fragt
    # erst die Kaskade — die Peptid-Meldung kommt nur, wenn die nichts findet.
    if (sequence := peptide.one_letter_sequence(name)) is not None:
        try:
            return Resolution(peptide.one_letter_smiles(sequence))
        except peptide.PeptideSequenceError as exc:
            raise NameResolutionError(
                str(exc), name=name, kind="not_found", attempts=[]
            ) from exc
    peptide_fault = ""
    try:
        if smiles := peptide.three_letter_smiles(name):
            return Resolution(smiles)
    except peptide.PeptideSequenceError as exc:
        peptide_fault = str(exc)

    if match := _ZWITTERION.fullmatch(name.strip()):
        try:
            base = _resolve_name_route(match.group(1), report)
        except NameResolutionError:
            base = None
        if base and (smiles := _zwitterion(base.smiles)):
            return Resolution(smiles, base.found_as)

    # OPSIN liest den Namen selbst; gewinnt PubChem die Gegenprobe, war es
    # derselbe Name — beides ist kein Umweg, also kein found_as.
    if smiles := _opsin_lookup(name):
        return Resolution(_opsin_checked(name, smiles, report))

    if smiles := _pubchem_lookup(name, report):
        smiles, query = _pubchem_checked(name, smiles, report)
        return Resolution(smiles, _found_as(name, query))

    transliterated = _transliterate(name)
    if transliterated:
        logger.info("Retrying with transliterated name: %r → %r", name, transliterated)
        if smiles := _pubchem_lookup(transliterated, report):
            return Resolution(smiles, _found_as(name, transliterated))
        if smiles := _nci_cir_lookup(transliterated, report):
            return Resolution(smiles, _found_as(name, transliterated))

    if smiles := _nci_cir_lookup(name, report):
        return Resolution(smiles)

    # Nur nach erfolglosem Original und vor der reinen PubChem-Übersetzung:
    # Citral A+B braucht OPSIN ohne E/Z, PubChem allein liefert Geranial (E).
    if base := form_variant(name):
        normalized = _resolve_name_route(base, report)
        return Resolution(normalized.smiles, _found_as(name, normalized.found_as or base))

    # Ganz hinten, damit kein heute aufgelöster Name einen anderen Weg nimmt.
    # Aus dem Original gebaut — "Maleinsaeure" hat kein "-säure" mehr.
    if (english := english_variant(name)) and english != transliterated:
        logger.info("Retrying with English spelling: %r → %r", name, english)
        if smiles := _pubchem_lookup(english, report):
            return Resolution(smiles, _found_as(name, english))

    # Salzname, dessen INN PubChem nur ohne Endungs-e kennt ("Cefalotin sodium",
    # nicht "Cefalotine sodium"; Salznamen-Messung 06.11.2026). Nur Namen mit
    # Gegenion am Ende, und nur wenn die Schreibweise neu ist.
    if salt := salt_variant(name):
        logger.info("Retrying with English counter-ion: %r → %r", name, salt)
        if smiles := _pubchem_lookup(salt, report):
            return Resolution(smiles, _found_as(name, salt))

    # Drehsinn neben R/S ("(S)-(−)-timolol"), ganz hinten aus demselben Grund.
    if rotation := _rotation_variant(name):
        logger.info("Retrying without the rotation sign: %r → %r", name, rotation)
        if smiles := _pubchem_lookup(rotation, report):
            return Resolution(smiles, _found_as(name, rotation))

    logger.info(
        "Resolution failed for %r: %s",
        name,
        "; ".join(f"{a.source}={a.status}({a.detail})" for a in report)
        or "no attempts",
    )
    error = _resolution_error(name, report)
    if peptide_fault and error.kind == "not_found":
        raise NameResolutionError(
            f"Could not resolve '{name.strip()}': no database knows this name, and "
            f"{peptide_fault[0].lower()}{peptide_fault[1:]}",
            name=name, kind="not_found", attempts=report,
        )
    raise error


# Tests und Messskripte leeren den Cache über resolve_name.
resolve_name.cache_clear = _ROUTE_CACHE.clear  # type: ignore[attr-defined]
resolve_name_route.cache_clear = _ROUTE_CACHE.clear  # type: ignore[attr-defined]


class Resolved(tuple):
    """(smiles, mol) wie immer — plus .found_as aus der Kaskade.

    Ein Tupel, damit `smiles, mol = resolve(x)` bei allen Aufrufern und
    Test-Attrappen gleich bleibt; wer den Umweg zeigen will, liest
    `getattr(r, "found_as", "")` (Attrappen liefern schlichte Tupel).
    """

    found_as: str

    def __new__(cls, smiles: str, mol: Chem.Mol, found_as: str = ""):
        self = super().__new__(cls, (smiles, mol))
        self.found_as = found_as
        return self


def resolve(input_str: str) -> Resolved:
    # Parse-first: anything that RDKit accepts as SMILES IS treated as SMILES.
    # The character heuristic (is_smiles) misses short valid SMILES without
    # special characters — "O" (water) and "CO" (methanol) went down the NAME
    # path, where PubChem's index resolves them to molecular oxygen and COBALT
    # respectively. The tool docstrings promise "SMILES strings are always
    # safe", so SMILES must win for ambiguous short inputs. Real names
    # ("Aspirin") don't parse as SMILES and still take the name path.
    candidate = input_str.strip()
    if not candidate:
        # MolFromSmiles("") ist ein gültiges leeres Molekül — ohne diese Zeile
        # galt eine leere Eingabe als aufgelöst (Datenblatt ohne Atome).
        raise NameResolutionError(
            "No compound was given. Pass a name or a SMILES string.",
            name=input_str, kind="not_found", attempts=[],
        )
    if " " not in candidate and not _STEREO_PREFIX.match(candidate):
        mol = validate_smiles(candidate)
        if mol is not None:
            return Resolved(candidate, mol)
        # Kaputtes SMILES bekommt eine eigene Diagnose und geht NIE in die
        # Namenskaskade — dort würde es still zu einem anderen Stoff (NCI:
        # "c1cccc1" → Cyclopentan) oder bekäme einen falschen Rat.
        if fault := _smiles_fault(candidate):
            raise NameResolutionError(
                fault, name=input_str, kind="invalid_smiles", attempts=[]
            )

    smiles, found_as = resolve_name_route(candidate)
    mol = validate_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return Resolved(smiles, mol, found_as)
