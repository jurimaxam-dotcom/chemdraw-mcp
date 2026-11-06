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
