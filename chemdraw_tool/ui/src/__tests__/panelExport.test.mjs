// DC-Platte und Kurvendiagramme: derselbe Exportknopf wie Molekül und Spektrum.
//
// Desktop-Befund 30.10.2026 (Codex, an SpectrumView): Grafik-Panels zeigten
// nur den PNG-Pfad, keinen Knopf. TlcView und PlotView (Titrationskurve,
// Speziesverteilung) hatten dieselbe Lücke.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import PlotView from "../PlotView";
import TlcView from "../TlcView";
import { buttonByText, render } from "./harness.mjs";

const SVG = "<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'></svg>";

const CASES = [
  ["TlcView", TlcView, {
    type: "tlc", name: "Veresterung", svg: SVG,
    lanes: [{ name: "A", spots: [{ rf: 0.3, label: "", intensity: 1 }] }],
    files: { png: "/x/dc-platten/veresterung.png" },
  }],
  ["PlotView", PlotView, {
    type: "plot", name: "Acetic acid with NaOH", svg: SVG,
    files: { png: "/x/diagramme/acetic.png" },
  }],
];

for (const [label, View, data] of CASES) {
  test(`${label} hat den PNG-Exportknopf`, () => {
    const { container, unmount } = render(React.createElement(View, { data }));
    const button = buttonByText(container, "Export PNG");
    assert.ok(button, `kein Export-PNG-Knopf in ${label}`);
    assert.ok(button.classList.contains("export-png"));
    unmount();
  });
}
