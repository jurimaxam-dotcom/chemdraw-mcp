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
  await click(buttonByText(container, "Structure"));

  assert.ok(panel("structure"), "keine Struktur-Ansicht nach dem Klick");
  assert.equal(panel("data"), null, "Datenblatt haengt noch daneben");
  assert.ok(panel("structure").querySelector("svg"), "Struktur ohne SVG");
  assert.equal(calls.length, 0, `Toolaufruf beim lokalen Umschalten: ${calls.length}`);
  unmount();
});

test("und wieder zurueck, ebenfalls ohne Aufruf", async () => {
  const { container, calls, panel, unmount } = setup();
  await click(buttonByText(container, "Structure"));
  await click(buttonByText(container, "Data"));

  assert.ok(panel("data"), "Rueckweg ins Datenblatt klappt nicht");
  assert.equal(calls.length, 0);
  unmount();
});

// --- GHS je Quelle (Etappe 5) ------------------------------------------------
import { DATABASE_GHS, DATABASE_GHS_FAILED } from "./fixtures.mjs";

async function openGhs(data) {
  const view = setup(data);
  await click(buttonByText(view.container, "GHS"));
  return view;
}

test("GHS: Leitquelle offen, die anderen zugeklappt", async () => {
  const { panel, unmount } = await openGhs(DATABASE_GHS);
  const text = textOf(panel("data"));
  assert.match(text, /EU harmonised/);
  assert.match(text, /Lead source/);
  assert.match(text, /Harmful if swallowed/);
  // zweite und dritte Quelle: Kopfzeile sichtbar, Inhalt nicht
  assert.match(text, /ECHA C&L notifications/);
  assert.match(text, /NITE-CMC/);
  assert.doesNotMatch(text, /98\.9/);
  assert.doesNotMatch(text, /May damage fertility/);
  unmount();
});

test("GHS: zweite Quelle aufklappen zeigt ihre Anteile — und nur ihre", async () => {
  const { container, panel, unmount } = await openGhs(DATABASE_GHS);
  const toggle = container.querySelector('[data-ghs-id="ghs-51"] button[aria-expanded]');
  assert.ok(toggle, "kein Aufklapp-Knopf für ECHA");
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  await click(toggle);

  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  const echa = textOf(container.querySelector('[data-ghs-id="ghs-51"]'));
  assert.match(echa, /98\.9%/);
  assert.match(echa, /Not classified/);
  assert.match(echa, /0\.6% of all reports \(13 of 2217\)/);
  assert.doesNotMatch(textOf(panel("data")), /May damage fertility/, "NITE blieb zu");
  unmount();
});

test("GHS: ohne Prozent wird keiner behauptet", async () => {
  const { container, unmount } = await openGhs(DATABASE_GHS);
  const eu = textOf(container.querySelector('[data-ghs-id="ghs-272"]'));
  assert.match(eu, /H302/, "Leitgruppe fehlt");
  assert.doesNotMatch(eu, /%/);
  unmount();
});

test("GHS: gescheiterter Abruf sagt das, statt leer zu sein", async () => {
  const { panel, unmount } = await openGhs(DATABASE_GHS_FAILED);
  assert.match(textOf(panel("data")), /could not be retrieved/);
  unmount();
});

// --- Link-Schema (Sicherheitsscan B7) ------------------------------------------
// Quell-URLs stammen aus PubChem-Depositor-Metadaten, also von Dritten.
test("Quell-Links nur mit http/https — javascript: wird nicht verlinkt", () => {
  const evil = {
    ...DATABASE,
    sources: [
      { ...DATABASE.sources[0], url: "javascript:alert(1)" },
      ...DATABASE.sources.slice(1),
    ],
  };
  const { container, unmount } = setup(evil);
  const hrefs = [...container.querySelectorAll("a")].map((a) => a.getAttribute("href"));
  assert.ok(!hrefs.some((h) => /^\s*javascript:/i.test(h || "")), `gefaehrlicher Link: ${hrefs}`);
  unmount();

  const ok = setup();
  const okHrefs = [...ok.container.querySelectorAll("a")].map((a) => a.getAttribute("href"));
  assert.ok(okHrefs.includes("https://pubchem.ncbi.nlm.nih.gov/compound/2244"), `https-Link fehlt: ${okHrefs}`);
  ok.unmount();
});
