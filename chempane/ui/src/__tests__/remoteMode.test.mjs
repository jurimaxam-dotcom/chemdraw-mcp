import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import MoleculeView from "../MoleculeView.jsx";
import { AppContext } from "../AppContext.js";
import { exportDeps } from "../components/ExportPngButton.jsx";
import { click, render } from "./harness.mjs";
import { MOLECULE } from "./fixtures.mjs";

const REMOTE_ASPIRIN = {
  ...MOLECULE,
  remote: true,
  views: ["all_h"],
  viewRequest: { name_or_smiles: "CC(=O)Oc1ccccc1C(=O)O" },
  files: {},
  cdxml_path: "",
};

test("Remote-Modus zeigt Struktur und Funktionsgruppen, aber keine lokalen/unbrauchbaren Aktionen", async () => {
  const { container, unmount } = render(React.createElement(MoleculeView, { data: REMOTE_ASPIRIN }));
  try {
    assert.ok(container.querySelector(".structure-canvas svg"));
    const chips = [...container.querySelectorAll('[aria-label="Functional groups"] button')];
    assert.ok(chips.length >= 1);
    await click(chips[0]);
    assert.equal(chips[0].getAttribute("aria-pressed"), "true");

    // Kein Data-Tab (nur Structure + Study)
    const tabLabels = [...container.querySelectorAll('[role="tab"]')].map((el) => el.textContent.trim());
    assert.deepEqual(tabLabels, ["Structure", "Study"]);

    // Kein 3D-Knopf, aber 2D + All H bleiben
    const axisLabels = [...container.querySelectorAll("[data-view-axis] button")].map((el) => el.textContent.trim());
    assert.ok(axisLabels.includes("2D"));
    assert.ok(axisLabels.includes("All H"));
    assert.ok(!axisLabels.includes("3D"));

    // Kein Add to Anki, keine lokalen Dateipfade
    assert.equal(container.querySelector(".add-anki"), null);
    assert.equal(container.querySelector(".panel-footer-file"), null);

    // ContinueRow verspricht keine nicht vorhandenen Tools (Mechanismus, IR, Compare)
    const followUpTexts = [...container.querySelectorAll(".continue-row button")].map((el) => el.textContent.trim());
    assert.ok(!followUpTexts.some((t) => /IR|Compare|mechanism/i.test(t)));
  } finally {
    unmount();
  }
});

test("Remote-Modus: Export PNG ruft bei blockierter Zwischenablage niemals save_png auf", async () => {
  const calls = [];
  const app = {
    callServerTool: async (req) => {
      calls.push(req);
      return { isError: true, content: [{ type: "text", text: "Unknown tool: save_png" }] };
    },
  };
  const origSvgToPng = exportDeps.svgToPngBlob;
  const origCopy = exportDeps.copyPngToClipboard;
  exportDeps.svgToPngBlob = async () => new Blob(["png"], { type: "image/png" });
  exportDeps.copyPngToClipboard = async () => {
    throw new Error("clipboard blocked");
  };
  const { container, unmount } = render(
    React.createElement(
      AppContext.Provider,
      { value: app },
      React.createElement(MoleculeView, { data: REMOTE_ASPIRIN })
    )
  );
  try {
    const btn = container.querySelector(".export-png");
    assert.ok(btn);
    await click(btn);
    await new Promise((r) => setTimeout(r, 30));
    assert.equal(calls.length, 0, "Remote Export PNG darf save_png nicht aufrufen");
  } finally {
    exportDeps.svgToPngBlob = origSvgToPng;
    exportDeps.copyPngToClipboard = origCopy;
    unmount();
  }
});
