// Text für Claude (U4b): Claude sieht kein Bild, nur diesen Text.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  MAX_CONTEXT,
  buildModelContext,
  moleculeContext,
  databaseContext,
  reactionContext,
  mechanismContext,
  genericContext,
  studyItems,
} from "./modelContext.js";

const MOLECULE = {
  type: "molecule",
  name: "Aspirin",
  formula: "C9H8O4",
  properties: { smiles: "CC(=O)Oc1ccccc1C(=O)O", mw: "180.16", cas: "50-78-2", pubchemTitle: "Aspirin", cid: "2244" },
  atoms: [{ idx: 0, el: "C" }, { idx: 1, el: "C" }, { idx: 2, el: "O" }],
  functionalGroups: [
    { name: "Ester", atomIndices: [0, 1, 2], count: 1 },
    { name: "Aromat", atomIndices: [3, 4, 5, 6, 7, 8], count: 1 },
  ],
  stereoWarnings: [{ kind: "atom", atoms: [1] }],
};

test("Molekül: Stoff, Formel, SMILES, Ansicht, Gruppen mit Anzahl, Stereo", () => {
  const text = moleculeContext(MOLECULE, { view: "structure", drawing: "skeletal" });
  assert.match(text, /Aspirin/);
  assert.match(text, /C9H8O4/);
  assert.match(text, /CC\(=O\)Oc1ccccc1C\(=O\)O/);
  assert.match(text, /Structure/);
  assert.match(text, /2D skeletal formula/);
  assert.match(text, /Ester ×1/);
  assert.match(text, /Aromatic ring ×1/);
  assert.match(text, /1 undefined stereocentre/);
  assert.doesNotMatch(text, /Pinned/);
});

test("Molekül: Ansichten All H, 3D und Daten werden genannt", () => {
  assert.match(moleculeContext(MOLECULE, { view: "structure", drawing: "all_h" }), /all hydrogens/i);
  assert.match(moleculeContext(MOLECULE, { view: "structure", is3d: true }), /3D/);
  assert.match(moleculeContext(MOLECULE, { view: "data" }), /Data sheet/);
});

test("Molekül: festgehaltene Gruppe bzw. Atom steht drin", () => {
  const group = moleculeContext(MOLECULE, { view: "structure", pinned: { kind: "group", name: "Ester" } });
  assert.match(group, /Pinned selection: the Ester group/);
  assert.match(group, /–COO–/);
  const atom = moleculeContext(MOLECULE, { view: "structure", pinned: { kind: "atom", idx: 2, el: "O" } });
  assert.match(atom, /Pinned selection: .*oxygen atom/i);
  assert.match(atom, /index 2/);
});

test("Lernmodus: nennt Verdecktes und bittet, es nicht zu verraten", () => {
  const items = studyItems(MOLECULE);
  assert.deepEqual(items.map((i) => i.key), ["name", "formula", "mass", "cas", "group:Ester", "group:Aromat"]);
  const text = moleculeContext(MOLECULE, { view: "study", revealed: ["formula", "group:Ester"] });
  assert.match(text, /Study mode/);
  assert.match(text, /Still covered: name, molar mass, CAS, functional group 2 \(Aromatic ring\)/);
  assert.match(text, /Revealed: formula, functional group 1 \(Ester\)/);
  assert.match(text, /4 of 6 still covered/);
  assert.match(text, /[Dd]o not reveal/);
  const all = moleculeContext(MOLECULE, { view: "study", revealed: items.map((i) => i.key) });
  assert.match(all, /Everything is revealed/);
});

test("Datenblatt, Reaktion, Mechanismus: knappe Fassungen", () => {
  const db = databaseContext({ name: "Aspirin", smiles: "CCO", formula: "C2H6O", sources: [{ source: "PubChem" }, { source: "ChEBI" }], functionalGroups: [] }, { view: "data" });
  assert.match(db, /Data sheet/);
  assert.match(db, /PubChem, ChEBI/);
  const r = reactionContext({ name: "Fischer esterification", reactants: [{ name: "acetic acid" }, { name: "ethanol" }], products: [{ name: "ethyl acetate" }], conditions: "H2SO4", balance: { balanced: true } });
  assert.match(r, /acetic acid \+ ethanol → ethyl acetate/);
  assert.match(r, /H2SO4/);
  assert.match(r, /balanced/);
  const m = mechanismContext({ name: "SN2", reaction_type: "sn2", steps: [{ label: "A" }, { label: "B" }] }, { mode: "step", step: 1 });
  assert.match(m, /step 2 of 2/);
  assert.match(m, /B/);
  assert.match(genericContext("spectrum", { name: "Aspirin", spectrum_type: "IR" }), /IR spectrum/);
});

test("Stapel: gemeinsamer Text plus die Karte im Fokus, nichts überschreibt sich", () => {
  const a = { text: "A full", summary: "Aspirin (C9H8O4)", focus: 0 };
  const b = { text: "B full with pin", summary: "Caffeine (C8H10N4O2)", focus: 2 };
  const c = { text: "C full", summary: "Ethanol (C2H6O)", focus: 1 };
  const text = buildModelContext([a, b, c]);
  assert.match(text, /3 cards/);
  assert.match(text, /Aspirin/);
  assert.match(text, /Caffeine/);
  assert.match(text, /Ethanol/);
  assert.match(text, /card 2 of 3/);
  assert.match(text, /B full with pin/);
  assert.doesNotMatch(text, /A full|C full/);
  assert.equal(buildModelContext([a]), "A full");
  assert.equal(buildModelContext([]), "");
});

test("nie länger als MAX_CONTEXT Zeichen", () => {
  const huge = { ...MOLECULE, name: "x".repeat(9000) };
  assert.ok(moleculeContext(huge, { view: "structure" }).length <= MAX_CONTEXT);
  assert.ok(buildModelContext([{ text: "y".repeat(9000), summary: "s", focus: 0 }]).length <= MAX_CONTEXT);
  assert.ok(MAX_CONTEXT <= 4000);
});
