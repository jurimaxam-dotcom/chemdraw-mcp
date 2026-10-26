// Stereo-Varianten (Grundlagen, Etappe 3): der Stereo-Hinweis im Molekuel-
// Panel bekommt „Show variants". Der Klick holt alle Stereoisomere ueber
// generate_molecule(stereo_variants=true) und zeigt sie wie die Isomer-Auswahl
// eines Familiennamens; ein Klick auf eine Variante zeichnet sie mit Keilen.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import { AppContext } from "../AppContext";
import DatabaseView from "../DatabaseView";
import MoleculeView, { VARIANTS_LOAD_ERROR } from "../MoleculeView";
import { DATABASE, MOLECULE, lookupFailure, lookupSuccess } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const CENTER = { kind: "atom", atoms: [1], label: "Unspecified stereocenter" };
const RACEMATE = { ...MOLECULE, name: "Ibuprofen", functionalGroups: [], stereoWarnings: [CENTER] };
const VARIANTS = {
  type: "ambiguous",
  name: "Ibuprofen",
  message: "'Ibuprofen' has 2 stereoisomers. Nothing was drawn.",
  candidates: [
    { label: "(R)-Ibuprofen", name: "(R)", smiles: "CC(C)Cc1ccc([C@@H](C)C(=O)O)cc1", svg: MOLECULE.svg },
    { label: "(S)-Ibuprofen", name: "(S)", smiles: "CC(C)Cc1ccc([C@H](C)C(=O)O)cc1", svg: MOLECULE.svg },
  ],
};

function setup(data, respond = () => lookupSuccess(VARIANTS)) {
  const calls = [];
  const app = {
    callServerTool: async (req) => {
      calls.push(req);
      return respond(req);
    },
  };
  const view = render(
    React.createElement(AppContext.Provider, { value: app }, React.createElement(MoleculeView, { data }))
  );
  return { ...view, calls };
}

const showButton = (container) => buttonByText(container, "Show variants");

test("Knopf erscheint am Stereo-Hinweis, ohne etwas nachzuladen", () => {
  const { container, calls, unmount } = setup(RACEMATE);
  const button = showButton(container);
  assert.ok(button, "kein Knopf Show variants");
  assert.ok(container.querySelector("[data-testid='stereo-note']").parentElement.contains(button), "Knopf nicht am Hinweis");
  assert.equal(calls.length, 0);
  unmount();
});

test("ohne offene Stereoelemente kein Knopf", () => {
  const { container, unmount } = setup(MOLECULE);
  assert.equal(showButton(container), undefined);
  unmount();
});

test("ueber drei offenen Elementen kein Knopf (Server-Grenze gespiegelt)", () => {
  const four = [0, 1, 2, 3].map((i) => ({ ...CENTER, atoms: [i] }));
  const { container, unmount } = setup({ ...RACEMATE, stereoWarnings: four });
  assert.ok(container.querySelector("[data-testid='stereo-note']"), "Hinweis selbst bleibt");
  assert.equal(showButton(container), undefined);
  unmount();
});

test("Datenblatt bekommt keinen Varianten-Knopf", () => {
  const view = render(
    React.createElement(
      AppContext.Provider,
      { value: {} },
      React.createElement(DatabaseView, { data: { ...DATABASE, stereoWarnings: [CENTER] } })
    )
  );
  assert.equal(showButton(view.container), undefined);
  view.unmount();
});

test("Klick holt die Varianten per SMILES und zeigt sie mit Label und Bild", async () => {
  const { container, calls, unmount } = setup(RACEMATE);
  await click(showButton(container));
  assert.deepEqual(calls, [
    {
      name: "generate_molecule",
      arguments: { name_or_smiles: MOLECULE.properties.smiles, stereo_variants: true, label: "Ibuprofen" },
    },
  ]);
  const candidates = [...container.querySelectorAll("button.candidate")];
  assert.deepEqual(
    candidates.map((b) => textOf(b.querySelector(".candidate-label"))),
    ["(R)-Ibuprofen", "(S)-Ibuprofen"]
  );
  assert.ok(candidates.every((b) => b.querySelector("svg")), "Variante ohne Vorschaubild");
  assert.match(textOf(container), /2 stereoisomers/);
  unmount();
});

test("Variante anklicken zeichnet sie; zurueck fuehrt zur Struktur", async () => {
  const drawn = { ...MOLECULE, name: "(S)-Ibuprofen", properties: { smiles: VARIANTS.candidates[1].smiles } };
  const { container, calls, unmount } = setup(RACEMATE, (req) =>
    lookupSuccess(req.arguments.stereo_variants ? VARIANTS : drawn)
  );
  await click(showButton(container));
  const s = [...container.querySelectorAll("button.candidate")][1];
  await click(s);
  assert.equal(calls[1].arguments.name_or_smiles, VARIANTS.candidates[1].smiles);
  assert.match(textOf(container.querySelector(".panel-title")), /\(S\)-Ibuprofen/);

  await click(buttonByText(container, "Back to the structure"));
  assert.equal(textOf(container.querySelector(".panel-title")), "Ibuprofen");
  assert.ok(showButton(container), "Knopf nach dem Zurueck weg");
  unmount();
});

test("zweiter Klick nutzt die geholten Varianten, kein zweiter Aufruf", async () => {
  const { container, calls, unmount } = setup(RACEMATE);
  await click(showButton(container));
  await click(buttonByText(container, "Back to the structure"));
  await click(showButton(container));
  assert.equal(calls.length, 1);
  assert.equal(container.querySelectorAll("button.candidate").length, 2);
  unmount();
});

test("Fehlschlag zeigt einen ruhigen Satz und bleibt wiederholbar", async () => {
  let fail = true;
  const { container, calls, unmount } = setup(RACEMATE, () => (fail ? lookupFailure() : lookupSuccess(VARIANTS)));
  await click(showButton(container));
  assert.match(textOf(container), new RegExp(VARIANTS_LOAD_ERROR.slice(0, 30)));
  assert.equal(container.querySelectorAll("button.candidate").length, 0);
  fail = false;
  await click(showButton(container));
  assert.equal(calls.length, 2);
  assert.equal(container.querySelectorAll("button.candidate").length, 2);
  unmount();
});

test("Doppelklick waehrend des Ladens loest nur einen Aufruf aus", async () => {
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  const { container, calls, unmount } = setup(RACEMATE, async () => {
    await pending;
    return lookupSuccess(VARIANTS);
  });
  const button = showButton(container);
  await click(button);
  await click(button);
  assert.equal(calls.length, 1);
  await act(async () => {
    release();
  });
  assert.equal(container.querySelectorAll("button.candidate").length, 2);
  unmount();
});
