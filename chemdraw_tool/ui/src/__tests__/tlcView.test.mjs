// DC-Platte: Unterzeile je Bahn. Desktop-Befund 14.11.2026: „Edukt: 0.30 Edukt“ —
// das Modell gibt dem Fleck oft denselben Namen wie der Bahn. Die Payload ist die
// Eingabe des Nutzers und bleibt; die Ansicht nennt den Namen nur einmal.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import TlcView from "../TlcView";
import { render } from "./harness.mjs";

const SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 12' width='10pt' height='12pt'></svg>";
const DATA = {
  type: "tlc",
  name: "DC-Platte",
  svg: SVG,
  lanes: [
    { name: "Edukt", spots: [{ rf: 0.3, label: "Edukt" }] },
    { name: "Co-Spot", spots: [{ rf: 0.3, label: "edukt " }, { rf: 0.65, label: "Produkt" }] },
  ],
  files: {},
};

test("Fleck mit dem Namen der Bahn: Name nur einmal", () => {
  const { container, unmount } = render(React.createElement(TlcView, { data: DATA }));
  const text = container.textContent;
  assert.ok(text.includes("Edukt: 0.30"), text);
  assert.ok(!text.includes("0.30 Edukt"), `Name doppelt: ${text}`);
  // Ein anderer Fleckname bleibt stehen (Co-Spot zeigt, welcher Fleck welcher ist).
  assert.match(text, /Co-Spot: 0\.30 edukt\s*· 0\.65 Produkt/);
  unmount();
});

test("Diagramm steckt in der gemeinsamen Diagrammfläche", () => {
  const { container, unmount } = render(React.createElement(TlcView, { data: DATA }));
  const card = container.querySelector(".plot-svg.tlc-svg");
  assert.ok(card, "keine .plot-svg.tlc-svg");
  assert.equal(card.getAttribute("data-svg-source"), "matplotlib");
  assert.ok(container.querySelector(".plot-panel"), "kein .plot-panel");
  unmount();
});
