// Reaktionsansicht: Bedingungen stehen am Pfeil (oben ueber, unten unter
// ihm), und der Pfeil zeigt den bestellten Typ (→, ⇌, ⇒).
//
// Vorher stand der Obertext als Kopfzeile ueber der ganzen Reaktion — fuer
// "unter dem Pfeil" gab es keinen Platz.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import ReactionView from "../ReactionView";
import { render } from "./harness.mjs";

// jsdom kennt keinen ResizeObserver; ScaledRow braucht nur, dass es ihn gibt.
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    disconnect() {}
  };
}

const MOL = { svg: "<svg></svg>", name: "x" };

function view(extra) {
  return render(
    React.createElement(ReactionView, {
      data: { type: "reaction", reactants: [MOL], products: [MOL], ...extra },
    })
  );
}

const before = (a, b) =>
  Boolean(a.compareDocumentPosition(b) & window.Node.DOCUMENT_POSITION_FOLLOWING);

test("Obertext ueber, Untertext unter dem Pfeil", () => {
  const { container, unmount } = view({
    conditions: "H₂SO₄ (cat.)",
    conditions_below: "reflux, 2 h",
    arrow: "equilibrium",
  });
  const above = container.querySelector("[data-conditions='above']");
  const below = container.querySelector("[data-conditions='below']");
  const arrow = container.querySelector("svg[data-arrow]");
  assert.equal(above.textContent, "H₂SO₄ (cat.)");
  assert.equal(below.textContent, "reflux, 2 h");
  assert.ok(before(above, arrow), "Obertext steht nicht vor dem Pfeil");
  assert.ok(before(arrow, below), "Untertext steht nicht nach dem Pfeil");
  // Beide gehoeren zur Pfeilspalte, nicht als Kopfzeile ueber die Reaktion.
  assert.equal(above.parentElement, arrow.parentElement);
  assert.equal(below.parentElement, arrow.parentElement);
  unmount();
});

for (const kind of ["forward", "equilibrium", "retro"]) {
  test(`Pfeiltyp ${kind}`, () => {
    const { container, unmount } = view({ arrow: kind });
    assert.equal(container.querySelector("svg[data-arrow]").dataset.arrow, kind);
    unmount();
  });
}

test("ohne Angabe: Vorwaertspfeil, keine leeren Textzeilen", () => {
  const { container, unmount } = view({});
  assert.equal(container.querySelector("svg[data-arrow]").dataset.arrow, "forward");
  assert.equal(container.querySelector("[data-conditions]"), null);
  unmount();
});

test("nur Untertext: kein leerer Obertext", () => {
  const { container, unmount } = view({ conditions: "", conditions_below: "Δ" });
  assert.equal(container.querySelector("[data-conditions='above']"), null);
  assert.equal(container.querySelector("[data-conditions='below']").textContent, "Δ");
  unmount();
});

test("die drei Pfeiltypen sehen verschieden aus", () => {
  const markup = ["forward", "equilibrium", "retro"].map((kind) => {
    const { container, unmount } = view({ arrow: kind });
    const html = container.querySelector("svg[data-arrow]").innerHTML;
    unmount();
    return html;
  });
  assert.equal(new Set(markup).size, 3);
});

// --- Etappe 6: Stoffbilanz als Badge ---------------------------------------

test("ausgeglichen: gruenes Badge 'balanced'", () => {
  const { container, unmount } = view({
    balance: { balanced: true, difference: {}, summary: "", suggestedEquation: "" },
  });
  const badge = container.querySelector("[data-testid='balance-badge']");
  assert.equal(badge.textContent, "balanced");
  assert.equal(badge.dataset.state, "balanced");
  assert.equal(container.querySelector("[data-testid='balance-suggestion']"), null);
  unmount();
});

test("nicht ausgeglichen: Differenz im Badge, kein Vorschlag", () => {
  const { container, unmount } = view({
    balance: { balanced: false, summary: "right side lacks H₂O", suggestedEquation: "" },
  });
  const badge = container.querySelector("[data-testid='balance-badge']");
  assert.equal(badge.textContent, "not balanced: right side lacks H₂O");
  assert.equal(badge.dataset.state, "unbalanced");
  assert.equal(container.querySelector("[data-testid='balance-suggestion']"), null);
  unmount();
});

test("Vorschlag steht getrennt vom Befund", () => {
  const { container, unmount } = view({
    balance: {
      balanced: false,
      summary: "left: +1 O",
      suggestedCoefficients: [2, 1, 2],
      suggestedEquation: "2 H₂ + O₂ → 2 H₂O",
    },
  });
  assert.equal(
    container.querySelector("[data-testid='balance-badge']").textContent,
    "not balanced: left: +1 O"
  );
  assert.equal(
    container.querySelector("[data-testid='balance-suggestion']").textContent,
    "suggested: 2 H₂ + O₂ → 2 H₂O"
  );
  unmount();
});

test("ohne Bilanz (Platzhalter, alte Payloads): kein Badge", () => {
  for (const extra of [{}, { balance: null }]) {
    const { container, unmount } = view(extra);
    assert.equal(container.querySelector("[data-testid='balance-badge']"), null);
    unmount();
  }
});
