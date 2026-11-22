// Etappe 4 (16.11.2026): Datenblatt-Zeilen und die Zeilen, die in jeder View Platz fressen.
// Was jsdom sehen kann: Aufbau, Klassen, Namen für Bedienungshilfen. Die Optik (Deckkraft
// bei Hover/Fokus, Höhe des Panels) prüft test:host im echten Browser.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import { ModelContextProvider } from "../ModelContext";
import DatabaseView from "../DatabaseView";
import MoleculeView from "../MoleculeView";
import CopyButton from "../components/CopyButton";
import PanelFooter from "../components/PanelFooter";
import { formulaParts } from "../components/Formula";
import { DATABASE, MOLECULE } from "./fixtures.mjs";
import { click, render, textOf } from "./harness.mjs";

const SHEET = {
  ...DATABASE,
  sources: [{
    type: "PubChem", source: "PubChem", url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
    rows: [
      { key: "Molecular formula", val: "C9H8O4" },
      { key: "CAS No.", val: "50-78-2" },
      { key: "InChIKey", val: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" },
    ],
  }],
};

const ALL = { serverTools: {}, message: { text: {} }, updateModelContext: { text: {} } };
function withHost(element) {
  const app = { getHostCapabilities: () => ALL, callServerTool: async () => ({ isError: true }),
    updateModelContext: async () => ({}), sendMessage: async () => ({}) };
  return render(React.createElement(AppContext.Provider, { value: app },
    React.createElement(ModelContextProvider, { app, delay: 10_000 }, element)));
}

// --- A1: keine Mini-Struktur in eigener Spalte -------------------------------------------
test("Datenblatt: keine Mini-Struktur neben der Tabelle — die Tabelle nimmt die Breite", () => {
  const view = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(DatabaseView, { data: SHEET })));
  const data = view.container.querySelector('[data-view="data"]');
  assert.ok(data, "keine Daten-Ansicht");
  // Boolean statt Element vergleichen: ein Diff mit DOM-Element hängt jsdom auf.
  assert.equal(Boolean(data.querySelector(".source-structure")), false, "Mini-Struktur steht noch neben der Tabelle");
  const bilder = [...data.querySelectorAll("svg")].filter((s) => !s.closest("button"));
  assert.equal(bilder.length, 0, "Strukturbild im Datenblatt (außer den Knopf-Symbolen)");
  view.unmount();
});

// --- A2: Kopierknöpfe treten zurück, bleiben aber benannt und bedienbar ---------------------
test("CopyButton: Aussehen über Klassen (Hover-Regeln greifen), Name bleibt", () => {
  const view = render(React.createElement(CopyButton, { text: "50-78-2", size: "sm" }));
  const b = view.container.querySelector("button");
  assert.equal(b.getAttribute("aria-label"), "Copy value");
  assert.ok(b.classList.contains("copy-button"), `Klasse fehlt: ${b.className}`);
  assert.equal(b.style.border, "", "Rahmen steht inline — keine Hover-Regel kommt dagegen an");
  assert.equal(b.style.opacity, "", "Deckkraft inline");
  view.unmount();
});

test("Kopierknöpfe in Datenblatt, Kernwerten und Fußzeile sind „leise“ (erst bei Hover/Fokus voll)", () => {
  const sheet = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(DatabaseView, { data: SHEET })));
  const rows = [...sheet.container.querySelectorAll(".source-row")];
  assert.equal(rows.length, 3);
  for (const r of rows) {
    const b = r.querySelector('button[aria-label="Copy value"]');
    assert.ok(b, `Kopierknopf fehlt in ${textOf(r)}`);
    assert.ok(b.classList.contains("is-quiet"), "Datenblatt-Knopf nicht leise");
  }
  sheet.unmount();

  const mol = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(MoleculeView, { data: MOLECULE })));
  const facts = [...mol.container.querySelectorAll(".fact button")];
  assert.ok(facts.length >= 1, "Kernwerte ohne Kopierknopf");
  assert.ok(facts.every((b) => b.classList.contains("is-quiet") && b.getAttribute("aria-label") === "Copy value"));
  mol.unmount();

  const foot = render(React.createElement(PanelFooter, { files: [{ label: "PNG", path: "/tmp/a.png" }] }));
  const p = foot.container.querySelector('button[aria-label="Copy path"]');
  assert.ok(p && p.classList.contains("is-quiet"), "Pfad-Knopf nicht leise");
  foot.unmount();
});

// --- A3: Etikett und Wert nah beieinander; Knopf direkt hinter dem Wert ---------------------
test("Datenblatt-Zeile: Wert und Kopierknopf in einer Gruppe, der Knopf direkt hinter dem Wert", () => {
  const view = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(DatabaseView, { data: SHEET })));
  const dd = view.container.querySelector(".source-row dd");
  const value = dd.querySelector(".source-value");
  assert.ok(value, "Wert ohne eigene Klasse");
  assert.equal(value.nextElementSibling?.tagName, "BUTTON", "Knopf steht nicht direkt hinter dem Wert");
  view.unmount();
});

// --- A4: Summenformel tiefgestellt, kopiert wird Klarschrift --------------------------------
test("Datenblatt: Summenformel mit tiefgestellten Ziffern", () => {
  const view = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(DatabaseView, { data: SHEET })));
  const row = [...view.container.querySelectorAll(".source-row")].find((r) => /Molecular formula/.test(textOf(r)));
  const subs = [...row.querySelectorAll("dd sub")].map((s) => s.textContent);
  assert.deepEqual(subs, ["9", "8", "4"]);
  const other = [...view.container.querySelectorAll(".source-row")].find((r) => /InChIKey/.test(textOf(r)));
  assert.equal(other.querySelectorAll("sub").length, 0, "InChIKey darf keine Tiefstellung bekommen");
  view.unmount();
});

test("formulaParts: Indizes tief, Koeffizienten nach · und Ladungen bleiben", () => {
  const sub = (s) => formulaParts(s).filter((p) => p.sub).map((p) => p.text);
  assert.deepEqual(sub("C8H9NO2"), ["8", "9", "2"]);
  assert.deepEqual(sub("CuSO4·5H2O"), ["4", "2"], "Kristallwasser-Koeffizient tiefgestellt");
  assert.deepEqual(sub("2H2O"), ["2"], "führender Koeffizient tiefgestellt");
  assert.deepEqual(sub("Ca(OH)2"), ["2"]);
  assert.equal(formulaParts("C8H9NO2").map((p) => p.text).join(""), "C8H9NO2");
});

// --- B5: Continue in chat als eine kompakte Zeile -------------------------------------------
test("Continue in chat: eine Zeile, Erklärung nur noch für Bedienungshilfen und als Tooltip", () => {
  const view = withHost(React.createElement(MoleculeView, { data: MOLECULE }));
  const row = view.container.querySelector("[data-testid='continue-row']");
  assert.equal(row.getAttribute("aria-label"), "Continue in chat");
  assert.equal(Boolean(row.querySelector(".continue-head")), false, "eigene Kopfzeile über den Knöpfen");
  const label = row.querySelector(".continue-label");
  assert.ok(label, "kleines Etikett vor den Knöpfen fehlt");
  assert.equal(label.textContent, "Continue in chat");
  assert.equal(label.getAttribute("title"), "Each button writes one message for Claude");
  const hintId = row.getAttribute("aria-describedby");
  assert.ok(hintId, "Erklärung nicht als Beschreibung verknüpft");
  const hint = row.ownerDocument.getElementById(hintId);
  assert.equal(hint?.textContent, "Each button writes one message for Claude");
  assert.ok(hint.classList.contains("visually-hidden"), "Erklärung steht noch sichtbar da");
  assert.equal(label.parentElement === row.querySelector(".continue-actions"), true, "Etikett steht nicht in der Knopfreihe");
  view.unmount();
});

// --- B6: Gruppen-Hinweis in der Überschrift -------------------------------------------------
// Panel-Umbau A (§5.1): das sichtbare Etikett „Functional groups“ entfällt, es lebt als aria-label der Sektion.
test("Gruppen: Chips und Hinweis in einer Zeile; der Hinweis ist knapp, der Rest Tooltip", async () => {
  const view = withHost(React.createElement(MoleculeView, { data: MOLECULE }));
  const section = view.container.querySelector(".group-section");
  const head = section.querySelector(".group-section-row");
  assert.ok(head, "keine gemeinsame Zeile");
  assert.equal(section.getAttribute("aria-label"), "Functional groups", "Sektion ohne Namen");
  assert.equal(head.querySelector(".section-label"), null, "sichtbares Etikett steht noch da");
  assert.ok(head.querySelector("button.functional-group"), "Chips nicht in der Zeile");
  const note = head.querySelector(".group-note[role=status]");
  assert.ok(note, "Status nicht in der Zeile");
  const hint = note.querySelector(".group-note-hint");
  assert.equal(hint.getAttribute("title"), "Click a group to pin it. The buttons below then ask Claude about it.");
  const visible = [...hint.childNodes].filter((n) => !(n.classList?.contains("visually-hidden"))).map((n) => n.textContent).join("");
  assert.equal(visible, "Click a group to pin it", "sichtbarer Hinweis nicht knapp");
  const ester = [...section.querySelectorAll("button.functional-group")].find((b) => b.textContent.includes("Ester"));
  await click(ester);
  assert.doesNotMatch(textOf(note), /Click a group/, "Hinweis bleibt trotz angehefteter Gruppe");
  assert.match(textOf(note), /Ester/);
  view.unmount();
});
