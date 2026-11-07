// E3 (Design-Kritik 07.11.2026, Rang 4): eine gemeinsame Fußzeile — links die
// Dateipfade, rechts die Aktionen — als letztes Kind jedes Panels, das Dateien
// oder Aktionen hat. Dazu sichtbare Rückmeldung nach Export PNG: Desktop-
// Handtest 07.11. 08:39 — die Datei landete still in ~/ChemDraw-Output/png/,
// das Panel zeigte nichts. Und 3D exportiert die aktuelle Drehlage, statt den
// Knopf zu verstecken.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import App from "../App";
import { AppContext } from "../AppContext";
import AmbiguousView from "../AmbiguousView";
import AnkiDeckView from "../AnkiDeckView";
import DatabaseView from "../DatabaseView";
import MechanismView from "../MechanismView";
import Molecule3DView from "../Molecule3DView";
import MoleculeView from "../MoleculeView";
import PlotView from "../PlotView";
import ReactionView from "../ReactionView";
import ScopeView from "../ScopeView";
import SpectrumView from "../SpectrumView";
import TlcView from "../TlcView";
import { exportDeps } from "../components/ExportPngButton";
import { AMBIGUOUS, DATABASE, MOLECULE, lookupFailure, lookupSuccess } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

// jsdom kennt keinen ResizeObserver; ScaledRow (Reaktion) braucht nur, dass es ihn gibt.
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    disconnect() {}
  };
}

const HOME = "/Users/x/ChemDraw-Output";
const PLOT_SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><path d='M0 0'/></svg>";
const MOL_SVG = "<?xml version='1.0' encoding='iso-8859-1'?>\n<svg version='1.1' xmlns='http://www.w3.org/2000/svg' width='120px' height='80px' viewBox='0 0 120 80'><path data-mol='1' d='M5 5'/></svg>";
const CONFORMER = {
  type: "molecule3d", name: "Aspirin",
  atoms: [{ symbol: "C", x: 0, y: 0, z: 0 }, { symbol: "O", x: 1.2, y: 0, z: 0 }],
  bonds: [{ a: 0, b: 1, order: 2 }],
  files: { sdf: `${HOME}/3d/aspirin.sdf` },
};
const MOLECULE_FILES = { ...MOLECULE, files: { png: `${HOME}/einzelmolekuele/aspirin.png`, svg: `${HOME}/einzelmolekuele/aspirin.svg` } };
const REACTION = {
  type: "reaction", name: "Esterification", conditions: "H2SO4",
  reactants: [{ svg: MOL_SVG, name: "acetic acid" }, { svg: MOL_SVG, name: "ethanol" }],
  products: [{ svg: MOL_SVG, name: "ethyl acetate", coefficient: 2 }],
  files: { png: `${HOME}/reaktionen/esterification.png` },
};
const MECHANISM = {
  type: "mechanism", name: "SN2", reaction_type: "sn2", current_step: 1,
  steps: [{ svg: PLOT_SVG.replace("M0 0", "M1 1"), label: "Reactants" }, { svg: PLOT_SVG.replace("M0 0", "M2 2"), label: "Products" }],
};

// [Name, Element, erwartete Pfade (gekürzt), erwartete Aktionen]
const CASES = [
  ["Molekül", () => React.createElement(MoleculeView, { data: MOLECULE_FILES }),
    ["~/ChemDraw-Output/einzelmolekuele/aspirin.png", "~/ChemDraw-Output/einzelmolekuele/aspirin.svg"], ["Export PNG", "Add to Anki"]],
  ["Datenblatt", () => React.createElement(DatabaseView, { data: DATABASE }), [], ["Export PNG"]],
  ["Reaktion", () => React.createElement(ReactionView, { data: REACTION }),
    ["~/ChemDraw-Output/reaktionen/esterification.png"], ["Export PNG"]],
  ["Mechanismus", () => React.createElement(MechanismView, { data: MECHANISM }), [], ["Export PNG"]],
  ["Spektrum", () => React.createElement(SpectrumView, { data: {
    type: "spectrum", spectrum_type: "ir", name: "Aspirin IR", svg: PLOT_SVG, files: { png: `${HOME}/spektren/aspirin-ir.png` } } }),
    ["~/ChemDraw-Output/spektren/aspirin-ir.png"], ["Export PNG"]],
  ["DC", () => React.createElement(TlcView, { data: {
    type: "tlc", name: "Veresterung", svg: PLOT_SVG, lanes: [{ name: "A", spots: [{ rf: 0.3 }] }],
    files: { png: `${HOME}/dc-platten/veresterung.png`, svg: `${HOME}/dc-platten/veresterung.svg` } } }),
    ["~/ChemDraw-Output/dc-platten/veresterung.png", "~/ChemDraw-Output/dc-platten/veresterung.svg"], ["Export PNG"]],
  ["Titration (PlotView)", () => React.createElement(PlotView, { data: {
    type: "plot", name: "Acetic acid", svg: PLOT_SVG, notes: ["n"], files: { png: `${HOME}/diagramme/acetic.png` } } }),
    ["~/ChemDraw-Output/diagramme/acetic.png"], ["Export PNG"]],
  ["Scope", () => React.createElement(ScopeView, { data: {
    type: "scope", name: "Scope", svg: PLOT_SVG, entries: [{ label: "1a", structure: "c1ccccc1" }], failed: ["xyz"],
    files: { png: `${HOME}/scope/scope.png` } } }),
    ["~/ChemDraw-Output/scope/scope.png"], ["Export PNG"]],
  ["3D-Einstieg", () => React.createElement(Molecule3DView, { data: CONFORMER }),
    ["~/ChemDraw-Output/3d/aspirin.sdf"], ["Export PNG"]],
  ["Anki-Deck", () => React.createElement(AnkiDeckView, { data: {
    type: "anki_deck", name: "ChemDraw", cards: 1, media: 1, fronts: ["Aspirin"], file: `${HOME}/anki/chemdraw.apkg` } }),
    ["~/ChemDraw-Output/anki/chemdraw.apkg"], []],
];

const withApp = (el, app = { callServerTool: async () => lookupSuccess() }) =>
  React.createElement(AppContext.Provider, { value: app }, el);

function footerParts(footer) {
  return {
    paths: [...footer.querySelectorAll(".panel-footer-path")].map((n) => textOf(n)),
    titles: [...footer.querySelectorAll(".panel-footer-path")].map((n) => n.getAttribute("title") || ""),
    actions: [...footer.querySelectorAll(".panel-footer-actions button")].map((b) => textOf(b)),
  };
}

for (const [label, make, paths, actions] of CASES) {
  test(`${label}: Fußzeile als letztes Kind, mit Pfad(en) links und Aktionen rechts`, () => {
    const { container, unmount } = render(withApp(make()));
    const root = container.firstElementChild;
    const footer = container.querySelector('[data-testid="panel-footer"]');
    assert.equal(Boolean(footer), true, `keine Fußzeile in ${label}`);
    assert.equal(container.querySelectorAll('[data-testid="panel-footer"]').length, 1, "mehr als eine Fußzeile");
    assert.equal(root.lastElementChild === footer, true, "Fußzeile ist nicht das letzte Kind des Panels");
    const got = footerParts(footer);
    assert.deepEqual(got.paths, paths);
    assert.equal(got.titles.every((t) => t.startsWith(HOME)), true, "Tooltip zeigt nicht den vollen Pfad");
    assert.equal(footer.querySelectorAll('button[aria-label="Copy path"]').length, paths.length, "Kopierknopf je Pfad fehlt");
    assert.deepEqual(got.actions, actions);
    // Kein doppelter Export-Knopf irgendwo im Panel, und keine Aktion mehr im Kopf.
    assert.equal(container.querySelectorAll("button.export-png").length, actions.includes("Export PNG") ? 1 : 0, "Export-Knopf doppelt");
    assert.equal(container.querySelectorAll("button.add-to-anki").length, actions.includes("Add to Anki") ? 1 : 0, "Anki-Knopf doppelt");
    assert.equal(container.querySelectorAll(".panel-header button.export-png, .panel-header button.add-to-anki").length, 0,
      "Aktion steht noch im Kopf");
    unmount();
  });
}

test("Panels ohne Datei und ohne Aktion bekommen keine leere Fußzeile", () => {
  for (const el of [
    React.createElement(AmbiguousView, { data: AMBIGUOUS }),
    React.createElement(AnkiDeckView, { data: { type: "anki_deck", name: "D", cards: 1, media: 0, fronts: ["x"], file: "" } }),
  ]) {
    const { container, unmount } = render(withApp(el));
    assert.equal(container.querySelectorAll('[data-testid="panel-footer"]').length, 0);
    unmount();
  }
});

test("Batch: jeder Eintrag endet mit seiner eigenen Fußzeile", () => {
  const second = { ...MOLECULE_FILES, name: "Caffeine", properties: { ...MOLECULE.properties, smiles: "Cn1cnc2c1c(=O)n(C)c(=O)n2C" },
    files: { png: `${HOME}/einzelmolekuele/caffeine.png` } };
  const { container, unmount } = render(withApp(React.createElement(App, {
    data: { type: "batch", molecules: [MOLECULE_FILES, second], cdxml_paths: [], failed: [] } })));
  const panels = [...container.querySelectorAll("article.molecule-panel")];
  assert.equal(panels.length, 2);
  for (const panel of panels) {
    assert.equal(panel.lastElementChild?.getAttribute("data-testid"), "panel-footer");
    assert.equal(panel.querySelectorAll("button.export-png").length, 1);
  }
  assert.match(textOf(panels[1].lastElementChild), /caffeine\.png/);
  unmount();
});

// --- Export PNG: sichtbare Rückmeldung ---------------------------------------

// jsdom hat kein Canvas und Node kein FileReader: Rastern, Base64 und
// Zwischenablage laufen über eine austauschbare Naht.
function mockExport({ clipboard = false, rasterFail = false } = {}) {
  const seen = [];
  const original = { ...exportDeps };
  exportDeps.svgToPngBlob = async (svg) => {
    if (rasterFail) throw new Error("kaputt");
    seen.push(svg);
    return { fake: true };
  };
  exportDeps.blobToBase64 = async () => "iVBORw0KGgo=";
  exportDeps.copyPngToClipboard = async () => {
    if (!clipboard) throw new Error("Clipboard-Image-API nicht verfügbar");
  };
  return { seen, restore: () => Object.assign(exportDeps, original) };
}

function exportApp(respond) {
  const calls = [];
  return {
    calls,
    app: { callServerTool: async (req) => {
      calls.push(req);
      return respond(req);
    } },
  };
}

const savedAt = (path) => ({ isError: false, content: [{ type: "text", text: path }] });
const feedback = (container) => container.querySelector('[data-testid="panel-footer"] .export-feedback');

test("Export PNG ohne Zwischenablage: Fußzeile zeigt den gespeicherten Pfad aus save_png", async () => {
  const mock = mockExport();
  const saved = "/Users/x/ChemDraw-Output/png/aspirin.png";
  const { app, calls } = exportApp(() => savedAt(saved));
  const { container, unmount } = render(withApp(React.createElement(SpectrumView, { data: {
    type: "spectrum", spectrum_type: "ir", name: "Aspirin", svg: PLOT_SVG, files: { png: `${HOME}/spektren/a.png` } } }), app));
  try {
    assert.equal(Boolean(feedback(container)), false, "Rückmeldung vor dem Klick");
    await click(container.querySelector("button.export-png"));
    assert.equal(calls.length, 1);
    assert.equal(calls[0].name, "save_png");
    const note = feedback(container);
    assert.equal(Boolean(note), true, "keine sichtbare Rückmeldung nach dem Klick");
    assert.equal(note.getAttribute("role"), "status");
    assert.equal(textOf(note), "Saved: ~/ChemDraw-Output/png/aspirin.png");
    // Der volle Pfad bleibt im Knopf-Titel (Host-Test liest ihn dort).
    assert.equal(container.querySelector("button.export-png").getAttribute("title"), `Saved: ${saved}`);
  } finally {
    mock.restore();
    unmount();
  }
});

test("Export PNG mit Zwischenablage: Rückmeldung „Copied to clipboard“, kein save_png", async () => {
  const mock = mockExport({ clipboard: true });
  const { app, calls } = exportApp(() => savedAt("/nie"));
  const { container, unmount } = render(withApp(React.createElement(MoleculeView, { data: MOLECULE_FILES }), app));
  try {
    await click(container.querySelector("button.export-png"));
    assert.equal(calls.length, 0, "save_png trotz gelungener Zwischenablage");
    assert.equal(textOf(feedback(container)), "Copied to clipboard");
  } finally {
    mock.restore();
    unmount();
  }
});

test("Export PNG schlägt fehl: Rückmeldung nennt den Grund", async () => {
  const mock = mockExport();
  const { app } = exportApp(() => lookupFailure());
  const { container, unmount } = render(withApp(React.createElement(TlcView, { data: {
    type: "tlc", name: "DC", svg: PLOT_SVG, lanes: [], files: {} } }), app));
  try {
    await click(container.querySelector("button.export-png"));
    const note = feedback(container);
    assert.equal(Boolean(note), true, "keine Fehlermeldung sichtbar");
    assert.match(textOf(note), /^Export failed: .*Stoff nicht gefunden/);
    assert.equal(note.classList.contains("is-error"), true);
  } finally {
    mock.restore();
    unmount();
  }
});

test("Export PNG: Rasterfehler wird als Grund gezeigt", async () => {
  const mock = mockExport({ rasterFail: true });
  const { app, calls } = exportApp(() => savedAt("/nie"));
  const { container, unmount } = render(withApp(React.createElement(PlotView, { data: {
    type: "plot", name: "P", svg: PLOT_SVG, files: {} } }), app));
  try {
    await click(container.querySelector("button.export-png"));
    assert.equal(calls.length, 0);
    assert.match(textOf(feedback(container)), /^Export failed: the drawing could not be rendered/);
  } finally {
    mock.restore();
    unmount();
  }
});

// --- 3D: Export der aktuellen Drehlage ---------------------------------------

test("Molekül in 3D: Export-Knopf bleibt, rastert das Kuhlen-SVG; Fußzeile zeigt den SDF-Pfad", async () => {
  const mock = mockExport();
  const { app, calls } = exportApp((req) =>
    req.name === "generate_3d" ? lookupSuccess(CONFORMER) : savedAt("/Users/x/ChemDraw-Output/png/aspirin.png"));
  const { container, unmount } = render(withApp(React.createElement(MoleculeView, { data: MOLECULE_FILES }), app));
  try {
    await click(buttonByText(container, "3D"));
    assert.equal(Boolean(container.querySelector("[data-view-3d]")), true, "3D-Viewer nicht sichtbar");
    const footer = container.querySelector('[data-testid="panel-footer"]');
    assert.deepEqual(footerParts(footer).paths, ["~/ChemDraw-Output/3d/aspirin.sdf"], "3D-Fußzeile zeigt nicht den SDF-Pfad");
    assert.doesNotMatch(textOf(container.querySelector(".panel-note-quiet")), /SDF/, "SDF-Pfad steht doppelt im Hinweis");
    const button = container.querySelector("button.export-png");
    assert.equal(Boolean(button), true, "Export PNG fehlt im 3D-Modus");
    await click(button);
    assert.equal(mock.seen.length, 1);
    const svg = mock.seen[0];
    assert.match(svg, /url\(#bowl\)/, "gerastert wurde nicht die Kuhle");
    assert.match(svg, /xmlns="http:\/\/www\.w3\.org\/2000\/svg"/, "ohne xmlns lädt <img> das SVG nicht");
    assert.doesNotMatch(svg, /M0 0/, "gerastert wurde die 2D-Zeichnung");
    assert.equal(calls.filter((c) => c.name === "save_png").length, 1);
    assert.equal(textOf(feedback(container)), "Saved: ~/ChemDraw-Output/png/aspirin.png");
  } finally {
    mock.restore();
    unmount();
  }
});

// Seit E1 kommen Kuhlenverlauf, Kontaktschatten und C/H aus Theme-Variablen
// (--bowl-*, --atom3d-*). Ein losgelöstes SVG im <img> kennt sie nicht — das PNG
// käme ohne Verläufe und Atomfarben heraus. Der Export muss sie in Farben auflösen.
test("3D-Export: keine var(--…) mehr im gerasterten SVG, Kuhle und C tragen echte Farben", async () => {
  // Das helle :root-Theme aus styles.css auf das Dokument legen, wie es das Stylesheet im Panel tut.
  const { readFileSync } = await import("node:fs");
  const css = readFileSync(new URL("../styles.css", import.meta.url), "utf8");
  const rootBlock = /:root\s*\{([^}]*)\}/.exec(css)[1];
  const vars = [...rootBlock.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map(([, name, value]) => [name, value.trim()]);
  const root = document.documentElement;
  for (const [name, value] of vars) root.style.setProperty(name, value);
  const mock = mockExport({ clipboard: true });
  const { container, unmount } = render(withApp(React.createElement(Molecule3DView, { data: CONFORMER })));
  try {
    await click(container.querySelector("button.export-png"));
    const svg = mock.seen[0] || "";
    assert.match(svg, /url\(#bowl\)/);
    assert.doesNotMatch(svg, /var\(--/, "ungelöste Theme-Variable im Export");
    const bowl0 = vars.find(([n]) => n === "--bowl-0")[1];
    const carbon = vars.find(([n]) => n === "--atom3d-c")[1];
    assert.ok(svg.includes(`stop-color: ${bowl0}`) || svg.includes(`stop-color:${bowl0}`), `Kuhlenfarbe ${bowl0} fehlt`);
    assert.ok(svg.includes(carbon), `Kohlenstofffarbe ${carbon} fehlt`);
  } finally {
    mock.restore();
    for (const [name] of vars) root.style.removeProperty(name);
    unmount();
  }
});

test("3D-Einstieg rastert ebenfalls das Kuhlen-SVG", async () => {
  const mock = mockExport({ clipboard: true });
  const { container, unmount } = render(withApp(React.createElement(Molecule3DView, { data: CONFORMER })));
  try {
    await click(container.querySelector("button.export-png"));
    assert.match(mock.seen[0] || "", /url\(#bowl\)/);
  } finally {
    mock.restore();
    unmount();
  }
});

test("Reaktion: Export rastert eine zusammengesetzte Gleichung aus allen Strukturen", async () => {
  const mock = mockExport({ clipboard: true });
  const { container, unmount } = render(withApp(React.createElement(ReactionView, { data: REACTION })));
  try {
    await click(container.querySelector("button.export-png"));
    const svg = mock.seen[0] || "";
    assert.equal((svg.match(/data-mol='1'/g) || []).length, 3, "nicht alle drei Strukturen im Export");
    assert.doesNotMatch(svg, /<\?xml/, "XML-Deklaration mitten im Dokument");
    assert.match(svg, /H2SO4/, "Bedingung fehlt am Pfeil");
  } finally {
    mock.restore();
    unmount();
  }
});

test("Mechanismus im Schrittmodus exportiert den gezeigten Schritt", async () => {
  const mock = mockExport({ clipboard: true });
  const { container, unmount } = render(withApp(React.createElement(MechanismView, { data: MECHANISM })));
  try {
    await click(container.querySelector("button.export-png"));
    assert.match(mock.seen[0] || "", /M1 1/, "nicht der gezeigte Schritt 1");
    await click(buttonByText(container, "Next →"));
    await click(container.querySelector("button.export-png"));
    assert.match(mock.seen.at(-1) || "", /M2 2/, "Export folgt dem Schritt nicht");
  } finally {
    mock.restore();
    unmount();
  }
});
