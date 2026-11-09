// Richtung „→ Daten": teuer, also genau einmal — und ein Fehlschlag muss
// sichtbar landen, nicht als leere Flaeche.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import MoleculeView, { DATA_LOAD_ERROR, VIEW_LOAD_ERROR } from "../MoleculeView";
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

test("ein neuer Stoff im selben App-Slot verwirft das alte Datenblatt", async () => {
  const { default: App } = await import("../App");
  const calls = [];
  const bridge = { callServerTool: async (req) => {
    calls.push(req.arguments.name);
    return lookupSuccess();
  } };
  const element = (data) => React.createElement(AppContext.Provider, { value: bridge }, React.createElement(App, { data }));
  const { container, rerender, unmount } = render(element(MOLECULE));
  await click(buttonByText(container, "Data"));
  assert.match(textOf(container.querySelector('[data-view="data"]')), /50-78-2/);
  rerender(element({ ...MOLECULE, name: "Caffeine", properties: { smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O" } }));
  assert.ok(container.querySelector('[data-view="structure"]'), "neuer Stoff muss mit eigener Struktur starten");
  await click(buttonByText(container, "Data"));
  assert.equal(calls.length, 2, "alter Stoff-Cache darf neuen Lookup nicht ersetzen");
  unmount();
});

// Was Studierende brauchen: Struktur, Formel, molare Masse, CAS, Gruppen.
// SMILES, Rule of Five und der IUPAC-Untertitel sind bewusst raus (Designentscheid 15.10.2026).
test("die Struktur-Ansicht zeigt die Kernwerte und nichts darueber hinaus", () => {
  const { panel, container, unmount } = setup();
  const text = textOf(panel("structure"));
  assert.match(text, /Formula/);
  assert.match(text, /Molar mass/);
  assert.match(text, /180\.16/);
  assert.match(text, /50-78-2/);
  assert.doesNotMatch(text, /CC\(=O\)Oc1ccccc1C\(=O\)O/, "SMILES steht noch im Panel");
  assert.doesNotMatch(text, /Lipinski|Rule of Five/, "Rule of Five steht noch im Panel");
  assert.doesNotMatch(textOf(container), /Acetyloxy/, "IUPAC-Untertitel steht noch im Kopf");
  unmount();
});

test("die Einheit der molaren Masse steht genau einmal da", () => {
  const data = { ...MOLECULE, properties: { ...MOLECULE.properties, mw: "180.16 g/mol" } };
  const view = render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(MoleculeView, { data })));
  assert.doesNotMatch(textOf(view.container), /g\/mol g\/mol/);
  assert.match(textOf(view.container), /180\.16 g\/mol/);
  view.unmount();
});

test("Hover auf eine Gruppe nennt sie unter den Gruppen, ohne Erklaersatz", async () => {
  const { container, unmount } = setup();
  const note = () => textOf(container.querySelector(".group-note"));
  assert.match(note(), /Hover a group/, "Ruhezustand ohne Hinweis");
  const group = [...container.querySelectorAll("button")].find((b) => b.textContent.includes("Ester"));
  await act(async () => group.focus());
  assert.match(note(), /Ester/);
  assert.match(note(), /–COO–/, "Formel der Gruppe fehlt");
  assert.doesNotMatch(note(), /hydrolys/i, "Erklaersatz steht noch da");
  await act(async () => group.blur());
  assert.match(note(), /Hover a group/, "Erklaerung bleibt nach dem Verlassen stehen");
  unmount();
});

test("funktionelle Gruppen sind per Tastatur fokussierbar und markieren die Struktur", async () => {
  const { container, unmount } = setup();
  const group = [...container.querySelectorAll('button')].find((b) => b.textContent.includes("Ester"));
  assert.ok(group, "Gruppe muss ein bedienbarer Knopf sein");
  await act(async () => group.focus());
  assert.equal(group.getAttribute("aria-pressed"), "true");
  await click(group);
  assert.equal(group.getAttribute("aria-pressed"), "true");
  unmount();
});

// Zusatzansichten (All H, Fischer, Haworth): das Payload sagt nur, OB es sie
// gibt. Der erste Klick holt die Zeichnung per generate_molecule(view=…), der
// zweite kommt aus dem Cache (Jay 26.10.: „Erst auf Klick“).
const SVG_ALL_H = "<svg viewBox='0 0 40 20'><path d='M1 1' data-all-h='1'/></svg>";
const SVG_FISCHER = "<svg viewBox='0 0 40 20'><text data-fischer='1'>CHO</text></svg>";
const SVG_HAWORTH = "<svg viewBox='0 0 40 20'><text data-haworth='1'>O</text></svg>";
const SVG_CHAIR = "<svg viewBox='0 0 40 20'><text data-chair='1'>OH</text></svg>";
const VIEW_SVG = { all_h: SVG_ALL_H, fischer: SVG_FISCHER, haworth: SVG_HAWORTH, chair: SVG_CHAIR };
const REQUEST = { name_or_smiles: "CC(=O)Oc1ccccc1C(=O)O", annotate_stereo: true };

function renderMolecule(data, respond) {
  const calls = [];
  const app = { callServerTool: async (req) => {
    calls.push(req);
    if (respond) return respond(req);
    const viewSvg = VIEW_SVG[req.arguments.view];
    return lookupSuccess({ type: "molecule", svg: "<svg/>", initialView: req.arguments.view, viewSvg, viewAtoms: [] });
  } };
  const view = render(
    React.createElement(AppContext.Provider, { value: app },
      React.createElement(MoleculeView, { data }))
  );
  return { ...view, calls };
}

test("„All H“ holt die Zeichnung beim ersten Klick, danach aus dem Cache", async () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data);
  const drawing = () => container.querySelector(".structure-drawing");
  assert.equal(calls.length, 0, "Laden ohne Klick");

  await click(buttonByText(container, "All H"));
  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "generate_molecule");
  assert.deepEqual(calls[0].arguments, { ...REQUEST, view: "all_h" });
  assert.ok(drawing().querySelector("[data-all-h]"), "H-Zeichnung nicht sichtbar");
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "true");

  await click(buttonByText(container, "All H"));
  assert.equal(drawing().querySelector("[data-all-h]"), null, "Rückweg zur Skelettformel fehlt");
  await click(buttonByText(container, "All H"));
  assert.ok(drawing().querySelector("[data-all-h]"));
  assert.equal(calls.length, 1, "zweiter Klick muss aus dem Cache kommen");
  unmount();
});

// 3D-Knopf: dieselbe Achse wie All H, nur holt er das Konformer per
// generate_3d (lazy, dann Cache) und ersetzt die Zeichenfläche durch den
// drehbaren Kugel-Stab-Viewer. Vorher ging 3D nur über den Chat.
const CONFORMER = {
  type: "molecule3d", name: "Aspirin",
  atoms: [{ symbol: "C", x: 0, y: 0, z: 0 }, { symbol: "O", x: 1.2, y: 0, z: 0 }],
  bonds: [{ a: 0, b: 1, order: 2 }],
  files: { sdf: "/Users/x/ChemDraw-Output/3d/aspirin.sdf" },
};

test("„3D“ holt das Konformer per generate_3d beim ersten Klick, danach aus dem Cache", async () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data, (req) =>
    req.name === "generate_3d" ? lookupSuccess(CONFORMER) : lookupSuccess({ type: "molecule", svg: "<svg/>", initialView: "all_h", viewSvg: SVG_ALL_H, viewAtoms: [] }));
  const viewer = () => container.querySelector("[data-view-3d]");
  assert.equal(Boolean(viewer()), false, "3D-Viewer ohne Klick");

  await click(buttonByText(container, "3D"));
  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "generate_3d");
  assert.deepEqual(calls[0].arguments, { name_or_smiles: MOLECULE.properties.smiles, label: MOLECULE.name });
  assert.ok(viewer(), "3D-Viewer nicht sichtbar");
  assert.ok(viewer().querySelectorAll("circle").length >= 2, "Atome fehlen im Viewer");
  assert.equal(buttonByText(container, "3D").getAttribute("aria-pressed"), "true");
  assert.equal(container.querySelector(".structure-drawing"), null, "2D-Zeichnung bleibt neben 3D stehen");
  // Jay 07.11.: 3D ist der Hebel — die Kuhle bekommt die volle Panelbreite, die Kernwerte rutschen darunter.
  assert.ok(container.querySelector(".structure-layout[data-layout-3d]"), "3D-Layout: Kuhle nicht über die volle Breite");

  await click(buttonByText(container, "3D"));
  assert.equal(Boolean(viewer()), false, "Rückweg zur Zeichnung fehlt");
  assert.ok(container.querySelector(".structure-drawing"));
  await click(buttonByText(container, "3D"));
  assert.ok(viewer());
  assert.equal(calls.length, 1, "zweiter Klick muss aus dem Cache kommen");

  // All H verdrängt 3D — eine Zeichenfläche, nie zwei.
  await click(buttonByText(container, "All H"));
  assert.equal(Boolean(viewer()), false, "3D und All H zugleich");
  assert.equal(container.querySelector(".structure-layout[data-layout-3d]"), null, "3D-Layout bleibt nach All H kleben");
  assert.ok(container.querySelector("[data-all-h]"));
  assert.equal(buttonByText(container, "3D").getAttribute("aria-pressed"), "false");
  unmount();
});

test("All H → 3D → All H zeigt die gecachte H-Zeichnung, nicht die Skelettformel; Export PNG bleibt in 3D", async () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data, (req) =>
    req.name === "generate_3d" ? lookupSuccess(CONFORMER) : lookupSuccess({ type: "molecule", svg: "<svg/>", initialView: "all_h", viewSvg: SVG_ALL_H, viewAtoms: [] }));
  // Boolean statt Element in assert.equal: schlägt der Vergleich fehl, versucht node:assert das
  // jsdom-Element zu inspizieren und hängt (zirkulärer Baum) — der Test wird dann nie rot.
  const hasExport = () => Boolean(container.querySelector('button[aria-label="Export as PNG"]'));
  assert.equal(hasExport(), true, "Export-Knopf fehlt in 2D");

  await click(buttonByText(container, "All H"));
  await click(buttonByText(container, "3D"));
  // E3 (Design-Kritik 3.14): früher pausierte der Knopf in 3D, weil er die 2D-Zeichnung exportiert hätte.
  // Jetzt rastert er das Kuhlen-SVG in der aktuellen Drehlage (panelFooter.test.mjs prüft den Inhalt).
  assert.equal(hasExport(), true, "Export PNG fehlt in 3D");
  await click(buttonByText(container, "All H"));
  assert.ok(container.querySelector("[data-all-h]"), "All H nach 3D fällt auf die Skelettformel zurück");
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "true");
  assert.equal(Boolean(container.querySelector("[data-view-3d]")), false);
  assert.equal(calls.length, 2, "All H aus dem Cache, 3D aus dem Cache");
  assert.equal(hasExport(), true, "Export-Knopf kommt mit der Zeichnung zurück");
  unmount();
});

test("„3D“ gibt es auch ohne Zusatzansichten, und ein Fehlschlag bleibt wiederholbar", async () => {
  let fail = true;
  const { container, calls, unmount } = renderMolecule(MOLECULE, () => {
    if (fail) return lookupFailure();
    return lookupSuccess(CONFORMER);
  });
  assert.ok(buttonByText(container, "3D"), "3D-Knopf fehlt ohne views");
  await click(buttonByText(container, "3D"));
  assert.equal(Boolean(container.querySelector("[data-view-3d]")), false);
  assert.match(textOf(container), /3D model could not be loaded/);
  fail = false;
  await click(buttonByText(container, "3D"));
  assert.ok(container.querySelector("[data-view-3d]"), "nach Fehlschlag nicht wiederholbar");
  assert.equal(calls.length, 2);
  unmount();
});

test("ohne Ansichten keine Knöpfe", () => {
  const { container, unmount } = renderMolecule(MOLECULE);
  for (const label of ["All H", "Fischer", "Haworth"]) assert.ok(!buttonByText(container, label), label);
  unmount();
});

test("„Fischer“ und „All H“ schließen einander aus", async () => {
  const data = { ...MOLECULE, views: ["all_h", "fischer"], viewRequest: REQUEST };
  const { container, unmount } = renderMolecule(data);
  const drawing = () => container.querySelector(".structure-drawing");
  assert.ok(!buttonByText(container, "Haworth"), "Haworth-Knopf ohne Ansicht");

  await click(buttonByText(container, "Fischer"));
  assert.ok(drawing().querySelector("[data-fischer]"), "Fischer-Projektion nicht sichtbar");
  await click(buttonByText(container, "All H"));
  assert.equal(drawing().querySelector("[data-fischer]"), null, "Ansichten schließen einander nicht aus");
  assert.ok(drawing().querySelector("[data-all-h]"));
  assert.equal(buttonByText(container, "Fischer").getAttribute("aria-pressed"), "false");
  unmount();
});

test("„Haworth“ zeigt den Ring und den Satz, warum es keine Fischer-Projektion gibt", async () => {
  const note = "The Fischer projection shows the open-chain form.";
  const data = { ...MOLECULE, views: ["haworth"], viewRequest: REQUEST, projectionNote: note };
  const { container, unmount } = renderMolecule(data);
  assert.doesNotMatch(textOf(container), /open-chain/, "Hinweis vor dem Klick");
  await click(buttonByText(container, "Haworth"));
  assert.ok(container.querySelector(".structure-drawing [data-haworth]"), "Haworth nicht sichtbar");
  assert.match(textOf(container), /open-chain/, "Hinweis fehlt in der Haworth-Ansicht");
  unmount();
});

test("„Chair“ holt den Sessel per view=chair, ohne den Haworth-Satz", async () => {
  const note = "The Fischer projection shows the open-chain form.";
  const data = { ...MOLECULE, views: ["all_h", "haworth", "chair"], viewRequest: REQUEST, projectionNote: note };
  const { container, calls, unmount } = renderMolecule(data);
  await click(buttonByText(container, "Chair"));
  assert.deepEqual(calls[0].arguments, { ...REQUEST, view: "chair" });
  assert.ok(container.querySelector(".structure-drawing [data-chair]"), "Sessel nicht sichtbar");
  assert.equal(buttonByText(container, "Chair").getAttribute("aria-pressed"), "true");
  assert.doesNotMatch(textOf(container), /open-chain/, "Haworth-Satz gehört nicht zum Sessel");
  unmount();
});

test("ein Fehlschlag bleibt sichtbar und wiederholbar", async () => {
  let fail = true;
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data, (req) =>
    fail ? lookupFailure() : lookupSuccess({ type: "molecule", svg: "<svg/>", viewSvg: VIEW_SVG[req.arguments.view] }));
  await click(buttonByText(container, "All H"));
  assert.match(textOf(container), new RegExp(VIEW_LOAD_ERROR.slice(0, 20)));
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "false");
  fail = false;
  await click(buttonByText(container, "All H"));
  assert.ok(container.querySelector(".structure-drawing [data-all-h]"));
  assert.equal(calls.length, 2);
  unmount();
});

test("ruft das Modell view selbst, startet das Panel auf der Ansicht — mit Knöpfen und Rückweg", async () => {
  const data = { ...MOLECULE, views: ["all_h", "haworth"], viewRequest: REQUEST, initialView: "haworth",
    viewSvg: SVG_HAWORTH, viewAtoms: [], projectionNote: "The Fischer projection shows the open-chain form." };
  const { container, calls, unmount } = renderMolecule(data);
  const drawing = () => container.querySelector(".structure-drawing");
  assert.ok(drawing().querySelector("[data-haworth]"), "startet nicht auf Haworth");
  assert.equal(buttonByText(container, "Haworth").getAttribute("aria-pressed"), "true");
  assert.match(textOf(container), /open-chain/);
  await click(buttonByText(container, "Haworth"));
  assert.equal(drawing().querySelector("[data-haworth]"), null, "Rückweg zur Skelettformel fehlt");
  await click(buttonByText(container, "Haworth"));
  assert.ok(drawing().querySelector("[data-haworth]"));
  assert.equal(calls.length, 0, "mitgelieferte Ansicht darf nicht nachgeladen werden");
  unmount();
});

// --- E2 (Design-Kritik 07.11., Rang 3): eine Ansicht-Achse direkt unter der Fläche ---

const STEREO = { kind: "atom", atoms: [1], label: "Unspecified stereocenter" };

test("eine Ansicht-Achse: 2D · All H · 3D direkt unter der Zeichenfläche, vor den Kernwerten", () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, unmount } = renderMolecule(data);
  const axes = container.querySelectorAll("[data-view-axis]");
  assert.equal(axes.length, 1, `genau eine Achse erwartet, ${axes.length} gefunden`);
  assert.equal(container.querySelectorAll(".structure-tools").length, 0, "alte Chip-Reihe steht noch da");
  const axis = axes[0];
  assert.deepEqual([...axis.querySelectorAll("button")].map((b) => b.textContent.trim()), ["2D", "All H", "3D"]);
  // Jeder Ansicht-Knopf genau einmal im Panel.
  for (const label of ["2D", "All H", "3D"]) {
    assert.equal([...container.querySelectorAll("button")].filter((b) => b.textContent.trim() === label).length, 1, label);
  }
  const canvas = container.querySelector(".structure-canvas");
  const facts = container.querySelector(".key-facts");
  const follows = (a, b) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
  assert.ok(follows(canvas, axis), "Achse steht nicht hinter der Zeichenfläche");
  assert.ok(follows(axis, facts), "Achse steht nicht vor den Kernwerten");
  assert.equal(buttonByText(container, "2D").getAttribute("aria-pressed"), "true", "2D nicht als aktiv markiert");
  unmount();
});

test("„2D“ holt die Skelettformel aus All H und aus 3D zurück, ohne Server-Aufruf", async () => {
  const data = { ...MOLECULE, views: ["all_h"], viewRequest: REQUEST };
  const { container, calls, unmount } = renderMolecule(data, (req) =>
    req.name === "generate_3d" ? lookupSuccess(CONFORMER) : lookupSuccess({ type: "molecule", svg: "<svg/>", initialView: "all_h", viewSvg: SVG_ALL_H, viewAtoms: [] }));
  await click(buttonByText(container, "All H"));
  await click(buttonByText(container, "2D"));
  assert.equal(Boolean(container.querySelector("[data-all-h]")), false, "2D zeigt noch All H");
  assert.equal(buttonByText(container, "2D").getAttribute("aria-pressed"), "true");
  await click(buttonByText(container, "3D"));
  await click(buttonByText(container, "2D"));
  assert.equal(Boolean(container.querySelector("[data-view-3d]")), false, "2D lässt 3D stehen");
  assert.equal(buttonByText(container, "3D").getAttribute("aria-pressed"), "false");
  assert.deepEqual(calls.map((c) => c.name), ["generate_molecule", "generate_3d"], "2D darf nichts laden");
  unmount();
});

test("ein ladender Ansicht-Knopf zeigt einen Spinner, nicht nur aria-busy", async () => {
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  const { container, unmount } = renderMolecule(MOLECULE, async () => { await pending; return lookupSuccess(CONFORMER); });
  await click(buttonByText(container, "3D"));
  const chip = buttonByText(container, "3D");
  assert.equal(chip.getAttribute("aria-busy"), "true");
  assert.ok(chip.querySelector(".seg-spinner"), "kein sichtbarer Spinner im 3D-Knopf");
  await act(async () => { release(); await pending; });
  assert.equal(Boolean(buttonByText(container, "3D").querySelector(".seg-spinner")), false, "Spinner bleibt nach dem Laden");
  assert.ok(container.querySelector("[data-view-3d]"));
  unmount();
});

test("styles.css gibt ladenden Chips einen sichtbaren Zustand", async () => {
  const { readFileSync } = await import("node:fs");
  const css = readFileSync(new URL("../styles.css", import.meta.url), "utf8");
  assert.match(css, /\.chip-toggle\[aria-busy="true"\][^{]*\{[^}]*\S[^}]*\}/, "keine Stilregel für .chip-toggle[aria-busy=\"true\"]");
  assert.doesNotMatch(css, /\.structure-tools\s*\{/, "alte Chip-Reihe noch im Stylesheet");
});

test("im 3D-Modus fehlen Stereo-Zeile und Gruppen-Chips, der Bedienhinweis bleibt; zurück in 2D sind sie wieder da", async () => {
  const data = { ...MOLECULE, stereoWarnings: [STEREO] };
  assert.ok(data.functionalGroups?.length, "Fixture ohne Gruppen");
  const { container, unmount } = renderMolecule(data, () => lookupSuccess(CONFORMER));
  const has = (sel) => Boolean(container.querySelector(sel));
  assert.ok(has("[data-testid='stereo-note']") && has(".group-section"), "Ausgangslage ohne Stereo/Gruppen");
  await click(buttonByText(container, "3D"));
  assert.ok(has("[data-view-3d]"));
  assert.equal(has("[data-testid='stereo-note']"), false, "Stereo-Zeile in 3D");
  assert.equal(Boolean(buttonByText(container, "Show variants")), false, "Show variants in 3D");
  assert.equal(has(".group-section"), false, "Gruppen-Chips in 3D");
  assert.match(textOf(container), /Drag to rotate/);
  await click(buttonByText(container, "3D"));
  assert.ok(has("[data-testid='stereo-note']") && has(".group-section"), "nach Rückkehr fehlen Stereo/Gruppen");
  unmount();
});

// Fund (d), Durchsicht 09.11.: der zweite Ansicht-Klick während der ersten
// Anfrage ging verloren — der Guard brach ab, die erste Antwort durfte nicht
// mehr zeigen, und die gewünschte Zeichnung wurde nie geholt.
test("ein zweiter Ansicht-Klick während des Ladens gewinnt", async () => {
  const data = { ...MOLECULE, views: ["all_h", "fischer"], viewRequest: REQUEST };
  const gates = {};
  const { container, calls, unmount } = renderMolecule(data, async (req) => {
    const v = req.arguments.view;
    await new Promise((resolve) => { gates[v] = resolve; });
    return lookupSuccess({ type: "molecule", svg: "<svg/>", initialView: v, viewSvg: VIEW_SVG[v], viewAtoms: [] });
  });
  const drawing = () => container.querySelector(".structure-drawing");

  await click(buttonByText(container, "Fischer")); // erste Anfrage hängt
  await click(buttonByText(container, "All H"));   // Nutzer entscheidet um
  await act(async () => { gates.fischer?.(); });
  await act(async () => { gates.all_h?.(); });

  assert.deepEqual(calls.map((c) => c.arguments.view), ["fischer", "all_h"], "All H wurde nie angefragt");
  assert.ok(drawing().querySelector("[data-all-h]"), "zuletzt gewählte Ansicht nicht sichtbar");
  assert.equal(buttonByText(container, "All H").getAttribute("aria-pressed"), "true");
  assert.equal(buttonByText(container, "Fischer").getAttribute("aria-pressed"), "false");

  // Die Fischer-Antwort ist trotzdem im Cache: ihr Klick lädt nicht neu.
  await click(buttonByText(container, "Fischer"));
  assert.ok(drawing().querySelector("[data-fischer]"));
  assert.equal(calls.length, 2);
  unmount();
});
