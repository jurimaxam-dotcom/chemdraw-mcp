// Batch: ein Name, der nicht aufgelöst wurde, darf nicht still verschwinden —
// sonst sieht die Liste vollständig aus (Design-Kritik 07.11.2026, F1).
// Form des Fehlschlags wie in server.py batch_generate: `failed` ist eine
// Liste von Strings, die Eingabe selbst, bei Familiennamen mit
// " (ambiguous: …)" dahinter.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import App from "../App";
import { MOLECULE } from "./fixtures.mjs";
import { render, textOf } from "./harness.mjs";

const SECOND = {
  ...MOLECULE,
  name: "Caffeine",
  properties: { ...MOLECULE.properties, smiles: "Cn1cnc2c1c(=O)n(C)c(=O)n2C" },
};

function batch(failed) {
  return { type: "batch", molecules: [MOLECULE, SECOND], cdxml_paths: [], failed };
}

test("Batch mit Fehlschlag: Liste „Not drawn“ unter den gelungenen Kacheln", () => {
  const { container, unmount } = render(
    React.createElement(App, {
      data: batch(["xyzzyl", "xylene (ambiguous: o-xylene, m-xylene, p-xylene)"]),
    })
  );
  const list = container.querySelector('[data-testid="batch-failed"]');
  assert.ok(list, "Liste der Fehlschläge fehlt");
  assert.equal(list.getAttribute("role"), "status");
  assert.match(textOf(list), /Not drawn/);
  const items = [...list.querySelectorAll("li")];
  assert.equal(items.length, 2);
  assert.equal(textOf(items[0].querySelector(".batch-failed-input")), "xyzzyl");
  assert.match(textOf(items[0]), /could not be resolved/i);
  assert.equal(textOf(items[1].querySelector(".batch-failed-input")), "xylene");
  assert.match(textOf(items[1]), /ambiguous: o-xylene, m-xylene, p-xylene/);
  // Die gelungenen bleiben vollständig da, die Liste steht dahinter.
  assert.match(textOf(container), /Aspirin/);
  assert.match(textOf(container), /Caffeine/);
  const last = container.firstElementChild.lastElementChild;
  assert.equal(Boolean(last === list), true, "Liste steht nicht unter den Kacheln");
  unmount();
});

test("Batch ohne Fehlschlag zeigt keine Liste", () => {
  const { container, unmount } = render(React.createElement(App, { data: batch([]) }));
  assert.equal(Boolean(container.querySelector('[data-testid="batch-failed"]')), false);
  assert.doesNotMatch(textOf(container), /Not drawn/);
  unmount();
});
