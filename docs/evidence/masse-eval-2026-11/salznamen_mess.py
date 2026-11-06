"""Salznamen-Messung (06.11.2026): deutsche Salznamen heute und mit welchen Umschreibungen PubChem sie trifft.

    uv run python docs/evidence/masse-eval-2026-11/salznamen_mess.py vorher    # Netz, ~15 min
    uv run python docs/evidence/masse-eval-2026-11/salznamen_mess.py nachher   # nach dem Fix

Liest `salznamen_liste.json` (Wikidata, siehe salznamen_liste.py) und schreibt
`salznamen_mess.json`: je Name das Ergebnis der echten Kaskade (`resolve_name_route`)
im Zustand vorher/nachher und — nur bei „vorher" — den PubChem-InChIKey für jede
Kandidaten-Umschreibung. Die Kandidaten sind Hypothesen, keine Regeln:

  trenn_de   Wortgrenze vor dem Gegenion, deutsch:   „Metformin hydrochlorid"
  trenn_en   dazu englische Endungen (INN + Gegenion): „Metformine hydrochloride"
  trenn_en0  englisches Gegenion, INN unverändert:    „Metformin hydrochloride"
  variante   was `english_variant` vor dem Fix baute (Messung am Worktree `bfbae23`)

Urteil je Name: richtig = voller InChIKey gleich Wikidata; Stamm = erster Block gleich
(andere Hydratstufe/Stereo); falsch = anderer Stoff; nicht gefunden.
Setzt fort, was in der Ausgabedatei schon steht.
"""

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from rdkit import Chem, RDLogger

from chemdraw_tool import resolver
from chemdraw_tool.de_names import english_variant
from chemdraw_tool.resolver import NameResolutionError

RDLogger.DisableLog("rdApp.*")
HIER = Path(__file__).parent
LISTE = json.loads((HIER / "salznamen_liste.json").read_text())
OUT = HIER / "salznamen_mess.json"

# Gegenion-Endungen deutsch → englisch (Messhypothese, längere zuerst)
GEGENION = {
    "dihydrochlorid": "dihydrochloride", "hydrochlorid": "hydrochloride",
    "hydrobromid": "hydrobromide", "hydrogentartrat": "bitartrate", "tartrat": "tartrate",
    "besilat": "besylate", "mesilat": "mesylate", "tosilat": "tosylate",
    "maleat": "maleate", "fumarat": "fumarate", "succinat": "succinate",
    "natrium": "sodium", "kalium": "potassium", "sulfat": "sulfate", "citrat": "citrate",
    "lactat": "lactate", "gluconat": "gluconate", "phosphat": "phosphate", "acetat": "acetate",
    "bromid": "bromide", "iodid": "iodide", "chlorid": "chloride", "nitrat": "nitrate",
}
SPLIT = re.compile(r"(?i)^(.+?)[ -]?(" + "|".join(GEGENION) + r")$")
INN_E = (("in", "ine"), ("on", "one"), ("id", "ide"), ("at", "ate"), ("im", "ime"), ("an", "ane"), ("ol", "ol"))


def ik(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return Chem.MolToInchiKey(mol) if mol is not None else None


def urteil(key, erwartet):
    if not key:
        return "nicht gefunden"
    if key == erwartet:
        return "richtig"
    return "Stamm" if key[:14] == erwartet[:14] else "falsch"


def kandidaten(name):
    m = SPLIT.match(name)
    if not m:
        return {}
    stamm, ion = m.group(1), m.group(2).lower()
    en_stamm = stamm
    for de, en in INN_E:
        if stamm.lower().endswith(de):
            en_stamm = stamm + en[len(de):]
            break
    return {
        "trenn_de": f"{stamm} {ion}",
        "trenn_en": f"{en_stamm} {GEGENION[ion]}",
        "trenn_en0": f"{stamm} {GEGENION[ion]}",
        "variante": english_variant(name),
    }


def kaskade(name):
    resolver.resolve_name.cache_clear()
    try:
        r = resolver.resolve_name_route(name)
        return ik(r.smiles), r.found_as
    except NameResolutionError as exc:
        return None, f"[{exc.kind}]"


def main():
    phase = sys.argv[1]
    daten = json.loads(OUT.read_text()) if OUT.exists() else {}
    for z in LISTE:
        eintrag = daten.setdefault(z["name"], dict(z))
        if phase in eintrag:
            continue
        key, found_as = kaskade(z["name"])
        eintrag[phase] = {"ik": key, "found_as": found_as, "urteil": urteil(key, z["erwartet"])}
        if phase == "vorher":
            proben = {}
            for art, text in kandidaten(z["name"]).items():
                if not text:
                    continue
                k = ik(resolver._pubchem_lookup(text, []))
                proben[art] = {"text": text, "ik": k, "urteil": urteil(k, z["erwartet"])}
                time.sleep(0.25)
            eintrag["proben"] = proben
        OUT.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n")
    for teil in ("einstellen", "holdout"):
        zeilen = [d for d in daten.values() if d["teil"] == teil and phase in d]
        print(teil, len(zeilen), dict(Counter(d[phase]["urteil"] for d in zeilen)))
        if phase == "vorher":
            for art in ("trenn_de", "trenn_en", "trenn_en0", "variante"):
                print("  ", art, dict(Counter(d["proben"].get(art, {}).get("urteil", "—") for d in zeilen)))


if __name__ == "__main__":
    main()
