"""Holdout für die OPSIN-Gegenprüfung (Befund 2): Präzision an Namen, die nicht zum Einstellen dienten.

Die Regel (Lokant → offline, sonst PubChem gegenprüfen, Tiebreak englische
Schreibweise) wurde an den 233 OPSIN-Treffern aus `stoffe-masse.json` und
`stoffe.json` eingestellt. Hier läuft sie über bekannte Stoffe aus Wikidata
(ATC-Code P267, englisches Label, genau ein InChIKey, ≥ 15 Wikipedia-Sprachen), die in
keiner der beiden Listen stehen. Gezählt wird nur, wo OPSIN etwas liefert:
alt = OPSIN allein (Stand vor Befund 2), neu = resolve_name heute.

    uv run python docs/evidence/masse-eval-2026-11/holdout_opsin_check.py   # Netz, ~5 min
"""

import json
import time
from collections import Counter
from pathlib import Path

import requests
from rdkit import Chem, RDLogger

from chemdraw_tool import resolver

RDLogger.DisableLog("rdApp.*")
HIER = Path(__file__).parent
REPO = HIER.parents[2]
BEKANNT = {
    s["eingabe"].lower()
    for f in ("stoffe-masse.json", "stoffe.json")
    for s in json.loads((REPO / "tests/identity" / f).read_text())["stoffe"]
    if isinstance(s.get("eingabe"), str)
}
SPARQL = """
SELECT ?label (SAMPLE(?ik) AS ?key) (COUNT(DISTINCT ?ik) AS ?nik) WHERE {
  ?item wdt:P267 ?atc ; wdt:P235 ?ik ; wikibase:sitelinks ?n . FILTER(?n >= 15)
  ?item rdfs:label ?label . FILTER(LANG(?label) = "en")
} GROUP BY ?label
"""


def skelett(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return Chem.MolToInchiKey(mol) if mol is not None else None


def main():
    antwort = requests.get(
        "https://query.wikidata.org/sparql",
        params={"query": SPARQL, "format": "json"},
        headers={"User-Agent": "chemdraw-mcp-masse-eval/1.0"},
        timeout=120,
    )
    antwort.raise_for_status()
    stoffe = [
        (b["label"]["value"], b["key"]["value"])
        for b in antwort.json()["results"]["bindings"]
        if b["nik"]["value"] == "1" and b["label"]["value"].lower() not in BEKANNT
    ]
    zahl = Counter()
    for name, erwartet in stoffe:
        alt = skelett(resolver._opsin_lookup(name))
        if not alt:
            zahl["OPSIN liefert nichts"] += 1
            continue
        resolver.resolve_name.cache_clear()
        try:
            neu = skelett(resolver.resolve_name(name))
        except Exception:
            neu = None
        time.sleep(0.2)
        a, n, e = (alt or "")[:14], (neu or "")[:14], erwartet[:14]
        if a == n:
            zahl["gleich (alt richtig)" if a == e else "gleich (beide falsch)"] += 1
            if a != e:
                print(f"=  {name}: beide {alt}, erwartet {erwartet}")
        elif n == e:
            zahl["neu behebt"] += 1
            print(f"+  {name}")
        elif a == e:
            zahl["neu bricht"] += 1
            print(f"XX {name}: OPSIN richtig, neu {neu}")
        else:
            zahl["beide falsch, verschieden"] += 1
            print(f"?  {name}: alt {alt} neu {neu} erwartet {erwartet}")
    print(f"Holdout: {len(stoffe)} Wikidata-Stoffe außerhalb der Listen · {dict(zahl)}")


if __name__ == "__main__":
    main()
