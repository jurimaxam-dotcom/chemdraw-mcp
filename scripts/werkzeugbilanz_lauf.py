#!/usr/bin/env python3
"""Führt alle 23 Tools einmal in-process aus und sichert Ausgaben + Laufzeit für scripts/werkzeugbilanz.py.

Aufruf (Projektordner, braucht Netz für Namen/PubChem):
    HOME=<wegwerf> uv run python scripts/werkzeugbilanz_lauf.py <ausgabe-ordner>
Testfixtures (Scope-Einträge, Kalibrierstandards, Einwaagen) kommen aus tests/, damit die
Beispiele dieselben sind wie im Gate. Ausgabeordner enthält je Tool <tool>.json, die Dateien
der Tools in <DIR>-Unterordnern und _ergebnis.json (ok, Sekunden, Typ, Länge).
"""
import importlib
import json
import pathlib
import sys
import time
import traceback

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(exist_ok=True)
sys.path.insert(0, ".")
s = importlib.import_module("chemdraw_tool.server")

for a in [x for x in dir(s) if x.endswith("_DIR")]:
    p = OUT / a.lower()
    p.mkdir(exist_ok=True)
    setattr(s, a, p)
tc = importlib.import_module("tests.test_server_calibration")
tcon = importlib.import_module("tests.test_server_content")
ts = importlib.import_module("tests.test_server_scope")

calls = {
 "generate_molecule": dict(name_or_smiles="ibuprofen"),
 "batch_generate": dict(molecules=["benzene","toluene","phenol"]),
 "compare_molecules": dict(structures=["aspirin","paracetamol"]),
 "generate_reaction": dict(reactants=["acetic acid","ethanol"], products=["ethyl acetate","water"], conditions="H2SO4, Δ", arrow="equilibrium"),
 "generate_mechanism": dict(reaction_type="sn2", substrates=["(R)-2-bromobutane","cyanide"], current_step=2),
 "generate_3d": dict(name_or_smiles="caffeine"),
 "generate_spectrum": dict(spectrum_type="ir", title="Aspirin", peaks=[{"position":1750,"intensity":1,"label":"C=O Ester"},{"position":1690,"intensity":0.9,"label":"C=O Säure"},{"position":3000,"intensity":0.4,"label":"O-H"}]),
 "generate_tlc": dict(lanes=[{"name":"Edukt","spots":[{"rf":0.30,"label":"Säure"}]},{"name":"Reaktion","spots":[{"rf":0.65,"label":"Ester"}]},{"name":"Co-Spot","spots":[{"rf":0.30},{"rf":0.65}]}], solvent="Hexan/EE 7:3", title="Veresterung"),
 "generate_titration_curve": dict(substance="Essigsäure", pka_values=[4.76], c_acid=0.1, v_acid_ml=25, c_titrant=0.1),
 "generate_species_distribution": dict(substance="Phosphorsäure", pka_values=[2.15,7.2,12.35]),
 "lookup": dict(name="paracetamol", topic="properties"),
 "lookup_molecule_data": dict(name="ibuprofen"),
 "predict_spectrum": dict(structure="aspirin", topic="ir_bands"),
 "calculate_ph": dict(topic="weak_acid", concentration=0.1, pka=4.76),
 "export_anki_deck": dict(deck_name="Beispiel", cards=[{"front":{"text":"Welche Substanz?","structure":"aspirin"},"back":{"text":"Aspirin"}}], deliver="apkg"),
}
calls.update({
 "generate_scope_table": dict(entries=ts.ENTRIES, title="Suzuki scope"),
 "generate_calibration_curve": dict(concentrations=tc.STANDARDS, signals=tc.SIGNALS, substance="Paracetamol", unknown_signals=[tc.SIGNALS[1]*1.1]),
 "generate_pk_curve": dict(dose_mg=500, vd_l=70, ke_per_h=0.15, ka_per_h=1.2, bioavailability=0.8, tau_h=8, drug="Ibuprofen"),
 "generate_dose_response": dict(ec50=10, unit="nM", antagonist_concentration=20, antagonist_kb=10, drug="Agonist A"),
 "calculate_solution": dict(topic="weigh_in", substance="NaOH", concentration=0.1, volume_ml=250),
 "calculate_content": dict(method="titration", weights_mg=tcon.WEIGHTS, measurements=tcon.VOLUMES, factor_mg_per_ml=8.806),
 "calculate_pharmacokinetics": dict(topic="half_life", clearance_l_per_h=5, vd_l=40),
})
res = {}  # alle 23 in einem Lauf
for name, kw in calls.items():
    fn = getattr(s, name)
    t0 = time.time()
    try:
        r = fn(**kw)
        if hasattr(r, "model_dump"):
            r = r.model_dump()
        txt = json.dumps(r, ensure_ascii=False, default=str) if not isinstance(r, str) else r
        res[name] = {"ok": True, "s": round(time.time()-t0,2), "type": (r.get("type") if isinstance(r,dict) else "text"), "len": len(txt), "keys": list(r.keys())[:25] if isinstance(r,dict) else None}
        (OUT / f"{name}.json").write_text(txt[:400000])
    except Exception as e:
        res[name] = {"ok": False, "s": round(time.time()-t0,2), "err": repr(e)[:400]}
        traceback.print_exc()
    print(name, res[name], flush=True)
json.dump(res, open(OUT/"_ergebnis.json","w"), indent=1, ensure_ascii=False)
