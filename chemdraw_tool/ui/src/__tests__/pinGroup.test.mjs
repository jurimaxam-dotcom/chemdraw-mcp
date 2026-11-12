// U4: Anklicken hält eine Gruppe (oder ein Atom) fest; Hover ist nur Vorschau
// und darf die Auswahl nie löschen.
import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import React, { act } from "react";

import { AppContext } from "../AppContext";
import { ModelContextProvider } from "../ModelContext";
import DatabaseView from "../DatabaseView";
import MoleculeView from "../MoleculeView";
import { ATOMS, DATABASE, MOLECULE, lookupSuccess } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

let original;
beforeEach(() => {
  // viewBox 40×20 auf 400×200 px: Atom (x, y) liegt bei (10x, 10y)
  original = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = () => ({ left: 0, top: 0, width: 400, height: 200, right: 400, bottom: 200, x: 0, y: 0 });
});
afterEach(() => {
  Element.prototype.getBoundingClientRect = original;
});

const CAPS = { message: { text: {} }, updateModelContext: { text: {} } };

function mount(element, caps = CAPS) {
  const app = { getHostCapabilities: () => caps, callServerTool: async () => ({ isError: true }),
    updateModelContext: async () => ({}), sendMessage: async () => ({}) };
  return render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 10_000 }, element)));
}

const chip = (c, label) => [...c.querySelectorAll("button.functional-group")].find((b) => b.textContent.includes(label));
const note = (c) => textOf(c.querySelector(".group-note"));
const fire = (el, type, init = {}) => act(async () => {
  el.dispatchEvent(new window.MouseEvent(type, { bubbles: true, cancelable: true, ...init }));
});

test("Klick hält die Gruppe fest, zweiter Klick löst; aria-pressed meint die Auswahl", async () => {
  const { container, unmount } = mount(React.createElement(MoleculeView, { data: MOLECULE }));
  assert.match(note(container), /Click a group to pin it\. Claude then knows which part you mean\./);
  const ester = chip(container, "Ester");
  await act(async () => ester.focus());
  assert.equal(ester.getAttribute("aria-pressed"), "false", "Fokus allein hält nichts fest");
  await click(ester);
  assert.equal(ester.getAttribute("aria-pressed"), "true");
  assert.match(note(container), /Ester/);
  assert.match(note(container), /–COO–/);
  assert.match(note(container), /Pinned\. Claude sees this selection with your next message\./);
  await click(ester);
  assert.equal(ester.getAttribute("aria-pressed"), "false");
  unmount();
});

test("Hover und Blur löschen die festgehaltene Auswahl nicht", async () => {
  const { container, unmount } = mount(React.createElement(MoleculeView, { data: MOLECULE }));
  const ester = chip(container, "Ester");
  await click(ester);
  await fire(ester, "mouseout", { relatedTarget: document.body });
  await act(async () => ester.blur());
  // Maus über die Zeichnung, weg vom Atom: setzt nur die Vorschau zurück
  const canvas = container.querySelector(".structure-canvas");
  await fire(canvas, "mousemove", { clientX: 5, clientY: 190 });
  await fire(canvas, "mouseout", { relatedTarget: document.body });
  assert.equal(ester.getAttribute("aria-pressed"), "true");
  assert.match(note(container), /Pinned/);
  assert.ok(container.querySelector(".group-glow"), "Glow der Auswahl fehlt");
  unmount();
});

test("„Clear“ löst die Auswahl", async () => {
  const { container, unmount } = mount(React.createElement(MoleculeView, { data: MOLECULE }));
  await click(chip(container, "Ester"));
  await click(buttonByText(container.querySelector(".group-note"), "Clear"));
  assert.equal(chip(container, "Ester").getAttribute("aria-pressed"), "false");
  assert.match(note(container), /Click a group to pin it/);
  unmount();
});

test("Klick auf ein Atom der Gruppe hält die Gruppe fest", async () => {
  const { container, unmount } = mount(React.createElement(MoleculeView, { data: MOLECULE }));
  const canvas = container.querySelector(".structure-canvas");
  await fire(canvas, "click", { clientX: ATOMS[1].x * 10, clientY: ATOMS[1].y * 10 });
  assert.equal(chip(container, "Ester").getAttribute("aria-pressed"), "true");
  unmount();
});

test("Klick auf ein Atom ohne Gruppe hält das Atom selbst fest", async () => {
  const data = { ...MOLECULE, functionalGroups: [{ name: "Ester", atomIndices: [0, 1], count: 1, color: "#d35400" }] };
  const { container, unmount } = mount(React.createElement(MoleculeView, { data }));
  const canvas = container.querySelector(".structure-canvas");
  await fire(canvas, "click", { clientX: 300, clientY: 100 });
  assert.match(note(container), /Oxygen atom/i);
  assert.match(note(container), /Pinned/);
  assert.equal(chip(container, "Ester").getAttribute("aria-pressed"), "false");
  await fire(canvas, "click", { clientX: 300, clientY: 100 });
  assert.match(note(container), /Click a group to pin it/);
  unmount();
});

test("ohne updateModelContext: Ruhezustand nennt den Hover-Hinweis, Auswahl ohne Claude-Satz", async () => {
  const { container, unmount } = mount(React.createElement(MoleculeView, { data: MOLECULE }), { message: { text: {} } });
  assert.match(note(container), /Hover a group to see where it sits in the structure\./);
  await click(chip(container, "Ester"));
  assert.match(note(container), /Pinned\./);
  assert.doesNotMatch(note(container), /Claude sees/);
  unmount();
});

test("DatabaseView: dieselbe Auswahl mit Hinweis-Karte", async () => {
  const { container, unmount } = mount(React.createElement(DatabaseView, { data: DATABASE }));
  await click(buttonByText(container, "Structure"));
  const ester = chip(container, "Ester");
  await click(ester);
  assert.equal(ester.getAttribute("aria-pressed"), "true");
  assert.match(note(container), /Pinned\. Claude sees this selection/);
  unmount();
});

test("Varianten-Ansicht: die verdeckte Ausgangsstruktur meldet keinen Kontext mehr", async () => {
  // Codex-Review 12.11.: nach „Show variants“ blieb die Elternansicht mit ihrer
  // festgehaltenen Gruppe im Fokus — Claude las die verdeckte Struktur.
  const sent = [];
  const variants = { type: "ambiguous", name: "stereoisomers",
    candidates: [{ label: "R candidate", smiles: "C[C@H](O)C(=O)O", svg: MOLECULE.svg }] };
  const app = { getHostCapabilities: () => CAPS, sendMessage: async () => ({}),
    updateModelContext: async (p) => { sent.push(p.content[0].text); return {}; },
    callServerTool: async () => lookupSuccess(variants) };
  const data = { ...MOLECULE, name: "parent compound", stereoWarnings: [{ kind: "atom", atomIndices: [0], label: "undefined" }] };
  const v = render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 1 }, React.createElement(MoleculeView, { data }))));
  await click(v.container.querySelector("button.functional-group"));
  await click(buttonByText(v.container, "Show variants"));
  await act(async () => { await new Promise((r) => setTimeout(r, 30)); });
  assert.equal(Boolean(sent.at(-1)?.includes("Pinned selection")), false, sent.at(-1));
  assert.equal(Boolean(sent.at(-1)?.includes("parent compound (formula")), false, sent.at(-1));
  v.unmount();
});
