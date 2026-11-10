import logging
import re
import sys
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# (connect, read): ein toter Host scheitert nach 3 s statt nach 10 s. Die
# Panel-Tools ketten mehrere Calls (_get_cid → properties → synonyms → safety);
# mit einem einzigen 10-s-Wert summiert sich das auf einen scheinbar
# eingefrorenen MCP-Server. Read bleibt großzügig — PubChem pug_view rechnet.
_TIMEOUT = (3, 10)


def _log_failure(message: str, *args) -> None:
    """Im except-Block aufrufen: was die Abfrage gekostet hat, passend laut.

    Ein HTTP 404 heißt bei PubChem/ChEBI/KEGG „kennt diesen Stoff nicht“ —
    der Normalfall für ein frei gebautes Peptid. Früher schrieb jeder 404
    einen vollen Traceback als WARNING ins Log (E17, 10.11.2026); jetzt ist es
    eine INFO-Zeile. 5xx, Timeouts und Parsefehler bleiben WARNING mit
    Traceback.
    """
    exc = sys.exc_info()[1]
    response = getattr(exc, "response", None)
    if isinstance(exc, requests.HTTPError) and getattr(response, "status_code", None) == 404:
        logger.info(message + ": not found (HTTP 404)", *args)
        return
    logger.warning(message, *args, exc_info=True)

# --- PubChem ---

_PUBCHEM_PROPS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    "/{name}/property/MolecularFormula,MolecularWeight,IUPACName,"
    "ExactMass,Charge,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "SMILES,InChIKey/JSON"
)
_PUBCHEM_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/synonyms/JSON"
)

_PUBCHEM_SMILES_PROPS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles"
    "/property/Title,MolecularFormula,MolecularWeight,IUPACName,"
    "ExactMass,Charge,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "SMILES,InChIKey/JSON"
)
_PUBCHEM_SMILES_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/synonyms/JSON"
)

# Der InChIKey ist der praezisere Schluessel: Auf ein SMILES antwortet PubChem
# mit IRGENDEINEM Datensatz gleicher Struktur — beim Metformin-SMILES mit
# "[14C]metformin" (CID 152743144) statt mit CID 4091. Ueber den InChIKey steht
# der Stammdatensatz an erster Stelle.
_PUBCHEM_INCHIKEY_PROPS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey"
    "/{key}/property/Title,MolecularFormula,MolecularWeight,IUPACName,"
    "ExactMass,Charge,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "SMILES,InChIKey/JSON"
)
_PUBCHEM_INCHIKEY_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{key}/synonyms/JSON"
)
_PUBCHEM_VIEW_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
    "/{cid}/JSON?heading={heading}"
)


def _get_cid(name: str) -> int | None:
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
        f"/{quote(name, safe='')}/cids/JSON"
    )
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()["IdentifierList"]["CID"][0]
    except Exception:
        _log_failure("PubChem CID lookup failed for %r", name)
        return None


def pubchem_properties(name: str) -> dict | None:
    try:
        resp = requests.get(
            _PUBCHEM_PROPS_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        props = resp.json().get("PropertyTable", {}).get("Properties", [])
        return props[0] if props else None
    except Exception:
        _log_failure("PubChem properties failed for %r", name)
        return None


def pubchem_properties_by_smiles(smiles: str) -> dict | None:
    try:
        resp = requests.post(
            _PUBCHEM_SMILES_PROPS_URL,
            data={"smiles": smiles},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        props = resp.json().get("PropertyTable", {}).get("Properties", [])
        return props[0] if props else None
    except Exception:
        _log_failure("PubChem SMILES properties failed for %r", smiles)
        return None


def pubchem_properties_by_inchikey(key: str) -> dict | None:
    """Properties des Stammdatensatzes zu einem InChIKey (erster Treffer)."""
    try:
        resp = requests.get(
            _PUBCHEM_INCHIKEY_PROPS_URL.format(key=quote(key, safe="")),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        props = resp.json().get("PropertyTable", {}).get("Properties", [])
        return props[0] if props else None
    except Exception:
        _log_failure("PubChem InChIKey properties failed for %r", key)
        return None


# Kurzer Timeout für den Titel im Mechanismus-Panel: ein Etikett darf die Zeichnung nicht um
# 10 s pro Substrat verzögern (der Lesewert von _TIMEOUT ist für pug_view gedacht).
_TITLE_TIMEOUT = (3, 3)
_PUBCHEM_INCHIKEY_TITLE_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{key}/property/Title/JSON"
)


def pubchem_title_by_inchikey(key: str) -> str | None:
    """PubChem-Titel (meist der gebräuchliche Name) des Stammdatensatzes; None bei jedem Fehler."""
    try:
        resp = requests.get(
            _PUBCHEM_INCHIKEY_TITLE_URL.format(key=quote(key, safe="")),
            timeout=_TITLE_TIMEOUT,
        )
        resp.raise_for_status()
        props = resp.json().get("PropertyTable", {}).get("Properties", [])
        return (props[0].get("Title") or None) if props else None
    except Exception:
        _log_failure("PubChem InChIKey title failed for %r", key)
        return None


_CAS_PATTERN = re.compile(r"[0-9]{2,7}-[0-9]{2}-[0-9]")


def _valid_cas(value: str) -> bool:
    # CAS-Prüfziffer: Ziffern von rechts mit 1, 2, … gewichten, modulo 10.
    # https://www.cas.org/ja/training/documentation/chemical-substances/checkdig
    if not _CAS_PATTERN.fullmatch(value):
        return False
    digits = value.replace("-", "")
    return sum(i * int(d) for i, d in enumerate(reversed(digits[:-1]), 1)) % 10 == int(
        digits[-1]
    )


def _cas_from_view(data: dict, cid: int) -> str | None:
    record = data.get("Record", {})
    if record.get("RecordNumber") != cid:
        return None
    sources = {
        ref["ReferenceNumber"]: ref["SourceName"]
        for ref in record.get("Reference", [])
        if ref.get("SourceName") and "ReferenceNumber" in ref
    }
    preferred_refs = {
        ref["ReferenceNumber"]
        for ref in record.get("Reference", [])
        if ref.get("SourceName") == "CAS Common Chemistry" and "ReferenceNumber" in ref
    }
    candidates, preferred = set(), set()
    votes: dict[str, set[str]] = {}

    def walk(sections):
        for section in sections:
            # Nur aktueller CAS-Abschnitt, niemals z. B. „Deprecated CAS“.
            if section.get("TOCHeading") == "CAS":
                for info in section.get("Information", []):
                    for item in info.get("Value", {}).get("StringWithMarkup", []):
                        value = item.get("String", "")
                        if _valid_cas(value):
                            candidates.add(value)
                            source = sources.get(info.get("ReferenceNumber"))
                            if source:
                                votes.setdefault(value, set()).add(source)
                            if info.get("ReferenceNumber") in preferred_refs:
                                preferred.add(value)
            walk(section.get("Section", []))

    walk(record.get("Section", []))
    # CAS selbst hat Vorrang. Falls auch CAS mehrere Werte führt, gewinnt
    # darunter der mit den meisten verschiedenen Quellen; ohne CAS-Quelle
    # gilt dieselbe Regel für alle Kandidaten. Wiederholte Einträge und
    # mehrere Referenzen derselben Quelle zählen nur einmal. Gleichstand: leer.
    choices = preferred or candidates
    if not choices:
        return None
    best = max(len(votes.get(value, set())) for value in choices)
    winners = [value for value in choices if len(votes.get(value, set())) == best]
    return winners[0] if len(winners) == 1 else None


def _synonyms_and_cas(info: dict) -> tuple[str | None, list[str]]:
    syns = info.get("Synonym", [])
    others = [s for s in syns[:10] if not _CAS_PATTERN.fullmatch(s)]
    cid = info.get("CID")
    if isinstance(cid, int) and cid > 0:
        try:
            resp = requests.get(
                _PUBCHEM_VIEW_URL.format(cid=cid, heading="CAS"), timeout=_TIMEOUT
            )
            resp.raise_for_status()
            return _cas_from_view(resp.json(), cid), others
        except Exception:
            _log_failure("PubChem CAS section failed for CID %s", cid)
    # Netz-Ausfall oder alte Antwort ohne CID: nur eine eindeutige gültige
    # Nummer zulassen. Die Synonymreihenfolge ist keine Quellenpriorität.
    candidates = {s for s in syns if _valid_cas(s)}
    return (next(iter(candidates)) if len(candidates) == 1 else None), others


def pubchem_synonyms_by_inchikey(key: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.get(
            _PUBCHEM_INCHIKEY_SYNONYMS_URL.format(key=quote(key, safe="")),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return _synonyms_and_cas(resp.json()["InformationList"]["Information"][0])
    except Exception:
        _log_failure("PubChem InChIKey synonyms failed for %r", key)
        return None, []


def pubchem_synonyms(name: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.get(
            _PUBCHEM_SYNONYMS_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        return _synonyms_and_cas(resp.json()["InformationList"]["Information"][0])
    except Exception:
        _log_failure("PubChem synonyms failed for %r", name)
        return None, []


def pubchem_synonyms_by_smiles(smiles: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.post(
            _PUBCHEM_SMILES_SYNONYMS_URL,
            data={"smiles": smiles},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return _synonyms_and_cas(resp.json()["InformationList"]["Information"][0])
    except Exception:
        _log_failure("PubChem SMILES synonyms failed for %r", smiles)
        return None, []


def _extract_pug_view_values(data: dict, heading: str) -> list[dict]:
    results = []
    try:
        for section in data.get("Record", {}).get("Section", []):
            _walk_sections(section, results)
    except Exception:
        _log_failure(
            "PubChem pug_view parse failed for heading %r", heading
        )
    return results


def _walk_sections(section: dict, results: list):
    if "Information" in section:
        for info in section["Information"]:
            entry = {"name": info.get("Name", section.get("TOCHeading", ""))}
            if "Value" in info:
                val = info["Value"]
                # Leere Listen überspringen: ein IndexError hier warf früher alle
                # schon gesammelten Eigenschaften mit weg (äußeres except).
                if val.get("StringWithMarkup"):
                    entry["value"] = val["StringWithMarkup"][0].get("String", "")
                elif val.get("Number"):
                    nums = val["Number"]
                    unit = val.get("Unit", "")
                    entry["value"] = f"{nums[0]} {unit}".strip()
            if "value" in entry:
                results.append(entry)
    for sub in section.get("Section", []):
        _walk_sections(sub, results)


# --- GHS nach Quelle (Etappe 5) ---
#
# Eigener Parser statt `_walk_sections`: der verliert die ReferenceNumber und
# alle StringWithMarkup-Eintraege nach [0] — bei Koffein standen so vier
# Signalwoerter ohne Herkunft untereinander, NITE-CMC nur mit H301 statt
# H301/H332/H360. `_walk_sections` bleibt fuer die physikalischen Eigenschaften.

_H_STATEMENT = re.compile(
    r"^\s*((?:EU)?H\d{3}[A-Za-z]*(?:\s*\+\s*(?:EU)?H\d{3}[A-Za-z]*)*)"
    r"\s*(?:\((\d+(?:\.\d+)?)\s*%\))?\s*:?\s*(.*)$"
)
# "does not meet GHS hazard criteria for 0.6% (13  of 2217) of reports."
# "... for 89.2% (1840 of 2063) of all reports."
_NOT_CLASSIFIED_NOTE = re.compile(
    r"not meet GHS hazard criteria for\s+(\d+(?:\.\d+)?)\s*%"
    r"(?:\s*\(\s*(\d+)\s+of\s+(\d+)\s*\))?",
    re.IGNORECASE,
)
_NOT_CLASSIFIED_COUNTS = re.compile(
    r"not meeting GHS hazard criteria (?:per|by)\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE
)
_REPORTS_TOTAL = re.compile(r"provided per\s+(\d+)\s+reports", re.IGNORECASE)
_EU_HARMONISED = "1272/2008"
_ECHA = "European Chemicals Agency"


def _ghs_strings(info: dict) -> list[dict]:
    return (info.get("Value") or {}).get("StringWithMarkup") or []


def _ghs_info_items(section: dict):
    """Alle Information-Eintraege unter der GHS-Ueberschrift, in Reihenfolge."""
    yield from section.get("Information", []) or []
    for sub in section.get("Section", []) or []:
        yield from _ghs_info_items(sub)


def _empty_ghs_source(ref, meta: dict) -> dict:
    return {
        "ref": ref,
        "source_name": meta.get("SourceName", "") or "",
        "record_name": meta.get("Name", "") or "",
        "url": meta.get("URL", "") or "",
        "signal": "",
        "hazards": [],
        "pictograms": [],
        "p_codes": [],
        "not_classified": None,
        "reports_total": None,
    }


def _set_not_classified(src: dict, percent=None, reports=None, total=None) -> None:
    # Prozent und Zaehler kommen in zwei Saetzen derselben Quelle — mergen,
    # nie einen fehlenden Wert als 0 eintragen.
    nc = src["not_classified"] or {"percent": None, "reports": None, "total": None}
    for key, val in (("percent", percent), ("reports", reports), ("total", total)):
        if val is not None and nc[key] is None:
            nc[key] = val
    src["not_classified"] = nc


def _parse_ghs_info(src: dict, info: dict) -> None:
    name = info.get("Name", "")
    strings = _ghs_strings(info)
    if name == "Pictogram(s)":
        for s in strings:
            for m in s.get("Markup", []) or []:
                label = m.get("Extra")
                if label and label not in src["pictograms"]:
                    src["pictograms"].append(label)
    elif name == "Signal":
        if strings and not src["signal"]:
            src["signal"] = strings[0].get("String", "").strip()
    elif name == "GHS Hazard Statements":
        for s in strings:
            text = s.get("String", "").strip()
            if text.casefold().startswith("not classified"):
                _set_not_classified(src)
                continue
            m = _H_STATEMENT.match(text)
            if not m:
                continue
            statement = m.group(3).split(" [", 1)[0].strip()
            src["hazards"].append(
                {
                    "code": re.sub(r"\s+", "", m.group(1)),
                    "percent": float(m.group(2)) if m.group(2) else None,
                    "text": statement,
                }
            )
    elif name == "Precautionary Statement Codes":
        for s in strings:
            text = s.get("String", "").split("(click", 1)[0]
            for part in re.split(r",|\band\b", text):
                code = part.strip()
                if code and code not in src["p_codes"]:
                    src["p_codes"].append(code)
    elif name in ("Note", "ECHA C&L Notifications Summary"):
        for s in strings:
            text = s.get("String", "")
            if m := _NOT_CLASSIFIED_NOTE.search(text):
                _set_not_classified(
                    src,
                    percent=float(m.group(1)),
                    reports=int(m.group(2)) if m.group(2) else None,
                    total=int(m.group(3)) if m.group(3) else None,
                )
            elif m := _NOT_CLASSIFIED_COUNTS.search(text):
                _set_not_classified(src, reports=int(m.group(1)), total=int(m.group(2)))
            if (m := _REPORTS_TOTAL.search(text)) and src["reports_total"] is None:
                src["reports_total"] = int(m.group(1))


def parse_ghs(data: dict) -> dict:
    """PUG-View-Antwort (heading=GHS Classification) → Quellen je ReferenceNumber.

    Rueckgabe: {"record_title", "sources": [...]}, Quellen in der Reihenfolge,
    in der PubChem sie zuerst nennt. Prozente gelten nur innerhalb ihrer Quelle.
    """
    record = data.get("Record", {}) or {}
    refs = {
        r.get("ReferenceNumber"): r
        for r in record.get("Reference", []) or []
        if isinstance(r, dict)
    }
    sources: dict = {}
    for section in record.get("Section", []) or []:
        for info in _ghs_info_items(section):
            ref = info.get("ReferenceNumber")
            if ref not in sources:
                sources[ref] = _empty_ghs_source(ref, refs.get(ref, {}))
            _parse_ghs_info(sources[ref], info)

    result = []
    for src in sources.values():
        # Stabil nach Prozent absteigend; ohne Prozent bleibt die PubChem-Reihenfolge.
        if any(h["percent"] is not None for h in src["hazards"]):
            src["hazards"].sort(
                key=lambda h: -(h["percent"] if h["percent"] is not None else -1)
            )
        if (
            src["signal"]
            or src["hazards"]
            or src["pictograms"]
            or src["p_codes"]
            or src["not_classified"]
        ):
            result.append(src)
    return {"record_title": record.get("RecordTitle", "") or "", "sources": result}


def _ghs_name_key(name: str) -> str:
    # ECHA: "Caffeine (EC: 200-362-1)", NITE: "caffeine - FY2008 (New/…)" —
    # verglichen wird der Stoffname davor.
    name = name.split(" (", 1)[0].split(" - ", 1)[0]
    return " ".join(name.split()).casefold()


def order_ghs_sources(sources: list[dict], names: list[str]) -> list[dict]:
    """Leitquelle vorn: EU-harmonisiert, sonst ECHA-Aggregat, sonst die erste.

    Leitquelle wird nur, wessen Stoffname zum gesuchten Stoff passt. Fremd oder
    gar nicht benannte Eintraege (NaCl: ein Azofarbstoff unter der
    EU-Verordnung) wandern ans Ende und tragen einen Hinweis.
    """
    wanted = {_ghs_name_key(n) for n in names if n and n.strip()}
    out = []
    for src in sources:
        s = dict(src)
        key = _ghs_name_key(s.get("record_name", "") or "")
        s["name_matches"] = bool(key) and key in wanted
        if s["name_matches"]:
            s["note"] = ""
        elif not key:
            s["note"] = "record name missing"
        else:
            s["note"] = f"record name differs: {s['record_name']}"
        s["lead"] = False
        out.append(s)

    matching = [s for s in out if s["name_matches"]]
    lead = (
        next((s for s in matching if _EU_HARMONISED in s.get("source_name", "")), None)
        or next((s for s in matching if _ECHA in s.get("source_name", "")), None)
        or (matching[0] if matching else None)
    )
    if lead is None:
        return out
    lead["lead"] = True
    rest = [s for s in out if s is not lead]
    return [lead] + [s for s in rest if s["name_matches"]] + [
        s for s in rest if not s["name_matches"]
    ]


def pubchem_ghs(cid: int) -> dict:
    """GHS-Einstufung je Quelle. status: "ok" | "empty" | "error".

    "empty" (PubChem kennt keine GHS-Daten, 404 oder leere Section) und
    "error" (Abruf gescheitert) sind verschiedene Befunde — beide sind etwas
    anderes als "not classified", das eine Quelle ausdruecklich meldet.
    """
    url = _PUBCHEM_VIEW_URL.format(cid=cid, heading="GHS+Classification")
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        if resp.status_code == 404:
            return {"status": "empty", "record_title": "", "sources": []}
        resp.raise_for_status()
        parsed = parse_ghs(resp.json())
    except Exception:
        _log_failure("PubChem GHS lookup failed for CID %s", cid)
        return {"status": "error", "record_title": "", "sources": []}
    status = "ok" if parsed["sources"] else "empty"
    return {"status": status, **parsed}


def pubchem_physical_properties(cid: int) -> list[dict]:
    try:
        url = _PUBCHEM_VIEW_URL.format(cid=cid, heading="Experimental+Properties")
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        results = []
        _walk_sections(resp.json().get("Record", {}).get("Section", [{}])[0], results)
        return results
    except Exception:
        _log_failure(
            "PubChem physical properties failed for CID %s", cid
        )
        return []


# --- ChEBI ---

_CHEBI_SEARCH_URL = (
    "https://www.ebi.ac.uk/ols4/api/search?q={name}&ontology=chebi&rows=3"
)


def chebi_lookup(name: str) -> dict | None:
    try:
        resp = requests.get(
            _CHEBI_SEARCH_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])
        if not docs:
            return None
        doc = docs[0]
        return {
            "id": doc.get("short_form", ""),
            "label": doc.get("label", ""),
            "description": doc.get("description", [""])[0]
            if doc.get("description")
            else "",
            "obo_id": doc.get("obo_id", ""),
        }
    except Exception:
        _log_failure("ChEBI lookup failed for %r", name)
        return None


# --- KEGG ---

_KEGG_FIND_URL = "https://rest.kegg.jp/find/compound/{name}"
_KEGG_GET_URL = "https://rest.kegg.jp/get/{kegg_id}"
_KEGG_PATHWAY_URL = "https://rest.kegg.jp/link/pathway/{kegg_id}"


def kegg_find(name: str) -> str | None:
    try:
        resp = requests.get(
            _KEGG_FIND_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        # Nur ein Eintrag, der den Namen wörtlich führt: KEGG sortiert unscharf,
        # für „glucose" stand UDP-glucose (C00029) vorn (Messung 30.10.2026).
        wanted = name.strip().lower()
        for line in resp.text.strip().split("\n"):
            kegg_id, _, names = line.partition("\t")
            if any(n.strip().lower() == wanted for n in names.split(";")):
                return kegg_id
        return None
    except Exception:
        _log_failure("KEGG find failed for %r", name)
        return None


def kegg_compound(kegg_id: str) -> dict:
    result = {"id": kegg_id, "names": [], "formula": "", "pathways": []}
    try:
        resp = requests.get(_KEGG_GET_URL.format(kegg_id=kegg_id), timeout=_TIMEOUT)
        resp.raise_for_status()
        current_field = ""
        for line in resp.text.split("\n"):
            if line.startswith("NAME"):
                current_field = "NAME"
                result["names"].append(line[12:].strip().rstrip(";"))
            elif line.startswith("FORMULA"):
                current_field = ""  # single-line field; don't treat the next
                result["formula"] = line[12:].strip()  # line as a NAME continuation
            elif line.startswith(" ") and current_field == "NAME":
                result["names"].append(line.strip().rstrip(";"))
            elif not line.startswith(" "):
                current_field = ""
    except Exception:
        _log_failure("KEGG compound fetch failed for %s", kegg_id)
    try:
        resp = requests.get(_KEGG_PATHWAY_URL.format(kegg_id=kegg_id), timeout=_TIMEOUT)
        resp.raise_for_status()
        for line in resp.text.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    result["pathways"].append(parts[1])
    except Exception:
        _log_failure("KEGG pathway fetch failed for %s", kegg_id)
    return result


# --- UniProt ---

_UNIPROT_SEARCH_URL = (
    "https://rest.uniprot.org/uniprotkb/search"
    "?query={name}+AND+organism_id:9606&size=3&format=json"
    "&fields=accession,protein_name,gene_names,organism_name,ec"
)


def uniprot_search(name: str) -> list[dict]:
    results = []
    try:
        resp = requests.get(
            _UNIPROT_SEARCH_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        for entry in resp.json().get("results", []):
            protein_name = ""
            if rec := entry.get("proteinDescription", {}).get("recommendedName", {}):
                protein_name = rec.get("fullName", {}).get("value", "")
            genes = []
            for gene in entry.get("genes", []):
                if gn := gene.get("geneName", {}).get("value"):
                    genes.append(gn)
            ec_numbers = []
            for ec in (
                entry.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("ecNumbers", [])
            ):
                ec_numbers.append(ec.get("value", ""))
            results.append(
                {
                    "accession": entry.get("primaryAccession", ""),
                    "name": protein_name,
                    "genes": genes,
                    "organism": entry.get("organism", {}).get("scientificName", ""),
                    "ec": ec_numbers,
                }
            )
    except Exception:
        logger.warning("UniProt search failed for %r", name, exc_info=True)
    return results


# --- Protein unter seinem Namen (E6, 10.11.2026) ------------------------------
# uniprot_search oben ist eine Volltextsuche: Für "glucose" liefert sie 3102
# Treffer, für "histidine" 1844, für "ATP" 23105 — "UniProt hat Treffer" heißt
# also nicht "der Name ist ein Protein". Hier zählt nur ein Eintrag, dessen
# empfohlener oder alternativer Name der Eingabe GLEICHT, höchstens mit einer
# Variantenkennung dahinter ("Lysozyme C", "Trypsin-2", "Alcohol dehydrogenase
# 1A") oder als Kette einer Familie ("Hemoglobin subunit alpha", "Collagen
# alpha-1(I) chain"). "Lysozyme-like protein 6", "Histidine decarboxylase",
# "Glucagon receptor" zählen nicht. Kurznamen ("Hb") bleiben draußen.

_UNIPROT_PROTEIN_URL = (
    "https://rest.uniprot.org/uniprotkb/search?query={query}&size=25&format=json"
    "&fields={fields}"
)
_PROTEIN_FIELDS = "accession,protein_name,organism_name,organism_id,length,mass,ft_signal,ft_propep"
_PROTEIN_DETAIL_FIELDS = _PROTEIN_FIELDS + ",ec,cc_function,xref_pdb"
# Der Resolver fragt UniProt nur, wenn schon alles andere gescheitert ist (oder
# bei Enzymnamen) — gemessen 0,2–0,6 s je Antwort; ein toter Host darf die
# Fehlermeldung nicht um 10 s verzögern.
PROTEIN_TIMEOUT = (2, 4)

_HUMAN = 9606
_PEPTIDE_MAX = 20  # = peptide.MAX_RESIDUES; hier ohne Import, databases bleibt RDKit-frei
_VARIANT_MARK = r"(?:-\d+|\s\d+[a-z]?|\s[a-z]|\s[ivx]+)"
_FAMILY_MEMBER = r"\s(?:subunit\s[a-z0-9-]+|alpha-\d+\([ivx]+\)\schain)"
_ANTIBODY = re.compile(r"[a-z]{3,}mab")


def is_antibody_name(name: str) -> bool:
    """INN-Stamm -mab: monoklonaler Antikörper (trastuzumab, adalimumab)."""
    return bool(_ANTIBODY.fullmatch(name.strip().casefold()))


def protein_name_variants(name: str) -> list[str]:
    """Der Name und höchstens eine englische Schreibung deutscher Proteinnamen.

    Gemessen 10.11.2026: UniProt kennt "Lysozym", "Katalase", "Hämoglobin",
    "Kollagen" nicht (0 Treffer). Drei Regeln decken sie: -zym → -zyme,
    ä/ö/ü → e/o/u, k vor a/o/u/l/r → c (Katalase, Kollagen, Glukagon). "kinase"
    bleibt, weil k dort vor i steht. Zusammengesetzte Wörter
    ("Alkoholdehydrogenase") deckt das nicht.
    """
    base = " ".join(name.replace('"', " ").split())
    variant = base.casefold().translate(str.maketrans({"ä": "e", "ö": "o", "ü": "u"}))
    variant = re.sub(r"k(?=[aoulr])", "c", variant)
    variant = re.sub(r"zym\b", "zyme", variant)
    return [base] if variant == base.casefold() else [base, variant]


def _protein_names(entry: dict) -> list[str]:
    desc = entry.get("proteinDescription", {})
    names = [desc.get("recommendedName", {}).get("fullName", {}).get("value", "")]
    names += [alt.get("fullName", {}).get("value", "") for alt in desc.get("alternativeNames", [])]
    return [n for n in names if n]


def _name_match(entry: dict, variants: list[str]) -> tuple[int, str] | None:
    """(Klasse, passender Name): 0 gleich, 1 mit Variantenkennung, 2 Familienkette."""
    best = None
    for name in _protein_names(entry):
        folded = name.casefold()
        for variant in variants:
            stem = re.escape(variant.casefold())
            if folded == variant.casefold():
                rank = 0
            elif re.fullmatch(stem + _VARIANT_MARK, folded):
                rank = 1
            elif re.fullmatch(stem + _FAMILY_MEMBER, folded):
                rank = 2
            else:
                continue
            if best is None or rank < best[0]:
                best = (rank, name)
    return best


def _is_human(entry: dict) -> bool:
    organism = entry.get("organism", {})
    return organism.get("taxonId") == _HUMAN or organism.get("scientificName") == "Homo sapiens"


def _function_text(entry: dict) -> str:
    for comment in entry.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            for text in comment.get("texts", []):
                if value := text.get("value"):
                    return value
    return ""


def _protein_record(entry: dict, matched: str, rank: int) -> dict:
    desc = entry.get("proteinDescription", {})
    sequence = entry.get("sequence", {})
    features = {f.get("type") for f in entry.get("features", [])}
    return {
        "accession": entry.get("primaryAccession", ""),
        "name": desc.get("recommendedName", {}).get("fullName", {}).get("value", "") or matched,
        "matched": matched,
        "family": rank == 2,
        "organism": entry.get("organism", {}).get("scientificName", ""),
        "length": sequence.get("length"),
        "mass": sequence.get("molWeight"),
        # Länge und Masse gelten für die ganze kodierte Sequenz; mit Signal-
        # oder Propeptid ist das reife Protein kürzer (Insulin: 110 → 51 aa).
        "precursor": bool(features & {"Signal", "Propeptide"}),
        "ec": [ec.get("value", "") for ec in desc.get("recommendedName", {}).get("ecNumbers", [])],
        "function": _function_text(entry),
        "pdb": [
            x.get("id", "")
            for x in entry.get("uniProtKBCrossReferences", [])
            if x.get("database") == "PDB"
        ][:3],
    }


def uniprot_protein(
    name: str, *, details: bool = False, timeout=PROTEIN_TIMEOUT, organism: str = ""
) -> dict | None:
    """Bester geprüfter (Swiss-Prot) Eintrag, dessen Name `name` gleicht — sonst None.

    Rang: Mensch vor anderen Organismen, dann gleicher Name vor Variante vor
    Familienkette, dann alphabetisch nach dem passenden Namen ("Hemoglobin
    subunit alpha" vor "… beta", "Trypsin-1" vor "Trypsin-2"). Die übrigen
    Treffer stehen unter "others" (höchstens drei). Netz- und Antwortfehler
    geben None — der Aufrufer behält dann seine bisherige Antwort.
    """
    variants = protein_name_variants(name)
    if not variants[0]:
        return None
    query = "(" + " OR ".join(f'protein_name:"{v}"' for v in variants) + ") AND reviewed:true"
    # E8: Organismus aus der Eingabe ("human lysozyme", "bovine trypsin") —
    # dann zählt dieser Organismus statt des Menschen als bevorzugt.
    if organism:
        query += f' AND organism_name:"{organism}"'
    url = _UNIPROT_PROTEIN_URL.format(
        query=quote(query, safe=""),
        fields=_PROTEIN_DETAIL_FIELDS if details else _PROTEIN_FIELDS,
    )
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        entries = resp.json().get("results", [])
    except Exception:
        logger.warning("UniProt protein lookup failed for %r", name, exc_info=True)
        return None
    hits = []
    for entry in entries:
        if match := _name_match(entry, variants):
            rank, matched = match
            human = True if organism else _is_human(entry)
            # Bis 20 Reste ist es ein Peptid mit lesbarer Strukturformel
            # (Grenze des Sequenz-Parsers): "oxytocin" traf sonst P69043 aus
            # dem Kaninchen (9 aa) und verdrängte ChEBI aus lookup biochem.
            length = entry.get("sequence", {}).get("length")
            if length is not None and length <= _PEPTIDE_MAX:
                continue
            # Andere Organismen nur mit genau diesem Namen: "glucagon" traf sonst
            # "Glucagon-1" aus Xenopus (266 aa), "ferritin" ein E.-coli-Protein.
            if human or rank == 0:
                hits.append(((not human, rank, matched.casefold()), entry, matched, rank))
    if not hits:
        return None
    hits.sort(key=lambda h: h[0])
    _, entry, matched, rank = hits[0]
    record = _protein_record(entry, matched, rank)
    # Weitere Einträge nur, wenn der Name nicht genau einen Eintrag trifft
    # ("trypsin" → Trypsin-1/-2/-3) — und nur aus derselben Organismengruppe.
    others, seen = [], {matched.casefold()}
    for key, e, m, _ in hits[1:]:
        if rank > 0 and key[0] == hits[0][0][0] and m.casefold() not in seen:
            seen.add(m.casefold())
            others.append({"name": m, "accession": e.get("primaryAccession", "")})
    record["others"] = others[:3]
    return record


# --- Genkürzel und Eintrag per Zugangsnummer (E8, 10.11.2026) -----------------
# Bakterielle Gen-/Proteinkürzel ("RecA", "LipA", "GroEL") kennt keine
# Strukturquelle als Stoff; "PabA" löst PubChem sogar als PABA
# (4-Aminobenzoesäure) auf. UniProts gene_exact ist aber
# groß/klein-unempfindlich und trifft Synonyme ("ATP" → atpA, "RecA" → das
# menschliche RAD51, "LacZ" → ein Plasmodium-"LACZ"). Darum zählt nur ein
# Eintrag, dessen Gen (Haupt- oder Synonymname) der Eingabe mit kleinem
# Anfangsbuchstaben GENAU gleicht ("RecA" → recA). Unter den Treffern gewinnt
# der häufigste Proteinname ("LipA": Lipoyl synthase vor den Lipasen, die
# ebenfalls lipA heißen), darin
# E. coli K-12, dann ein Eintrag mit PDB-Struktur, dann UniProts Reihenfolge.
# Gemessen: 0,16–0,42 s je Abfrage.

_GENE_FIELDS = (
    "accession,reviewed,protein_name,gene_names,organism_name,lineage,length,mass,xref_pdb"
)
_GENE_URL = (
    "https://rest.uniprot.org/uniprotkb/search?query={query}&size={size}&format=json"
    "&fields={fields}"
)
_ENTRY_FIELDS = (
    "accession,reviewed,protein_name,gene_primary,organism_name,lineage,length,mass,"
    "sequence,ft_chain,ft_peptide,ft_signal,ft_propep,ec,cc_function,"
    "cc_catalytic_activity,cc_cofactor,xref_pdb"
)
_ENTRY_URL = "https://rest.uniprot.org/uniprotkb/{acc}.json?fields={fields}"

# Mittlere Restmassen (Da) für die Masse der reifen Kette(n) aus der Sequenz.
_RESIDUE_MASS = {
    "A": 71.0788, "R": 156.1875, "N": 114.1038, "D": 115.0886, "C": 103.1388,
    "E": 129.1155, "Q": 128.1307, "G": 57.0519, "H": 137.1411, "I": 113.1594,
    "L": 113.1594, "K": 128.1741, "M": 131.1926, "F": 147.1766, "P": 97.1167,
    "S": 87.0782, "T": 101.1051, "W": 186.2132, "Y": 163.1760, "V": 99.1326,
    "U": 150.0388, "O": 237.3018,
}
_WATER = 18.01528


def chain_mass(sequence: str) -> float:
    """Mittlere Masse einer Kette (Da) — Restmassen plus ein Wasser."""
    return sum(_RESIDUE_MASS.get(c, 110.0) for c in sequence) + _WATER


def _gene_names(entry: dict) -> tuple[list[str], list[str]]:
    primary, synonyms = [], []
    for gene in entry.get("genes", []):
        if value := gene.get("geneName", {}).get("value"):
            primary.append(value)
        synonyms += [s.get("value", "") for s in gene.get("synonyms", [])]
    return primary, synonyms


def _entry_name(entry: dict) -> str:
    desc = entry.get("proteinDescription", {})
    rec = desc.get("recommendedName") or (desc.get("submissionNames") or [{}])[0]
    return rec.get("fullName", {}).get("value", "")


def _domain(entry: dict) -> str:
    lineage = entry.get("organism", {}).get("lineage") or entry.get("lineages") or []
    first = lineage[0] if lineage else ""
    return {"Archaea": "archaeon", "Bacteria": "bacterium", "Eukaryota": "eukaryote"}.get(
        first if isinstance(first, str) else first.get("scientificName", ""), ""
    )


def _has_pdb(entry: dict) -> bool:
    return any(x.get("database") == "PDB" for x in entry.get("uniProtKBCrossReferences", []))


def _gene_search(query: str, timeout, size: int = 25) -> list[dict]:
    url = _GENE_URL.format(query=quote(query, safe=""), size=size, fields=_GENE_FIELDS)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json().get("results", [])


def _gene_record(entry: dict, gene: str) -> dict:
    return {
        "accession": entry.get("primaryAccession", ""),
        "name": _entry_name(entry),
        "gene": gene,
        "organism": entry.get("organism", {}).get("scientificName", ""),
        "domain": _domain(entry),
        "reviewed": "unreviewed" not in entry.get("entryType", "").casefold(),
        "length": entry.get("sequence", {}).get("length"),
        "mass": entry.get("sequence", {}).get("molWeight"),
        "pdb": _has_pdb(entry),
    }


def _pick_gene_entry(entries: list[dict], gene: str) -> tuple[dict | None, list[dict]]:
    """(bester Eintrag, Einträge derselben Namensgruppe) — exakter Genname Pflicht."""
    hits = []
    for order, entry in enumerate(entries):
        primary, synonyms = _gene_names(entry)
        if gene in primary or gene in synonyms:
            hits.append((order, entry))
    if not hits:
        return None, []
    groups: dict[str, list] = {}
    for order, entry in hits:
        groups.setdefault(_entry_name(entry).casefold(), []).append((order, entry))
    group = max(groups.values(), key=lambda g: (len(g), -g[0][0]))

    def rank(item):
        order, entry = item
        organism = entry.get("organism", {}).get("scientificName", "")
        return ("Escherichia coli (strain K12)" not in organism, not _has_pdb(entry), order)

    group.sort(key=rank)
    return group[0][1], [e for _, e in group[1:]]


def gene_symbol_form(symbol: str) -> str:
    """"RecA" → "recA" (bakterielle Genschreibweise: erster Buchstabe klein)."""
    return symbol[:1].lower() + symbol[1:]


def uniprot_gene(symbol: str, organism: str = "", *, timeout=PROTEIN_TIMEOUT) -> dict | None:
    """Protein zu einem Genkürzel — geprüfte Einträge zuerst, sonst None.

    Mit Organismus gelten auch ungeprüfte (TrEMBL-)Einträge; kennt dort kein
    Eintrag das Gen, sucht eine zweite Abfrage nach den Proteinnamen, die das
    Gen anderswo trägt (TrEMBL-Einträge aus Genomprojekten führen oft nur
    einen ORF-Namen). Ohne Organismus nennt "others"
    bis zu drei weitere Organismen mit demselben Gen. Netzfehler → None.
    """
    gene = gene_symbol_form(symbol.strip())
    try:
        if organism:
            org = f' AND organism_name:"{organism}"'
            entries = _gene_search(f'gene_exact:"{gene}"{org}', timeout)
            best, _ = _pick_gene_entry(
                sorted(entries, key=lambda e: "unreviewed" in e.get("entryType", "").casefold()),
                gene,
            )
            found_by = "gene"
            if best is None:
                # Nur die Namen geprüfter Einträge und der häufigste Name — unter
                # einem Genkürzel stehen oft auch fremde Proteine mit demselben
                # Gennamen.
                named = [
                    e for e in _gene_search(f'gene_exact:"{gene}"', timeout)
                    if gene in sum(_gene_names(e), [])
                ]
                if not named:
                    return None
                counts: dict[str, int] = {}
                for e in named:
                    counts[_entry_name(e)] = counts.get(_entry_name(e), 0) + 1
                names = {max(counts, key=counts.get)} | {
                    _entry_name(e) for e in named if "unreviewed" not in e.get("entryType", "").casefold()
                }
                query = "(" + " OR ".join(f'protein_name:"{n}"' for n in sorted(names)) + ")" + org
                candidates = _gene_search(query, timeout, size=10)
                candidates = [e for e in candidates if _entry_name(e) in names]
                if not candidates:
                    return None
                candidates.sort(key=lambda e: "unreviewed" in e.get("entryType", "").casefold())
                best, found_by = candidates[0], "name"
            record = _gene_record(best, gene)
            record["found_by"] = found_by
            record["others"] = []
            return record
        reviewed = _gene_search(f'gene_exact:"{gene}" AND reviewed:true', timeout)
        best, group = _pick_gene_entry(reviewed, gene)
        if best is None:
            unreviewed = _gene_search(f'gene_exact:"{gene}" AND reviewed:false', timeout)
            best, group = _pick_gene_entry(unreviewed, gene)
            if best is None:
                return None
        record = _gene_record(best, gene)
        record["found_by"] = "gene"
        organisms = [e.get("organism", {}).get("scientificName", "") for e in group]
        if len({o.split(" (")[0] for o in organisms + [record["organism"]]}) < 2:
            # Nur ein Organismus geprüft: die anderen stehen in TrEMBL.
            more = _gene_search(f'gene_exact:"{gene}" AND reviewed:false', timeout, size=10)
            organisms += [
                e.get("organism", {}).get("scientificName", "")
                for e in more
                if gene in sum(_gene_names(e), [])
            ]
        others, seen = [], {record["organism"].split(" (")[0]}
        for o in organisms:
            short = o.split(" (")[0]
            if short and short not in seen:
                seen.add(short)
                others.append(short)
        record["others"] = others[:3]
        return record
    except Exception:
        logger.warning("UniProt gene lookup failed for %r", symbol, exc_info=True)
        return None


def mature_chains(entry: dict) -> list[tuple[str, int, int]]:
    """Reife Kette(n) aus den UniProt-Merkmalen: (Name, Start, Ende).

    "Chain"-Merkmale, die in keinem anderen liegen (Trypsin: Serine protease 1
    statt seiner zwei α-Trypsin-Hälften; Chymotrypsin: drei Ketten nebeneinander).
    Ohne Chain die "Peptide"-Merkmale mit "chain" im Namen (Insulin: B- und
    A-Kette, nicht das C-Peptid).
    """
    def spans(kind, need=""):
        out = []
        for f in entry.get("features", []):
            if f.get("type") != kind or need not in f.get("description", "").casefold():
                continue
            loc = f.get("location", {})
            try:
                out.append((f.get("description", ""), int(loc["start"]["value"]), int(loc["end"]["value"])))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    chains = spans("Chain")
    if chains:
        return [
            c for c in chains
            if not any(o is not c and o[1] <= c[1] and c[2] <= o[2] and (o[1], o[2]) != (c[1], c[2]) for o in chains)
        ]
    return spans("Peptide", "chain")


def uniprot_entry(accession: str, *, timeout=PROTEIN_TIMEOUT) -> dict | None:
    """Datenblatt-Fakten eines Eintrags: reife Länge/Masse, EC, Reaktion, Cofaktoren."""
    try:
        resp = requests.get(_ENTRY_URL.format(acc=accession, fields=_ENTRY_FIELDS), timeout=timeout)
        resp.raise_for_status()
        entry = resp.json()
    except Exception:
        logger.warning("UniProt entry fetch failed for %r", accession, exc_info=True)
        return None
    sequence = entry.get("sequence", {})
    seq = sequence.get("value", "")
    mature = mature_chains(entry)
    record = {
        "accession": entry.get("primaryAccession", accession),
        "name": _entry_name(entry),
        "gene": "",
        "organism": entry.get("organism", {}).get("scientificName", ""),
        "domain": _domain(entry),
        "reviewed": "unreviewed" not in entry.get("entryType", "").casefold(),
        "length": sequence.get("length"),
        "mass": sequence.get("molWeight"),
        "mature_length": None,
        "mature_mass": None,
        "ec": [],
        "function": _function_text(entry),
        "reactions": [],
        "cofactors": [],
        "pdb": [
            x.get("id", "")
            for x in entry.get("uniProtKBCrossReferences", [])
            if x.get("database") == "PDB"
        ][:3],
    }
    for gene in entry.get("genes", []):
        if value := gene.get("geneName", {}).get("value"):
            record["gene"] = value
            break
    desc = entry.get("proteinDescription", {}).get("recommendedName", {})
    record["ec"] = [ec.get("value", "") for ec in desc.get("ecNumbers", [])]
    if mature and seq:
        length = sum(end - start + 1 for _, start, end in mature)
        if length != len(seq):
            record["mature_length"] = length
            record["mature_mass"] = round(sum(chain_mass(seq[s - 1 : e]) for _, s, e in mature))
    for comment in entry.get("comments", []):
        kind = comment.get("commentType")
        if kind == "CATALYTIC ACTIVITY":
            reaction = comment.get("reaction", {})
            rhea = next(
                (x.get("id", "") for x in reaction.get("reactionCrossReferences", []) if x.get("database") == "Rhea"),
                "",
            )
            if reaction.get("name"):
                record["reactions"].append({"equation": reaction["name"], "rhea": rhea})
                if not record["ec"] and reaction.get("ecNumber"):
                    record["ec"].append(reaction["ecNumber"])
        elif kind == "COFACTOR":
            record["cofactors"] += [c.get("name", "") for c in comment.get("cofactors", []) if c.get("name")]
    return record

