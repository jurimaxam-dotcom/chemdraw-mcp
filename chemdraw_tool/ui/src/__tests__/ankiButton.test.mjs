// Lernweg Molekül → Anki: ein Klick am Panel baut genau eine Karte zu genau
// diesem Molekül und lässt den Server sie an Anki übergeben. Async-Pfade nur
// in act() — sonst bleibt das Folge-Render ungeflusht und der Test grün.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import { AppContext } from "../AppContext";
import MoleculeView from "../MoleculeView";
import AddToAnkiButton, { ANKI_DECK } from "../components/AddToAnkiButton";
import { MOLECULE, lookupFailure } from "./fixtures.mjs";
import { buttonByText, click, render } from "./harness.mjs";

function ankiSuccess(delivery = "open") {
  const payload = {
    type: "anki_deck", name: ANKI_DECK, cards: 1, media: 1, delivery,
    fronts: [MOLECULE.properties.smiles], file: "/tmp/anki/chemdraw.apkg",
  };
  return { isError: false, content: [{ type: "text", text: JSON.stringify(payload) }] };
}

function setup(respond = () => ankiSuccess(), data = MOLECULE) {
  const calls = [];
  const app = { callServerTool: async (req) => { calls.push(req); return respond(req); } };
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(MoleculeView, { data }))
  );
  const button = () => view.container.querySelector("button.add-to-anki");
  return { ...view, calls, button };
}

test("das Molekül-Panel trägt einen Add-to-Anki-Knopf neben dem PNG-Export", () => {
  const { container, button, calls, unmount } = setup();
  assert.ok(button(), "kein Anki-Knopf im Panel");
  assert.equal(button().textContent.trim(), "Add to Anki");
  assert.ok(container.querySelector(".panel-actions button.add-to-anki"), "Knopf nicht in den Panel-Aktionen");
  assert.equal(calls.length, 0, "Toolaufruf ohne Klick");
  unmount();
});

test("ein Klick ruft export_anki_deck mit einer Karte: Struktur vorn, Name und Formel hinten", async () => {
  const { button, calls, unmount } = setup();
  await click(button());

  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "export_anki_deck");
  const args = calls[0].arguments;
  assert.equal(args.deck_name, ANKI_DECK);
  assert.equal(args.deliver, "open");
  assert.equal(args.cards.length, 1, "genau eine Karte");
  const [card] = args.cards;
  // SMILES statt Name: kein Netz nötig, und die GUID hängt am Molekül.
  assert.equal(card.front.structure, MOLECULE.properties.smiles);
  assert.equal(card.front.text ?? "", "");
  assert.match(card.back.text, /Aspirin/);
  assert.match(card.back.text, /C<sub>9<\/sub>H<sub>8<\/sub>O<sub>4<\/sub>/);
  unmount();
});

test("Erfolg meldet sich kurz als Added", async () => {
  const { button, unmount } = setup();
  await click(button());
  assert.equal(button().textContent.trim(), "Added");
  assert.match(button().title, /chemdraw\.apkg/);
  unmount();
});

test("ohne Öffnen (nicht macOS) meldet der Knopf ehrlich nur das Speichern", async () => {
  const { button, unmount } = setup(() => ankiSuccess("apkg"));
  await click(button());
  assert.equal(button().textContent.trim(), "Saved");
  unmount();
});

test("während der Server arbeitet, ist der Knopf deaktiviert und nimmt keinen zweiten Klick", async () => {
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  const { button, calls, unmount } = setup(async () => { await pending; return ankiSuccess(); });

  await click(button());
  assert.equal(button().disabled, true, "Knopf bleibt während des Laufs bedienbar");
  await click(button());
  assert.equal(calls.length, 1, "Doppelklick löst einen zweiten Export aus");

  await act(async () => { release(); await pending; });
  assert.equal(button().disabled, false);
  assert.equal(button().textContent.trim(), "Added");
  unmount();
});

test("ein Fehlschlag ist sichtbar und der nächste Klick ein neuer Versuch", async () => {
  let ok = false;
  const { button, calls, unmount } = setup(() => (ok ? ankiSuccess() : lookupFailure()));
  await click(button());
  assert.equal(button().textContent.trim(), "Retry Anki");
  assert.equal(button().disabled, false, "Fehlschlag sperrt den Knopf");
  ok = true;
  await click(button());
  assert.equal(calls.length, 2);
  assert.equal(button().textContent.trim(), "Added");
  unmount();
});

test("ohne SMILES gibt es keinen Anki-Knopf", () => {
  const data = { ...MOLECULE, properties: { ...MOLECULE.properties, smiles: "" } };
  const { button, unmount } = setup(undefined, data);
  assert.equal(button(), null);
  unmount();
});

test("der Knopf funktioniert auch ohne umgebendes Panel", async () => {
  const calls = [];
  const app = { callServerTool: async (req) => { calls.push(req); return ankiSuccess(); } };
  const { container, unmount } = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(AddToAnkiButton, { smiles: "CCO", name: "Ethanol", formula: "C2H6O" }))
  );
  await click(buttonByText(container, "Add to Anki"));
  assert.equal(calls[0].arguments.cards[0].back.text.includes("Ethanol"), true);
  unmount();
});
