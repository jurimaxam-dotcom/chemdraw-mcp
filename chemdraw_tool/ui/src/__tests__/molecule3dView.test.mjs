// Etappe 5 (16.11.2026): 3D-Einzelansicht mit Summenformel und Molmasse (aus den Atomen des
// Konformers, explizite H) und „Reset view“, der die Ausgangsdrehung wiederherstellt — im
// Chat-Einstieg (generate_3d) wie hinter dem 3D-Knopf des Molekül-Panels, gleicher Name.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import Molecule3DView from "../Molecule3DView";
import { formulaOfAtoms, massOfAtoms } from "../utils/atoms3d.js";
import { buttonByText, click, render, textOf } from "./harness.mjs";

const ETHANOL = {
  type: "molecule3d", name: "Ethanol",
  atoms: [
    { symbol: "C", x: -1.2, y: 0.1, z: 0 }, { symbol: "C", x: 0.2, y: -0.3, z: 0.1 }, { symbol: "O", x: 1.1, y: 0.6, z: -0.2 },
    ...[[-1.8, -0.7, 0], [-1.3, 0.7, 0.9], [-1.5, 0.7, -0.8], [0.3, -1, 0.9], [0.4, -0.9, -0.8], [2, 0.3, -0.1]]
      .map(([x, y, z]) => ({ symbol: "H", x, y, z })),
  ],
  bonds: [{ a: 0, b: 1, order: 1 }, { a: 1, b: 2, order: 1 }],
  files: { sdf: "/Users/x/ChemDraw-Output/3d/ethanol.sdf" },
};

test("Summenformel nach Hill und Molmasse aus den Atomen", () => {
  assert.equal(formulaOfAtoms(ETHANOL.atoms), "C2H6O");
  assert.equal(formulaOfAtoms([{ symbol: "Cl" }, { symbol: "Na" }]), "ClNa");
  assert.ok(Math.abs(massOfAtoms(ETHANOL.atoms) - 46.07) < 0.01);
  assert.equal(massOfAtoms([{ symbol: "Xx" }]), null, "unbekanntes Element: keine Masse statt einer falschen");
});

test("Kopf: Formel und Molmasse im Untertitel, der mit „3D conformer“ beginnt", () => {
  const { container, unmount } = render(React.createElement(Molecule3DView, { data: ETHANOL }));
  const sub = container.querySelector(".panel-subtitle");
  assert.match(sub.textContent, /^3D conformer/);
  assert.match(sub.textContent, /C2H6O · 46\.07 g\/mol/);
  assert.equal(sub.querySelectorAll("sub").length, 2, "Indizes tiefgestellt");
  unmount();
});

const geometry = (c) => JSON.stringify([...c.querySelectorAll("circle[fill^='url(#atom-']")].map((a) => [a.getAttribute("cx"), a.getAttribute("cy")]));
const pointer = (el, type, x, y) => act(async () => {
  el.dispatchEvent(new window.MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y }));
});

test("Reset view stellt die Ausgangsdrehung wieder her", async () => {
  const { container, unmount } = render(React.createElement(Molecule3DView, { data: ETHANOL }));
  const svg = container.querySelector("svg");
  const start = geometry(container);
  await pointer(svg, "pointerdown", 100, 100);
  await pointer(svg, "pointermove", 180, 140);
  await pointer(svg, "pointerup", 180, 140);
  assert.notEqual(geometry(container), start, "Ziehen dreht nicht");
  const reset = buttonByText(container, "Reset view");
  assert.ok(reset, "Knopf Reset view fehlt");
  await click(reset);
  assert.equal(geometry(container), start);
  assert.match(textOf(container), /Drag to rotate/);
  assert.equal(container.querySelector("svg"), container.querySelector("svg[role='img']"), "das erste SVG ist das Modell");
  unmount();
});
