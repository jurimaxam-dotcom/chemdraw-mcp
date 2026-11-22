// Panel-Umbau Paket B: die Grafik-Panels
// stehen im gemeinsamen Rahmen (Panel, PanelHead, Stage, Facts, Hint, PanelFoot). Geprüft wird die
// Form, die ohne CSS im DOM sichtbar ist: Bühnen-Variante je Panel, keine Inline-Farbe, keine
// eingebetteten <style>-Blöcke, Bilanz und Mechanismus-Navigation als ruhige Knöpfe.
import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";

import React from "react";

import { AppContext } from "../AppContext";
import MechanismView from "../MechanismView";
import PlotView from "../PlotView";
import ReactionView from "../ReactionView";
import ScopeView from "../ScopeView";
import SpectrumView from "../SpectrumView";
import TlcView from "../TlcView";
import { buttonByText, click, render, textOf } from "./harness.mjs";

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    disconnect() {}
  };
}

const h = React.createElement;
const MPL = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 720 468'><!-- Created with matplotlib --></svg>";
const STEP = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200'><path d='M0 0'/></svg>";
const MOL = { svg: "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='80'></svg>", name: "x" };

const VIEWS = [
  ["Spektrum", "spectrum", () => h(SpectrumView, { data: { type: "spectrum", spectrum_type: "ir", name: "IR", svg: MPL, files: {} } }), "plain"],
  ["DC", "tlc", () => h(TlcView, { data: { type: "tlc", name: "DC", svg: MPL, lanes: [{ name: "A", spots: [{ rf: 0.3 }] }], files: {} } }), "plain"],
  ["Plot", "plot", () => h(PlotView, { data: { type: "plot", name: "Titration", subtitle: "s", svg: MPL, files: {} } }), "plain"],
  ["Reaktion", "reaction", () => h(ReactionView, { data: { type: "reaction", name: "R", reactants: [MOL], products: [MOL], conditions: "Δ",
    balance: { balanced: false, summary: "left: +1 O", suggestedEquation: "2 A → B" } } }), "plain"],
  ["Mechanismus", "mechanism", () => h(MechanismView, { data: { type: "mechanism", name: "M", reaction_type: "sn2", current_step: 0,
    steps: [{ svg: STEP, label: "a" }, { svg: STEP, label: "TS", is_transition_state: true }] } }), "plain"],
  ["Scope", "scope", () => h(ScopeView, { data: { type: "scope", name: "Scope", svg: MOL.svg,
    entries: [{ label: "1a", yield_text: "92 %" }], failed: ["xyz"], files: {} } }), "paper"],
];

for (const [label, kind, make, variant] of VIEWS) {
  test(`${label}: Panel-Rahmen mit Kopf, einer Bühne „${variant}“ und ohne Inline-Farbe`, () => {
    const { container, unmount } = render(make());
    const panel = container.firstElementChild;
    assert.equal(panel.tagName, "ARTICLE", "kein <Panel>");
    assert.equal(panel.getAttribute("data-panel"), kind);
    assert.equal(panel.firstElementChild.classList.contains("panel-head"), true, "Kopf ist nicht das erste Kind");
    const stages = container.querySelectorAll(".stage");
    assert.equal(stages.length, 1, `${stages.length} Bühnen`);
    assert.equal(stages[0].getAttribute("data-stage"), variant);
    assert.equal(stages[0].parentElement === panel, true, "Bühne ist kein direktes Kind des Panels (Fill-Kette)");
    assert.equal(container.querySelectorAll("style").length, 0, "eingebetteter <style>-Block");
    // Gemeinsame Bausteine (Kopf, Continue-Zeile, Fuß mit Export) gehören Paket A und zählen hier nicht.
    const colored = [...container.querySelectorAll("[style]")].filter((el) => !el.closest("svg, .panel-head, .continue-row, .panel-foot")
      && /(^|;)\s*(color|background|border|box-shadow|fill|stroke)[\w-]*\s*:|var\(--(radius|shadow)/.test(el.getAttribute("style")));
    assert.deepEqual(colored.map((el) => el.getAttribute("style")), [], "Inline-Farbe oder alter Rahmen-Token");
    unmount();
  });
}

test("Plot: Notizen mit „Name = Wert“ werden Kernwerte, der Rest ein Hinweis; Fettdruck bleibt", () => {
  const data = { type: "plot", name: "PK", svg: MPL, files: {},
    notes: ["t½ = 6 h · CL = 4.62 L/h", "Signal 0.47 → **4.61612** (x = (y − b) / a)"] };
  const { container, unmount } = render(h(PlotView, { data }));
  const facts = container.querySelector("dl.panel-facts");
  assert.ok(facts, "keine Kernwert-Zeile");
  assert.deepEqual([...facts.querySelectorAll("dt")].map(textOf), ["t½", "CL"]);
  assert.deepEqual([...facts.querySelectorAll("dd .fact-value")].map(textOf), ["6 h", "4.62 L/h"]);
  const hint = container.querySelector("p.hint");
  assert.ok(hint, "Satz-Notiz steht nicht als Hinweis");
  assert.equal(textOf(hint), "Signal 0.47 → 4.61612 (x = (y − b) / a)");
  assert.equal(hint.querySelector("strong")?.textContent, "4.61612");
  unmount();
});

test("DC: Rf-Werte als Kernwerte (Bahn → Wert), keine Mono-Schrift", () => {
  const data = { type: "tlc", name: "DC", svg: MPL, files: {},
    lanes: [{ name: "Edukt", spots: [{ rf: 0.3, label: "Edukt" }] }, { name: "Co-Spot", spots: [{ rf: 0.3 }, { rf: 0.65, label: "Produkt" }] }] };
  const { container, unmount } = render(h(TlcView, { data }));
  const facts = container.querySelector("dl.panel-facts");
  assert.deepEqual([...facts.querySelectorAll("dt")].map(textOf), ["Edukt", "Co-Spot"]);
  assert.deepEqual([...facts.querySelectorAll("dd .fact-value")].map(textOf), ["0.30", "0.30 · 0.65 Produkt"]);
  assert.equal([...container.querySelectorAll("[style]")].some((el) => /monospace/.test(el.getAttribute("style"))), false);
  unmount();
});

test("Reaktion: „balanced“ mit Häkchen-Symbol; Apply und Undo sind ruhige Knöpfe", async () => {
  const H2 = { svg: "<svg></svg>", name: "H2" };
  const request = { reactants: ["[H][H]"], products: ["O"] };
  const unbalanced = { type: "reaction", reactants: [H2], products: [H2], request,
    balance: { balanced: false, summary: "left: +1 O", suggestedCoefficients: [2, 1], suggestedEquation: "2 H₂ → H₂O" } };
  const applied = { ...unbalanced, reactants: [{ ...H2, coefficient: 2 }], balance: { balanced: true } };
  const app = { callServerTool: async () => ({ structuredContent: applied, content: [{ type: "text", text: "{}" }] }) };
  const { container, unmount } = render(h(AppContext.Provider, { value: app }, h(ReactionView, { data: unbalanced })));
  const off = container.querySelector("[data-testid='balance-badge']");
  assert.ok(off.closest("p.hint.hint-warn"), "Befund steht nicht als Hinweis (warn)");
  const apply = buttonByText(container, "Apply coefficients");
  assert.equal(apply.classList.contains("btn"), true, "Apply ist kein ruhiger Knopf");
  assert.equal(buttonByText(container, "Undo"), undefined, "Undo vor dem Übernehmen");
  await click(apply);
  const ok = container.querySelector("[data-testid='balance-badge']");
  assert.equal(ok.textContent, "balanced");
  assert.ok(ok.querySelector("svg.icon-check"), "kein Häkchen-Symbol");
  const undo = buttonByText(container, "Undo");
  assert.ok(undo && undo.classList.contains("btn"), "kein Undo nach dem Übernehmen");
  await click(undo);
  assert.equal(container.querySelector("[data-testid='balance-badge']").dataset.state, "unbalanced", "Undo stellt die Gleichung nicht wieder her");
  assert.ok(buttonByText(container, "Apply coefficients"), "Apply nach Undo nicht wieder da");
  unmount();
});

test("Mechanismus: Back/Next als ruhige Knöpfe mit Chevron in der Bühnenleiste, Zähler eigenes Element", async () => {
  const steps = [{ svg: STEP, label: "Reactants" }, { svg: STEP, label: "TS", is_transition_state: true }, { svg: STEP, label: "Products" }];
  const { container, unmount } = render(h(MechanismView, { data: { type: "mechanism", name: "M", steps, current_step: 1 } }));
  const back = buttonByText(container, "Back");
  const next = buttonByText(container, "Next");
  for (const [b, icon] of [[back, "chevron-left"], [next, "chevron-right"]]) {
    assert.ok(b, "Knopf fehlt");
    assert.equal(b.classList.contains("btn-quiet"), true);
    assert.ok(b.closest(".stage-bar"), "nicht in der Bühnenleiste");
    assert.ok(b.querySelector(`svg.icon-${icon}`), `kein ${icon}`);
  }
  assert.equal(back.disabled, true);
  const counter = [...container.querySelectorAll(".stage-bar *")].find((el) => el.children.length === 0 && el.textContent === "Step 1 / 3");
  assert.ok(counter, "Zähler „Step 1 / 3“ nicht als eigenes Element");
  assert.equal(container.querySelectorAll(".stage-bar [aria-label^='Step ']").length, 3, "Punkte fehlen in der Leiste");
  await click(next);
  assert.match(textOf(container.querySelector(".stage-bar")), /Step 2 \/ 3/);
  assert.match(textOf(container.querySelector(".stage-bar")), /\[TS\]‡/);
  unmount();
});

test("Mechanismus: Hinweis steht nach der Bühne als Hint", () => {
  const { container, unmount } = render(h(MechanismView, { data: { type: "mechanism", name: "M", current_step: 0,
    steps: [{ svg: STEP, label: "a" }], notes: ["E2 elimination competes."] } }));
  const note = container.querySelector(".mech-note");
  assert.equal(note.tagName, "P");
  assert.equal(note.classList.contains("hint"), true);
  const stage = container.querySelector(".stage");
  assert.equal(Boolean(stage.compareDocumentPosition(note) & window.Node.DOCUMENT_POSITION_FOLLOWING), true, "Hinweis vor der Bühne");
  unmount();
});

test("Scope: Papierbühne trägt die Ausnahme-Klasse, Fehlliste als Warnhinweis, Einträge als Kernwerte", () => {
  const { container, unmount } = render(h(ScopeView, { data: { type: "scope", name: "Scope", svg: MOL.svg,
    entries: [{ label: "1a", yield_text: "92 %" }, { label: "1b" }], failed: ["xyz"], files: {} } }));
  assert.ok(container.querySelector(".stage.stage-paper.scope-svg svg"));
  assert.deepEqual([...container.querySelectorAll("dl.panel-facts dt")].map(textOf), ["1a"], "Eintrag ohne Angabe gehört nicht in die Zeile");
  const warn = container.querySelector("p.hint.hint-warn");
  assert.match(textOf(warn), /Not resolved, left out of the figure: xyz/);
  unmount();
});

test("b-graphics.css: nur Tokens — Hex-Farben ausschließlich in SVG-Umfärberegeln, kein Rollbereich", () => {
  const css = readFileSync(new URL("../styles/b-graphics.css", import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = css.split("}").map((r) => r.trim()).filter(Boolean);
  const offenders = rules.filter((r) => /#[0-9a-fA-F]{3,6}\b/.test(r.split("{").at(-1)) && !/(svg|\[style\*=)/.test(r.split("{").at(-2) ?? ""));
  assert.deepEqual(offenders, [], "Hex-Farbe außerhalb einer SVG-Umfärberegel");
  assert.doesNotMatch(css, /overflow(-y)?\s*:\s*(auto|scroll)/, "Rollbereich im Rollbereich");
});
