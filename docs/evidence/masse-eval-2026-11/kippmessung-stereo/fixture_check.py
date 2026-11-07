"""Fixture-Prüfung zur Kippmessung (Chef-Auftrag 07.11.2026, Teil 2).

Je Stoff unabhängige Quellen nach dem vollen InChIKey fragen — PubChem (Name),
ChEMBL (Vorzugsname, Arzneistoff-Record), Wikidata (P235 am Fixture-Item),
KEGG DRUG (Molfile → RDKit-Key). Nur lesen; Fixtures werden nicht geändert.

  uv run python fixture_check.py   → fixture_check.json
"""

import json
import time
from pathlib import Path

import requests
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
OUT = Path(__file__).parent
H = {"User-Agent": "chemdraw-mcp-kippmessung/1.0"}

# Stoff → (Fixture-Key, Wikidata-Item der Fixture, Suchname englisch)
STOFFE = {
    "Nicotin": ("SNICXCGAKADSCV-UHFFFAOYSA-N", "Q12144", "nicotine"),
    "Citral": ("WTEVQBCEXWBHNA-UHFFFAOYSA-N", "Q60176530", "citral"),
    "Lincomycin": ("OJMMVQQUTAEWLP-KIDUDLJLSA-N", None, "lincomycin"),
    "Prostacyclin": ("KAQKFAOMNZTLHT-OZUDYXHBSA-N", None, "epoprostenol"),
    "Vareniclin": ("JQSHBVHOMNKWFT-UHFFFAOYSA-N", None, "varenicline"),
    "Mefloquin": ("XEEQGYMUWCZPDN-UHFFFAOYSA-N", "Q736270", "mefloquine"),
}


def get(url, **kw):
    for _ in range(3):
        try:
            r = requests.get(url, headers=H, timeout=30, **kw)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2)
    return None


def pubchem(name):
    r = get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/InChIKey,IUPACName/JSON"
    )
    return (
        [
            (p["CID"], p["InChIKey"], p.get("IUPACName"))
            for p in r.json()["PropertyTable"]["Properties"]
        ]
        if r
        else None
    )


def chembl(name):
    r = get(
        "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
        params={"pref_name__iexact": name},
    )
    if not r:
        return None
    return [
        (
            m["molecule_chembl_id"],
            (m.get("molecule_structures") or {}).get("standard_inchi_key"),
            m.get("max_phase"),
        )
        for m in r.json()["molecules"]
    ]


def wikidata_item(q):
    r = get(f"https://www.wikidata.org/wiki/Special:EntityData/{q}.json")
    if not r:
        return None
    ent = r.json()["entities"][q]
    keys = [
        c["mainsnak"]["datavalue"]["value"]
        for c in ent["claims"].get("P235", [])
        if "datavalue" in c["mainsnak"]
    ]
    return {"label": ent["labels"].get("en", {}).get("value"), "P235": keys}


def wikidata_by_key(key):
    q = f'SELECT ?i ?l WHERE {{ ?i wdt:P235 "{key}" . OPTIONAL {{ ?i rdfs:label ?l FILTER(lang(?l)="en") }} }}'
    r = get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"})
    if not r:
        return None
    return [
        (b["i"]["value"].rsplit("/", 1)[1], b.get("l", {}).get("value"))
        for b in r.json()["results"]["bindings"]
    ]


def kegg(name):
    r = get(f"https://rest.kegg.jp/find/drug/{name}")
    if not r or not r.text.strip():
        return None
    out = []
    for line in r.text.strip().splitlines()[:4]:
        did, title = line.split("\t", 1)
        did = did.replace("dr:", "")
        m = get(f"https://rest.kegg.jp/get/{did}/mol")
        mol = Chem.MolFromMolBlock(m.text) if m else None
        out.append((did, title, Chem.MolToInchiKey(mol) if mol else None))
    return out


def main():
    erg = {}
    for stoff, (fix, q, name) in STOFFE.items():
        e = {"fixture": fix, "suchname": name}
        e["pubchem"] = pubchem(name)
        e["chembl"] = chembl(name)
        e["kegg"] = kegg(name)
        if q:
            e["wikidata_fixture_item"] = {q: wikidata_item(q)}
        blk1 = fix[:14]
        # alle Wikidata-Items mit demselben Gerüst, flach und definiert
        e["wikidata_fixture_key"] = wikidata_by_key(fix)
        pc_keys = {k for _, k, _ in (e["pubchem"] or []) if k[:14] == blk1}
        e["wikidata_pubchem_keys"] = {
            k: wikidata_by_key(k) for k in pc_keys if k != fix
        }
        erg[stoff] = e
        print(stoff, json.dumps(e, ensure_ascii=False)[:600], flush=True)
        time.sleep(1)
    (OUT / "fixture_check.json").write_text(
        json.dumps(erg, ensure_ascii=False, indent=1)
    )


if __name__ == "__main__":
    main()
