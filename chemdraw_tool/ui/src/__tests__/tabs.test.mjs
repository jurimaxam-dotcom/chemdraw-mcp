// Das gemeinsame Reiter-Bauteil (Etappe 3): eine Machart für Struktur/Daten/Study,
// Mechanismus, Datenblatt-Quellen und Protein — Tastatur nach WAI-ARIA-Tabs
// (Pfeile bewegen den Fokus, Enter/Leertaste bzw. Klick wählen; Data lädt erst dann).
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";
import { act } from "react";

import Tabs from "../components/Tabs";
import DatabaseView from "../DatabaseView";
import MechanismView from "../MechanismView";
import { DATABASE_GHS } from "./fixtures.mjs";
import { buttonByText, click, render } from "./harness.mjs";

const TABS = [{ key: "a", label: "Alpha" }, { key: "b", label: "Beta" }, { key: "c", label: "Gamma" }];

function setup(props = {}) {
  const calls = [];
  const view = render(React.createElement(Tabs, { label: "Probe", tabs: TABS, value: "b", onChange: (k) => calls.push(k), ...props }));
  const tabs = () => [...view.container.querySelectorAll('[role="tab"]')];
  return { ...view, calls, tabs };
}

async function key(el, k) {
  await act(async () => {
    el.dispatchEvent(new window.KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
  });
}

test("Tabliste mit Namen, Reitern und aria-selected", () => {
  const { container, tabs, unmount } = setup();
  const list = container.querySelector('[role="tablist"]');
  assert.equal(list.getAttribute("aria-label"), "Probe");
  assert.deepEqual(tabs().map((t) => t.textContent), ["Alpha", "Beta", "Gamma"]);
  assert.deepEqual(tabs().map((t) => t.getAttribute("aria-selected")), ["false", "true", "false"]);
  unmount();
});

test("nur der gewählte Reiter liegt in der Tab-Reihenfolge (roving tabindex)", () => {
  const { tabs, unmount } = setup();
  assert.deepEqual(tabs().map((t) => t.tabIndex), [-1, 0, -1]);
  unmount();
});

test("Pfeile bewegen den Fokus mit Umlauf, Home/End springen — gewählt wird erst per Klick", async () => {
  const { tabs, calls, unmount } = setup();
  tabs()[1].focus();
  await key(tabs()[1], "ArrowRight");
  assert.equal(document.activeElement, tabs()[2]);
  await key(tabs()[2], "ArrowRight");
  assert.equal(document.activeElement, tabs()[0], "kein Umlauf am Ende");
  await key(tabs()[0], "ArrowLeft");
  assert.equal(document.activeElement, tabs()[2], "kein Umlauf am Anfang");
  await key(tabs()[2], "Home");
  assert.equal(document.activeElement, tabs()[0]);
  await key(tabs()[0], "End");
  assert.equal(document.activeElement, tabs()[2]);
  assert.deepEqual(calls, [], "Pfeiltaste hat schon gewählt (Data würde laden)");
  await click(tabs()[2]);
  assert.deepEqual(calls, ["c"]);
  unmount();
});

test("klein und groß unterscheiden sich nur in der Größe, nicht in der Machart", () => {
  const big = setup();
  const small = setup({ size: "sm" });
  const cls = (v) => v.container.querySelector('[role="tablist"]').className;
  assert.match(cls(big), /\bseg\b/);
  assert.match(cls(small), /\bseg\b/);
  assert.match(cls(small), /\bseg-sm\b/);
  big.unmount();
  small.unmount();
});

test("Datenblatt: PubChem/GHS sind Reiter des Bauteils, keine aria-pressed-Knöpfe", async () => {
  const view = render(React.createElement(DatabaseView, { data: DATABASE_GHS }));
  const list = view.container.querySelector('[role="tablist"][aria-label="Data sources"]');
  assert.ok(list, "keine Tabliste für die Quellen");
  assert.match(list.className, /\bseg-sm\b/);
  const ghs = [...list.querySelectorAll('[role="tab"]')].find((t) => t.textContent === "GHS");
  assert.equal(ghs.getAttribute("aria-selected"), "false");
  await click(ghs);
  assert.equal(ghs.getAttribute("aria-selected"), "true");
  view.unmount();
});

test("Mechanismus: Overview/Step by step sind Reiter des Bauteils", async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><rect width="10" height="10"/></svg>';
  const data = { type: "mechanism", name: "SN2", reaction_type: "sn2", steps: [{ svg, label: "a" }, { svg, label: "b" }] };
  const view = render(React.createElement(MechanismView, { data }));
  const list = view.container.querySelector('[role="tablist"]');
  assert.ok(list, "keine Tabliste im Mechanismus");
  const step = [...list.querySelectorAll('[role="tab"]')].find((t) => t.textContent === "Step by step");
  assert.ok(step);
  await click(step);
  assert.equal(step.getAttribute("aria-selected"), "true");
  assert.ok(buttonByText(view.container, "Overview"));
  view.unmount();
});
