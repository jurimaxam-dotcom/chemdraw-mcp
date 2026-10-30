// Spektrenansicht: derselbe Exportknopf wie im Molekül-Panel.
//
// Desktop-Befund 30.10.2026 (Codex, Welle 2): SpectrumView zeigte nur den
// PNG-Pfad, keinen Knopf — wer das Spektrum ins Protokoll kopieren wollte,
// musste die Datei im Finder suchen. Der Knopf ist der generische
// ExportPngButton (Zwischenablage zuerst, sonst save_png); den echten Klick
// mit Zwischenablage und Rückfall prüft test:host.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import SpectrumView from "../SpectrumView";
import { buttonByText, render } from "./harness.mjs";

const DATA = {
  type: "spectrum",
  spectrum_type: "ir",
  name: "Aspirin IR",
  svg: "<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'></svg>",
  files: { png: "/Users/x/ChemDraw-Output/spektren/aspirin-ir.png" },
};

test("Spektrum hat den PNG-Exportknopf", () => {
  const { container, unmount } = render(React.createElement(SpectrumView, { data: DATA }));
  const button = buttonByText(container, "Export PNG");
  assert.ok(button, "kein Export-PNG-Knopf im Spektrum-Panel");
  assert.ok(button.classList.contains("export-png"), "nicht der generische ExportPngButton");
  unmount();
});

test("ohne SVG kein Exportknopf", () => {
  const { container, unmount } = render(
    React.createElement(SpectrumView, { data: { ...DATA, svg: "" } })
  );
  assert.equal(buttonByText(container, "Export PNG"), undefined);
  unmount();
});
