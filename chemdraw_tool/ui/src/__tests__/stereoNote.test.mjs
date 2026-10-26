// Unbestimmte Stereoelemente (Etappe 4): eine Hinweiszeile unter der Struktur,
// Hover/Klick hebt die betroffenen Atome mit demselben Glow hervor wie die
// funktionellen Gruppen — kein zweiter Mechanismus.
import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import React, { act } from "react";

import { AppContext } from "../AppContext";
import DatabaseView from "../DatabaseView";
import MoleculeView from "../MoleculeView";
import { ATOMS, DATABASE, MOLECULE } from "./fixtures.mjs";
import { click, render, textOf } from "./harness.mjs";

// jsdom misst alles mit 0 px — dann rechnet getSvgTransform keine Lage aus
// und der Glow bliebe immer leer. Eine feste Flaeche macht ihn pruefbar.
let original;
before(() => {
  original = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = () => ({ left: 0, top: 0, width: 400, height: 200, right: 400, bottom: 200, x: 0, y: 0 });
});
after(() => {
  Element.prototype.getBoundingClientRect = original;
});

const WARNINGS = [
  { kind: "atom", atoms: [1], label: "Unspecified stereocenter" },
  { kind: "atom", atoms: [2], label: "Unspecified stereocenter" },
];

function renderMolecule(data) {
  return render(
    React.createElement(AppContext.Provider, { value: {} }, React.createElement(MoleculeView, { data }))
  );
}

const hint = (container) => container.querySelector("[data-testid='stereo-note']");
const glow = (container) => container.querySelector(".group-glow");

test("ohne unbestimmte Stereoelemente keine Hinweiszeile", () => {
  const { container, unmount } = renderMolecule(MOLECULE);
  assert.equal(hint(container), null);
  unmount();
});

test("zeigt die Zahl der unbestimmten Zentren", () => {
  const { container, unmount } = renderMolecule({ ...MOLECULE, functionalGroups: [], stereoWarnings: WARNINGS });
  assert.equal(textOf(hint(container)), "2 unspecified stereocenters");
  assert.equal(glow(container), null, "Glow ohne Hover");
  unmount();
});

test("nennt Doppelbindungen getrennt", () => {
  const warnings = [...WARNINGS.slice(0, 1), { kind: "double_bond", atoms: [0, 1], label: "x" }];
  const { container, unmount } = renderMolecule({ ...MOLECULE, stereoWarnings: warnings });
  assert.equal(textOf(hint(container)), "1 unspecified stereocenter · 1 unspecified double bond (E/Z)");
  unmount();
});

test("Hover hebt die betroffenen Atome hervor, Verlassen nimmt es zurueck", async () => {
  const { container, unmount } = renderMolecule({ ...MOLECULE, functionalGroups: [], stereoWarnings: WARNINGS });
  const button = hint(container).querySelector("button");
  await act(async () => {
    button.dispatchEvent(new window.MouseEvent("mouseover", { bubbles: true }));
  });
  const g = glow(container);
  assert.ok(g, "kein Glow beim Hover");
  // Atome 1 und 2 liegen im Bindungsabstand → genau eine Linie, kein Kreis.
  assert.equal(g.querySelectorAll("line").length, 1);
  assert.equal(button.getAttribute("aria-pressed"), "true");
  await act(async () => {
    button.dispatchEvent(new window.MouseEvent("mouseout", { bubbles: true }));
  });
  assert.equal(glow(container), null, "Glow bleibt nach dem Verlassen");
  unmount();
});

test("Klick haelt die Hervorhebung fest, zweiter Klick loest sie", async () => {
  const { container, unmount } = renderMolecule({ ...MOLECULE, functionalGroups: [], stereoWarnings: [WARNINGS[0]] });
  const button = hint(container).querySelector("button");
  await click(button);
  const g = glow(container);
  assert.ok(g, "Klick zeigt keinen Glow");
  assert.equal(g.querySelectorAll("circle").length, 1, "einzelnes Zentrum = ein Fleck");
  await click(button);
  assert.equal(glow(container), null);
  unmount();
});

test("ohne zeichenbare Atome (abgekuerzt) bleibt der Hinweis, aber ohne Knopf", () => {
  const warnings = [{ kind: "atom", atoms: [], label: "Unspecified stereocenter" }];
  const { container, unmount } = renderMolecule({ ...MOLECULE, atoms: [], stereoWarnings: warnings });
  assert.equal(textOf(hint(container)), "1 unspecified stereocenter");
  assert.equal(hint(container).querySelector("button"), null);
  unmount();
});

test("das Datenblatt zeigt denselben Hinweis in der Struktur-Ansicht", async () => {
  const { container, unmount } = render(
    React.createElement(DatabaseView, { data: { ...DATABASE, atoms: ATOMS, stereoWarnings: WARNINGS } })
  );
  const structureTab = [...container.querySelectorAll("button")].find((b) => b.textContent.trim() === "Structure");
  await click(structureTab);
  assert.equal(textOf(hint(container)), "2 unspecified stereocenters");
  unmount();
});
