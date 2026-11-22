import test from "node:test";
import assert from "node:assert/strict";
import { naturalWidth } from "./svgSize.js";

test("liest die viewBox-Breite mit einfachen Anführungszeichen (RDKit)", () => {
  assert.equal(naturalWidth("<svg viewBox='10 20 300 120' width='100%'>"), 300);
});
test("liest die viewBox-Breite mit doppelten Anführungszeichen", () => {
  assert.equal(naturalWidth('<svg viewBox="0 0 450.5 350">'), 450.5);
});
test("ohne viewBox: null (Aufrufer fällt auf Kachelbreite zurück)", () => {
  assert.equal(naturalWidth("<svg width='100'>"), null);
  assert.equal(naturalWidth(""), null);
  assert.equal(naturalWidth(undefined), null);
});

import { naturalHeight } from "./svgSize.js";
test("liest die viewBox-Höhe (RDKit und doppelte Anführungszeichen)", () => {
  assert.equal(naturalHeight("<svg viewBox='10 20 300 120' width='100%'>"), 120);
  assert.equal(naturalHeight('<svg viewBox="0 0 450.5 350.25">'), 350.25);
  assert.equal(naturalHeight("<svg width='100'>"), null);
});
