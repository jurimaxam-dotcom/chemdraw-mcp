// U3/U4b: Knöpfe „Continue in chat“ (app.sendMessage) und der Text für Claude
// (app.updateModelContext) — ein Besitzer, entprellt, nur mit Host-Fähigkeit.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import App from "../App";
import { AppContext } from "../AppContext";
import { ModelContextProvider } from "../ModelContext";
import MoleculeView from "../MoleculeView";
import { MOLECULE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const ALL = { serverTools: {}, message: { text: {} }, updateModelContext: { text: {} } };

function fakeApp({ caps = ALL, onMessage, onContext } = {}) {
  const log = [];
  return {
    log,
    getHostCapabilities: () => caps,
    callServerTool: async () => ({ isError: true }),
    updateModelContext: async (p) => {
      log.push(["context", p.content[0].text]);
      return onContext ? onContext(p) : {};
    },
    sendMessage: async (p) => {
      log.push(["message", p.content[0].text, p.role]);
      return onMessage ? onMessage(p) : {};
    },
  };
}

function mount(app, element, delay = 20) {
  return render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(ModelContextProvider, { app, delay }, element))
  );
}

const wait = (ms) => act(async () => { await new Promise((r) => setTimeout(r, ms)); });
const row = (c) => c.querySelector("[data-testid='continue-row']");
const contexts = (app) => app.log.filter(([k]) => k === "context").map(([, t]) => t);

test("ohne Host-Fähigkeit `message`: keine Weiter-Zeile, auch kein leerer Kasten", () => {
  const app = fakeApp({ caps: { serverTools: {} } });
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  assert.equal(row(view.container), null);
  assert.doesNotMatch(textOf(view.container), /Continue in chat/);
  view.unmount();
});

test("mit `message`: Zeile über der Fußzeile, Klick schickt den Satz als Nutzernachricht", async () => {
  const app = fakeApp();
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  const r = row(view.container);
  assert.ok(r, "Weiter-Zeile fehlt");
  assert.match(textOf(r), /Continue in chat/);
  const footer = view.container.querySelector("[data-testid='panel-footer']");
  assert.ok(r.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING, "Zeile steht nicht über der Fußzeile");
  await click(buttonByText(r, "Predict the IR bands"));
  const messages = app.log.filter(([k]) => k === "message");
  assert.equal(messages.length, 1);
  assert.equal(messages[0][1], "Predict the IR bands of Aspirin.");
  assert.equal(messages[0][2], "user");
  view.unmount();
});

test("vor sendMessage geht der aktuelle Kontext sofort raus (ohne Entprellung)", async () => {
  const app = fakeApp();
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }), 10_000);
  assert.equal(contexts(app).length, 0, "vor Ablauf der Entprellung schon gesendet");
  await click(buttonByText(row(view.container), "Explain the structure"));
  const kinds = app.log.map(([k]) => k);
  assert.deepEqual(kinds, ["context", "message"], `Reihenfolge: ${kinds}`);
  assert.match(contexts(app)[0], /Aspirin/);
  view.unmount();
});

test("isError oder Ablehnung: ruhiger Hinweis in der Zeile, Knopf bleibt bedienbar", async () => {
  let mode = "isError";
  const app = fakeApp({
    onMessage: () => (mode === "isError" ? { isError: true } : Promise.reject(new Error("weg"))),
  });
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  const button = () => buttonByText(row(view.container), "Predict the IR bands");
  await click(button());
  assert.match(textOf(row(view.container)), /did not take the message/);
  assert.equal(button().disabled, false);
  mode = "reject";
  await click(button());
  assert.match(textOf(row(view.container)), /could not be sent/);
  assert.equal(app.log.filter(([k]) => k === "message").length, 2, "Knopf war nach dem Fehler tot");
  view.unmount();
});

test("Doppelklick während des Flugs schickt nur eine Nachricht", async () => {
  let release;
  const app = fakeApp({ onMessage: () => new Promise((r) => { release = r; }) });
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  const b = buttonByText(row(view.container), "Predict the IR bands");
  await click(b);
  await click(b);
  assert.equal(app.log.filter(([k]) => k === "message").length, 1);
  assert.equal(b.getAttribute("aria-busy"), "true");
  await act(async () => release({}));
  await click(b);
  assert.equal(app.log.filter(([k]) => k === "message").length, 2);
  view.unmount();
});

test("Kontext: entprellt, nur bei geändertem Text, nur mit Fähigkeit", async () => {
  const app = fakeApp();
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  await wait(60);
  assert.equal(contexts(app).length, 1, "Anfangszustand nicht genau einmal gesendet");
  view.rerender(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 20 }, React.createElement(MoleculeView, { data: MOLECULE }))));
  await wait(60);
  assert.equal(contexts(app).length, 1, "unveränderter Text erneut gesendet");
  view.unmount();

  const mute = fakeApp({ caps: { serverTools: {}, message: { text: {} } } });
  const v2 = mount(mute, React.createElement(MoleculeView, { data: MOLECULE }));
  await wait(60);
  await click(buttonByText(row(v2.container), "Predict the IR bands"));
  assert.equal(contexts(mute).length, 0, "ohne updateModelContext-Fähigkeit gesendet");
  assert.equal(mute.log.filter(([k]) => k === "message").length, 1);
  v2.unmount();
});

test("Kontext-Fehler werden still geschluckt", async () => {
  const app = fakeApp({ onContext: () => Promise.reject(new Error("nein")) });
  const view = mount(app, React.createElement(MoleculeView, { data: MOLECULE }));
  await wait(60);
  assert.ok(row(view.container));
  view.unmount();
});

test("Stapel: ein gemeinsamer Text, die bediente Karte im Fokus", async () => {
  const second = { ...MOLECULE, name: "Caffeine", formula: "C8H10N4O2", properties: { ...MOLECULE.properties, smiles: "Cn1cnc2c1c(=O)n(C)c(=O)n2C" } };
  const app = fakeApp();
  const view = mount(app, React.createElement(App, { data: { type: "batch", molecules: [MOLECULE, second], failed: [] } }));
  await wait(60);
  const first = contexts(app).at(-1);
  assert.match(first, /2 cards/);
  assert.match(first, /Aspirin/);
  assert.match(first, /Caffeine/);
  const cards = view.container.querySelectorAll("article.molecule-panel");
  const ester = [...cards[1].querySelectorAll("button.functional-group")][0];
  await click(ester);
  await wait(60);
  const last = contexts(app).at(-1);
  assert.match(last, /card 2 of 2/);
  assert.match(last, /Pinned selection: the Ester group/);
  assert.match(last, /Aspirin/, "Überblick verlor die andere Karte");
  view.unmount();
});
