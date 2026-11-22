// Batch (batch_generate) als Raster kompakter Karten (Etappe 2, 16.11.2026).
// Vorher stapelte das Panel n volle Molekül-Karten untereinander — schon drei
// Stoffe waren höher als das Fenster. Jetzt: Übersicht (Zeichnung, Name, Formel,
// Molmasse), Klick öffnet die volle Molekül-Ansicht eines Stoffs, ein Rückweg
// führt zur Übersicht.
//
// Fehlschläge: ein Name, der nicht aufgelöst wurde, darf nicht still
// verschwinden (Design-Kritik 07.11.2026, F1). Form wie in server.py
// batch_generate: `failed` ist eine Liste von Strings, die Eingabe selbst, bei
// Familiennamen mit " (ambiguous: …)" dahinter.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import App from "../App";
import { AppContext } from "../AppContext";
import { ModelContextProvider } from "../ModelContext";
import { MOLECULE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const HOME = "/Users/x/ChemDraw-Output/einzelmolekuele";
const FIRST = { ...MOLECULE, files: { png: `${HOME}/aspirin.png`, svg: `${HOME}/aspirin.svg` } };
const SECOND = {
  ...MOLECULE,
  name: "Caffeine",
  formula: "C8H10N4O2",
  properties: { ...MOLECULE.properties, smiles: "Cn1cnc2c1c(=O)n(C)c(=O)n2C", mw: "194.19 g/mol", cas: "58-08-2" },
  files: { png: `${HOME}/caffeine.png`, svg: `${HOME}/caffeine.svg` },
};

function batch(failed = []) {
  return { type: "batch", molecules: [FIRST, SECOND], cdxml_paths: [], failed };
}

const ALL = { serverTools: {}, message: { text: {} }, updateModelContext: { text: {} } };
function fakeApp() {
  const log = [];
  return {
    log,
    getHostCapabilities: () => ALL,
    callServerTool: async () => ({ isError: true }),
    updateModelContext: async (p) => { log.push(p.content[0].text); return {}; },
    sendMessage: async () => ({}),
  };
}
function mount(element, app = fakeApp()) {
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(ModelContextProvider, { app, delay: 10 }, element))
  );
  return { ...view, app };
}
const wait = (ms) => act(async () => { await new Promise((r) => setTimeout(r, ms)); });
const cards = (c) => [...c.querySelectorAll("button.batch-card")];

test("Übersicht: je Stoff eine kompakte Karte mit Zeichnung, Name, Formel und Molmasse", () => {
  const { container, unmount } = mount(React.createElement(App, { data: batch() }));
  const list = cards(container);
  assert.equal(list.length, 2);
  assert.equal(container.querySelectorAll("article.molecule-panel").length, 0, "volle Molekül-Karten in der Übersicht");
  assert.equal(container.querySelectorAll("[role='tab']").length, 0, "Reiter gehören in die Detailansicht");
  const [a, b] = list;
  assert.equal(a.getAttribute("type"), "button", "Karte ist kein echter Knopf (Enter/Leertaste)");
  assert.ok(a.querySelector(".batch-card-structure svg"), "Zeichnung fehlt");
  assert.equal(textOf(a.querySelector(".batch-card-name")), "Aspirin");
  assert.match(textOf(a), /C9H8O4/);
  assert.match(textOf(a), /180\.16 g\/mol/);
  assert.match(textOf(b), /194\.19 g\/mol/);
  assert.doesNotMatch(textOf(b), /g\/mol g\/mol/);
  // Bedienungshilfen-Name beginnt mit dem Stoff (Desktop-Probe sucht so), die Zeichnung schweigt.
  assert.match(a.getAttribute("aria-label"), /^Aspirin, C9H8O4, 180\.16 g\/mol/);
  assert.equal(a.querySelector(".batch-card-structure").getAttribute("aria-hidden"), "true");
  unmount();
});

test("Übersicht: eine Weiter-Zeile und eine Fußzeile mit dem Ausgabeordner statt n Stück", () => {
  const { container, unmount } = mount(React.createElement(App, { data: batch() }));
  assert.equal(container.querySelectorAll("[data-testid='continue-row']").length, 1);
  const footers = container.querySelectorAll("[data-testid='panel-footer']");
  assert.equal(footers.length, 1);
  assert.match(textOf(footers[0]), /einzelmolekuele/);
  assert.doesNotMatch(textOf(footers[0]), /aspirin\.png/, "Einzelpfade gehören in die Detailansicht");
  unmount();
});

test("Klick auf eine Karte öffnet die volle Ansicht, der Rückweg führt zur Übersicht", async () => {
  const { container, unmount } = mount(React.createElement(App, { data: batch() }));
  await click(cards(container)[1]);
  const panels = container.querySelectorAll("article.molecule-panel");
  assert.equal(panels.length, 1);
  assert.equal(textOf(panels[0].querySelector(".panel-title")), "Caffeine");
  assert.ok(panels[0].querySelector("[role='tab']"), "Reiter fehlen in der Detailansicht");
  assert.equal(cards(container).length, 0, "Übersicht steht noch daneben");
  // Dateipfade dieses Stoffs in seiner Fußzeile.
  assert.match(textOf(panels[0].querySelector("[data-testid='panel-footer']")), /caffeine\.png/);
  const back = buttonByText(container, "Back to all structures");
  assert.ok(back, "Rückweg fehlt");
  assert.equal(Boolean(document.activeElement === back), true, "Fokus nicht auf dem Rückweg");
  await click(back);
  assert.equal(cards(container).length, 2);
  assert.equal(container.querySelectorAll("article.molecule-panel").length, 0);
  assert.equal(Boolean(document.activeElement === cards(container)[1]), true, "Fokus nicht zurück auf der Karte");
  unmount();
});

test("Rückweg nennt keinen Stoff (Lernmodus verrät den Namen nirgends)", async () => {
  const { container, unmount } = mount(React.createElement(App, { data: batch() }));
  await click(cards(container)[0]);
  await click(buttonByText(container, "Study"));
  const back = buttonByText(container, "Back to all structures");
  const bar = back.parentElement;
  assert.doesNotMatch(bar.outerHTML, /Aspirin/i);
  unmount();
});

test("Modellkontext: Übersicht meldet die Liste, Detail meldet sich selbst, zurück wieder die Liste", async () => {
  const { container, app, unmount } = mount(React.createElement(App, { data: batch(["xyzzyl"]) }));
  await wait(40);
  const overview = app.log.at(-1);
  assert.match(overview, /2 structures/);
  assert.match(overview, /1\. Aspirin \(C9H8O4\)/);
  assert.match(overview, /2\. Caffeine \(C8H10N4O2\)/);
  assert.match(overview, /Not drawn: xyzzyl/);
  await click(cards(container)[1]);
  await wait(40);
  const detail = app.log.at(-1);
  assert.match(detail, /Compound: Caffeine/);
  assert.doesNotMatch(detail, /Aspirin/, "verdeckte Übersicht meldet noch");
  await click(buttonByText(container, "Back to all structures"));
  await wait(40);
  const again = app.log.at(-1);
  assert.equal(again, overview);
  unmount();
});

test("Batch mit Fehlschlag: Liste „Not drawn“ kompakt direkt unter dem Raster", () => {
  const { container, unmount } = mount(
    React.createElement(App, {
      data: batch(["xyzzyl", "xylene (ambiguous: o-xylene, m-xylene, p-xylene)"]),
    })
  );
  const list = container.querySelector('[data-testid="batch-failed"]');
  assert.ok(list, "Liste der Fehlschläge fehlt");
  assert.equal(list.getAttribute("role"), "status");
  assert.match(textOf(list), /Not drawn \(2\)/);
  const items = [...list.querySelectorAll("li")];
  assert.equal(items.length, 2);
  assert.equal(textOf(items[0].querySelector(".batch-failed-input")), "xyzzyl");
  assert.match(textOf(items[0]), /could not be resolved/i);
  assert.equal(textOf(items[1].querySelector(".batch-failed-input")), "xylene");
  assert.match(textOf(items[1]), /ambiguous: o-xylene, m-xylene, p-xylene/);
  const grid = container.querySelector(".batch-grid");
  assert.equal(Boolean(grid.nextElementSibling === list), true, "Liste steht nicht direkt unter dem Raster");
  unmount();
});

test("Batch ohne Fehlschlag zeigt keine Liste", () => {
  const { container, unmount } = mount(React.createElement(App, { data: batch([]) }));
  assert.equal(Boolean(container.querySelector('[data-testid="batch-failed"]')), false);
  assert.doesNotMatch(textOf(container), /Not drawn/);
  unmount();
});

test("Neues Ergebnis im selben Panel: Übersicht statt altem Detail, Kontext meldet die neue Liste", async () => {
  const app = fakeApp();
  const withCtx = (data) => React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 10 }, React.createElement(App, { data })));
  const view = render(withCtx(batch()));
  await click(cards(view.container)[1]);
  await wait(40);
  const THIRD = { ...MOLECULE, name: "Ethanol", formula: "C2H6O", properties: { ...MOLECULE.properties, smiles: "CCO", mw: "46.07" } };
  view.rerender(withCtx({ type: "batch", molecules: [THIRD], cdxml_paths: [], failed: [] }));
  await wait(40);
  assert.equal(view.container.querySelectorAll("article.molecule-panel").length, 0, "altes Detail steht noch");
  assert.equal(cards(view.container).length, 1);
  assert.match(app.log.at(-1), /1\. Ethanol \(C2H6O\)/);
  view.unmount();
});
