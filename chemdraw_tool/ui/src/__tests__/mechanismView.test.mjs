// Etappe E2 (06.11.2026): das Panel zeigt den Hinweis auf eine konkurrierende Eliminierung und
// zeichnet bei der Fischer-Veresterung ⇌ zwischen den Schritten — jeder Schritt ist ein Gleichgewicht.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import MechanismView from "../MechanismView";
import { render, textOf } from "./harness.mjs";

const SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'></svg>";
const steps = [
  { svg: SVG, label: "Reactants", is_transition_state: false },
  { svg: SVG, label: "Loss of water", is_transition_state: false },
  { svg: SVG, label: "Products", is_transition_state: false },
];

function show(extra) {
  return render(
    React.createElement(MechanismView, {
      data: { type: "mechanism", name: "Test", reaction_type: "x", steps, current_step: 0, ...extra },
    })
  );
}

test("Hinweis auf die Eliminierung steht im Panel", () => {
  const note = "E2 elimination competes: a strong base also removes a β-hydrogen.";
  const { container, unmount } = show({ notes: [note] });
  assert.ok(container.querySelector(".mech-note"), "Hinweiszeile fehlt");
  assert.match(textOf(container), /E2 elimination competes/);
  unmount();
});

test("ohne Hinweis keine leere Hinweiszeile", () => {
  const { container, unmount } = show({ notes: [] });
  assert.equal(container.querySelector(".mech-note"), null);
  unmount();
});

test("Gleichgewicht: zwischen den Schritten steht ⇌ statt →", () => {
  const { container, unmount } = show({ reversible: true });
  assert.equal(container.querySelectorAll("[data-arrow='equilibrium']").length, steps.length - 1);
  assert.equal(container.querySelectorAll("[data-arrow='forward']").length, 0);
  unmount();
});

test("ohne Gleichgewicht bleibt der einfache Pfeil", () => {
  const { container, unmount } = show({});
  assert.equal(container.querySelectorAll("[data-arrow='forward']").length, steps.length - 1);
  assert.equal(container.querySelectorAll("[data-arrow='equilibrium']").length, 0);
  unmount();
});

// Etappe 5 (16.11.2026): Untertitel lesbar statt Rohwert, Übersicht ohne inneren Rollbereich,
// Klick auf einen Schritt öffnet ihn in „Step by step“.
test("Untertitel: lesbare Familie und Schrittzahl statt des Rohwerts, ohne den Titel zu wiederholen", () => {
  const sub = (extra) => {
    const { container, unmount } = show(extra);
    const t = container.querySelector(".panel-subtitle")?.textContent ?? "";
    unmount();
    return t;
  };
  assert.equal(sub({ name: "Test", reaction_type: "sn1" }), "SN1 · 3 steps");
  assert.equal(sub({ name: "Nucleophilic Substitution (SN2) — X", reaction_type: "sn2" }), "3 steps");
  assert.equal(sub({ name: "Fischer esterification — A + B", reaction_type: "fischer_ester", reversible: true }), "3 steps · each step an equilibrium");
  assert.equal(sub({ name: "Test", reaction_type: "fischer_ester" }), "Fischer esterification · 3 steps");
  assert.equal(sub({}), "3 steps", "unbekannte Familie: nur die Schrittzahl");
});

test("Übersicht: die Bühne rollt nicht selbst (kein Rollbereich im Rollbereich)", () => {
  const { container, unmount } = show({});
  const stage = container.querySelector(".mech-stage");
  assert.ok(!/auto|scroll/.test(stage.style.overflow + stage.style.overflowY), `overflow: ${stage.style.overflow}`);
  assert.equal(container.querySelectorAll("[aria-label^='Open step']").length, 3);
  unmount();
});

test("Klick auf einen Schritt der Übersicht öffnet ihn in Step by step", async () => {
  const { container, unmount } = show({});
  const { click } = await import("./harness.mjs");
  await click(container.querySelector("[aria-label^='Open step 2']"));
  assert.match(textOf(container), /Step 2 \/ 3/);
  assert.equal(container.querySelector("[role=tab][aria-selected='true']")?.textContent, "Step by step");
  unmount();
});
