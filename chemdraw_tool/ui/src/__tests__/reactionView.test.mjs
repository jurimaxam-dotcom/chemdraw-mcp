// Reaktionsansicht: Bedingungen stehen am Pfeil (oben ueber, unten unter
// ihm), und der Pfeil zeigt den bestellten Typ (→, ⇌, ⇒).
//
// Vorher stand der Obertext als Kopfzeile ueber der ganzen Reaktion — fuer
// "unter dem Pfeil" gab es keinen Platz.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import ReactionView from "../ReactionView";
import { buttonByText, click, render, textOf } from "./harness.mjs";

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

// --- Koeffizienten uebernehmen (Grundlagen, Etappe 2) -----------------------
// Der Knopf ruft generate_reaction mit denselben Argumenten plus Koeffizienten
// und zeigt das Ergebnis an Ort und Stelle. Nie ungefragt: ohne Klick kein Aufruf.

const H2 = { svg: "<svg></svg>", name: "[H][H]" };
const O2 = { svg: "<svg></svg>", name: "O=O" };
const H2O = { svg: "<svg></svg>", name: "O" };
const REQUEST = {
  reactants: ["[H][H]", "O=O"], products: ["O"], conditions: "", conditions_below: "",
  arrow: "forward", name: "", abbreviate_groups: false, render_style: "",
};
const UNBALANCED = {
  type: "reaction", reactants: [H2, O2], products: [H2O], request: REQUEST,
  balance: { balanced: false, summary: "left: +1 O", suggestedCoefficients: [2, 1, 2],
             suggestedEquation: "2 H₂ + O₂ → 2 H₂O" },
};
const APPLIED = {
  ...UNBALANCED, coefficients: [2, 1, 2],
  reactants: [{ ...H2, coefficient: 2 }, { ...O2, coefficient: 1 }],
  products: [{ ...H2O, coefficient: 2 }],
  balance: { balanced: true },
};

function withBridge(data, respond) {
  const calls = [];
  const app = { callServerTool: async (req) => { calls.push(req); return respond(req); } };
  const view = render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ReactionView, { data })));
  return { ...view, calls };
}

test("„Apply coefficients“ ruft generate_reaction mit denselben Argumenten plus Koeffizienten", async () => {
  const { container, calls, unmount } = withBridge(UNBALANCED, () => ({
    structuredContent: APPLIED, content: [{ type: "text", text: "{}" }],
  }));
  assert.equal(calls.length, 0, "Aufruf ohne Klick");
  await click(buttonByText(container, "Apply coefficients"));

  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "generate_reaction");
  assert.deepEqual(calls[0].arguments, { ...REQUEST, coefficients: [2, 1, 2] });
  assert.equal(
    container.querySelector("[data-testid='balance-badge']").dataset.state, "balanced",
    "Ergebnis ersetzt die Ansicht nicht"
  );
  const coefs = [...container.querySelectorAll("[data-coefficient]")].map((n) => n.textContent);
  assert.deepEqual(coefs, ["2", "2"], "Koeffizient 1 wird nicht gezeigt");
  assert.ok(!buttonByText(container, "Apply coefficients"), "Knopf nach dem Uebernehmen noch da");
  unmount();
});

test("fehlgeschlagenes Uebernehmen laesst die Zeichnung stehen und sagt es", async () => {
  const { container, unmount } = withBridge(UNBALANCED, () => ({
    isError: true, content: [{ type: "text", text: "boom" }],
  }));
  await click(buttonByText(container, "Apply coefficients"));
  assert.equal(container.querySelector("[data-testid='balance-badge']").dataset.state, "unbalanced");
  assert.match(textOf(container), /could not be applied/);
  unmount();
});

test("ohne request (alte Payloads) kein Knopf", () => {
  const { container, unmount } = withBridge({ ...UNBALANCED, request: undefined }, () => ({}));
  assert.ok(!buttonByText(container, "Apply coefficients"));
  unmount();
});
