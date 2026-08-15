// Richtung „→ Daten": teuer, also genau einmal — und ein Fehlschlag muss
// sichtbar landen, nicht als leere Flaeche.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import MoleculeView, { DATA_LOAD_ERROR } from "../MoleculeView";
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
