// Lernmodus (U4b): dritter Reiter „Study“. Zeichnung bleibt, Name, Kernwerte und
// Gruppen sind verdeckt; nichts im DOM verrät den Namen.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import { ModelContextProvider } from "../ModelContext";
import MoleculeView from "../MoleculeView";
import DatabaseView from "../DatabaseView";
import { DATABASE, MOLECULE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const DATA = {
  ...MOLECULE,
  foundAs: "Aspirin",
  properties: { ...MOLECULE.properties, pubchemTitle: "Aspirin", cid: "2244" },
  files: { png: "/Users/x/ChemDraw-Output/aspirin.png", svg: "/Users/x/ChemDraw-Output/aspirin.svg" },
  functionalGroups: [
    { name: "Ester", atomIndices: [0, 1, 2], count: 1, color: "#d35400" },
    { name: "Aromat", atomIndices: [0], count: 1, color: "#2980b9" },
  ],
};

function mount(data = DATA) {
  const log = [];
  const app = {
    getHostCapabilities: () => ({ message: { text: {} }, updateModelContext: { text: {} } }),
    callServerTool: async (req) => (log.push(["tool", req.name]), { isError: true }),
    updateModelContext: async (p) => (log.push(["context", p.content[0].text]), {}),
    sendMessage: async (p) => (log.push(["message", p.content[0].text]), {}),
  };
  const view = render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 10_000 }, React.createElement(MoleculeView, { data }))));
  return { ...view, log };
}

/** Text plus alle Attributwerte — Tooltips und aria-label zählen mit. */
function everything(container) {
  const attrs = [...container.querySelectorAll("*")].flatMap((el) => [...el.attributes].map((a) => a.value));
  return `${container.textContent} ${attrs.join(" ")}`;
}

test("Study ist ein dritter Reiter; Standard bleibt Structure", () => {
  const { container, unmount } = mount();
  const tabs = [...container.querySelectorAll("[role='tab']")].map((t) => t.textContent.trim());
  assert.deepEqual(tabs, ["Structure", "Data", "Study"]);
  assert.ok(container.querySelector("[data-view='structure']"));
  unmount();
});

test("DatabaseView bekommt keinen Study-Reiter", () => {
  const app = { getHostCapabilities: () => ({}) };
  const view = render(React.createElement(AppContext.Provider, { value: app }, React.createElement(DatabaseView, { data: DATABASE })));
  const tabs = [...view.container.querySelectorAll("[role='tab']")].map((t) => t.textContent.trim());
  assert.deepEqual(tabs, ["Structure", "Data"]);
  view.unmount();
});

test("im Lernmodus verrät nichts den Namen, CAS oder die Gruppen — auch keine Attribute", async () => {
  const { container, log, unmount } = mount();
  await click(buttonByText(container, "Study"));
  assert.ok(container.querySelector("[data-view='study']"), "Lernansicht fehlt");
  assert.equal(log.filter(([k]) => k === "tool").length, 0, "Study löst einen Toolaufruf aus");
  const all = everything(container);
  for (const secret of [/aspirin/i, /50-78-2/, /C9H8O4|C₉H₈O₄/, /Ester/, /Aromatic/, /CID 2244/, /ChemDraw-Output/]) {
    assert.doesNotMatch(all, secret, `verrät ${secret}`);
  }
  assert.ok(container.querySelector("[data-view='study'] svg"), "Zeichnung fehlt");
  assert.match(textOf(container), /6 of 6 still covered/);
  assert.match(textOf(container), /Group 1/);
  assert.match(textOf(container), /Group 2/);
  assert.ok(buttonByText(container, "Add to Anki"), "Add to Anki fehlt im Lernmodus");
  assert.equal(buttonByText(container, "Export PNG"), undefined, "Export PNG trägt den Namen im Dateinamen");
  unmount();
});

test("Aufdecken: Stück für Stück, Zähler, Glow, Reveal all und Cover again", async () => {
  const { container, unmount } = mount();
  await click(buttonByText(container, "Study"));
  await click(container.querySelector("button[aria-label='Show formula']"));
  assert.match(textOf(container), /C9H8O4/);
  assert.match(textOf(container), /5 of 6 still covered/);
  await click(container.querySelector("button[aria-label='Show group 1']"));
  assert.match(textOf(container), /Ester/);
  assert.match(textOf(container), /4 of 6 still covered/);
  await click(buttonByText(container, "Reveal all"));
  assert.match(textOf(container), /Aspirin/);
  assert.match(textOf(container), /50-78-2/);
  assert.match(textOf(container), /Everything revealed/);
  await click(buttonByText(container, "Cover again"));
  assert.doesNotMatch(everything(container), /aspirin/i);
  assert.match(textOf(container), /6 of 6 still covered/);
  unmount();
});

test("Weiter-Knöpfe im Lernmodus: Hinweis, Quiz, nächster Stoff — Satz ohne den Namen", async () => {
  const { container, log, unmount } = mount();
  await click(buttonByText(container, "Study"));
  const r = container.querySelector("[data-testid='continue-row']");
  const labels = [...r.querySelectorAll("button")].map((b) => b.textContent.trim());
  assert.deepEqual(labels, ["Give me a hint", "Quiz me on this compound", "Next: a similar compound"]);
  await click(buttonByText(r, "Give me a hint"));
  const msg = log.find(([k]) => k === "message")[1];
  assert.doesNotMatch(msg, /aspirin/i);
  assert.match(msg, /CC\(=O\)Oc1ccccc1C\(=O\)O/);
  const ctx = log.filter(([k]) => k === "context").at(-1)[1];
  assert.match(ctx, /Study mode/);
  assert.match(ctx, /Aspirin/, "Claude kennt den Stoff nicht");
  unmount();
});

test("zurück auf Structure: alles wie vorher, Name wieder da", async () => {
  const { container, unmount } = mount();
  await click(buttonByText(container, "Study"));
  await click(buttonByText(container, "Structure"));
  assert.match(textOf(container.querySelector(".panel-title")), /Aspirin/);
  assert.ok(container.querySelector("[data-view='structure']"));
  unmount();
});
