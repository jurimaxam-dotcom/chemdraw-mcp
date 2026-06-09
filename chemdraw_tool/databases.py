import logging
import re
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 10

# --- PubChem ---

_PUBCHEM_PROPS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    "/{name}/property/MolecularFormula,MolecularWeight,IUPACName,"
    "ExactMass,Charge,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "CanonicalSMILES,IsomericSMILES,InChIKey/JSON"
)
_PUBCHEM_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/synonyms/JSON"
)

_PUBCHEM_SMILES_PROPS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles"
    "/property/MolecularFormula,MolecularWeight,IUPACName,"
    "ExactMass,Charge,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "CanonicalSMILES,IsomericSMILES,InChIKey/JSON"
)
_PUBCHEM_SMILES_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/synonyms/JSON"
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


def pubchem_safety(cid: int) -> list[dict]:
    try:
        url = _PUBCHEM_VIEW_URL.format(cid=cid, heading="GHS+Classification")
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        results = []
        _walk_sections(resp.json().get("Record", {}).get("Section", [{}])[0], results)
        return results
    except Exception:
        logger.warning("PubChem safety lookup failed for CID %s", cid, exc_info=True)
        return []


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
        lines = resp.text.strip().split("\n")
        if lines and lines[0]:
            return lines[0].split("\t")[0]
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
