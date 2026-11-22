import { test } from "node:test";
import assert from "node:assert/strict";
import { extractSvgPixelSize } from "./svgToPng.js";

test("prefers viewBox over percentage width/height", () => {
  const svg = "<svg width='100%' height='100%' viewBox='340 258 215 179'>";
  assert.deepEqual(extractSvgPixelSize(svg), { w: 215, h: 179 });
});

test("falls back to numeric width/height when no viewBox", () => {
  const svg = "<svg width='150px' height='120px'>";
  assert.deepEqual(extractSvgPixelSize(svg), { w: 150, h: 120 });
});

test("throws when no usable dimensions", () => {
  assert.throws(() => extractSvgPixelSize("<svg></svg>"), /Maße/);
});

test("does not mistake stroke-width for the root width on the fallback path", () => {
  // No viewBox, only a stroke-width → must throw, not return {w:2,...}.
  assert.throws(
    () => extractSvgPixelSize("<svg><path stroke-width='2px'/></svg>"),
    /Maße/
  );
});

test("reads the real width despite a preceding stroke-width", () => {
  const svg = "<svg stroke-width='2px' width='150px' height='120px'></svg>";
  assert.deepEqual(extractSvgPixelSize(svg), { w: 150, h: 120 });
});
