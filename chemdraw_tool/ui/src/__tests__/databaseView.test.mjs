// Richtung „→ Struktur": alles liegt im Payload. Ein Toolaufruf waere hier
// kein Schoenheitsfehler, sondern eine Netzrunde fuer nichts.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import DatabaseView from "../DatabaseView";
import { DATABASE } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

function setup(data = DATABASE) {
  const calls = [];
  const app = { callServerTool: async (req) => (calls.push(req), { isError: true }) };
  const view = render(
    React.createElement(
      AppContext.Provider,
      { value: app },
      React.createElement(DatabaseView, { data })
    )
  );
  const panel = (which) => view.container.querySelector(`[data-view="${which}"]`);
  return { ...view, calls, panel };
}

test("startet im Datenblatt und zeigt die Quellzeilen", () => {
  const { panel, unmount } = setup();
  assert.ok(panel("data"), "keine Daten-Ansicht");
  assert.match(textOf(panel("data")), /50-78-2/);
  unmount();
});

test("Der Struktur-Reiter schaltet lokal um — ohne jeden Toolaufruf", async () => {
  const { container, calls, panel, unmount } = setup();
  await click(buttonByText(container, "Struktur"));

  assert.ok(panel("structure"), "keine Struktur-Ansicht nach dem Klick");
  assert.equal(panel("data"), null, "Datenblatt haengt noch daneben");
  assert.ok(panel("structure").querySelector("svg"), "Struktur ohne SVG");
  assert.equal(calls.length, 0, `Toolaufruf beim lokalen Umschalten: ${calls.length}`);
  unmount();
});

test("und wieder zurueck, ebenfalls ohne Aufruf", async () => {
  const { container, calls, panel, unmount } = setup();
  await click(buttonByText(container, "Struktur"));
  await click(buttonByText(container, "Daten"));

  assert.ok(panel("data"), "Rueckweg ins Datenblatt klappt nicht");
  assert.equal(calls.length, 0);
  unmount();
});
