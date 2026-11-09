// Panel-Befunde aus dem Review 09.11.2026 (jeder Fall einmal rot gesehen).
// Gemeinsames Muster der ersten drei: ein zweites Tool-Ergebnis im selben Panel
// traf auf Zustand, der zum vorigen Ergebnis gehoerte.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import AnkiDeckView from "../AnkiDeckView";
import App from "../App";
import { AppContext } from "../AppContext";
import CopyButton from "../components/CopyButton";
import MoleculeView, { VIEW_LOAD_ERROR } from "../MoleculeView";
import { MOLECULE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'></svg>";
const mechanism = (name, n, current) => ({
  type: "mechanism", name, reaction_type: "x", current_step: current,
  steps: Array.from({ length: n }, (_, i) => ({ svg: SVG, label: `Step ${i + 1}`, is_transition_state: false })),
});

test("zweiter Mechanismus mit weniger Schritten stuerzt nicht ab", () => {
  const view = render(React.createElement(App, { data: mechanism("Fischer", 5, 5) }));
  assert.match(textOf(view.container), /Step 5 \/ 5/);
  view.rerender(React.createElement(App, { data: mechanism("SN2", 3, 0) }));
  assert.match(textOf(view.container), /SN2/);
  view.unmount();
});

test("Schritt-Index jenseits der Liste wird begrenzt", () => {
  const view = render(React.createElement(App, { data: mechanism("SN2", 3, 7) }));
  assert.match(textOf(view.container), /Step 3 \/ 3/);
  view.unmount();
});

test("neue Reaktion bekommt eine neue Komponente (applied gehoert zur alten)", () => {
  const a = { type: "reaction", name: "A", svg: SVG, request: { reactants: ["CCO"], products: ["CC=O"] } };
  const b = { ...a, name: "B", request: { reactants: ["CO"], products: ["C=O"] } };
  assert.notEqual(App({ data: a }).key, App({ data: b }).key);
  assert.equal(App({ data: a }).key, App({ data: { ...a } }).key);
});

test("derselbe Stoff mit angeforderter Ansicht ist ein neues Panel", () => {
  const plain = { ...MOLECULE, type: "molecule" };
  const haworth = { ...plain, initialView: "haworth", viewSvg: SVG };
  assert.notEqual(App({ data: plain }).key, App({ data: haworth }).key);
});

test("Kopieren: verweigert die Zwischenablage, greift der Rueckfall", async () => {
  const realClipboard = navigator.clipboard;
  const realExec = document.execCommand;
  let fallback = 0;
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: () => Promise.reject(new Error("NotAllowedError")) },
  });
  document.execCommand = () => { fallback += 1; return true; };
  const unhandled = [];
  const onUnhandled = (e) => unhandled.push(e);
  process.on("unhandledRejection", onUnhandled);
  try {
    const view = render(React.createElement(CopyButton, { text: "50-78-2" }));
    await click(view.container.querySelector("button"));
    await new Promise((r) => setTimeout(r, 0));
    assert.equal(fallback, 1, "execCommand-Rueckfall lief nicht");
    assert.equal(unhandled.length, 0, "unbehandelte Rejection");
    view.unmount();
  } finally {
    process.off("unhandledRejection", onUnhandled);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: realClipboard });
    document.execCommand = realExec;
  }
});

test("Anki-Deck: delivery=open heisst geoeffnet, nicht „bitte importieren“", () => {
  const view = render(React.createElement(AnkiDeckView, {
    data: { type: "anki_deck", name: "Deck", cards: 2, media: 1, delivery: "open", fronts: [] },
  }));
  assert.match(textOf(view.container), /opened in Anki/);
  assert.doesNotMatch(textOf(view.container), /import the \.apkg into Anki/);
  view.unmount();
});

test("Schritt-Punkte haben einen Namen fuer Screenreader", async () => {
  const view = render(React.createElement(App, { data: mechanism("SN2", 3, 1) }));
  const dots = [...view.container.querySelectorAll("button[aria-label^='Step ']")];
  assert.equal(dots.length, 3);
  assert.equal(dots[0].getAttribute("aria-current"), "step");
  assert.equal(dots[1].getAttribute("aria-current"), null);
  view.unmount();
});

test("Fehlerhinweis einer Zeichnung verschwindet beim Wechsel zurueck auf 2D", async () => {
  const app = { callServerTool: async () => ({ isError: true, content: [] }) };
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: { name_or_smiles: "CCO" } };
  const view = render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(MoleculeView, { data })));
  await click(buttonByText(view.container, "All H"));
  assert.match(textOf(view.container), new RegExp(VIEW_LOAD_ERROR.slice(0, 20)));
  await click(buttonByText(view.container, "2D"));
  assert.doesNotMatch(textOf(view.container), new RegExp(VIEW_LOAD_ERROR.slice(0, 20)));
  view.unmount();
});
