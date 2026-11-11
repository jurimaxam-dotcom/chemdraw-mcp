// U2 (M10): Layout nach dem, was der Host meldet — Hook, Expand-Knopf, Diagnose.
// Der Chat-Weg (kein Kontext oder nur maxHeight) muss exakt wie bisher bleiben:
// kein Attribut, keine Variable, kein Knopf.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import { AppContext, HostContext } from "../AppContext";
import MoleculeView from "../MoleculeView";
import HostDiagnostics from "../components/HostDiagnostics";
import { applyHostLayout, canRequestFullscreen, useHostLayout } from "../utils/useHostLayout";
import { MOLECULE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const html = () => document.documentElement;
const reset = () => applyHostLayout(null);

test("feste Höhe gemeldet: Datenattribut und Variablen für Höhe und Breite", () => {
  applyHostLayout({ displayMode: "fullscreen", containerDimensions: { width: 1000, height: 1200 } });
  assert.equal(html().hasAttribute("data-host-height"), true);
  assert.equal(html().style.getPropertyValue("--host-height"), "1200px");
  assert.equal(html().style.getPropertyValue("--host-width"), "1000px");
  assert.equal(html().getAttribute("data-display-mode"), "fullscreen");
  reset();
});

test("Chat-Weg (width + maxHeight) setzt keine feste Höhe", () => {
  applyHostLayout({ displayMode: "fullscreen", containerDimensions: { width: 1000, height: 1200 } });
  applyHostLayout({ displayMode: "inline", containerDimensions: { width: 700, maxHeight: 6000 } });
  assert.equal(html().hasAttribute("data-host-height"), false);
  assert.equal(html().style.getPropertyValue("--host-height"), "");
  assert.equal(html().style.getPropertyValue("--host-width"), "700px");
  reset();
});

test("kein Kontext: nichts am Dokument", () => {
  applyHostLayout(null);
  assert.equal(html().hasAttribute("data-host-height"), false);
  assert.equal(html().hasAttribute("data-safe-area"), false);
  assert.equal(html().hasAttribute("data-display-mode"), false);
  assert.equal(html().style.getPropertyValue("--host-width"), "");
});

test("safeAreaInsets: nur gesetzt, wenn ein Rand > 0 ist", () => {
  applyHostLayout({ safeAreaInsets: { top: 0, right: 0, bottom: 0, left: 0 } });
  assert.equal(html().hasAttribute("data-safe-area"), false);
  applyHostLayout({ safeAreaInsets: { top: 0, right: 0, bottom: 0, left: 24 } });
  assert.equal(html().hasAttribute("data-safe-area"), true);
  assert.equal(html().style.getPropertyValue("--safe-left"), "24px");
  assert.equal(html().style.getPropertyValue("--safe-top"), "0px");
  reset();
  assert.equal(html().hasAttribute("data-safe-area"), false);
});

test("Expand nur bei angebotenem fullscreen im Modus inline", () => {
  assert.equal(canRequestFullscreen({ availableDisplayModes: ["inline", "fullscreen"], displayMode: "inline" }), true);
  assert.equal(canRequestFullscreen({ availableDisplayModes: ["inline", "fullscreen"], displayMode: "fullscreen" }), false);
  assert.equal(canRequestFullscreen({ availableDisplayModes: ["inline"], displayMode: "inline" }), false);
  assert.equal(canRequestFullscreen({ displayMode: "inline" }), false);
  assert.equal(canRequestFullscreen(null), false);
});

// Ein App-Ersatz mit dem Teil der ext-apps-Schnittstelle, den das Panel nutzt.
function fakeApp(ctx, caps = { serverTools: {} }) {
  const listeners = [];
  const app = {
    ctx,
    requests: [],
    getHostContext: () => app.ctx,
    getHostCapabilities: () => caps,
    addEventListener: (name, fn) => { if (name === "hostcontextchanged") listeners.push(fn); },
    requestDisplayMode: async (params) => { app.requests.push(params); return { mode: params.mode }; },
    callServerTool: async () => ({}),
    change(next) { app.ctx = { ...app.ctx, ...next }; listeners.forEach((fn) => fn(next)); },
  };
  return app;
}

function Probe({ app, onState }) {
  const { hostContext, attach, sync } = useHostLayout();
  React.useEffect(() => { attach(app); sync(app); }, [app, attach, sync]);
  onState(hostContext);
  return null;
}

test("Hook liest den Kontext nach dem Verbinden und bei jedem hostcontextchanged", () => {
  const app = fakeApp({ displayMode: "inline", containerDimensions: { width: 600, maxHeight: 4000 } });
  let state = null;
  const view = render(React.createElement(Probe, { app, onState: (s) => { state = s; } }));
  assert.equal(state?.displayMode, "inline");
  assert.equal(html().hasAttribute("data-host-height"), false);
  act(() => app.change({ displayMode: "fullscreen", containerDimensions: { width: 600, height: 900 } }));
  assert.equal(state?.displayMode, "fullscreen");
  assert.equal(html().style.getPropertyValue("--host-height"), "900px");
  act(() => app.change({ displayMode: "inline", containerDimensions: { width: 600, maxHeight: 4000 } }));
  assert.equal(html().hasAttribute("data-host-height"), false);
  view.unmount();
  reset();
});

function molecule(app, ctx) {
  return render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(HostContext.Provider, { value: ctx },
        React.createElement(MoleculeView, { data: MOLECULE })))
  );
}

test("Expand-Knopf: sichtbar im Chat, wenn der Host fullscreen anbietet; Klick fragt den Host", async () => {
  const ctx = { displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"] };
  const app = fakeApp(ctx);
  const view = molecule(app, ctx);
  const button = buttonByText(view.container, "Expand");
  assert.equal(Boolean(button), true, "kein Expand-Knopf");
  assert.equal(Boolean(button.closest(".panel-header")), true, "Knopf nicht in der Kopfzeile");
  await click(button);
  assert.deepEqual(app.requests, [{ mode: "fullscreen" }]);
  view.unmount();
});

test("Expand-Knopf fehlt im Vollbild, ohne Angebot und ganz ohne Kontext", () => {
  for (const ctx of [
    { displayMode: "fullscreen", availableDisplayModes: ["inline", "fullscreen"] },
    { displayMode: "inline", availableDisplayModes: ["inline"] },
    null,
  ]) {
    const view = molecule(fakeApp(ctx), ctx);
    assert.equal(Boolean(buttonByText(view.container, "Expand")), false, `Knopf bei ${JSON.stringify(ctx)}`);
    view.unmount();
  }
});

test("Diagnose: Dreifachklick auf den Titel blendet Fähigkeiten und Kontext ein und wieder aus", async () => {
  const ctx = {
    displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"],
    containerDimensions: { width: 700, maxHeight: 5000 }, safeAreaInsets: { top: 0, right: 0, bottom: 0, left: 8 },
    platform: "desktop", theme: "dark",
  };
  const app = fakeApp(ctx, { serverTools: {}, message: { text: {} } });
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(HostContext.Provider, { value: ctx },
        React.createElement(HostDiagnostics, { app, hostContext: ctx },
          React.createElement(MoleculeView, { data: MOLECULE }))))
  );
  const block = () => view.container.querySelector("[data-testid='host-diagnostics']");
  assert.equal(Boolean(block()), false, "Diagnose ohne Klick sichtbar");
  const title = view.container.querySelector(".panel-title");
  const tripleClick = async (detail) => act(async () => {
    title.dispatchEvent(new window.MouseEvent("click", { bubbles: true, detail }));
  });
  await tripleClick(1);
  await tripleClick(2);
  assert.equal(Boolean(block()), false, "Einfach-/Doppelklick öffnet die Diagnose");
  await tripleClick(3);
  assert.equal(Boolean(block()), true, "Dreifachklick öffnet keine Diagnose");
  const text = textOf(block());
  for (const needle of ["message", "serverTools", "displayMode", "inline", "availableDisplayModes", "fullscreen",
    "containerDimensions", "maxHeight", "5000", "safeAreaInsets", "platform", "desktop"]) {
    assert.match(text, new RegExp(needle), `Diagnose ohne ${needle}`);
  }
  assert.doesNotMatch(text, /theme/, "Diagnose zeigt mehr als die verlangten Felder");
  await tripleClick(3);
  assert.equal(Boolean(block()), false, "zweiter Dreifachklick schließt die Diagnose nicht");
  view.unmount();
});

test("Stapel (batch): keine Expand-Knöpfe an den einzelnen Karten", async () => {
  const { default: App } = await import("../App");
  const ctx = { displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"] };
  const app = fakeApp(ctx);
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(HostContext.Provider, { value: ctx },
        React.createElement(App, { data: { type: "batch", molecules: [MOLECULE, { ...MOLECULE, name: "Zwei", properties: { ...MOLECULE.properties, smiles: "CCO" } }], failed: [] } })))
  );
  assert.equal(view.container.querySelectorAll(".molecule-panel").length, 2);
  assert.equal(Boolean(buttonByText(view.container, "Expand")), false, "Expand-Knopf an einer Stapelkarte");
  view.unmount();
});
