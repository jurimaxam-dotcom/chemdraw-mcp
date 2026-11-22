// Platzhalter aus `toolinput`: was die Argumente vor dem Ergebnis hergeben.
import assert from "node:assert/strict";
import { test } from "node:test";

import { placeholderFromInput } from "./placeholder.js";

test("Molekül: Titel aus label, sonst name_or_smiles", () => {
  assert.equal(placeholderFromInput({ name_or_smiles: "CCO", label: "Ethanol" }).title, "Ethanol");
  assert.equal(placeholderFromInput({ name_or_smiles: "aspirin" }).title, "aspirin");
  assert.deepEqual(placeholderFromInput({ name_or_smiles: "aspirin" }).items, []);
});

test("Stapel: Namensliste als beschriftete Platzhalter", () => {
  const p = placeholderFromInput({ molecules: ["aspirin", "caffeine", "ethanol"] });
  assert.equal(p.title, "3 structures");
  assert.deepEqual(p.items, ["aspirin", "caffeine", "ethanol"]);
});

test("Reaktion, Mechanismus, Spektrum, Protein", () => {
  assert.equal(placeholderFromInput({ reactants: ["A", "B"], products: ["C"] }).title, "A + B → C");
  assert.equal(placeholderFromInput({ reactants: ["A"], products: ["C"], name: "Named" }).title, "Named");
  assert.equal(placeholderFromInput({ reaction_type: "sn2", substrates: ["CBr", "[OH-]"] }).title, "SN2 mechanism: CBr + [OH-]");
  assert.equal(placeholderFromInput({ spectrum_type: "IR", title: "" }).title, "IR spectrum");
  assert.equal(placeholderFromInput({ name: "trastuzumab" }).title, "trastuzumab");
  assert.deepEqual(placeholderFromInput({ structures: ["A", "B"] }).items, ["A", "B"]);
});

test("ohne verwertbare Argumente: kein Titel, keine Liste", () => {
  assert.deepEqual(placeholderFromInput({}), { title: "", items: [] });
  assert.deepEqual(placeholderFromInput(undefined), { title: "", items: [] });
  assert.deepEqual(placeholderFromInput({ molecules: [1, null, "x"] }).items, ["x"]);
});
