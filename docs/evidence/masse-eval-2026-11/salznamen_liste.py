"""Deutsche Salznamen aus Wikidata (06.11.2026): Messliste für den Salznamen-Fix.

Stoffliste und Holdout aus Lauf 8 enthalten fast keine deutschen zusammengesetzten
Salznamen ("Metforminhydrochlorid"): Wikidata führt dort die freie Base. Diese
Liste holt sie gezielt: deutsches Label = Wort + Gegenion am Ende (auch mit
Leerzeichen/Bindestrich), genau ein InChIKey, und laut Wikidata-SMILES (P233)
wirklich ein Salz — mehrere Komponenten, die größte mit ≥ 8 C. Das schließt
Ester ("Retinylacetat") und Säurechloride ("Benzoylchlorid") aus, die auch auf
-acetat/-chlorid enden. Erwartung = Wikidata P235, nicht unser Code.

Aufteilung fest nach Item-ID (Q-Nummer gerade = Einstellen, ungerade = Holdout),
damit die Regel nie an den Namen geprüft wird, an denen sie entstand.

    uv run python docs/evidence/masse-eval-2026-11/salznamen_liste.py   # Netz, ~1 min
"""

import json
import time
from collections import defaultdict
from pathlib import Path

import requests
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
HIER = Path(__file__).parent
OUT = HIER / "salznamen_liste.json"
URL = "https://query.wikidata.org/sparql"
KOPF = {"User-Agent": "chemdraw-mcp-masse-eval/1.0"}

# Gruppen: mit allen Endungen auf einmal bricht Wikidata den Strom ab (502/504).
# Der SMILES-Filter (Punkt = mehrere Komponenten) zuerst macht den Label-Scan klein.
ENDUNGEN = (
    "(di)?hydrochlorid|hydrobromid|(hydrogen)?tartrat",
    "besilat|mesilat|tosilat|maleat|fumarat|succinat",
    "natrium|kalium|citrat|lactat|gluconat",
    "sulfat|acetat|phosphat",
    "bromid|iodid|chlorid|nitrat",
)
LABELS = """
SELECT ?item ?label ?ik ?s WHERE {
  ?item wdt:P233 ?s . FILTER(CONTAINS(?s, "."))
  ?item wdt:P235 ?ik ; rdfs:label ?label . FILTER(LANG(?label) = "de")
  FILTER(REGEX(?label, "^[A-Z][a-zäöü]+[ -]?(?i:%s)$"))
}
"""


ROH = HIER.parents[2] / ".cache" / "salznamen_wikidata.json"  # Zwischenstand: Wikidata bricht oft mit 502/504 ab
cache = json.loads(ROH.read_text()) if ROH.exists() else {}


def frage(query):
    if query in cache:
        return cache[query]
    for versuch in range(8):
        try:
            antwort = requests.get(URL, params={"query": query, "format": "json"}, headers=KOPF, timeout=180)
            antwort.raise_for_status()
            cache[query] = antwort.json()["results"]["bindings"]
            ROH.parent.mkdir(exist_ok=True)
            ROH.write_text(json.dumps(cache))
            return cache[query]
        except (requests.RequestException, ValueError):
            time.sleep(20 * (versuch + 1))
    raise SystemExit("Wikidata antwortet nicht — erneut starten, fertige Abfragen sind zwischengespeichert")


def ist_arzneisalz(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    teile = Chem.GetMolFrags(mol, asMols=True)
    if len(teile) < 2:
        return False
    gross = max(teile, key=lambda f: f.GetNumHeavyAtoms())
    return sum(a.GetAtomicNum() == 6 for a in gross.GetAtoms()) >= 8


def main():
    items = defaultdict(lambda: {"labels": set(), "iks": set()})
    smiles = {}
    for endungen in ENDUNGEN:
        for b in frage(LABELS % endungen):
            q = b["item"]["value"].rsplit("/", 1)[1]
            items[q]["labels"].add(b["label"]["value"])
            items[q]["iks"].add(b["ik"]["value"])
            smiles[q] = b["s"]["value"]
    eindeutig = sorted(q for q, v in items.items() if len(v["iks"]) == 1)
    zeilen = [
        {"name": label, "erwartet": next(iter(items[q]["iks"])), "wikidata": q,
         "teil": "einstellen" if int(q[1:]) % 2 == 0 else "holdout"}
        for q in eindeutig
        if q in smiles and ist_arzneisalz(smiles[q])
        for label in sorted(items[q]["labels"])
    ]
    zeilen.sort(key=lambda x: x["name"].lower())
    OUT.write_text(json.dumps(zeilen, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(items)} Items, {len(eindeutig)} mit einem InChIKey, {len(smiles)} mit SMILES, "
          f"{len(zeilen)} Arzneisalz-Namen ({sum(z['teil'] == 'holdout' for z in zeilen)} Holdout)")


if __name__ == "__main__":
    main()
