// Etappe 5: Aufteilung der Mechanismus-Übersicht — Maße aus dem echten Server (SN2: drei
// Schritte à 405×224, Fischer: acht à 573×292 viewBox-Einheiten).
import assert from "node:assert/strict";
import { test } from "node:test";

import { overviewLayout, MIN_SCALE } from "./mechanismLayout.js";

const SN2 = Array(3).fill({ w: 405, h: 224 });
const FISCHER = Array(8).fill({ w: 573, h: 292 });

test("SN2 im Chat bei 1000 px: drei Schritte nebeneinander, lesbar groß", () => {
  const l = overviewLayout(SN2, 920, 470);
  assert.deepEqual(l.rows, [[0, 1, 2]]);
  assert.ok(l.scale >= MIN_SCALE, `Maßstab ${l.scale}`);
  assert.equal(l.overflow, false);
  assert.ok(l.height <= 470);
});

test("SN2 im Seitenpanel (≈250 px): untereinander, in die Breite eingepasst", () => {
  const l = overviewLayout(SN2, 248, 380);
  assert.deepEqual(l.rows, [[0], [1], [2]]);
  assert.ok(12 + l.scale * 405 <= 248, "Kachel breiter als die Bühne");
});

test("Fischer (8 Schritte) breit und hoch genug: mehrere Zeilen, nie kleiner als MIN_SCALE", () => {
  const l = overviewLayout(FISCHER, 1500, 900);
  assert.ok(l.rows.length > 1 && l.rows.length < 8, `${l.rows.length} Zeilen`);
  assert.equal(l.rows.flat().length, 8);
  assert.ok(l.scale >= MIN_SCALE && !l.overflow && l.height <= 900, JSON.stringify(l));
});

test("Fischer bei 1000 px: passt nicht in die Höhe — Maßstab bleibt lesbar, das Panel wächst", () => {
  const l = overviewLayout(FISCHER, 920, 470);
  assert.equal(l.scale, MIN_SCALE);
  assert.equal(l.overflow, true);
  assert.ok(l.height > 470);
  assert.ok(l.rows.every((r) => 12 * r.length + 30 * (r.length - 1) + l.scale * 573 * r.length <= 920), "Zeile breiter als die Bühne");
});

test("stabil: gemessene Höhe gleich der benötigten ergibt dieselbe Aufteilung", () => {
  const a = overviewLayout(FISCHER, 920, 470);
  const b = overviewLayout(FISCHER, 920, a.height);
  assert.deepEqual(b.rows, a.rows);
  assert.equal(b.scale, a.scale);
});

test("ohne Maß (jsdom): eine Spalte im alten Maßstab", () => {
  const l = overviewLayout(SN2, 0, 0);
  assert.deepEqual(l.rows, [[0], [1], [2]]);
  assert.equal(l.scale, MIN_SCALE);
});
