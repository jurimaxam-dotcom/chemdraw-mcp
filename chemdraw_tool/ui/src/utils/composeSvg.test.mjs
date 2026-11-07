import assert from "node:assert/strict";
import { test } from "node:test";

import { composeSvg } from "./composeSvg.js";
import { extractSvgPixelSize } from "./svgToPng.js";

const MOL = "<?xml version='1.0' encoding='iso-8859-1'?>\n<svg version='1.1' xmlns='http://www.w3.org/2000/svg' width='120px' height='80px' viewBox='0 0 120 80'><path d='M0 0'/></svg>";

test("Reihe aus Strukturen, Plus und Pfeil: ein gültiges SVG mit Maßen", () => {
  const svg = composeSvg([
    { kind: "svg", svg: MOL, caption: "A" },
    { kind: "text", text: "+" },
    { kind: "svg", svg: MOL, caption: "B & C" },
    { kind: "arrow", above: "H2SO4", below: "reflux" },
    { kind: "svg", svg: MOL },
  ]);
  assert.ok(svg.startsWith("<svg xmlns=\"http://www.w3.org/2000/svg\""));
  const { w, h } = extractSvgPixelSize(svg);
  assert.ok(w > 3 * 120 && h >= 80, `Maße ${w}×${h}`);
  assert.equal((svg.match(/<svg\b/g) || []).length, 4, "drei eingebettete Strukturen + Hülle");
  assert.doesNotMatch(svg, /<\?xml/);
  assert.match(svg, /B &amp; C/, "Text nicht escaped");
  assert.match(svg, /H2SO4/);
  assert.match(svg, /reflux/);
});

test("eingebettete Struktur behält ihr Seitenverhältnis über die viewBox", () => {
  const svg = composeSvg([{ kind: "svg", svg: "<svg width='50' height='20'><path d='M1 1'/></svg>" }]);
  assert.match(svg, /<svg x="[\d.]+" y="[\d.]+" width="50" height="20" viewBox="0 0 50 20"/);
});

test("Spalte: Höhe wächst mit jedem Teil, Pfeil senkrecht", () => {
  const one = extractSvgPixelSize(composeSvg([{ kind: "svg", svg: MOL }], { direction: "column" }));
  const three = extractSvgPixelSize(composeSvg([
    { kind: "svg", svg: MOL }, { kind: "arrow", reversible: true }, { kind: "svg", svg: MOL },
  ], { direction: "column" }));
  assert.ok(three.h > 2 * one.h - 40, `${three.h} vs ${one.h}`);
  assert.ok(three.w >= 120);
});

test("Teil ohne verwertbares SVG wird übersprungen statt zu werfen", () => {
  const svg = composeSvg([{ kind: "svg", svg: "<svg></svg>" }, { kind: "svg", svg: MOL }]);
  assert.equal((svg.match(/<svg\b/g) || []).length, 2);
});
