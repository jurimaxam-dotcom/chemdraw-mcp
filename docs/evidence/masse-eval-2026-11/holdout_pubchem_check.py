"""Holdout für die PubChem-Variantenprobe (Befund 3): Präzision an Namen, die nicht zum Einstellen dienten.

Die Regel (PubChem-Direkttreffer gegen die Schreibvariante prüfen — englisch,
ohne Stereo-Klammerpräfix —, bei anderem Gerüst gewinnt die Variante) wurde an
den 139 Eingaben aus `stoffe-masse.json` eingestellt, die diesen Weg nehmen.
Hier läuft sie über bekannte Arzneistoffe aus Wikidata (ATC-Code P267, genau ein
InChIKey, ≥ 15 Wikipedia-Sprachen), englisches UND deutsches Label, die in keiner
der beiden Listen stehen. Gezählt wird nur, wo die Regel greifen kann: OPSIN
schweigt, PubChem trifft direkt, eine Variante existiert.
alt = PubChem-Direkttreffer (Stand vor Befund 3), neu = resolve_name heute.

    uv run python docs/evidence/masse-eval-2026-11/holdout_pubchem_check.py   # Netz, ~10 min

Jeder Fall landet als Einzelfall in `holdout_pubchem_check.json`
(Name, Variante, erwartet, alt, neu, Urteil), damit die Zähler nachprüfbar sind.
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
  ?item rdfs:label ?label . FILTER(LANG(?label) = "%s")
} GROUP BY ?label
"""


def inchikey(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return Chem.MolToInchiKey(mol) if mol is not None else None


def main():
    bindungen = []
    for sprache in ("en", "de"):  # eine Abfrage mit beiden Sprachen läuft bei Wikidata in 502
        antwort = requests.get(
            "https://query.wikidata.org/sparql",
            params={"query": SPARQL % sprache, "format": "json"},
            headers={"User-Agent": "chemdraw-mcp-masse-eval/1.0"},
            timeout=180,
        )
        antwort.raise_for_status()
        bindungen += antwort.json()["results"]["bindings"]
    stoffe = sorted({
        (b["label"]["value"], b["key"]["value"])
        for b in bindungen
        if b["nik"]["value"] == "1" and b["label"]["value"].lower() not in BEKANNT
    })
    zahl = Counter()
    faelle = []
    for name, erwartet in stoffe:
        variante = resolver._spelling_variant(name)
        if variante is None:
            zahl["ohne Variante"] += 1
            continue
        if resolver._opsin_lookup(name):
            zahl["OPSIN-Weg"] += 1
            continue
        alt = inchikey(resolver._pubchem_lookup(name, []))
        time.sleep(0.25)
        if not alt:
            zahl["PubChem kennt den Namen nicht"] += 1
            continue
        resolver.resolve_name.cache_clear()
        try:
            neu = inchikey(resolver.resolve_name(name))
        except Exception:
            neu = None
        time.sleep(0.5)
        a, n, e = alt[:14], (neu or "")[:14], erwartet[:14]
        if a == n:
            urteil = "gleich (alt richtig)" if a == e else "gleich (beide falsch)"
        elif n == e:
            urteil = "neu behebt"
        elif a == e:
            urteil = "neu bricht"
        else:
            urteil = "beide falsch, verschieden"
        zahl[urteil] += 1
        faelle.append({"name": name, "variante": variante, "erwartet": erwartet,
                       "alt": alt, "neu": neu, "urteil": urteil})
        if not urteil.startswith("gleich (alt"):
            print(f"{urteil:28} {name} → {variante}: alt {alt} neu {neu} erwartet {erwartet}", flush=True)
    (HIER / "holdout_pubchem_check.json").write_text(
        json.dumps(faelle, ensure_ascii=False, indent=1) + "\n"
    )
    print(f"\n{len(stoffe)} Holdout-Labels · {dict(zahl)}")


if __name__ == "__main__":
    main()
