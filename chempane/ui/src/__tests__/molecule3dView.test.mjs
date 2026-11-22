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

// Umbau C (17.11.2026, Spezifikation §5.11): Formel und Molmasse wandern aus dem Untertitel
// in die Kernwert-Zeile unter der Bühne; der Untertitel beginnt weiter mit „3D conformer“ (Probe).
test("Kopf: Untertitel beginnt mit „3D conformer“, Formel und Molmasse stehen als Kernwerte darunter", () => {
  const { container, unmount } = render(React.createElement(Molecule3DView, { data: ETHANOL }));
  const sub = container.querySelector(".panel-subtitle");
  assert.match(sub.textContent, /^3D conformer/);
  assert.doesNotMatch(sub.textContent, /C2H6O|g\/mol/, "Formel und Masse gehören in die Kernwerte");
  const facts = container.querySelector(".panel-facts");
  assert.ok(facts, "Kernwert-Zeile fehlt");
  assert.match(facts.textContent, /Formula\s*C2H6O/);
  assert.match(facts.textContent, /Molar mass\s*46\.07 g\/mol/);
  assert.equal(facts.querySelectorAll("sub").length, 2, "Indizes tiefgestellt");
  unmount();
});

test("Kernwerte nehmen Formel und Molmasse des Servers, nicht die aus den Atomen (Isotope, Ladung)", () => {
  // Codex-Review 16.11.2026: schweres Wasser stand mit 18,02 statt 20,03 g/mol im Kopf.
  const data = { ...ETHANOL, formula: "H2O", molar_mass: 20.03 };
  const { container, unmount } = render(React.createElement(Molecule3DView, { data }));
  const facts = container.querySelector(".panel-facts");
  assert.match(facts.textContent, /H2O/);
  assert.match(facts.textContent, /20\.03 g\/mol/);
  assert.equal(/46\.07/.test(container.textContent), false);
  unmount();
});

test("Zonen nach §2: Kopf → StageBar (Hinweis, Reset view) → 3D-Bühne → Kernwerte → Fuß", () => {
  const { container, unmount } = render(React.createElement(Molecule3DView, { data: ETHANOL }));
  const panel = container.firstElementChild;
  assert.ok(panel.matches("article.panel.m3d-panel[data-fill]"), panel.outerHTML.slice(0, 120));
  const zones = [...panel.children].map((el) => el.classList.contains("panel-head") ? "head"
    : el.classList.contains("stage-bar") ? "bar" : el.classList.contains("stage") ? "stage"
      : el.classList.contains("panel-facts") ? "facts" : el.classList.contains("panel-foot") ? "foot" : el.className);
  assert.deepEqual(zones, ["head", "bar", "stage", "facts", "foot"]);
  const stage = panel.querySelector(".stage");
  assert.ok(stage.classList.contains("stage-3d") && stage.classList.contains("m3d-stage"), "Bühne variant 3d mit Haken .m3d-stage");
  assert.ok(stage.querySelector("svg[aria-label='3D model, drag to rotate']"));
  const bar = panel.querySelector(".stage-bar");
  assert.ok(buttonByText(bar, "Reset view"), "Reset view steht in der StageBar");
  assert.match(bar.textContent, /Drag to rotate/);
  assert.equal(panel.querySelector(".rotate-row"), null, "alte Zeile unter dem Modell entfällt");
  assert.equal(panel.style.padding, "", "kein Inline-Polster mehr");
  unmount();
});

test("Stylesheet: keine 640-px-Kappe, in Fill höchstens so hoch wie breit (Rest unter dem Fuß)", async () => {
  const { readFileSync } = await import("node:fs");
  const css = readFileSync(new URL("../styles/c-protein-3d-anki.css", import.meta.url), "utf8");
  assert.doesNotMatch(css, /max-height:\s*640px/, "3D nie kleiner als 720 im Chat");
  assert.match(css, /\.m3d-panel[^{]*\{[^}]*container-type:\s*inline-size/);
  assert.match(css, /data-host-height[^{]*\.m3d-stage[^{]*\{[^}]*max-height:\s*100cqw/);
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
