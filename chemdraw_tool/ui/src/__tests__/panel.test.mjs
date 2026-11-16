// A0 der Panel-Überarbeitung (docs/design/panel-ueberarbeitung-2026-11-17.md, §4): die gemeinsamen
// Bausteine aus components/Panel.jsx. Sie sind der Vertrag für die Pakete A, B und C — geprüft
// werden Zonen, Klassen (auch die alten Haken, auf die Tests und Probe zielen), der Files-Schalter
// und die Bühnen-Varianten. DOM-Elemente nie direkt vergleichen (Boolean(...)), sonst hängt der Lauf.
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import {
  Button, Chip, Facts, Hint, Icon, Panel, PanelFoot, PanelHead, PanelState, Stage, StageBar,
} from "../components/Panel";
import { click, render, textOf } from "./harness.mjs";

const h = React.createElement;
const HOME = "/Users/x/ChemDraw-Output";
const FILES = [
  { label: "PNG", path: `${HOME}/einzelmolekuele/aspirin.png` },
  { label: "SVG", path: `${HOME}/einzelmolekuele/aspirin.svg` },
];

async function key(element, name) {
  await act(async () => {
    element.dispatchEvent(new window.KeyboardEvent("keydown", { key: name, bubbles: true, cancelable: true }));
  });
}

test("Panel: article.panel mit data-panel, Zonen in fester Reihenfolge, leere Zonen entfallen", () => {
  const { container, unmount } = render(h(Panel, { kind: "molecule", fill: true, className: "molecule-panel" },
    h(PanelHead, { title: "Caffeine", subtitle: "PubChem: Caffeine (CID 2519)" }),
    h(StageBar, {}),
    h(Stage, {}, "drawing"),
    h(Facts, { items: [] }),
    h(Hint, {}),
    h(PanelFoot, { files: FILES }),
  ));
  const panel = container.firstElementChild;
  assert.equal(panel.tagName, "ARTICLE");
  assert.equal(panel.classList.contains("panel"), true);
  assert.equal(panel.classList.contains("molecule-panel"), true, "className wird nicht durchgereicht");
  assert.equal(panel.getAttribute("data-panel"), "molecule");
  assert.equal(panel.hasAttribute("data-fill"), true, "fill setzt data-fill");
  const zones = [...panel.children].map((n) => n.className.split(" ")[0]);
  assert.deepEqual(zones, ["panel-head", "stage", "panel-foot"], "leere StageBar/Facts/Hint dürfen keinen Knoten hinterlassen");
  unmount();
  const plain = render(h(Panel, { kind: "plot" }, h(Stage, {})));
  assert.equal(plain.container.firstElementChild.hasAttribute("data-fill"), false);
  plain.unmount();
});

test("PanelHead: Titel, Untertitel mit vollem Text im title, Found as, Reiter und Expand rechts", () => {
  const { container, unmount } = render(h(PanelHead, {
    title: "Caffeine", subtitle: "PubChem: Caffeine (CID 2519)", foundAs: "Koffein",
    tabs: h("div", { role: "tablist", "data-x": "tabs" }), expand: h("button", { type: "button", "aria-label": "Expand" }),
  }));
  const head = container.firstElementChild;
  assert.equal(head.tagName, "HEADER");
  assert.equal(head.classList.contains("panel-head"), true);
  assert.equal(head.classList.contains("panel-header"), true, "Alias .panel-header fehlt");
  assert.equal(textOf(head.querySelector("h2.panel-title")), "Caffeine");
  const sub = head.querySelector("p.panel-subtitle");
  assert.equal(textOf(sub), "PubChem: Caffeine (CID 2519)");
  assert.equal(sub.getAttribute("title"), "PubChem: Caffeine (CID 2519)");
  assert.equal(textOf(head.querySelector("[data-testid='found-as']")), "Found as “Koffein”");
  const actions = head.querySelector(".panel-actions");
  assert.equal(Boolean(actions?.querySelector("[data-x='tabs']")), true, "Reiter nicht in .panel-actions");
  assert.equal(Boolean(actions?.querySelector("button[aria-label='Expand']")), true, "Expand nicht in .panel-actions");
  unmount();
  const bare = render(h(PanelHead, { title: "Only" }));
  assert.equal(bare.container.querySelectorAll(".panel-actions").length, 0, "leere Aktionen-Zone");
  bare.unmount();
  const none = render(h(PanelHead, {}));
  assert.equal(none.container.childElementCount, 0, "leerer Kopf muss entfallen");
  none.unmount();
});

test("PanelHead: heading ersetzt Titel und Untertitel (Study: verdeckter Name)", () => {
  const { container, unmount } = render(h(PanelHead, {
    title: "Secret", heading: h("button", { type: "button", className: "study-name" }, "Reveal name"),
  }));
  assert.equal(container.querySelectorAll("h2").length, 0);
  assert.doesNotMatch(container.innerHTML, /Secret/, "Titel leckt trotz heading");
  assert.equal(Boolean(container.querySelector(".panel-heading > button.study-name")), true);
  unmount();
});

test("StageBar: links und rechts, Hinweis rechts mit title", () => {
  const { container, unmount } = render(h(StageBar, {
    left: h("div", { role: "group", "aria-label": "View" }), hint: "Drag to rotate",
    right: h(Button, {}, "Reset view"),
  }));
  const bar = container.firstElementChild;
  assert.equal(bar.classList.contains("stage-bar"), true);
  assert.equal(Boolean(bar.querySelector(".stage-bar-start [role=group]")), true);
  const end = bar.querySelector(".stage-bar-end");
  assert.equal(textOf(end.querySelector(".stage-bar-hint")), "Drag to rotate");
  assert.equal(end.getAttribute("title"), "Drag to rotate");
  assert.equal(textOf(end.querySelector("button")), "Reset view");
  unmount();
});

test("Stage: Varianten plain (Standard), paper, 3d; reicht className, style, data-*, title und ref durch", () => {
  const ref = React.createRef();
  const { container, unmount } = render(h("div", {},
    h(Stage, { ref, className: "structure-canvas", style: { height: 100 }, "data-view-3d": "", title: "pinch to zoom" }),
    h(Stage, { variant: "paper" }),
    h(Stage, { variant: "3d" }),
  ));
  const [plain, paper, three] = container.firstElementChild.children;
  assert.equal(plain.classList.contains("stage"), true);
  assert.equal(plain.classList.contains("stage-plain"), true);
  assert.equal(plain.getAttribute("data-stage"), "plain");
  assert.equal(plain.classList.contains("structure-canvas"), true);
  assert.equal(plain.style.height, "100px");
  assert.equal(plain.hasAttribute("data-view-3d"), true);
  assert.equal(plain.getAttribute("title"), "pinch to zoom");
  assert.equal(ref.current === plain, true, "ref zeigt nicht auf die Bühne");
  assert.equal(paper.classList.contains("stage-paper"), true);
  assert.equal(three.classList.contains("stage-3d"), true);
  assert.equal(three.getAttribute("data-stage"), "3d");
  unmount();
});

test("Facts: dl.panel-facts.key-facts, Etikett und Wert, Kopierknopf, title; leere Werte entfallen", () => {
  const { container, unmount } = render(h(Facts, {
    items: [
      { label: "Formula", value: "C8H10N4O2", copy: "C8H10N4O2" },
      { label: "Molar mass", value: "194.19 g/mol", title: "average mass" },
      { label: "CAS", value: "" },
    ],
  }, h("div", { className: "fact", "data-x": "extra" })));
  const dl = container.firstElementChild;
  assert.equal(dl.tagName, "DL");
  assert.equal(dl.classList.contains("panel-facts"), true);
  assert.equal(dl.classList.contains("key-facts"), true);
  const facts = [...dl.querySelectorAll(":scope > .fact:not([data-x])")];
  assert.deepEqual(facts.map((f) => textOf(f.querySelector("dt"))), ["Formula", "Molar mass"]);
  assert.equal(facts[0].querySelectorAll("button[aria-label='Copy value']").length, 1);
  assert.equal(facts[1].querySelectorAll("button").length, 0, "Kopierknopf ohne copy");
  assert.equal(facts[1].querySelector("dd").getAttribute("title"), "average mass");
  assert.equal(Boolean(dl.querySelector("[data-x='extra']")), true, "children fehlen");
  unmount();
  const empty = render(h(Facts, { items: [{ label: "CAS", value: null }] }));
  assert.equal(empty.container.childElementCount, 0, "leere Facts-Zone muss entfallen");
  empty.unmount();
});

test("Chip: button.chip mit aria-pressed, Punkt in --group-color, Zahl", async () => {
  let clicks = 0;
  const { container, unmount } = render(h(Chip, {
    pressed: false, color: "#d6336c", count: 3, className: "functional-group", onClick: () => { clicks += 1; },
  }, "Amide"));
  const chip = container.firstElementChild;
  assert.equal(chip.tagName, "BUTTON");
  assert.equal(chip.getAttribute("type"), "button");
  assert.equal(chip.classList.contains("chip"), true);
  assert.equal(chip.classList.contains("functional-group"), true);
  assert.equal(chip.getAttribute("aria-pressed"), "false");
  assert.equal(chip.style.getPropertyValue("--group-color"), "#d6336c");
  assert.equal(chip.querySelector(".chip-dot").getAttribute("aria-hidden"), "true");
  assert.equal(textOf(chip.querySelector(".chip-count")), "3");
  await click(chip);
  assert.equal(clicks, 1);
  unmount();
  const free = render(h(Chip, {}, "Plain"));
  assert.equal(free.container.firstElementChild.hasAttribute("aria-pressed"), false, "ohne pressed kein aria-pressed");
  free.unmount();
});

test("Button: quiet (Standard) und primary, Symbol aria-hidden, disabled bleibt sichtbar und klickt nicht", async () => {
  let clicks = 0;
  const ref = React.createRef();
  const { container, unmount } = render(h("div", {},
    h(Button, { ref, icon: "download", className: "export-png", onClick: () => { clicks += 1; } }, "Export PNG"),
    h(Button, { variant: "primary" }, "Reveal all"),
    h(Button, { disabled: true, onClick: () => { clicks += 1; } }, "Next"),
    h(Button, { icon: "expand", "aria-label": "Expand" }),
  ));
  const [quiet, primary, off, iconOnly] = container.firstElementChild.children;
  assert.equal(quiet.classList.contains("btn"), true);
  assert.equal(quiet.classList.contains("btn-quiet"), true);
  assert.equal(quiet.classList.contains("export-png"), true);
  assert.equal(quiet.getAttribute("type"), "button");
  assert.equal(ref.current === quiet, true, "ref zeigt nicht auf den Knopf");
  const svg = quiet.querySelector("svg");
  assert.equal(Boolean(svg), true, "Symbol fehlt");
  assert.equal(svg.getAttribute("aria-hidden"), "true");
  assert.equal(textOf(quiet), "Export PNG");
  assert.equal(primary.classList.contains("btn-primary"), true);
  assert.equal(off.disabled, true);
  assert.equal(off.classList.contains("btn"), true, "disabled verliert die Form");
  await click(off);
  await click(quiet);
  assert.equal(clicks, 1, "disabled hat geklickt");
  assert.equal(iconOnly.classList.contains("is-icon"), true, "Nur-Symbol-Knopf ohne is-icon");
  unmount();
});

test("Icon: Strich-Symbole, 1,5 px, aria-hidden; unbekannter Name rendert nichts", () => {
  for (const name of ["expand", "chevron-down", "chevron-left", "chevron-right", "check", "download", "copy"]) {
    const { container, unmount } = render(h(Icon, { name }));
    const svg = container.querySelector("svg");
    assert.equal(Boolean(svg), true, `Symbol ${name} fehlt`);
    assert.equal(svg.getAttribute("aria-hidden"), "true");
    assert.equal(svg.getAttribute("stroke-width"), "1.5");
    assert.equal(svg.getAttribute("fill"), "none");
    unmount();
  }
  const none = render(h(Icon, { name: "nope" }));
  assert.equal(none.container.childElementCount, 0);
  none.unmount();
});

test("PanelFoot zu: Files-Schalter mit Name „Files, 2“, Liste hidden, Pfade trotzdem mit title im DOM", () => {
  const { container, unmount } = render(h(PanelFoot, { files: FILES }, h(Button, { className: "export-png" }, "Export PNG")));
  const foot = container.firstElementChild;
  assert.equal(foot.tagName, "FOOTER");
  for (const cls of ["panel-foot", "panel-footer"]) assert.equal(foot.classList.contains(cls), true, cls);
  assert.equal(foot.getAttribute("data-testid"), "panel-footer");
  const toggle = foot.querySelector("button[aria-expanded]");
  assert.equal(Boolean(toggle), true, "Files-Schalter fehlt");
  assert.equal(toggle.getAttribute("aria-label"), "Files, 2");
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  const list = document.getElementById(toggle.getAttribute("aria-controls"));
  assert.equal(Boolean(list), true, "aria-controls zeigt ins Leere");
  assert.equal(list.hidden, true, "Liste nicht hidden");
  const paths = [...list.querySelectorAll(".panel-footer-path")];
  assert.deepEqual(paths.map((p) => textOf(p)), ["~/ChemDraw-Output/einzelmolekuele/aspirin.png", "~/ChemDraw-Output/einzelmolekuele/aspirin.svg"]);
  assert.deepEqual(paths.map((p) => p.getAttribute("title")), FILES.map((f) => f.path));
  assert.deepEqual([...list.querySelectorAll(".panel-footer-label")].map((n) => textOf(n)), ["PNG", "SVG"]);
  assert.equal(list.querySelectorAll("button[aria-label='Copy path']").length, 2);
  assert.equal(list.querySelectorAll("button[aria-label='Copy folder']").length, 1);
  assert.deepEqual([...foot.querySelectorAll(".panel-footer-actions button")].map((b) => textOf(b)), ["Export PNG"]);
  unmount();
});

test("PanelFoot: Klick öffnet die Liste, Escape schließt sie und setzt den Fokus auf den Schalter", async () => {
  const { container, unmount } = render(h(PanelFoot, { files: FILES }));
  const toggle = container.querySelector("button[aria-expanded]");
  const list = container.querySelector(".panel-foot-list");
  await click(toggle);
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.equal(list.hidden, false, "Liste nach Klick nicht sichtbar");
  const copy = list.querySelector("button[aria-label='Copy path']");
  copy.focus();
  await key(copy, "Escape");
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(list.hidden, true, "Escape schließt nicht");
  assert.equal(document.activeElement === toggle, true, "Fokus nicht zurück auf dem Schalter");
  await click(toggle);
  await click(toggle);
  assert.equal(list.hidden, true, "zweiter Klick schließt nicht");
  unmount();
});

test("PanelFoot: hideFiles zeigt weder Schalter noch Pfade; ohne Dateien und Aktionen entfällt der Fuß", () => {
  const { container, unmount } = render(h(PanelFoot, { files: FILES, hideFiles: true }, h(Button, { className: "add-to-anki" }, "Add to Anki")));
  const foot = container.firstElementChild;
  assert.equal(foot.querySelectorAll("button[aria-expanded]").length, 0);
  assert.equal(foot.querySelectorAll(".panel-footer-path, [title*='aspirin']").length, 0, "Pfad leckt trotz hideFiles");
  assert.doesNotMatch(foot.innerHTML, /aspirin/);
  assert.equal(textOf(foot), "Add to Anki");
  unmount();
  for (const props of [{ files: [] }, { files: FILES, hideFiles: true }]) {
    const empty = render(h(PanelFoot, props));
    assert.equal(empty.container.childElementCount, 0, `leerer Fuß bei ${JSON.stringify(props).slice(0, 40)}`);
    empty.unmount();
  }
});

test("Hint: p.hint, Ton warn mit Punkt; ohne Inhalt nichts", () => {
  const { container, unmount } = render(h("div", {}, h(Hint, {}, "Drag to rotate"), h(Hint, { tone: "warn" }, "Not drawn (1): xyz")));
  const [quiet, warn] = container.firstElementChild.children;
  assert.equal(quiet.tagName, "P");
  assert.equal(quiet.classList.contains("hint"), true);
  assert.equal(quiet.classList.contains("hint-warn"), false);
  assert.equal(warn.classList.contains("hint-warn"), true);
  assert.equal(warn.querySelector(".hint-dot").getAttribute("aria-hidden"), "true");
  assert.equal(textOf(warn), "Not drawn (1): xyz");
  unmount();
});

test("PanelState: loading mit Spinner und role=status, error mit Titel und Satz", () => {
  const { container, unmount } = render(h("div", {},
    h(PanelState, { kind: "loading", message: "Preparing the panel…" }),
    h(PanelState, { kind: "error", title: "The tool could not produce a result", message: "Not found" }),
    h(PanelState, { kind: "empty", message: "No peaks" }),
  ));
  const [loading, error, empty] = container.firstElementChild.children;
  for (const n of [loading, error, empty]) assert.equal(n.classList.contains("panel-state"), true);
  assert.equal(loading.getAttribute("data-state"), "loading");
  assert.equal(loading.getAttribute("role"), "status");
  assert.equal(Boolean(loading.querySelector(".seg-spinner")), true, "Lade-Spinner fehlt");
  assert.equal(error.getAttribute("data-state"), "error");
  assert.equal(textOf(error.querySelector(".panel-state-title")), "The tool could not produce a result");
  assert.equal(textOf(error.querySelector(".panel-state-message")), "Not found");
  assert.equal(Boolean(error.querySelector(".seg-spinner")), false);
  assert.equal(empty.getAttribute("data-state"), "empty");
  unmount();
});

test("PanelFoot: Rückmeldung einer Aktion (FooterStatus) ersetzt den Schalter, die Liste bleibt im DOM", async () => {
  const { FooterStatus } = await import("../components/PanelFooter");
  function Saver() {
    const report = React.useContext(FooterStatus);
    return h(Button, { onClick: () => report({ text: "Saved: ~/x.png" }) }, "Export PNG");
  }
  const { container, unmount } = render(h(PanelFoot, { files: FILES }, h(Saver)));
  await click([...container.querySelectorAll("button")].find((b) => textOf(b) === "Export PNG"));
  const note = container.querySelector(".export-feedback");
  assert.equal(Boolean(note), true, "keine Rückmeldung");
  assert.equal(note.getAttribute("role"), "status");
  assert.equal(container.querySelectorAll("button[aria-expanded]").length, 0, "Schalter steht neben der Rückmeldung");
  assert.equal(container.querySelectorAll(".panel-foot-list .panel-footer-path[title]").length, 2, "Liste verschwand mit dem Schalter");
  unmount();
});
