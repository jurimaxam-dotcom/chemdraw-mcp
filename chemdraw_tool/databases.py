import logging
import re
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# (connect, read): ein toter Host scheitert nach 3 s statt nach 10 s. Die
# Panel-Tools ketten mehrere Calls (_get_cid → properties → synonyms → safety);
# mit einem einzigen 10-s-Wert summiert sich das auf einen scheinbar
# eingefrorenen MCP-Server. Read bleibt großzügig — PubChem pug_view rechnet.
_TIMEOUT = (3, 10)

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
        logger.warning("PubChem CID lookup failed for %r", name, exc_info=True)
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
        logger.warning("PubChem properties failed for %r", name, exc_info=True)
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
        logger.warning("PubChem SMILES properties failed for %r", smiles, exc_info=True)
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
        logger.warning("PubChem InChIKey properties failed for %r", key, exc_info=True)
        return None


def pubchem_synonyms_by_inchikey(key: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.get(
            _PUBCHEM_INCHIKEY_SYNONYMS_URL.format(key=quote(key, safe="")),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        syns = resp.json()["InformationList"]["Information"][0].get("Synonym", [])
        cas_list = [s for s in syns[:30] if re.match(r"^\d{2,7}-\d{2}-\d$", s)]
        cas = cas_list[0] if cas_list else None
        others = [s for s in syns[:10] if s not in cas_list]
        return cas, others
    except Exception:
        logger.warning("PubChem InChIKey synonyms failed for %r", key, exc_info=True)
        return None, []


def pubchem_synonyms(name: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.get(
            _PUBCHEM_SYNONYMS_URL.format(name=quote(name, safe="")), timeout=_TIMEOUT
        )
        resp.raise_for_status()
        syns = resp.json()["InformationList"]["Information"][0].get("Synonym", [])
        cas_list = [s for s in syns[:30] if re.match(r"^\d{2,7}-\d{2}-\d$", s)]
        cas = cas_list[0] if cas_list else None
        others = [s for s in syns[:10] if s not in cas_list]
        return cas, others
    except Exception:
        logger.warning("PubChem synonyms failed for %r", name, exc_info=True)
        return None, []


def pubchem_synonyms_by_smiles(smiles: str) -> tuple[str | None, list[str]]:
    try:
        resp = requests.post(
            _PUBCHEM_SMILES_SYNONYMS_URL,
            data={"smiles": smiles},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        syns = resp.json()["InformationList"]["Information"][0].get("Synonym", [])
        cas_list = [s for s in syns[:30] if re.match(r"^\d{2,7}-\d{2}-\d$", s)]
        cas = cas_list[0] if cas_list else None
        others = [s for s in syns[:10] if s not in cas_list]
        return cas, others
    except Exception:
        logger.warning("PubChem SMILES synonyms failed for %r", smiles, exc_info=True)
        return None, []


def _extract_pug_view_values(data: dict, heading: str) -> list[dict]:
    results = []
    try:
        for section in data.get("Record", {}).get("Section", []):
            _walk_sections(section, results)
    except Exception:
        logger.warning(
            "PubChem pug_view parse failed for heading %r", heading, exc_info=True
        )
    return results


def _walk_sections(section: dict, results: list):
    if "Information" in section:
        for info in section["Information"]:
            entry = {"name": info.get("Name", section.get("TOCHeading", ""))}
            if "Value" in info:
                val = info["Value"]
                if "StringWithMarkup" in val:
                    entry["value"] = val["StringWithMarkup"][0].get("String", "")
                elif "Number" in val:
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
        logger.warning("PubChem GHS lookup failed for CID %s", cid, exc_info=True)
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
        logger.warning(
            "PubChem physical properties failed for CID %s", cid, exc_info=True
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
        logger.warning("ChEBI lookup failed for %r", name, exc_info=True)
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
        logger.warning("KEGG find failed for %r", name, exc_info=True)
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
        logger.warning("KEGG compound fetch failed for %s", kegg_id, exc_info=True)
    try:
        resp = requests.get(_KEGG_PATHWAY_URL.format(kegg_id=kegg_id), timeout=_TIMEOUT)
        resp.raise_for_status()
        for line in resp.text.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    result["pathways"].append(parts[1])
    except Exception:
        logger.warning("KEGG pathway fetch failed for %s", kegg_id, exc_info=True)
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
