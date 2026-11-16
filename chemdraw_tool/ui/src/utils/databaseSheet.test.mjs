// Datenblatt aus lookup_molecule_data als Molekül-Ansicht (Etappe 3): die Kernwerte
// stehen im DatabasePayload nur als Zeilen der PubChem-Quelle.
import assert from "node:assert/strict";
import { test } from "node:test";

import { databaseAsMolecule } from "./databaseSheet.js";

const SERVER = {
  type: "database", name: "paracetamol", smiles: "CC(=O)Nc1ccc(O)cc1", molecule_svg: "<svg/>",
  atoms: [{ idx: 0 }], functionalGroups: [{ name: "Amide" }], stereoWarnings: [], foundAs: "Paracetamol",
  sources: [
    { type: "PubChem", source: "PubChem CID 1983", rows: [
      { key: "CID", val: "1983" }, { key: "Molecular formula", val: "C8H9NO2" },
      { key: "Molar mass", val: "151.16 g/mol" }, { key: "CAS No.", val: "103-90-2" }] },
    { type: "GHS", source: "GHS", rows: [{ key: "CAS", val: "nicht diese" }] },
  ],
};

test("Formel, Molmasse, CAS und CID aus den PubChem-Zeilen (Server-Schlüssel)", () => {
  const m = databaseAsMolecule(SERVER);
  assert.equal(m.type, "molecule");
  assert.equal(m.svg, "<svg/>");
  assert.deepEqual(m.properties, { smiles: "CC(=O)Nc1ccc(O)cc1", formula: "C8H9NO2", mw: "151.16 g/mol", cas: "103-90-2", cid: "1983" });
  assert.equal(m.formula, "C8H9NO2");
  assert.deepEqual(m.functionalGroups, SERVER.functionalGroups);
  assert.equal(m.foundAs, "Paracetamol");
  assert.equal(m.name, "paracetamol");
});

test("älterer Schlüssel „CAS“ zählt auch; fehlende Zeilen bleiben leer", () => {
  const m = databaseAsMolecule({ name: "Aspirin", smiles: "CCO", molecule_svg: "<svg/>",
    sources: [{ type: "PubChem", rows: [{ key: "CAS", val: "50-78-2" }] }] });
  assert.equal(m.properties.cas, "50-78-2");
  assert.equal(m.properties.formula, undefined);
  assert.equal(m.properties.mw, undefined);
});

test("ohne Quellen kein Absturz", () => {
  const m = databaseAsMolecule({ name: "x" });
  assert.deepEqual(m.functionalGroups, []);
  assert.equal(m.properties.cas, undefined);
});
