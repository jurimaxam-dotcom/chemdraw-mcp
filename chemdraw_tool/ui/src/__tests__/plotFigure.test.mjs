// Gemeinsame Diagrammfläche (Etappe 1, 16.11.2026): Spektrum, DC und PlotView tragen
// dieselbe Klasse, an der Größe und Thema in styles.css hängen; der Strukturvergleich
// (RDKit) ist als solcher markiert, damit die dunkle Umfärbung der Striche greift.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import PlotView from "../PlotView";
import SpectrumView from "../SpectrumView";
import { svgSource } from "../components/PlotFigure";
import { render } from "./harness.mjs";

const MPL = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 720 468'><!-- Created with matplotlib --></svg>";
const RDKIT = "<svg version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:rdkit='http://www.rdkit.org/xml' viewBox='0 0 1000 450'></svg>";

test("svgSource unterscheidet RDKit von matplotlib", () => {
  assert.equal(svgSource(RDKIT), "rdkit");
  assert.equal(svgSource(MPL), "matplotlib");
  assert.equal(svgSource(""), "matplotlib");
});

test("Vergleich (RDKit) und Kurve (matplotlib) in PlotView", () => {
  for (const [svg, source] of [[RDKIT, "rdkit"], [MPL, "matplotlib"]]) {
    const { container, unmount } = render(React.createElement(PlotView, { data: { type: "plot", name: "x", svg } }));
    const card = container.querySelector(".plot-panel > .plot-svg");
    assert.ok(card, "keine .plot-svg im .plot-panel");
    assert.equal(card.getAttribute("data-svg-source"), source);
    unmount();
  }
});

test("Spektrum nutzt dieselbe Fläche, Klasse spectrum-svg bleibt", () => {
  const { container, unmount } = render(
    React.createElement(SpectrumView, { data: { type: "spectrum", spectrum_type: "ir", name: "IR", svg: MPL, files: {} } })
  );
  assert.ok(container.querySelector(".plot-panel > .plot-svg.spectrum-svg"));
  unmount();
});
