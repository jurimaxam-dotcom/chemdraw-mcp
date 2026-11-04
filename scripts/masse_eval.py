#!/usr/bin/env python3
"""Masse-Evaluation: viele Stoffe, Erwartung aus einer UNABHÄNGIGEN Quelle.

`scripts/identitaet.py` prüft 24 handverlesene Einträge. Für "hunderte
Moleküle, damit uns nichts entgeht" reicht Handarbeit nicht — und die
Erwartung darf nicht aus derselben Kette kommen, die geprüft wird
(OPSIN → PubChem → NCI). Deshalb kommen Stoffliste und Erwartungs-InChIKey
aus Wikidata, gegengeprüft gegen ChEMBL (EBI). Beide sind nicht Teil der
Auflösungskette.

Unterbefehle (alle außerhalb des Auto-Gates; `liste` braucht Netz):

    uv run python scripts/masse_eval.py liste   # tests/identity/stoffe-masse.json neu bauen
    uv run python scripts/masse_eval.py ir      # IR-Regelabdeckung → docs/evidence/…/ir-abdeckung.md
    uv run python scripts/masse_eval.py ph      # pH-Aufgaben → docs/evidence/…/ph.md
    uv run --with sympy python scripts/masse_eval.py ph-referenz   # Referenzwerte neu rechnen

Der Identitätslauf selbst bleibt in scripts/identitaet.py:

    uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

LISTE = REPO / "tests" / "identity" / "stoffe-masse.json"
KURATIERT = REPO / "tests" / "identity" / "stoffe.json"
PH_AUFGABEN = REPO / "tests" / "identity" / "ph-aufgaben.json"
EVIDENZ = REPO / "docs" / "evidence" / "masse-eval-2026-11"

UA = "chemdraw-mcp-masse-eval/0.1 (https://github.com/jurimaxam-dotcom/chemdraw-mcp)"
SPARQL = "https://query.wikidata.org/sparql"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"

# WHO Model List of Essential Medicines: Wikidata-Rolle P2868 = Q35456.
EML_ROLLE = "Q35456"

# Lehrbuch-Grundstoffe, die keine Arzneistoffe sind (oder auf der EML
# fehlen). Die AUSWAHL ist unsere — die Erwartung kommt trotzdem aus
# Wikidata (englisches Label → Objekt → P235). Ein Objekt mit mehr als einem
# InChIKey (Zucker, Milchsäure …) fliegt raus: dort ist die Referenz selbst
# mehrdeutig, und ein Rot wäre ein Befund über Wikidata, nicht über uns.
LEHRBUCH: dict[str, list[str]] = {
    "Aminosäure": [
        "L-alanine", "L-arginine", "L-Asparagine", "L-aspartic acid",
        "L-cysteine", "L-glutamic acid", "L-glutamine", "glycine",
        "L-histidine", "L-isoleucine", "L-leucine", "L-lysine",
        "L-methionine", "phenylalanine", "L-proline", "L-serine",
        "L-threonine", "tryptophan", "L-tyrosine", "L-valine",
    ],
    "Lösungsmittel/Grundchemikalie": [
        "methanol", "ethanol", "propyl alcohol", "isopropyl alcohol", "1-butanol",
        "acetone", "diethyl ether", "tetrahydrofuran", "dichloromethane",
        "chloroform", "carbon tetrachloride", "toluene", "benzene", "hexane",
        "cyclohexane", "ethyl acetate", "acetonitrile", "dimethyl sulfoxide",
        "dimethylformamide", "pyridine", "1,4-dioxane", "glycerol",
        "ethylene glycol", "phenol", "aniline", "formaldehyde",
        "acetaldehyde", "benzaldehyde", "nitrobenzene", "styrene",
        "naphthalene", "anthracene", "ethylene", "acetylene", "isoprene",
        "cyclohexanone", "chlorobenzene", "anisole", "benzonitrile",
        "acetophenone", "benzyl alcohol", "acetic anhydride", "acetyl chloride",
    ],
    "Säure/Base": [
        "formic acid", "propionic acid", "butyric acid", "oxalic acid",
        "malonic acid", "succinic acid", "fumaric acid", "maleic acid",
        "phthalic acid", "trifluoroacetic acid", "ammonia", "methylamine",
        "triethylamine", "imidazole", "piperidine", "morpholine",
        "edetic acid", "hydroxyacetic acid", "pyruvic acid",
        "acrylic acid", "oleic acid", "stearic acid", "palmitic acid",
        "sulfanilamide", "4-aminobenzoic acid", "hydroquinone", "resorcin",
        "catechol",
    ],
    "Zucker/Zuckeralkohol": [
        "sucrose", "lactose", "maltose", "D-ribose", "D-galactose",
        "D-mannose", "sorbitol", "xylitol", "trehalose", "D-fructose",
    ],
    "Vitamin/Cofaktor": [
        "thiamine", "nicotinic acid", "pantothenic acid", "biotin",
        "alpha-tocopherol", "menadione", "cyanocobalamin",
    ],
    "Naturstoff/Botenstoff": [
        "cholesterol", "testosterone", "estradiol", "progesterone",
        "epinephrine", "norepinephrine", "dopamine", "serotonin",
        "histamine", "acetylcholine", "nicotine", "cocaine", "atropine",
        "theophylline", "theobromine", "vanillin", "eugenol",
        "salicylaldehyde", "adenine", "guanine", "cytosine", "thymine",
        "uracil", "adenosine", "citral", "capsaicin", "melatonin",
        "γ-aminobutyric acid",
    ],
    "Arzneistoff (nicht EML)": [
        "diclofenac", "naproxen", "captopril", "warfarin", "benzocaine",
        "procaine", "sulfamethoxazole", "phenacetin", "acetanilide",
        "diphenhydramine", "cetirizine", "pantoprazole", "atorvastatin",
        "sildenafil", "tramadol", "ramipril", "metamizole", "levothyroxine",
        "candesartan", "torasemide",
    ],
}


def _sparql(query: str) -> list[dict]:
    url = SPARQL + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json", "User-Agent": UA}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        daten = json.load(resp)
    return [
        {k: v["value"] for k, v in zeile.items()}
        for zeile in daten["results"]["bindings"]
    ]


def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _sammle(zeilen: list[dict]) -> dict[str, dict]:
    """SPARQL-Zeilen (eine je Wertkombination) → ein Datensatz je Objekt."""
    objekte: dict[str, dict] = {}
    for z in zeilen:
        o = objekte.setdefault(
            _qid(z["i"]),
            {"keys": set(), "chembl": set(), "smiles": set(), "en": None, "de": None,
             "inn": None, "suchwort": z.get("l")},
        )
        o["keys"].add(z["key"])
        for feld, ziel in (("chembl", "chembl"), ("smi", "smiles")):
            if z.get(feld):
                o[ziel].add(z[feld])
        for feld in ("en", "de", "inn"):
            if z.get(feld):
                o[feld] = z[feld]
    return objekte


_FELDER = """
  OPTIONAL { ?i rdfs:label ?en FILTER(LANG(?en)="en") }
  OPTIONAL { ?i rdfs:label ?de FILTER(LANG(?de)="de") }
  OPTIONAL { ?i wdt:P2275 ?inn FILTER(LANG(?inn)="en") }
  OPTIONAL { ?i wdt:P592 ?chembl }
  OPTIONAL { ?i wdt:P2017|wdt:P233 ?smi }
"""


def _eml() -> dict[str, dict]:
    q = f"SELECT * WHERE {{ ?i wdt:P2868 wd:{EML_ROLLE} ; wdt:P235 ?key . {_FELDER} }}"
    return _sammle(_sparql(q))


def _lehrbuch() -> dict[str, dict]:
    werte = " ".join(f'"{n}"@en' for namen in LEHRBUCH.values() for n in namen)
    q = f"SELECT * WHERE {{ VALUES ?l {{ {werte} }} ?i rdfs:label ?l ; wdt:P235 ?key . {_FELDER} }}"
    objekte = _sammle(_sparql(q))
    gruppe = {n: g for g, namen in LEHRBUCH.items() for n in namen}
    for o in objekte.values():
        o["gruppe"] = gruppe.get(o["suchwort"], "?")
    return objekte


def _chembl_nach_keys(keys: list[str]) -> dict[str, str]:
    """InChIKey → ChEMBL-ID, für alle Keys, die ChEMBL kennt."""
    gefunden: dict[str, str] = {}
    for start in range(0, len(keys), 40):
        teil = keys[start : start + 40]
        url = CHEMBL + "?" + urllib.parse.urlencode(
            {
                "molecule_structures__standard_inchi_key__in": ",".join(teil),
                "only": "molecule_chembl_id,molecule_structures",
                "limit": 1000,
            }
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as resp:
            for m in json.load(resp)["molecules"]:
                s = m.get("molecule_structures") or {}
                if s.get("standard_inchi_key"):
                    gefunden[s["standard_inchi_key"]] = m["molecule_chembl_id"]
        time.sleep(0.5)
    return gefunden


def _chembl_nach_ids(ids: list[str]) -> dict[str, str]:
    """ChEMBL-ID → InChIKey, für die Gegenprobe bei Abweichung."""
    gefunden: dict[str, str] = {}
    for start in range(0, len(ids), 40):
        teil = ids[start : start + 40]
        url = CHEMBL + "?" + urllib.parse.urlencode(
            {
                "molecule_chembl_id__in": ",".join(teil),
                "only": "molecule_chembl_id,molecule_structures",
                "limit": 1000,
            }
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as resp:
            for m in json.load(resp)["molecules"]:
                s = m.get("molecule_structures") or {}
                if s.get("standard_inchi_key"):
                    gefunden[m["molecule_chembl_id"]] = s["standard_inchi_key"]
        time.sleep(0.5)
    return gefunden


def _formel(smiles: str) -> str | None:
    from rdkit import Chem
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula

    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return CalcMolFormula(mol) if mol else None


def _hat_kohlenstoff(smiles: str) -> bool:
    # Nicht per Formelstring: "Ca" und "ClK" enthalten auch ein "C".
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    return mol is not None and any(a.GetAtomicNum() == 6 for a in mol.GetAtoms())


def _passendes_smiles(smiles: set[str], key: str) -> str | None:
    """Das SMILES des Objekts, dessen InChIKey zum Erwartungsschlüssel passt."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem import inchi

    RDLogger.DisableLog("rdApp.*")
    for s in sorted(smiles):
        mol = Chem.MolFromSmiles(s)
        if mol is not None and inchi.MolToInchiKey(mol) == key:
            return s
    return None


def baue_liste(_: argparse.Namespace) -> int:
    kuratiert = {
        e["eingabe"].casefold()
        for e in json.loads(KURATIERT.read_text(encoding="utf-8"))["stoffe"]
    }
    eml = _eml()
    for o in eml.values():
        o["gruppe"] = "Arzneistoff (WHO-EML)"
    lehr = _lehrbuch()
    gesucht = {n for namen in LEHRBUCH.values() for n in namen}
    nicht_gefunden = sorted(gesucht - {o["suchwort"] for o in lehr.values()})

    alle = {**lehr, **eml}  # EML gewinnt bei Überschneidung
    verworfen: list[dict] = []
    behalten: dict[str, dict] = {}
    for qid, o in alle.items():
        name = o["inn"] or o["en"] or ""
        grund = None
        if len(o["keys"]) != 1:
            grund = f"{len(o['keys'])} InChIKeys im Objekt — Referenz selbst mehrdeutig"
        elif "/" in name:
            grund = "Kombinationspräparat"
        elif not o["smiles"]:
            grund = "kein SMILES in Wikidata (Element/Polymer/Gemisch)"
        else:
            key = next(iter(o["keys"]))
            smi = _passendes_smiles(o["smiles"], key)
            if smi is None:
                grund = "SMILES und InChIKey im Objekt passen nicht zusammen"
            elif not _hat_kohlenstoff(smi) or "Pt" in smi:
                grund = "anorganisch/Metallkomplex — außerhalb des Zeichenauftrags"
            else:
                o["key"], o["smiles_ok"] = key, smi
        if grund:
            verworfen.append({"qid": qid, "name": name, "grund": grund})
        else:
            behalten[qid] = o

    keys = sorted({o["key"] for o in behalten.values()})
    chembl_treffer = _chembl_nach_keys(keys)
    offen = sorted(
        c for o in behalten.values() if o["key"] not in chembl_treffer for c in o["chembl"]
    )
    chembl_ids = _chembl_nach_ids(offen) if offen else {}

    stoffe: list[dict] = []
    gesehen: set[str] = set()
    for qid, o in sorted(behalten.items(), key=lambda kv: (kv[1]["gruppe"], kv[1]["inn"] or kv[1]["en"] or "")):
        key = o["key"]
        quelle = [f"wikidata:{qid}"]
        notiz = []
        unsicher = False
        if key in chembl_treffer:
            quelle.append(f"chembl:{chembl_treffer[key]}")
        elif o["chembl"]:
            abweichend = sorted(
                {chembl_ids.get(c) for c in o["chembl"] if chembl_ids.get(c)}
            )
            if abweichend:
                unsicher = True
                notiz.append(
                    "ChEMBL " + ",".join(sorted(o["chembl"])) + " führt " + ",".join(abweichend)
                )
            else:
                notiz.append("ChEMBL-ID ohne Struktur — nur Wikidata")
        else:
            notiz.append("in ChEMBL nicht unter diesem InChIKey — nur Wikidata")

        basis = {
            "inchikey": key,
            "formel": _formel(o["smiles_ok"]),
            "gruppe": o["gruppe"],
            "quelle": " + ".join(quelle),
            "smiles_referenz": o["smiles_ok"],
        }
        if unsicher:
            basis["unsicher"] = True
        if notiz:
            basis["notiz"] = "; ".join(notiz)

        namen = []
        if o["inn"]:
            namen.append((o["inn"], "en/INN (wikidata P2275)"))
        if o["en"] and (not o["inn"] or o["en"].casefold() != o["inn"].casefold()):
            namen.append((o["en"], "en (wikidata-Label)"))
        if o["de"] and all(o["de"].casefold() != n.casefold() for n, _ in namen):
            namen.append((o["de"], "de (wikidata-Label = de.wikipedia)"))
        for name, herkunft in namen:
            if name.casefold() in kuratiert or name.casefold() in gesehen:
                continue
            gesehen.add(name.casefold())
            stoffe.append({"eingabe": name, "sprache": herkunft, **basis})

    daten = {
        "zweck": (
            "Masse-Evaluation der Namensauflösung: Eingabe → erwarteter InChIKey aus "
            "einer Quelle AUSSERHALB der Auflösungskette. Gefahren von scripts/identitaet.py "
            "--datei tests/identity/stoffe-masse.json, NICHT vom Auto-Gate (braucht Netz)."
        ),
        "aufgenommen": dt.date.today().isoformat(),
        "herkunft": (
            "Erwartungs-InChIKey = Wikidata P235 (https://query.wikidata.org/sparql). "
            "Stoffauswahl: (1) alle Wikidata-Objekte mit Rolle 'WHO essential medicines' "
            f"(P2868 = {EML_ROLLE}) und genau einem InChIKey, (2) eine eigene Liste von "
            "Lehrbuch-Grundstoffen (englische Labels, in scripts/masse_eval.py LEHRBUCH). "
            "Gegenprobe: ChEMBL (https://www.ebi.ac.uk/chembl/api/data/molecule) per "
            "InChIKey; 'chembl:…' in 'quelle' heißt, ChEMBL führt genau diesen Schlüssel. "
            "'unsicher': ChEMBL führt unter der verlinkten ID einen anderen Schlüssel — der "
            "Lauf wertet solche Einträge nie als rot. Eingaben: INN (P2275), englisches und "
            "deutsches Wikidata-Label. Neu bauen: uv run python scripts/masse_eval.py liste"
        ),
        "verworfen": verworfen,
        "nicht_in_wikidata_gefunden": nicht_gefunden,
        "stoffe": stoffe,
    }
    LISTE.write_text(
        json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    stoffzahl = len({s["inchikey"] for s in stoffe})
    print(
        f"{len(stoffe)} Eingaben für {stoffzahl} Stoffe → {LISTE.relative_to(REPO)}\n"
        f"Gruppen: {dict(Counter(s['gruppe'] for s in stoffe))}\n"
        f"ChEMBL bestätigt: {sum('chembl:' in s['quelle'] for s in stoffe)} · "
        f"unsicher: {sum(bool(s.get('unsicher')) for s in stoffe)}\n"
        f"verworfen: {len(verworfen)} · Lehrbuchnamen ohne Wikidata-Treffer: {nicht_gefunden}"
    )
    return 0


# --- IR-Regelabdeckung -------------------------------------------------------
#
# Eigene Gruppenliste, unabhängig von spectro._IR_TABLE geschrieben. Je Gruppe:
# SMARTS, die Tabellengruppen, die sie korrekt abdecken würden ("regeln"), und
# ob die Gruppe laut Lehrbuch (Hesse/Meier/Zeeh, Kap. IR) überhaupt eine
# diagnostische Bande hat. Nur "diagnostisch und keine Regel trifft" ist eine
# Lücke der Tabelle; eine tertiäre Aminogruppe ohne Regel ist keine.
IR_GRUPPEN: list[tuple[str, str, list[str], bool, str]] = [
    ("Carbonsäure", "[CX3](=O)[OX2H1]", ["C=O (carboxylic acid)", "O–H (carboxylic acid)"], True, ""),
    ("Carboxylat", "[CX3](=O)[O-]", [], True, "COO⁻ asym. 1550–1610, sym. ~1400"),
    ("Ester (ohne Carbamat/Carbonat)", "[#6][CX3](=O)[OX2][#6]", ["C=O (ester)"], True, ""),
    ("Keton", "[#6][CX3](=O)[#6]", ["C=O (ketone)"], True, ""),
    ("Aldehyd", "[CX3H1](=O)[#6]", ["C=O (aldehyde)"], True, ""),
    ("Formaldehyd", "[CH2]=O", [], True, "C=O ~1745"),
    ("Amid (ohne Harnstoff/Carbamat/Imid)",
     "[#6][CX3](=O)[NX3;!$(N(C=O)C=O)]", ["C=O (amide, band I)"], True, ""),
    ("β-Lactam", "O=C1CCN1", [], True, "C=O 1760–1780 — deutlich über der Amid-I-Bande"),
    ("Harnstoff", "[NX3][CX3](=O)[NX3]", ["C=O (amide, band I)"], True, ""),
    ("Carbamat", "[NX3][CX3](=O)[OX2][#6]", [], True, "C=O 1690–1740; Tabelle meldet Amid UND Ester"),
    ("Imid", "[CX3](=O)[NX3][CX3](=O)", [], True, "zwei C=O, ~1700 und ~1770"),
    ("Säurehalogenid", "[CX3](=O)[Cl,Br,I,F]", ["C=O (acid halide)"], True, ""),
    ("Anhydrid", "[CX3](=O)[OX2][CX3]=O", ["C=O (anhydride)"], True, ""),
    ("Nitril", "[NX1]#[CX2]", ["C≡N (nitrile)"], True, ""),
    ("Nitro", "[$([NX3](=O)=O),$([NX3+](=O)[O-])][#6]", ["N=O (nitro, antisymmetric)"], True,
     "N=O 1500–1560 und 1345–1385 — die Regel existiert, ihr SMARTS [NX3](=O)=O passt aber nicht auf "
     "die ladungsgetrennte Form [N+](=O)[O-], in der RDKit jede Nitrogruppe speichert"),
    ("Nitratester", "[OX2][$([NX3](=O)=O),$([NX3+](=O)[O-])]", [], True, "1620–1640 und 1270–1290"),
    ("Azid", "[$(N=[N+]=[N-]),$(N=N#N)]", [], True, "N₃ asym. ~2100, sehr stark"),
    ("Sulfonamid", "[SX4](=O)(=O)[NX3]", [], True, "S=O asym. 1330–1370, sym. 1140–1180"),
    ("Sulfon", "[#6][SX4](=O)(=O)[#6]", [], True, "S=O 1300–1350 und 1120–1160"),
    ("Sulfonsäure/Sulfat/Sulfonat", "[SX4](=O)(=O)[OX2H1,OX1-,OX2]", [], True, "S=O 1150–1250, 1030–1060"),
    ("Sulfoxid", "[#6][SX3](=O)[#6]", [], True, "S=O ~1050"),
    ("Thiocarbonyl (Thioamid/-harnstoff)", "[CX3]=[SX1]", [], True, "C=S 1050–1250"),
    ("Phosphat/Phosphonat", "[PX4](=O)", [], True, "P=O 1250–1300, P–O 950–1050"),
    ("Thiol", "[SX2H]", ["S–H (thiol)"], True, ""),
    ("Thioether", "[#6][SX2][#6]", [], False, "C–S schwach, unspezifisch"),
    ("Alkohol", "[OX2H][CX4]", ["O–H (alcohol)"], True, ""),
    ("Phenol", "[OX2H]c", ["O–H (phenol)"], True, ""),
    ("Ether (aliphatisch/aromatisch)", "[#6;!$([CX3]=[OX1])][OX2][#6;!$([CX3]=[OX1])]", ["C–O (ether)"], True, ""),
    ("Amin primär", "[NX3;H2;!$(N[CX3]=[O,S,N]);!$(NS(=O)=O)][#6]", ["N–H (primary amine)"], True, ""),
    ("Amin sekundär", "[NX3;H1;!$(N[CX3]=[O,S,N]);!$(NS(=O)=O);!$(N[a]);!a]([#6])[#6]",
     ["N–H (secondary amine)"], True,
     "N–H 3300–3500; die Tabellenregel verlangt sp³- oder Aryl-Nachbarn, Enamin-NH (Dihydropyridin) fällt durch"),
    ("Arylamin sekundär", "[NX3;H1;!$(N[CX3]=[O,S,N]);!$(NS(=O)=O);!a]([#6])c", ["N–H (secondary amine)"], True, ""),
    ("Amin tertiär", "[NX3;H0;!$(N[CX3]=[O,S,N]);!$(NS(=O)=O);!$(N=*);!a;+0]([#6])([#6])[#6]",
     [], False, "keine N–H-Bande — IR zeigt es nicht"),
    ("Ammonium quartär", "[NX4+;H0]", [], False, ""),
    ("Imin/Amidin/Guanidin (C=N, nicht aromatisch)", "[CX3]=[NX2;!a]", [], True, "C=N 1640–1690"),
    ("Azo", "[#6][NX2]=[NX2][#6]", [], False, "N=N schwach"),
    ("Heteroaromat-NH (Pyrrol/Indol/Imidazol)", "[nH]", [], True, "N–H 3400–3500 (scharf)"),
    ("Heteroaromat (Ring-N/O/S)", "[a;!c]", ["C=C (aromatic ring)"], True,
     "Ringschwingungen 1400–1600; ohne Benzolring im Molekül meldet die Tabelle keine"),
    ("Benzolring", "c1ccccc1", ["C=C (aromatic ring)"], True, ""),
    ("Alken (nicht aromatisch)", "[CX3]=[CX3]", ["C=C (alkene)"], True, ""),
    ("Alkin", "[CX2]#[CX2]", ["C≡C (alkyne)"], True, ""),
    ("Fluor (aliphatisch, C–F)", "[CX4]F", [], True, "C–F 1000–1400, sehr stark"),
    ("Halogenaryl (C–F/Cl/Br/I)", "c[F,Cl,Br,I]", [], True, "Ar–F 1100–1250 stark; Ar–Cl ~1090"),
    ("Alkylchlorid/-bromid/-iodid", "[CX4][Cl,Br,I]", [], True, "C–Cl 600–800, C–Br 500–600"),
]


def _ir_stoffe() -> list[dict]:
    """Ein Molekül je InChIKey, SMILES aus Wikidata (nicht aus resolve())."""
    eintraege = json.loads(LISTE.read_text(encoding="utf-8"))["stoffe"]
    je_key: dict[str, dict] = {}
    for e in eintraege:
        je_key.setdefault(e["inchikey"], e)
    return list(je_key.values())


def ir_abdeckung(_: argparse.Namespace) -> int:
    from rdkit import Chem, RDLogger

    from chemdraw_tool.spectro import _IR_TABLE, expected_ir_bands

    RDLogger.DisableLog("rdApp.*")
    tabellengruppen = {e["group"] for e in _IR_TABLE}
    for name, _, regeln, _, _ in IR_GRUPPEN:
        unbekannt = set(regeln) - tabellengruppen
        assert not unbekannt, f"{name}: {unbekannt} gibt es in _IR_TABLE nicht"

    muster = [(g, Chem.MolFromSmarts(sm), regeln, diag, band) for g, sm, regeln, diag, band in IR_GRUPPEN]
    for g, p, *_ in muster:
        assert p is not None, f"SMARTS kaputt: {g}"

    stoffe = _ir_stoffe()
    vorkommen: Counter = Counter()
    luecke: dict[str, list[str]] = {}
    stattdessen: dict[str, Counter] = {}
    tabelle_feuert: Counter = Counter()
    ohne_jede_bande: list[str] = []
    for s in stoffe:
        mol = Chem.MolFromSmiles(s["smiles_referenz"])
        if mol is None:
            continue
        gemeldet = {b["group"] for b in expected_ir_bands(s["smiles_referenz"])}
        tabelle_feuert.update(gemeldet)
        if not gemeldet - {"C–H (alkane, sp³)"}:
            ohne_jede_bande.append(s["eingabe"])
        for g, p, regeln, diag, _ in muster:
            if not mol.HasSubstructMatch(p):
                continue
            vorkommen[g] += 1
            if diag and not (set(regeln) & gemeldet):
                luecke.setdefault(g, []).append(s["eingabe"])
                stattdessen.setdefault(g, Counter()).update(gemeldet)

    heute = dt.date.today().isoformat()
    zeilen = [
        "# IR-Regelabdeckung — Masse-Evaluation",
        "",
        f"Stand {heute} · `uv run python scripts/masse_eval.py ir` · offline, < 10 s",
        "",
        f"**{len(stoffe)} Moleküle** (ein Eintrag je InChIKey aus `tests/identity/stoffe-masse.json`, "
        "SMILES aus Wikidata, nicht aus `resolve()` — der Bericht hängt also nicht vom Identitätslauf ab). "
        f"Je Molekül: {len(IR_GRUPPEN)} eigene SMARTS-Gruppen (unabhängig von `_IR_TABLE` geschrieben, "
        "Liste `IR_GRUPPEN` im Skript) gegen die Gruppen, die `spectro.expected_ir_bands` "
        "(= `predict_spectrum`) meldet.",
        "",
        "**Lücke** = Gruppe mit diagnostischer Bande ist im Molekül, aber keine passende Regel der "
        "Tabelle feuert. Gruppen ohne diagnostische Bande (tertiäres Amin, Thioether, Azo, "
        "quartäres Ammonium) zählen nie als Lücke. Keine Änderung an `spectro.py` — nur Befund.",
        "",
        "## Lücken der Tabelle (nach Zahl betroffener Moleküle)",
        "",
        "| Gruppe | kommt vor in | ohne passende Bande | Anteil | Regel in `_IR_TABLE`? | erwartete Bande / Ursache | Beispiele |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    band = {g: b for g, _, _, _, b in IR_GRUPPEN}
    hat_regel = {g: bool(r) for g, _, r, _, _ in IR_GRUPPEN}
    for g, namen in sorted(luecke.items(), key=lambda kv: -len(kv[1])):
        zeilen.append(
            f"| {g} | {vorkommen[g]} | {len(namen)} | {len(namen) / vorkommen[g]:.0%} | "
            f"{'ja, feuert hier nicht' if hat_regel[g] else 'nein'} | "
            f"{band[g] or '—'} | {', '.join(namen[:4])} |"
        )
    zeilen += [
        "",
        "## Was die Tabelle bei den Lücken stattdessen meldet",
        "",
        "Die häufigsten gemeldeten Gruppen in den betroffenen Molekülen — zeigt, ob eine Lücke "
        "still bleibt oder eine falsche Bande an ihre Stelle tritt (z. B. β-Lactam → Amid I).",
        "",
        "| Gruppe | häufigste gemeldete Gruppen |",
        "|---|---|",
    ]
    for g, c in sorted(stattdessen.items(), key=lambda kv: -len(luecke[kv[0]])):
        top = ", ".join(f"{n} ({k})" for n, k in c.most_common(4))
        zeilen.append(f"| {g} | {top} |")
    zeilen += [
        "",
        "## Alle Gruppen: Vorkommen und Abdeckung",
        "",
        "| Gruppe | diagnostisch | kommt vor in | abgedeckt | Regel(n) in `_IR_TABLE` |",
        "|---|---|---:|---:|---|",
    ]
    for g, _, regeln, diag, _ in IR_GRUPPEN:
        n = vorkommen[g]
        ok = n - len(luecke.get(g, []))
        zeilen.append(
            f"| {g} | {'ja' if diag else 'nein'} | {n} | {ok if diag else '—'} | "
            f"{', '.join(regeln) or '— keine —'} |"
        )
    nie = sorted(tabellengruppen - set(tabelle_feuert))
    zeilen += [
        "",
        "## Tabellenregeln, die in keinem der Moleküle feuern",
        "",
        ", ".join(nie) if nie else "keine",
        "",
        f"Moleküle, für die außer sp³-C–H gar keine Bande gemeldet wird: {len(ohne_jede_bande)}"
        + (f" ({', '.join(ohne_jede_bande[:10])})" if ohne_jede_bande else ""),
        "",
    ]
    ziel = EVIDENZ / "ir-abdeckung.md"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("\n".join(zeilen), encoding="utf-8")
    print(f"{len(stoffe)} Moleküle · {len(luecke)} Gruppen mit Lücken → {ziel.relative_to(REPO)}")
    for g, namen in sorted(luecke.items(), key=lambda kv: -len(kv[1])):
        print(f"  {g:<45} {len(namen):>4} / {vorkommen[g]}")
    return 0


# --- pH-Aufgaben -------------------------------------------------------------
#
# Referenz: sympy löst die Ladungsbilanz als Polynom in [H+] und nimmt die
# einzige positive reelle Wurzel. Unabhängig von ph_core in Formulierung
# (Spezieskonzentrationen aus dem Massenwirkungsgesetz, ausmultipliziert),
# Methode (Polynomwurzel statt Bisektion über α-Fraktionen) und Code. NICHT
# unabhängig in der Physik — es ist dieselbe Ladungsbilanz bei pKw = 14,
# weil es nur eine richtige gibt. Lehrbuch-Ankerwerte prüfen zusätzlich, dass
# die Referenz selbst stimmt.
#
# Aufgaben: (id, topic, parameter, lehrbuch-wert oder None, quelle/zweck)
PH_SPEZ: list[tuple[str, str, dict, float | None, str]] = [
    # Starke Säuren/Basen
    ("hcl-0.1", "strong_acid", {"concentration": 0.1}, 1.00, "Lehrbuch-Standardbeispiel: 0,1 M HCl → pH 1"),
    ("hcl-0.01", "strong_acid", {"concentration": 0.01}, 2.00, "Lehrbuch-Standardbeispiel"),
    ("hcl-1e-5", "strong_acid", {"concentration": 1e-5}, None, "verdünnt, Wasser noch vernachlässigbar"),
    ("hcl-1e-7", "strong_acid", {"concentration": 1e-7}, 6.79, "Grenzfall: Säure und Wasser gleich stark (Lehrbuchwert 6,79)"),
    ("hcl-1e-8", "strong_acid", {"concentration": 1e-8}, 6.98, "Klassische Fangfrage: 1e-8 M HCl ist nicht basisch (pH 6,98)"),
    ("hcl-2", "strong_acid", {"concentration": 2.0}, -0.30, "konzentriert: negativer pH (ideal gerechnet)"),
    ("naoh-0.1", "strong_base", {"concentration": 0.1}, 13.00, "Lehrbuch-Standardbeispiel"),
    ("naoh-1e-3", "strong_base", {"concentration": 1e-3}, 11.00, "Lehrbuch-Standardbeispiel"),
    ("naoh-1e-8", "strong_base", {"concentration": 1e-8}, 7.02, "Spiegelbild der Fangfrage"),
    ("naoh-2", "strong_base", {"concentration": 2.0}, 14.30, "konzentriert: pH über 14 (ideal gerechnet)"),
    # Schwache Säuren
    ("essig-0.1", "weak_acid", {"concentration": 0.1, "pka": 4.76}, 2.88, "Essigsäure 0,1 M: Lehrbuchwert pH 2,88"),
    ("essig-0.01", "weak_acid", {"concentration": 0.01, "pka": 4.76}, 3.38, "Essigsäure 0,01 M: Lehrbuchwert ≈ 3,4"),
    ("essig-1e-4", "weak_acid", {"concentration": 1e-4, "pka": 4.76}, None, "Näherung bricht: Säure merklich dissoziiert"),
    ("essig-1e-6", "weak_acid", {"concentration": 1e-6, "pka": 4.76}, None, "fast vollständig dissoziiert + Wasser"),
    ("essig-1", "weak_acid", {"concentration": 1.0, "pka": 4.76}, 2.38, "Essigsäure 1 M"),
    ("ameisen-0.1", "weak_acid", {"concentration": 0.1, "pka": 3.75}, None, "Ameisensäure"),
    ("hf-0.1", "weak_acid", {"concentration": 0.1, "pka": 3.17}, None, "Flusssäure"),
    ("hcn-0.1", "weak_acid", {"concentration": 0.1, "pka": 9.21}, 5.11, "Blausäure, sehr schwach: pH ≈ 5,1"),
    ("nh4-0.1", "weak_acid", {"concentration": 0.1, "pka": 9.25}, 5.13, "Ammoniumchlorid 0,1 M: pH ≈ 5,1"),
    ("phenol-0.01", "weak_acid", {"concentration": 0.01, "pka": 10.0}, None, "sehr schwache Säure, verdünnt — Wasser zählt"),
    ("mittelstark-0.01", "weak_acid", {"concentration": 0.01, "pka": 1.0}, None, "pKs 1: fast vollständig dissoziiert"),
    ("mittelstark-0.1", "weak_acid", {"concentration": 0.1, "pka": 2.0}, None, "pKs 2: Näherung weit daneben"),
    ("stark-konz", "weak_acid", {"concentration": 5.0, "pka": 0.5}, None, "Randfall: exakter pH < 0"),
    ("schwach-konz", "weak_acid", {"concentration": 10.0, "pka": -1.0}, None, "Randfall: pKs < 0, pH deutlich < 0"),
    # Mehrprotonige Säuren
    ("h3po4-0.1", "weak_acid", {"concentration": 0.1, "pka_values": [2.12, 7.21, 12.67]}, 1.62, "Phosphorsäure 0,1 M: pH ≈ 1,6"),
    ("h3po4-0.001", "weak_acid", {"concentration": 0.001, "pka_values": [2.12, 7.21, 12.67]}, None, "verdünnte Phosphorsäure"),
    ("citronen-0.1", "weak_acid", {"concentration": 0.1, "pka_values": [3.13, 4.76, 6.40]}, None, "Citronensäure"),
    ("kohlen-0.01", "weak_acid", {"concentration": 0.01, "pka_values": [6.35, 10.33]}, None, "Kohlensäure"),
    ("oxal-0.05", "weak_acid", {"concentration": 0.05, "pka_values": [1.25, 4.27]}, None, "Oxalsäure"),
    ("h2s-0.1", "weak_acid", {"concentration": 0.1, "pka_values": [7.0, 12.9]}, None, "Schwefelwasserstoff"),
    # Schwache Basen
    ("nh3-0.1", "weak_base", {"concentration": 0.1, "pkb": 4.75}, 11.13, "Ammoniak 0,1 M: Lehrbuchwert 11,13"),
    ("nh3-0.01", "weak_base", {"concentration": 0.01, "pkb": 4.75}, None, "Ammoniak 0,01 M"),
    ("nh3-1e-5", "weak_base", {"concentration": 1e-5, "pkb": 4.75}, None, "Näherung bricht"),
    ("acetat-0.1", "weak_base", {"concentration": 0.1, "pkb": 9.24}, 8.88, "Natriumacetat 0,1 M: pH ≈ 8,9"),
    ("pyridin-0.1", "weak_base", {"concentration": 0.1, "pka": 5.25}, None, "Pyridin über pKs der korresp. Säure"),
    ("methylamin-0.1", "weak_base", {"concentration": 0.1, "pkb": 3.36}, None, "Methylamin"),
    ("starkebase-konz", "weak_base", {"concentration": 5.0, "pkb": 0.5}, None, "Randfall: exakter pH > 14"),
    # Puffer
    ("acetatpuffer-1:1", "buffer", {"acid_concentration": 0.1, "base_concentration": 0.1, "pka": 4.76}, 4.76, "Äquimolarer Puffer: pH = pKs"),
    ("acetatpuffer-1:10", "buffer", {"acid_concentration": 0.1, "base_concentration": 0.01, "pka": 4.76}, 3.76, "HH: pKs − 1"),
    ("acetatpuffer-10:1", "buffer", {"acid_concentration": 0.01, "base_concentration": 0.1, "pka": 4.76}, 5.76, "HH: pKs + 1"),
    ("phosphatpuffer", "buffer", {"acid_concentration": 0.05, "base_concentration": 0.05, "pka": 7.21}, 7.21, "Phosphatpuffer"),
    ("ammonpuffer", "buffer", {"acid_concentration": 0.1, "base_concentration": 0.2, "pka": 9.25}, 9.55, "NH4Cl/NH3 1:2"),
    ("puffer-verduennt", "buffer", {"acid_concentration": 1e-5, "base_concentration": 1e-5, "pka": 4.76}, None, "sehr verdünnt: HH gilt nicht mehr"),
    ("puffer-saurer-pks", "buffer", {"acid_concentration": 0.01, "base_concentration": 0.01, "pka": 2.0}, None, "pKs 2: HA dissoziiert merklich, HH daneben"),
    ("puffer-basisch-verduennt", "buffer", {"acid_concentration": 1e-4, "base_concentration": 1e-4, "pka": 10.0}, None, "basischer Puffer verdünnt"),
    # Ionisierung (Henderson-Hasselbalch, Anteil ungeladen)
    ("ion-ass-magen", "ionisation", {"pka": 3.5, "target_ph": 1.5, "drug_type": "acid"}, None, "ASS im Magen"),
    ("ion-ass-blut", "ionisation", {"pka": 3.5, "target_ph": 7.4, "drug_type": "acid"}, None, "ASS im Blut"),
    ("ion-base-blut", "ionisation", {"pka": 9.0, "target_ph": 7.4, "drug_type": "base"}, None, "basischer Arzneistoff im Blut"),
    ("ion-gleich", "ionisation", {"pka": 6.0, "target_ph": 6.0, "drug_type": "base"}, 50.0, "pH = pKs: die Hälfte ungeladen"),
    # Pufferrezept (Stoffmenge Säure)
    ("rezept-acetat-pH5", "buffer_recipe", {"target_ph": 5.0, "pka": 4.76, "total_concentration": 0.1, "volume_ml": 1000.0}, None, "Acetatpuffer pH 5, 1 L, 0,1 M"),
    ("rezept-phosphat-pH7.4", "buffer_recipe", {"target_ph": 7.4, "pka": 7.21, "total_concentration": 0.05, "volume_ml": 500.0}, None, "Phosphatpuffer pH 7,4"),
]


def _ph_referenz(topic: str, p: dict) -> tuple[str, float, str]:
    """(Feld, Wert, Herleitung) — exakt mit sympy, ohne chemdraw_tool."""
    import sympy as sp

    h = sp.symbols("h", positive=True)
    kw = sp.Rational(1, 10**14)

    def k(pk: float):
        return sp.Pow(10, -sp.nsimplify(pk))

    def c(x: float):
        return sp.nsimplify(x)

    def loese(bilanz, text: str) -> tuple[str, float, str]:
        zaehler = sp.numer(sp.together(bilanz))
        poly = sp.Poly(sp.expand(zaehler), h)
        wurzeln = [r for r in poly.nroots(n=40, maxsteps=500) if r.is_real and r > 0]
        assert len(wurzeln) == 1, (text, wurzeln)
        ph = -sp.log(wurzeln[0], 10)
        return "ph", float(sp.N(ph, 20)), f"{text}; Polynom Grad {poly.degree()} in [H⁺], einzige positive Wurzel"

    if topic == "strong_acid":
        return loese(h - c(p["concentration"]) - kw / h, "[H⁺] = c + [OH⁻]")
    if topic == "strong_base":
        return loese(h - kw / h + c(p["concentration"]), "[H⁺] + c(Na⁺) = [OH⁻]")
    if topic == "weak_acid":
        pks = p.get("pka_values") or [p["pka"]]
        ks = [k(x) for x in pks]
        # Spezies H(n-j)A^(j-): Anteil ∝ h^(n-j)·K1…Kj
        n = len(ks)
        terme = [h ** (n - j) * sp.prod(ks[:j]) for j in range(n + 1)]
        nenner = sum(terme)
        anion_ladung = sum(j * terme[j] for j in range(n + 1)) / nenner * c(p["concentration"])
        return loese(h - kw / h - anion_ladung, f"[H⁺] = [OH⁻] + Σ j·[H(n−j)A^(j−)], n = {n}")
    if topic == "weak_base":
        ka = k(p["pka"]) if "pka" in p else kw / k(p["pkb"])
        cb = c(p["concentration"])
        bh = cb * h / (h + ka)
        return loese(h + bh - kw / h, "[H⁺] + [BH⁺] = [OH⁻], [BH⁺] = c·h/(h + Ks)")
    if topic == "buffer":
        ka = k(p["pka"])
        ca, cb = c(p["acid_concentration"]), c(p["base_concentration"])
        anion = (ca + cb) * ka / (h + ka)
        return loese(cb + h - kw / h - anion, "c(Na⁺) + [H⁺] = [OH⁻] + [A⁻], [A⁻] = (cHA + cA⁻)·Ks/(h + Ks)")
    if topic == "ionisation":
        expo = (c(p["target_ph"]) - c(p["pka"])) if p["drug_type"] == "acid" else (c(p["pka"]) - c(p["target_ph"]))
        ungeladen = 1 / (1 + sp.Pow(10, expo)) * 100
        return "ungeladen_prozent", float(sp.N(ungeladen, 20)), "ungeladen = 1/(1 + 10^Δ), Δ aus dem Massenwirkungsgesetz"
    if topic == "buffer_recipe":
        r = sp.Pow(10, c(p["target_ph"]) - c(p["pka"]))
        mol = c(p["total_concentration"]) * c(p["volume_ml"]) / 1000 / (1 + r)
        return "acid_mol", float(sp.N(mol, 20)), "n(HA) = c·V/(1 + 10^(pH − pKs))"
    raise ValueError(topic)


def ph_referenz(_: argparse.Namespace) -> int:
    aufgaben = []
    for aid, topic, param, lehrbuch, quelle in PH_SPEZ:
        feld, wert, herleitung = _ph_referenz(topic, param)
        eintrag = {
            "id": aid,
            "topic": topic,
            "parameter": param,
            "feld": feld,
            "erwartet": round(wert, 6),
            "toleranz": 0.005 if feld == "ph" else (0.05 if feld == "ungeladen_prozent" else 1e-6),
            "quelle": quelle,
            "herleitung": f"sympy: {herleitung}",
        }
        if lehrbuch is not None:
            eintrag["lehrbuch"] = lehrbuch
            # Die Referenz muss den Lehrbuchwert treffen, sonst stimmt sie selbst nicht.
            assert abs(wert - lehrbuch) <= 0.02, (aid, wert, lehrbuch)
        aufgaben.append(eintrag)
    daten = {
        "zweck": "pH-Aufgaben mit Referenzlösung außerhalb von chemdraw_tool. Gefahren von scripts/masse_eval.py ph (offline).",
        "aufgenommen": dt.date.today().isoformat(),
        "herkunft": (
            "Referenzwert = sympy, Ladungsbilanz als Polynom in [H⁺], einzige positive reelle "
            "Wurzel (40 Stellen), pKw = 14, ideale Lösung (Aktivität = Konzentration). Unabhängig "
            "von ph_core in Formulierung, Methode und Code, nicht in der Physik. 'lehrbuch' = "
            "gängiger Lehrbuch-Ankerwert ohne Seitenangabe; die Referenz muss ihn auf ±0,02 "
            "treffen. Neu rechnen: uv run --with sympy python scripts/masse_eval.py ph-referenz"
        ),
        "aufgaben": aufgaben,
    }
    PH_AUFGABEN.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(aufgaben)} Aufgaben → {PH_AUFGABEN.relative_to(REPO)}")
    return 0


def _ph_rechne(topic: str, p: dict) -> dict:
    from chemdraw_tool import ph_calc

    if topic == "strong_acid":
        return ph_calc.strong_acid_ph(p["concentration"])
    if topic == "strong_base":
        return ph_calc.strong_base_ph(p["concentration"])
    if topic == "weak_acid":
        return ph_calc.weak_acid_ph(p["concentration"], pka=p.get("pka"), pka_values=p.get("pka_values"))
    if topic == "weak_base":
        return ph_calc.weak_base_ph(p["concentration"], pkb=p.get("pkb"), pka=p.get("pka"))
    if topic == "buffer":
        return ph_calc.buffer_ph(p["acid_concentration"], p["base_concentration"], p["pka"])
    if topic == "ionisation":
        r = ph_calc.ionisation(p["pka"], p["target_ph"], p["drug_type"])
        return {**r, "ungeladen_prozent": r["fraction_unionised"] * 100}
    if topic == "buffer_recipe":
        return ph_calc.buffer_recipe(p["target_ph"], p["pka"], p["total_concentration"], p["volume_ml"])
    raise ValueError(topic)


# Deutung der Abweichungen, sobald sie verstanden sind — steht im Bericht neben der Zeile.
PH_DEUTUNG = {
    "naoh-2": (
        "Auslöschung in `_with_water_autoprotolysis` (Base-Zweig): [H⁺] = (−c + √(c² + 4Kw))/2 "
        "zieht zwei fast gleiche Zahlen voneinander ab; bei c ≥ 1 M bleibt nur Rundungsrauschen. "
        "10 M NaOH → pH 15,05 statt 15,00. Stabil wäre [H⁺] = 2Kw/(c + √(c² + 4Kw))."
    ),
    "stark-konz": (
        "`ph_core.exact_ph` sucht per Bisektion nur in [0, 14] und klemmt am Rand: Ergebnis pH 0,00 "
        "statt −0,05. Die Näherung (−0,10) liegt hier näher an der Wahrheit als der 'exakte' Wert."
    ),
    "schwach-konz": "wie stark-konz: Klemme bei pH 0 — 0,00 statt −0,79.",
    "starkebase-konz": "Spiegelbild: Klemme bei pH 14 — 14,00 statt 14,05.",
}


def ph_pruefen(_: argparse.Namespace) -> int:
    import re

    from chemdraw_tool.server import calculate_ph

    daten = json.loads(PH_AUFGABEN.read_text(encoding="utf-8"))["aufgaben"]
    zeilen_ab, zeilen_alle = [], []
    gruen = rot = 0
    for a in daten:
        r = _ph_rechne(a["topic"], a["parameter"])
        ist = r[a["feld"]]
        diff = ist - a["erwartet"]
        ok = abs(diff) <= a["toleranz"]
        # Was der Nutzer liest: die Überschrift des Tools, auf 2 Stellen.
        text = calculate_ph(topic=a["topic"], **a["parameter"])
        kopf = re.search(r"\*\*pH = (-?[\d.]+)\*\*", text)
        tool_ph = float(kopf.group(1)) if kopf and a["feld"] == "ph" else None
        tool_ok = tool_ph is None or abs(tool_ph - a["erwartet"]) <= 0.0051
        naeherung = r.get("ph_approx", r.get("ph_henderson_hasselbalch", r.get("ph_naive")))
        status = "grün" if ok and tool_ok else "rot"
        gruen += status == "grün"
        rot += status == "rot"
        param = ", ".join(f"{k}={v}" for k, v in a["parameter"].items())
        zeile = (
            f"| {a['id']} | {a['topic']} | {param} | {a['erwartet']:.4g} | {ist:.4g} | {diff:+.2g} | "
            f"{'' if tool_ph is None else f'{tool_ph:.2f}'} | "
            f"{'' if naeherung is None else f'{naeherung:.2f}'} | {status} | {a['quelle']} |"
        )
        zeilen_alle.append(zeile)
        if status == "rot":
            zeilen_ab.append(zeile)
    kopf_tab = [
        "| Aufgabe | Thema | Parameter | Referenz | ph_calc | Δ | Tool-Kopf | Näherung | Status | Quelle/Zweck |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    md = [
        "# pH-Aufgaben — Masse-Evaluation",
        "",
        f"Stand {dt.date.today().isoformat()} · `uv run python scripts/masse_eval.py ph` · offline, < 5 s",
        "",
        f"**{len(daten)} Aufgaben: {gruen} grün · {rot} rot.** Referenz aus `tests/identity/ph-aufgaben.json` "
        "(sympy, Polynomwurzel der Ladungsbilanz — Herleitung je Aufgabe in der Datei). Geprüft werden "
        "der Rückgabewert von `ph_calc` (Toleranz in der Datei, pH ±0,005) UND die Überschrift, die "
        "`calculate_ph` dem Nutzer zeigt (auf 2 Stellen gerundet). Spalte *Näherung* = Lehrbuchnäherung "
        "bzw. Henderson-Hasselbalch bzw. −log c, nur zur Einordnung, nicht geprüft.",
        "",
        "## Abweichungen",
        "",
    ]
    md += (kopf_tab + zeilen_ab) if zeilen_ab else ["Keine."]
    rote_ids = {z.split(" | ")[0].lstrip("| ") for z in zeilen_ab}
    deutung = [f"- **{i}**: {PH_DEUTUNG[i]}" for i in PH_DEUTUNG if i in rote_ids]
    ungedeutet = sorted(rote_ids - set(PH_DEUTUNG))
    if deutung or ungedeutet:
        md += ["", "### Deutung", ""] + deutung + [f"- **{i}**: noch ungedeutet" for i in ungedeutet]
    md += ["", "## Alle Aufgaben", ""] + kopf_tab + zeilen_alle + [""]
    ziel = EVIDENZ / "ph.md"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("\n".join(md), encoding="utf-8")
    print(f"{len(daten)} Aufgaben: {gruen} grün, {rot} rot → {ziel.relative_to(REPO)}")
    for z in zeilen_ab:
        print("  " + z)
    return 0


# --- Identitätsbericht -------------------------------------------------------

PROTOKOLL = EVIDENZ / "identitaet-lauf.json"

# Handdeutung einzelner Fälle (Eingabe → Satz), nach Sichtung des Laufs.
IDENT_DEUTUNG: dict[str, str] = {
    "chloroxylenol": (
        "OPSIN (0,0 s, offline) zerlegt den Trivialnamen systematisch in chloro-xylen-ol und baut "
        "ein nicht-aromatisches Cyclohexadienol (CC1C(=CC=CC1(C)O)Cl) — gemeint ist PCMX, "
        "4-Chlor-3,5-dimethylphenol. OPSIN gewinnt vor PubChem, darum fragt niemand nach."
    ),
    "methyldopa": (
        "OPSIN (offline, 0,0 s) liest 'methyl' + 'dopa' als N-Methyl-L-DOPA (CN[C@H](C(=O)O)…); "
        "Methyldopa ist α-Methyl-DOPA. Zweiter OPSIN-Fehlgriff bei einem Trivialnamen."
    ),
    "methylthioninium chloride": (
        "OPSIN baut aus 'methyl-thioninium' einen Methylthiepinium-Ring ([Cl-].CC=1[SH+]C=CC=CC=CC1) "
        "statt Methylenblau — dritter OPSIN-Fehlgriff, wieder offline in 0,0 s."
    ),
    "Bendamustin": "PubChem führt den deutschen Namen beim Hydrochlorid — Salz statt Wirkstoff.",
    "(−)-Ephedrin": (
        "PubChem selbst ordnet das Synonym '(−)-Ephedrin' CID 104213 zu (1-Brom-3-methyl-5-nitrobenzol; "
        "per curl auf /compound/name/…/cids nachgeprüft, mit Unicode-Minus und ASCII-Minus). "
        "Fehler im PubChem-Synonymindex; die Kaskade übernimmt den ersten Treffer ungeprüft."
    ),
    "Prussian blue": "Eisen-Cyanid-Gerüst; Wikidata und PubChem modellieren den Komplex verschieden — kein Zeichenfall.",
    "Berliner Blau": "wie Prussian blue.",
    # Nachgeprüft 05.11. per PubChem-Titel beider InChIKeys (erwartet vs. erhalten):
    "tropicamide": (
        "OPSIN (0,0 s, offline) liest 'tropic-amide' und baut das Amid der Tropasäure "
        "(C(C(CO)c1ccccc1)(=O)N) — vierter OPSIN-Fehlgriff bei einem Trivialnamen."
    ),
    "Tropicamid": "wie tropicamide (OPSIN).",
    "Risperidon": (
        "PubChem führt den deutschen Namen als eigenes Record CID 44402564 (C23H29FN4O2, Dihydro-Form); "
        "per curl auf /compound/name/Risperidon/cids nachgeprüft. Synonymfehler bei PubChem, wie (−)-Ephedrin."
    ),
    "fumaric acid": (
        "Referenzfehler: Wikidata Q125026916 (Formel C20H33N3) ist nicht Fumarsäure; der Resolver liefert "
        "PubChems Fumaric Acid (C4H4O4). Lehrbuch-Liste beim nächsten `liste`-Lauf auf Q139857 pinnen."
    ),
    "tenofovir disoproxil": (
        "Referenzfehler: Wikidata Q155954 trägt den InChIKey von Tenofovir (C9H14N5O4P), die Eingabe heißt "
        "aber Disoproxil; der Resolver liefert PubChems Tenofovir Disoproxil (C19H30N5O10P) — richtig."
    ),
    "doxycycline": (
        "Tautomer: gleiche Formel C22H24N2O8, PubChem modelliert die Carboximidsäure-Form; den "
        "Wikidata/ChEMBL-Schlüssel kennt PubChem nicht. Kein falscher Stoff."
    ),
    "Doxycyclin": "wie doxycycline (Tautomer).",
    "rifabutin": (
        "Gleiche Formel C46H62N4O11, den erwarteten Schlüssel kennt PubChem nicht; erhalten ist PubChems "
        "Rifabutin. Tautomer-/Darstellungsunterschied der Referenz, kein falscher Stoff."
    ),
    "cyanocobalamin": (
        "Gleiche Formel C63H88CoN14O14P; Cobalt-Komplex, von Wikidata und PubChem verschieden modelliert "
        "(wie Prussian blue). PubChems Titel des Erhaltenen: Cyanocobalamin."
    ),
    "Hydroxycobalamin": "Cobalt-Komplex, PubChem-Record als Hydrat mit anderer Ladungsschreibweise — wie cyanocobalamin.",
    "sodium calcium edetate": "Anderes Salz-Verhältnis (CaNa₂ erwartet, CaNa erhalten); gleicher Wirkstoff.",
}

_ART_TEXT = {
    "skelett": "anderes Gerüst — falscher Stoff",
    "stereo": "gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer)",
    "ladung": "gleicher Stoff, andere Protonierung/Salzform",
    "salz": "gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich)",
}


def _pubchem_smiles(key: str) -> str | None:
    """Nur zur EINORDNUNG eines roten Falls, nie als Erwartung."""
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/"
        f"{key}/property/SMILES,Title/JSON"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            p = json.load(resp)["PropertyTable"]["Properties"][0]
        time.sleep(0.3)
        return p.get("SMILES") or p.get("IsomericSMILES")
    except (OSError, KeyError, IndexError, ValueError):
        return None


def _nachklassifizieren(rot: list[dict], liste: dict[str, dict]) -> None:
    """Ältere Protokolle kennen 'salz' noch nicht: per Elternfragment nachziehen."""
    from rdkit import Chem

    sys.path.insert(0, str(REPO / "scripts"))
    from identitaet import elternkey

    for e in rot:
        if e.get("art") not in ("skelett", "stereo") or not e.get("erhalten"):
            continue
        ref = liste[e["eingabe"]].get("smiles_referenz")
        smi = _pubchem_smiles(e["erhalten"])
        if not (ref and smi):
            continue
        a = elternkey(Chem.MolFromSmiles(smi))
        if a and a == elternkey(Chem.MolFromSmiles(ref)):
            e["art"] = "salz"


def _chembl_namen(keys: list[str]) -> dict[str, str]:
    namen: dict[str, str] = {}
    for start in range(0, len(keys), 40):
        teil = keys[start : start + 40]
        url = CHEMBL + "?" + urllib.parse.urlencode(
            {
                "molecule_structures__standard_inchi_key__in": ",".join(teil),
                "only": "pref_name,molecule_structures",
                "limit": 1000,
            }
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for m in json.load(resp)["molecules"]:
                    k = (m.get("molecule_structures") or {}).get("standard_inchi_key")
                    if k and m.get("pref_name"):
                        namen[k] = m["pref_name"].lower()
        except OSError:
            pass
        time.sleep(0.5)
    return namen


def identitaet_bericht(_: argparse.Namespace) -> int:
    liste = {e["eingabe"]: e for e in json.loads(LISTE.read_text(encoding="utf-8"))["stoffe"]}
    # Nur Eingaben, die (noch) in der Liste stehen — die Liste kann nach dem Lauf
    # strenger gefiltert worden sein.
    lauf = [e for e in json.loads(PROTOKOLL.read_text(encoding="utf-8")) if e["eingabe"] in liste]
    zahl = Counter(e["status"] for e in lauf)
    rot = [e for e in lauf if e["status"] == "rot"]
    gelb = [e for e in lauf if e["status"] == "gelb"]
    _nachklassifizieren(rot, liste)
    namen = _chembl_namen(sorted({e["erhalten"] for e in rot if e.get("erhalten")}))
    zeiten = sorted(e["sekunden"] for e in lauf)
    gesamt = sum(zeiten)

    def q(p: float) -> float:
        return zeiten[min(len(zeiten) - 1, int(p * len(zeiten)))]

    md = [
        "# Identität — Masse-Evaluation",
        "",
        f"Lauf {dt.date.fromtimestamp(PROTOKOLL.stat().st_mtime).isoformat()} · "
        "`uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json "
        "--protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: "
        "`uv run python scripts/masse_eval.py identitaet`",
        "",
        f"**{len(lauf)} Eingaben ({len({liste[e['eingabe']]['inchikey'] for e in lauf if e['eingabe'] in liste})} Stoffe): "
        f"{zahl['gruen']} grün · {zahl['gelb']} gelb · {zahl['rot']} rot.**",
        "",
        f"Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). "
        f"Laufzeit gesamt {gesamt / 60:.0f} min · Median {q(0.5):.1f} s · 90 % ≤ {q(0.9):.1f} s · "
        f"langsamste {zeiten[-1]:.1f} s je Eingabe (inkl. 0,3 s Pause).",
        "",
        "## Rot nach Art",
        "",
        "| Art | Zahl | Bedeutung |",
        "|---|---:|---|",
    ]
    arten = Counter(e.get("art", "nicht aufgelöst") for e in rot)
    for art, n in arten.most_common():
        md.append(f"| {art} | {n} | {_ART_TEXT.get(art, 'Kaskade findet nichts, obwohl die Quelle den Stoff führt')} |")
    # Nicht aufgelöst nach Sprache: deutsche Wikidata-Labels ohne PubChem-Synonym
    # sind der erwartete Hauptfall (seit dem NCI-Fix cc13e47 rot statt gelb).
    sprachen = Counter(liste[e["eingabe"]].get("sprache", "?")[:2] for e in rot if "art" not in e)
    if sprachen:
        md += ["", "Nicht aufgelöst nach Sprache der Eingabe: " + " · ".join(f"{sp} {n}" for sp, n in sprachen.most_common())]
    md += ["", "## Alle roten Fälle", ""]
    for art in [a for a, _ in arten.most_common()]:
        md += [
            f"### {art}",
            "",
            "| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |",
            "|---|---|---|---|---|---|",
        ]
        for e in rot:
            if e.get("art", "nicht aufgelöst") != art:
                continue
            ref = liste.get(e["eingabe"], {})
            erhalten = e.get("erhalten", "—")
            deutung = IDENT_DEUTUNG.get(e["eingabe"], _ART_TEXT.get(art, e["text"]))
            md.append(
                f"| {e['eingabe']} | {ref.get('sprache', '')[:2]} | `{e['erwartet']}` | `{erhalten}` | "
                f"{namen.get(erhalten, '')} | {deutung} |"
            )
        md.append("")
    md += ["## Gelb", "", "| Eingabe | Grund |", "|---|---|"]
    md += [f"| {e['eingabe']} | {e['text']} |" for e in gelb] or ["| — | — |"]
    md += [
        "",
        "## Langsamste Eingaben",
        "",
        "| Eingabe | Sekunden | Status |",
        "|---|---:|---|",
    ]
    for e in sorted(lauf, key=lambda e: -e["sekunden"])[:10]:
        md.append(f"| {e['eingabe']} | {e['sekunden']:.1f} | {e['status']} |")
    md.append("")
    ziel = EVIDENZ / "identitaet.md"
    ziel.write_text("\n".join(md), encoding="utf-8")
    print(f"{len(lauf)} Eingaben: {dict(zahl)} · Arten {dict(arten)} → {ziel.relative_to(REPO)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="befehl", required=True)
    sub.add_parser("liste", help="Stoffliste aus Wikidata/ChEMBL bauen").set_defaults(f=baue_liste)
    sub.add_parser("ir", help="IR-Regelabdeckung (offline)").set_defaults(f=ir_abdeckung)
    sub.add_parser("identitaet", help="Bericht aus dem Identitätsprotokoll").set_defaults(f=identitaet_bericht)
    sub.add_parser("ph", help="pH-Aufgaben gegen ph_calc (offline)").set_defaults(f=ph_pruefen)
    sub.add_parser("ph-referenz", help="Referenzwerte mit sympy neu rechnen").set_defaults(f=ph_referenz)
    args = parser.parse_args()
    return args.f(args)


if __name__ == "__main__":
    raise SystemExit(main())
