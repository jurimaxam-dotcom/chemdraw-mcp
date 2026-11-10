// Proteinpanel (E8, E13): Cartoon über die Engine, Rückfall SVG-Spur, Umschalter
// Sekundärstruktur/Kette/Regenbogen/Konfidenz. jsdom hat kein WebGL: ohne
// Attrappe scheitert die Engine hier immer — das ist der Rückfallweg.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import ProteinView, { viewerDeps } from "../ProteinView";
import BackboneCanvas from "../components/BackboneCanvas";
import App from "../App";
import { buttonByText, click, render, textOf } from "./harness.mjs";

// Zwei kurze Ketten im Ansichtsrahmen; Format wie vom Server (protein_view.py):
// Cα Base64 int16 in 0,1 Å, O − Cα Base64 int8 in 0,1 Å.
function helixPoints(n, x0) {
  const out = [];
  for (let i = 0; i < n; i++) out.push([x0 + 1.5 * i, 2.3 * Math.cos(i * 1.75), 2.3 * Math.sin(i * 1.75)]);
  return out;
}
const b64 = (Typed, values) => Buffer.from(new Typed(values).buffer).toString("base64");
function seg(n, x0, ss, q) {
  const ca = helixPoints(n, x0).flat().map((v) => Math.round(v * 10));
  const o = Array.from({ length: n }, (_, i) => [12, -15, i % 2 ? 8 : -8]).flat();
  return { ca: b64(Int16Array, ca), o: b64(Int8Array, o), ss, ...(q ? { q } : {}) };
}
// Häm-Attrappe: drei Atome reichen für Legende und mmCIF
const HEME = { code: "HEM", name: "heme b", chain: "A", e: "Fe N C", xyz: b64(Int16Array, [0, 0, 0, 20, 0, 0, 0, 20, 0]) };

const PROTEIN = {
  type: "protein",
  name: "insulin",
  files: { png: "/out/proteine/insulin.png", svg: "/out/proteine/insulin.svg" },
  protein: {
    title: "Insulin, Homo sapiens (human)",
    subtitle: "PDB 3I40, chains A/B · smoothed Cα trace · 51 residues",
    source: "pdb",
    identifier: "3I40",
    colorBy: "chain",
    citation: "Structure: PDB 3I40 (wwPDB, CC0)",
    ligands: [HEME, HEME],
    chains: [
      { id: "A", label: "A chain", color: "#0072B2", first: "1", last: "21",
        segments: [seg(12, -20, "CCHHHHHHHHCC")] },
      { id: "B", label: "B chain", color: "#E69F00", first: "1", last: "30",
        segments: [seg(10, 2, "CCEEEEECCC")] },
    ],
  },
};

const AF = {
  ...PROTEIN,
  name: "LipA",
  protein: {
    ...PROTEIN.protein,
    title: "Lipoyl synthase (LipA), Escherichia coli (bacterium)",
    source: "alphafold",
    colorBy: "ss",
    plddtMean: 91.6,
    chains: [{ id: "A", label: "chain A", color: "#0072B2", first: "1", last: "12",
      segments: [seg(12, -8, "CCHHHHHHHHCC", "112344444444")] }],
  },
};

const pieces = (container) => [...container.querySelectorAll("[data-residue-ss]")];
const strokes = (container) => pieces(container).map((p) => p.getAttribute("stroke")).join(",");
const geometry = (container) => pieces(container).map((p) => p.getAttribute("d")).join("|");
const pointer = (el, type, x, y) => act(async () => {
  el.dispatchEvent(new window.MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y }));
});

test("Kopf nennt Protein, Quelle und dass es eine Rückgratspur ist", () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
  const text = textOf(container);
  assert.ok(text.includes("Insulin, Homo sapiens (human)"));
  assert.ok(text.includes("PDB 3I40, chains A/B"));
  assert.ok(text.includes("Structure: PDB 3I40 (wwPDB, CC0)"));
  assert.equal(pieces(container).length, 11 + 9, "ein Stück je Restübergang");
  unmount();
});

test("Ziehen dreht die Projektion", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
  const svg = container.querySelector("svg[data-backbone]");
  const before = geometry(container);
  await pointer(svg, "pointerdown", 100, 100);
  await pointer(svg, "pointermove", 160, 130);
  await pointer(svg, "pointerup", 160, 130);
  assert.notEqual(geometry(container), before, "Drehung ändert die Projektion nicht");
  unmount();
});

test("mehrere Ketten starten nach Kette gefärbt, Umschalter auf Sekundärstruktur", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
  assert.ok(strokes(container).includes("#0072B2") && strokes(container).includes("#E69F00"));
  assert.ok(textOf(container).includes("A chain"));
  const byChain = strokes(container);
  await click(buttonByText(container, "Secondary"));
  assert.notEqual(strokes(container), byChain);
  assert.ok(textOf(container).includes("α-helix") && textOf(container).includes("β-strand"));
  assert.equal(buttonByText(container, "Confidence"), undefined, "Konfidenz nur bei AlphaFold");
  unmount();
});

test("AlphaFold-Modell: Konfidenz-Ansicht mit pLDDT-Klassen", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: AF }));
  assert.ok(textOf(container).includes("predicted"), "Kopf sagt nicht, dass es ein Modell ist");
  await click(buttonByText(container, "Confidence"));
  const colors = new Set(pieces(container).map((p) => p.getAttribute("stroke")));
  assert.ok(colors.has("#0053D6") && colors.has("#FF7D45"), [...colors].join(","));
  assert.ok(textOf(container).includes("pLDDT > 90"));
  unmount();
});

test("App leitet type protein an die Proteinansicht", () => {
  const { container, unmount } = render(React.createElement(App, { data: PROTEIN }));
  assert.ok(container.querySelector("svg[data-backbone]"), textOf(container));
  unmount();
});

// --- E13: Engine und Rückfall ---------------------------------------------------

const flush = () => act(async () => { await new Promise((r) => setTimeout(r, 0)); });

function fakeEngine(log) {
  return {
    create: async (host, scene, options) => {
      log.push(["create", scene, options]);
      const canvas = host.ownerDocument.createElement("canvas");
      host.appendChild(canvas);
      return {
        canvas,
        setColors: async (colors) => log.push(["colors", colors]),
        setStyle: async (style) => log.push(["style", style]),
        resetView: () => log.push(["reset"]),
        intro: () => {},
        snapshot: async () => ({ url: "data:image/png;base64,AAAA", width: 3, height: 3 }),
        dispose: () => log.push(["dispose"]),
      };
    },
  };
}

test("ohne WebGL bleibt die SVG-Spur stehen und sagt warum — nie eine leere Fläche", async () => {
  const original = viewerDeps.loadEngine;
  viewerDeps.loadEngine = async () => ({ create: async () => { throw new Error("Could not create a WebGL rendering context"); } });
  const warn = console.warn;
  console.warn = () => {};
  try {
    const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
    assert.ok(container.querySelector("svg[data-backbone]"), "Spur schon während des Ladens");
    await flush();
    assert.equal(container.querySelector("[data-protein-viewer]").getAttribute("data-protein-viewer"), "failed");
    assert.ok(pieces(container).length > 0, "Rückfall zeichnet die Spur");
    assert.ok(textOf(container).includes("3D cartoon unavailable here"));
    assert.equal(buttonByText(container, "Cartoon"), undefined, "kein Darstellungs-Umschalter ohne Engine");
    unmount();
  } finally {
    viewerDeps.loadEngine = original;
    console.warn = warn;
  }
});

test("eine blockierte Engine (Script nicht ausgeführt) nimmt denselben Rückfall", async () => {
  const original = viewerDeps.loadEngine;
  viewerDeps.loadEngine = () => Promise.reject(new Error("cartoon engine blocked"));
  const warn = console.warn;
  console.warn = () => {};
  try {
    const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
    await flush();
    assert.ok(container.querySelector("svg[data-backbone]"));
    assert.ok(textOf(container).includes("showing the backbone trace"));
    unmount();
  } finally {
    viewerDeps.loadEngine = original;
    console.warn = warn;
  }
});

test("mit Engine: Cartoon statt Spur, Umschalter färben um, Darstellung und Zurücksetzen", async () => {
  const original = viewerDeps.loadEngine;
  const log = [];
  viewerDeps.loadEngine = async () => fakeEngine(log);
  try {
    const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
    await flush();
    assert.equal(container.querySelector("svg[data-backbone]"), null, "Spur weicht dem Cartoon");
    assert.ok(container.querySelector("[data-cartoon-host] canvas"));
    const [, scene] = log.find(([k]) => k === "create");
    assert.ok(scene.protein.includes("_struct_conf.conf_type_id") && scene.protein.includes("_struct_sheet_range"));
    assert.ok(scene.ligands.includes("HETATM") && scene.ligands.includes(" FE "));
    assert.equal(scene.colors.get("A:3"), "#0072B2", "Ausgang: nach Kette");
    await click(buttonByText(container, "Secondary"));
    const colors = log.filter(([k]) => k === "colors").at(-1)[1];
    assert.equal(colors.get("A:3"), "#c8423b", "Rest 3 von A ist Helix");
    await click(buttonByText(container, "Rainbow N→C"));
    const rainbowColors = log.filter(([k]) => k === "colors").at(-1)[1];
    assert.notEqual(rainbowColors.get("A:1"), rainbowColors.get("A:12"));
    await click(buttonByText(container, "Trace"));
    assert.deepEqual(log.filter(([k]) => k === "style").at(-1), ["style", "trace"]);
    await click(buttonByText(container, "Reset"));
    assert.ok(log.some(([k]) => k === "reset"));
    unmount();
    assert.ok(log.some(([k]) => k === "dispose"), "WebGL-Kontext wird beim Aushängen freigegeben");
  } finally {
    viewerDeps.loadEngine = original;
  }
});

test("Legende nennt gebundene Gruppen zusammengefasst", () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: PROTEIN }));
  assert.ok(textOf(container).includes("heme b (HEM) ×2"), textOf(container));
  const dot = container.querySelector("[data-ligand] span");
  assert.notEqual(dot.style.background, "rgb(224, 102, 51)", "Häm-Punkt nicht in Fe-Orange");
  unmount();
});

test("Lader: ohne Engine-Block oder mit blockiertem Script lehnt er ab (→ Rückfall)", async () => {
  // jsdom führt eingefügte Scripts nicht aus — genau der Fall „Host blockiert
  // Inline-Script“. Den Erfolgsweg prüft test:host in Chromium.
  const { loadEngine, resetEngine, ENGINE_ID } = await import("../protein/loadEngine.js");
  delete window.__chemCartoon;
  resetEngine();
  await assert.rejects(loadEngine(), /not bundled/);
  const block = document.createElement("script");
  block.type = "text/plain";
  block.id = ENGINE_ID;
  block.textContent = "window.__chemCartoon = { create: () => 'engine' };";
  document.body.appendChild(block);
  try {
    await assert.rejects(loadEngine(), /blocked/);
    window.__chemCartoon = { create: () => "engine" };
    assert.equal((await loadEngine()).create(), "engine", "einmal geladen, sofort wieder da");
  } finally {
    block.remove();
    delete window.__chemCartoon;
    resetEngine();
  }
});

// --- Antikörper-Schema und Färbungen (Handtest Desktop 10.11.) -----------------

const ONE_CHAIN = {
  type: "protein", name: "lysozyme",
  protein: { title: "Lysozyme C", subtitle: "PDB 1LYZ", source: "pdb", colorBy: "ss",
    chains: [{ id: "A", label: "chain A", color: "#0072B2", first: "1", last: "12", segments: [seg(12, -8, "CCHHHHHHHHCC")] }] },
};

test("eine Kette: mindestens zwei Färbungen (Sekundärstruktur und Regenbogen)", () => {
  const { container, unmount } = render(React.createElement(ProteinView, { data: ONE_CHAIN }));
  const tabs = [...container.querySelectorAll('[aria-label="Colour by"] button')].map((b) => b.textContent);
  assert.deepEqual(tabs, ["Secondary", "Rainbow N→C"]);
  unmount();
});

function antibody(scheme) {
  return { ...PROTEIN, name: "anti-GFP", protein: { ...PROTEIN.protein, scheme } };
}

test("allgemeiner Antikörper öffnet auf dem Schema, Struktur einen Klick entfernt", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, {
    data: antibody({ start: "scheme", highlight: "", caption: "General IgG1 architecture" }),
  }));
  const svg = container.querySelector("svg[data-igg-scheme]");
  assert.ok(svg, "Schema sofort sichtbar");
  assert.equal(svg.getAttribute("data-igg-scheme"), "none");
  assert.equal(container.querySelector('[aria-label="Colour by"]'), null, "Färbung gehört zur Struktur");
  assert.ok(textOf(container).includes("heavy chain") && textOf(container).includes("General IgG1 architecture"));
  await click(buttonByText(container, "Structure"));
  assert.equal(container.querySelector("svg[data-igg-scheme]"), null);
  assert.ok(container.querySelector("svg[data-backbone]"));
  unmount();
});

test("Fab-Struktur: öffnet auf der Struktur, im Schema ist ein Fab-Arm markiert", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, {
    data: antibody({ start: "structure", highlight: "fab", caption: "The structure shown (PDB 1N8Z) is one Fab arm of the IgG." }),
  }));
  assert.equal(container.querySelector("svg[data-igg-scheme]"), null);
  await click(buttonByText(container, "Scheme"));
  const svg = container.querySelector("svg[data-igg-scheme]");
  assert.equal(svg.getAttribute("data-igg-scheme"), "fab");
  assert.equal(svg.querySelectorAll("[data-highlight='fab'] polygon").length, 1, "genau ein Arm markiert");
  unmount();
});

test("Schema-Text folgt dem Farbschema: keine feste Textfarbe außerhalb der Domänen", () => {
  const { container, unmount } = render(React.createElement(ProteinView, {
    data: antibody({ start: "scheme", highlight: "igg", caption: "" }),
  }));
  const texts = [...container.querySelectorAll("svg[data-igg-scheme] text")];
  const loose = texts.filter((t) => !t.closest("g[transform]"));
  assert.ok(loose.length >= 6);
  for (const t of loose) assert.match(t.getAttribute("fill"), /^var\(--/, t.textContent);
  unmount();
});

// --- E19: Bildgröße wie der 3D-Knopf im Molekülpanel ---------------------------
// jsdom kennt kein Layout: hier nur der Vertrag (eine gemeinsame, selbst bemessene
// Fläche für Cartoon, Spur und Schema; keine feste Panelhöhe). Die Pixel misst
// test:host in Chromium.

test("E19: Panel ohne feste Höhe, eine Bildfläche für Cartoon, Spur und Schema", async () => {
  const { container, unmount } = render(React.createElement(ProteinView, {
    data: antibody({ start: "structure", highlight: "fab", caption: "" }),
  }));
  const root = container.firstElementChild;
  assert.equal(root.style.height, "", "intrinsische Höhe: der Host bemisst das iframe am Inhalt");
  const stage = container.querySelector("[data-protein-viewer]");
  assert.ok(stage.classList.contains("protein-stage"), "Bildfläche trägt ihre eigene Größe");
  assert.equal(stage.style.flex, "", "nicht mehr der Rest einer festen Höhe");
  assert.ok(stage.contains(container.querySelector("svg[data-backbone]")), "Spur in der Fläche");
  assert.ok(stage.contains(container.querySelector("[data-cartoon-host]")), "Cartoon in der Fläche");
  await click(buttonByText(container, "Scheme"));
  assert.ok(stage.contains(container.querySelector("svg[data-igg-scheme]")), "Schema in derselben Fläche");
  unmount();
});

test("E19: styles.css bemisst die Bildfläche wie den 3D-Knopf (Quadrat, höchstens 720 px)", async () => {
  const { readFileSync } = await import("node:fs");
  const css = readFileSync(new URL("../styles.css", import.meta.url), "utf8");
  const yardstick = /\.structure-layout\[data-layout-3d\] \.structure-canvas \{[^}]*aspect-ratio: 1 \/ 1;[^}]*720px/.exec(css);
  assert.ok(yardstick, "Maßstab: 3D-Fläche im Molekülpanel");
  const rule = /\.protein-stage \{([^}]*)\}/.exec(css);
  assert.ok(rule, ".protein-stage fehlt");
  for (const decl of ["width: 100%", "aspect-ratio: 1 / 1", "max-height: 720px", "position: relative"]) {
    assert.ok(rule[1].includes(decl), `.protein-stage: ${decl}`);
  }
  assert.ok(!/\d+vh/.test(rule[1]), "keine vh-Höhe — die Größenmeldung misst max-content");
});

test("E19: Spur übernimmt die gemessene Fläche als Zeichenmaß (kein Briefkasten)", () => {
  const { container, unmount } = render(React.createElement(BackboneCanvas, { chains: ONE_CHAIN.protein.chains, width: 796, height: 720 }));
  assert.equal(container.querySelector("svg[data-backbone]").getAttribute("viewBox"), "0 0 796 720");
  unmount();
});
