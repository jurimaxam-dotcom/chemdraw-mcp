// Herkunft und Zaehlweise: zwei Zahlen im Panel, die etwas anderes bedeutet
// haben, als sie aussahen.
//
// 1. "Ester 5" war die Zahl der markierten Atome, gelesen wurde sie als
//    Zahl der Estergruppen.
// 2. CAS und XLogP stammen woertlich aus einem PubChem-Datensatz. Welcher
//    das ist, stand nirgends — ein falsch aufgeloester Name faellt damit
//    niemandem auf.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import FunctionalGroupList from "../components/FunctionalGroupList";
import MoleculeView from "../MoleculeView";
import { MOLECULE } from "./fixtures.mjs";
import { render } from "./harness.mjs";

test("zeigt die Zahl der Gruppen, nicht die der markierten Atome", () => {
  const groups = [
    { name: "Ester", atomIndices: [0, 1, 2, 3, 4], color: "#d35400", count: 1 },
  ];
  const { container, unmount } = render(
    React.createElement(FunctionalGroupList, {
      groups,
      hoveredGroup: null,
      onHoverGroup: () => {},
    })
  );
  const text = container.textContent;
  assert.match(text, /Ester/);
  assert.match(text, /1/, `Gruppenzahl fehlt: ${text}`);
  assert.ok(!/5/.test(text), `Atomzahl steht noch da: ${text}`);
  unmount();
});

test("nennt den PubChem-Datensatz, aus dem die Zahlen stammen", () => {
  const data = {
    ...MOLECULE,
    properties: {
      ...MOLECULE.properties,
      pubchemTitle: "Methylphenidate",
      cid: "4158",
    },
  };
  const { container, unmount } = render(
    React.createElement(
      AppContext.Provider,
      { value: { callServerTool: async () => ({}) } },
      React.createElement(MoleculeView, { data })
    )
  );
  assert.match(container.textContent, /PubChem: Methylphenidate \(CID 4158\)/);
  unmount();
});

test("ohne PubChem-Datensatz bleibt der Kopf still", () => {
  const { container, unmount } = render(
    React.createElement(
      AppContext.Provider,
      { value: { callServerTool: async () => ({}) } },
      React.createElement(MoleculeView, { data: MOLECULE })
    )
  );
  assert.ok(!/PubChem:/.test(container.textContent), "PubChem-Zeile ohne Datensatz");
  unmount();
});
