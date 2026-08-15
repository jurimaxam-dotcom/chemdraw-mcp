// Der Umschalter selbst: Tastatur- und Screenreader-Semantik plus der
// Ladezustand, den nur die teure Richtung (→ Daten) braucht.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import ViewToggle from "../components/ViewToggle";
import { buttonByText, click, render } from "./harness.mjs";

function setup(props) {
  const calls = [];
  const view = render(
    React.createElement(ViewToggle, {
      view: "structure",
      onChange: (v) => calls.push(v),
      ...props,
    })
  );
  return { ...view, calls };
}

test("ist eine Tabliste mit genau zwei Reitern, Struktur zuerst", () => {
  const { container, unmount } = setup();
  const list = container.querySelector('[role="tablist"]');
  assert.ok(list, "kein role=tablist im Umschalter");
  const tabs = [...container.querySelectorAll('[role="tab"]')];
  assert.deepEqual(
    tabs.map((t) => t.textContent.trim()),
    ["Structure", "Data"]
  );
  unmount();
});

test("aria-selected markiert die aktive Ansicht", () => {
  const { container, rerender, unmount } = setup();
  const selected = () =>
    [...container.querySelectorAll('[role="tab"]')]
      .filter((t) => t.getAttribute("aria-selected") === "true")
      .map((t) => t.textContent.trim());

  assert.deepEqual(selected(), ["Structure"]);
  rerender(React.createElement(ViewToggle, { view: "data", onChange: () => {} }));
  assert.deepEqual(selected(), ["Data"]);
  unmount();
});

test("ein Klick meldet die gewuenschte Ansicht nach oben", async () => {
  const { container, calls, unmount } = setup();
  await click(buttonByText(container, "Data"));
  await click(buttonByText(container, "Structure"));
  assert.deepEqual(calls, ["data", "structure"]);
  unmount();
});

test("der Spinner steckt im Daten-Knopf und nur waehrend des Ladens", () => {
  const { container, rerender, unmount } = setup();
  assert.equal(container.querySelector(".seg-spinner"), null);

  rerender(
    React.createElement(ViewToggle, {
      view: "structure",
      onChange: () => {},
      loading: true,
    })
  );
  const spinner = container.querySelector(".seg-spinner");
  assert.ok(spinner, "kein Spinner im Ladezustand");
  assert.equal(
    spinner.closest('[role="tab"]').textContent.trim(),
    "Data",
    "der Spinner gehoert in den Knopf, der laedt"
  );
  unmount();
});
