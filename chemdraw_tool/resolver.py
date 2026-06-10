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


def _pubchem_lookup(name: str) -> str | None:
    try:
        resp = requests.get(_PUBCHEM_URL.format(name=quote(name, safe="")), timeout=10)
        resp.raise_for_status()
        props_list = resp.json().get("PropertyTable", {}).get("Properties", [])
        if not props_list:
            return None
        props = props_list[0]
        return props.get("SMILES") or props.get("IsomericSMILES")
    except Exception:
        return None


def _nci_cir_lookup(name: str) -> str | None:
    try:
        resp = requests.get(_NCI_CIR_URL.format(name=quote(name, safe="")), timeout=10)
        if resp.status_code != 200:
            return None
        smiles = resp.text.strip().split("\n")[0]
        if smiles and validate_smiles(smiles):
            return smiles
        return None
    except Exception:
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


def resolve_name(name: str) -> str:
    """Resolve a compound name to SMILES via fallback cascade.

    1. OPSIN (offline, rule-based — systematic IUPAC names, no DB index needed)
    2. PubChem direct (handles English names + many synonyms)
    3. PubChem with umlaut transliteration (ä→ae etc.)
    4. NCI CIR with transliteration
    """
    if smiles := _opsin_lookup(name):
        return smiles

    if smiles := _pubchem_lookup(name):
        return smiles

    transliterated = _transliterate(name)
    if transliterated:
        logger.info("Retrying with transliterated name: %r → %r", name, transliterated)
        if smiles := _pubchem_lookup(transliterated):
            return smiles
        if smiles := _nci_cir_lookup(transliterated):
            return smiles

    if smiles := _nci_cir_lookup(name):
        return smiles

    raise ValueError(
        f"Could not resolve '{name}' to a SMILES structure. "
        f"Use an English/IUPAC name or provide the SMILES directly."
    )


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
