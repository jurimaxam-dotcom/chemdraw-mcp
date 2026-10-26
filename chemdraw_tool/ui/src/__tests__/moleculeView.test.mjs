// Richtung „→ Daten": teuer, also genau einmal — und ein Fehlschlag muss
// sichtbar landen, nicht als leere Flaeche.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import MoleculeView, { DATA_LOAD_ERROR, VIEW_LOAD_ERROR } from "../MoleculeView";
import { MOLECULE, lookupFailure, lookupSuccess } from "./fixtures.mjs";
import { act } from "react";

import { buttonByText, click, render, textOf } from "./harness.mjs";

function setup(respond = () => lookupSuccess()) {
  const calls = [];
  const app = {
    callServerTool: async (req) => {
      calls.push(req);
      return respond(req);
    },
  };
  const view = render(
    React.createElement(
      AppContext.Provider,
      { value: app },
      React.createElement(MoleculeView, { data: MOLECULE })
    )
  );
  const panel = (which) => view.container.querySelector(`[data-view="${which}"]`);
  return { ...view, calls, panel };
}

test("startet in der Struktur-Ansicht, ohne irgendetwas nachzuladen", () => {
  const { container, calls, panel, unmount } = setup();
  assert.ok(panel("structure"), "keine Struktur-Ansicht");
  assert.equal(panel("data"), null, "Datenblatt schon sichtbar");
  assert.ok(container.querySelector("svg"), "Struktur ohne SVG");
  assert.equal(calls.length, 0, "Toolaufruf ohne Klick");
  unmount();
});

test("Der Daten-Reiter ruft lookup_molecule_data mit dem SMILES und zeigt die Quellen", async () => {
  const { container, calls, panel, unmount } = setup();
  await click(buttonByText(container, "Data"));

  assert.equal(calls.length, 1, `erwartet 1 Aufruf, waren ${calls.length}`);
  assert.equal(calls[0].name, "lookup_molecule_data");
  assert.equal(calls[0].arguments.name, MOLECULE.properties.smiles);

  const sheet = panel("data");
  assert.ok(sheet, "keine Daten-Ansicht nach dem Klick");
  assert.match(textOf(sheet), /50-78-2/, "Quellzeilen fehlen im Datenblatt");
  unmount();
});

test("der zweite Klick nimmt den Cache — kein zweiter Toolaufruf", async () => {
  const { container, calls, panel, unmount } = setup();
  await click(buttonByText(container, "Data"));
  await click(buttonByText(container, "Structure"));
  assert.ok(panel("structure"), "Rueckweg zur Struktur klappt nicht");
  await click(buttonByText(container, "Data"));

  assert.equal(calls.length, 1, `erwartet 1 Aufruf, waren ${calls.length}`);
  assert.ok(panel("data"), "Cache-Klick zeigt kein Datenblatt");
  unmount();
});

test("ein fehlgeschlagener Aufruf zeigt einen Hinweis statt einer leeren Flaeche", async () => {
  const { container, panel, unmount } = setup(() => lookupFailure());
  await click(buttonByText(container, "Data"));

  const sheet = panel("data");
  assert.ok(sheet, "Fehlschlag laesst das Panel im Nichts");
  const text = textOf(sheet);
  assert.notEqual(text, "", "Daten-Ansicht ist leer");
  assert.equal(text, DATA_LOAD_ERROR);
  assert.doesNotMatch(text, /Error:|Traceback|at .*\.jsx/, "Stacktrace im Panel");
  unmount();
});

test("nach einem Fehlschlag ist der naechste Klick ein neuer Versuch", async () => {
  let ok = false;
  const { container, calls, panel, unmount } = setup(() =>
    ok ? lookupSuccess() : lookupFailure()
  );
  await click(buttonByText(container, "Data"));
  ok = true;
  await click(buttonByText(container, "Data"));

  assert.equal(calls.length, 2, "Fehlschlag darf nicht gecacht werden");
  assert.match(textOf(panel("data")), /50-78-2/);
  unmount();
});

// Die Ecke, die beim Bauen offen blieb: waehrend „Data" laedt, klickt der
// Nutzer zurueck auf „Structure". Loest der Aufruf danach auf, darf er die
// Ansicht NICHT unter dem Nutzer wegziehen — sein Klick ist die juengere
// Absicht. Bei PubChem-Latenz ist das kein Randfall, sondern Alltag.
test("ein Rueckwechsel waehrend des Ladens ueberstimmt das eintreffende Ergebnis", async () => {
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  const { container, panel, unmount } = setup(async () => {
    await pending;
    return lookupSuccess();
  });

  await click(buttonByText(container, "Data"));      // startet den Aufruf
  await click(buttonByText(container, "Structure")); // Nutzer wechselt zurueck
  assert.ok(panel("structure"), "Rueckwechsel greift nicht sofort");

  // In act() aufloesen, sonst bleibt das Folge-Render ungeflusht und der
  // Test waere gruen, ohne den Fall ueberhaupt zu erreichen.
  await act(async () => {
    release();
    await pending;
  });

  assert.ok(
    panel("structure"),
    "das eintreffende Datenblatt hat die Ansicht unter dem Nutzer weggezogen"
  );

  // Geholt ist geholt: der naechste Klick darf den Cache nehmen.
  await click(buttonByText(container, "Data"));
  assert.ok(panel("data"), "Datenblatt nach dem Rueckwechsel nicht abrufbar");
  unmount();
});

test("ein neuer Stoff im selben App-Slot verwirft das alte Datenblatt", async () => {
  const { default: App } = await import("../App");
  const calls = [];
  const bridge = { callServerTool: async (req) => {
    calls.push(req.arguments.name);
    return lookupSuccess();
  } };
  const element = (data) => React.createElement(AppContext.Provider, { value: bridge }, React.createElement(App, { data }));
  const { container, rerender, unmount } = render(element(MOLECULE));
  await click(buttonByText(container, "Data"));
  assert.match(textOf(container.querySelector('[data-view="data"]')), /50-78-2/);
  rerender(element({ ...MOLECULE, name: "Caffeine", properties: { smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O" } }));
  assert.ok(container.querySelector('[data-view="structure"]'), "neuer Stoff muss mit eigener Struktur starten");
  await click(buttonByText(container, "Data"));
  assert.equal(calls.length, 2, "alter Stoff-Cache darf neuen Lookup nicht ersetzen");
  unmount();
});

// Was Studierende brauchen: Struktur, Formel, molare Masse, CAS, Gruppen.
// SMILES, Rule of Five und der IUPAC-Untertitel sind bewusst raus (Designentscheid 15.10.2026).
test("die Struktur-Ansicht zeigt die Kernwerte und nichts darueber hinaus", () => {
  const { panel, container, unmount } = setup();
  const text = textOf(panel("structure"));
  assert.match(text, /Formula/);
  assert.match(text, /Molar mass/);
  assert.match(text, /180\.16/);
  assert.match(text, /50-78-2/);
  assert.doesNotMatch(text, /CC\(=O\)Oc1ccccc1C\(=O\)O/, "SMILES steht noch im Panel");
  assert.doesNotMatch(text, /Lipinski|Rule of Five/, "Rule of Five steht noch im Panel");
  assert.doesNotMatch(textOf(container), /Acetyloxy/, "IUPAC-Untertitel steht noch im Kopf");
  unmount();
});

test("die Einheit der molaren Masse steht genau einmal da", () => {
  const data = { ...MOLECULE, properties: { ...MOLECULE.properties, mw: "180.16 g/mol" } };
  const view = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(MoleculeView, { data })));
  assert.doesNotMatch(textOf(view.container), /g\/mol g\/mol/);
  assert.match(textOf(view.container), /180\.16 g\/mol/);
  view.unmount();
});

test("Hover auf eine Gruppe nennt sie unter den Gruppen, ohne Erklaersatz", async () => {
  const { container, unmount } = setup();
  const note = () => textOf(container.querySelector(".group-note"));
  assert.match(note(), /Hover a group/, "Ruhezustand ohne Hinweis");
  const group = [...container.querySelectorAll("button")].find((b) => b.textContent.includes("Ester"));
  await act(async () => group.focus());
  assert.match(note(), /Ester/);
  assert.match(note(), /–COO–/, "Formel der Gruppe fehlt");
  assert.doesNotMatch(note(), /hydrolys/i, "Erklaersatz steht noch da");
  await act(async () => group.blur());
  assert.match(note(), /Hover a group/, "Erklaerung bleibt nach dem Verlassen stehen");
  unmount();
});

test("funktionelle Gruppen sind per Tastatur fokussierbar und markieren die Struktur", async () => {
  const { container, unmount } = setup();
  const group = [...container.querySelectorAll('button')].find((b) => b.textContent.includes("Ester"));
  assert.ok(group, "Gruppe muss ein bedienbarer Knopf sein");
  await act(async () => group.focus());
  assert.equal(group.getAttribute("aria-pressed"), "true");
  await click(group);
  assert.equal(group.getAttribute("aria-pressed"), "true");
  unmount();
});

// Zusatzansichten (All H, Fischer, Haworth): das Payload sagt nur, OB es sie
// gibt. Der erste Klick holt die Zeichnung per generate_molecule(view=…), der
// zweite kommt aus dem Cache (Jay 26.10.: „Erst auf Klick“).
const SVG_ALL_H = "<svg viewBox='0 0 40 20'><path d='M1 1' data-all-h='1'/></svg>";
const SVG_FISCHER = "<svg viewBox='0 0 40 20'><text data-fischer='1'>CHO</text></svg>";
const SVG_HAWORTH = "<svg viewBox='0 0 40 20'><text data-haworth='1'>O</text></svg>";
const VIEW_SVG = { all_h: SVG_ALL_H, fischer: SVG_FISCHER, haworth: SVG_HAWORTH };
const REQUEST = { name_or_smiles: "CC(=O)Oc1ccccc1C(=O)O", annotate_stereo: true };

function renderMolecule(data, respond) {
  const calls = [];
  const app = { callServerTool: async (req) => {
    calls.push(req);
    if (respond) return respond(req);
    const svg = VIEW_SVG[req.arguments.view];
    return lookupSuccess({ type: "molecule", svg, atoms: [] });
  } };
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(MoleculeView, { data }))
  );
  return { ...view, calls };
}

test("„All H“ holt die Zeichnung beim ersten Klick, danach aus dem Cache", async () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data);
  const drawing = () => container.querySelector(".structure-drawing");
  assert.equal(calls.length, 0, "Laden ohne Klick");

  await click(buttonByText(container, "All H"));
  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "generate_molecule");
  assert.deepEqual(calls[0].arguments, { ...REQUEST, view: "all_h" });
  assert.ok(drawing().querySelector("[data-all-h]"), "H-Zeichnung nicht sichtbar");
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "true");

  await click(buttonByText(container, "All H"));
  assert.equal(drawing().querySelector("[data-all-h]"), null, "Rückweg zur Skelettformel fehlt");
  await click(buttonByText(container, "All H"));
  assert.ok(drawing().querySelector("[data-all-h]"));
  assert.equal(calls.length, 1, "zweiter Klick muss aus dem Cache kommen");
  unmount();
});

test("ohne Ansichten keine Knöpfe", () => {
  const { container, unmount } = renderMolecule(MOLECULE);
  for (const label of ["All H", "Fischer", "Haworth"]) assert.ok(!buttonByText(container, label), label);
  unmount();
});

test("„Fischer“ und „All H“ schließen einander aus", async () => {
  const data = { ...MOLECULE, views: ["all_h", "fischer"], viewRequest: REQUEST };
  const { container, unmount } = renderMolecule(data);
  const drawing = () => container.querySelector(".structure-drawing");
  assert.ok(!buttonByText(container, "Haworth"), "Haworth-Knopf ohne Ansicht");

  await click(buttonByText(container, "Fischer"));
  assert.ok(drawing().querySelector("[data-fischer]"), "Fischer-Projektion nicht sichtbar");
  await click(buttonByText(container, "All H"));
  assert.equal(drawing().querySelector("[data-fischer]"), null, "Ansichten schließen einander nicht aus");
  assert.ok(drawing().querySelector("[data-all-h]"));
  assert.equal(buttonByText(container, "Fischer").getAttribute("aria-pressed"), "false");
  unmount();
});

test("„Haworth“ zeigt den Ring und den Satz, warum es keine Fischer-Projektion gibt", async () => {
  const note = "The Fischer projection shows the open-chain form.";
  const data = { ...MOLECULE, views: ["haworth"], viewRequest: REQUEST, projectionNote: note };
  const { container, unmount } = renderMolecule(data);
  assert.doesNotMatch(textOf(container), /open-chain/, "Hinweis vor dem Klick");
  await click(buttonByText(container, "Haworth"));
  assert.ok(container.querySelector(".structure-drawing [data-haworth]"), "Haworth nicht sichtbar");
  assert.match(textOf(container), /open-chain/, "Hinweis fehlt in der Haworth-Ansicht");
  unmount();
});

test("ein Fehlschlag bleibt sichtbar und wiederholbar", async () => {
  let fail = true;
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data, (req) =>
    fail ? lookupFailure() : lookupSuccess({ type: "molecule", svg: VIEW_SVG[req.arguments.view] }));
  await click(buttonByText(container, "All H"));
  assert.match(textOf(container), new RegExp(VIEW_LOAD_ERROR.slice(0, 20)));
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "false");
  fail = false;
  await click(buttonByText(container, "All H"));
  assert.ok(container.querySelector(".structure-drawing [data-all-h]"));
  assert.equal(calls.length, 2);
  unmount();
});
