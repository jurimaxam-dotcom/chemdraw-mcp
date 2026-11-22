import test from "node:test";
import assert from "node:assert/strict";
import { groupBonds, groupInfo } from "./groupInfo.js";

// Aspirin-Ausschnitt: Acetyl-C(1) mit =O(2) und -O(3), Bindungslaenge 1.5.
// 2 und 3 liegen im 120°-Winkel ~2.6 auseinander — das ist KEINE Bindung.
const ATOMS = [
  { idx: 0, x: 0, y: 0 },
  { idx: 1, x: 1.5, y: 0 },
  { idx: 2, x: 2.25, y: 1.3 },
  { idx: 3, x: 2.25, y: -1.3 },
  { idx: 4, x: 3.75, y: -1.3 },
];

test("verbindet nur Gruppenatome im Bindungsabstand", () => {
  const bonds = groupBonds(ATOMS, [1, 2, 3]);
  const pairs = bonds.map(([a, b]) => [a.idx, b.idx].sort().join("-")).sort();
  assert.deepEqual(pairs, ["1-2", "1-3"]);
});

test("Atome ausserhalb der Gruppe bekommen keinen Glow", () => {
  const bonds = groupBonds(ATOMS, [3, 4]);
  assert.deepEqual(bonds.map(([a, b]) => [a.idx, b.idx]), [[3, 4]]);
});

test("ohne Atome oder Gruppe gibt es nichts zu leuchten", () => {
  assert.deepEqual(groupBonds([], [1, 2]), []);
  assert.deepEqual(groupBonds(ATOMS, []), []);
  assert.deepEqual(groupBonds(undefined, undefined), []);
});

test("Servernamen werden zu englischem Namen und Kurzformel", () => {
  const acid = groupInfo("Carbonsäure");
  assert.equal(acid.label, "Carboxylic acid");
  assert.equal(acid.formula, "–COOH");
  assert.equal(acid.note, undefined, "kein Erklaersatz mehr");
  assert.equal(groupInfo("Aromat").label, "Aromatic ring");
});

test("ein unbekannter Gruppenname bleibt lesbar statt leer", () => {
  const info = groupInfo("Azid");
  assert.equal(info.label, "Azid");
  assert.equal(info.formula, "");
});
