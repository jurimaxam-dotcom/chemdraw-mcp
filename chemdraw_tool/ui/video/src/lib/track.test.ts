// Kameraspur fürs Hochformat: aus dem Click-Log der Panel-Aufnahme wird eine Folge von
// Posen, die im 1080×1920-Bild nie Rand zeigt, wo keiner hingehört.
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildTrack, clampPose, framePose, placePanel, sampleTrack, S_MAX, type Stage } from "./track.ts";
import type { ClickLog } from "./click-log.ts";

const vp = { width: 1440, height: 1440 };
const stage: Stage = { frameW: 1080, frameH: 1920, fit: 0.92 };
const base = { scale: 1, cx: 0.5, cy: 0.5 };

const log: ClickLog = {
  name: "molecule",
  viewport: vp,
  durationMs: 10000,
  trimBeforeMs: 1000,
  offsetMs: 0,
  clicks: [
    { label: "group 1", tDepartMs: 2000, tMs: 2100, x: 180, y: 960, rect: { x: 32, y: 930, w: 300, h: 72 }, content: { x: 32, y: 200, w: 908, h: 804 } },
    { label: "group 2", tDepartMs: 3500, tMs: 3600, x: 430, y: 960, rect: { x: 348, y: 930, w: 177, h: 72 }, content: { x: 32, y: 200, w: 908, h: 804 } },
    { label: "data", tDepartMs: 6500, tMs: 7250, tDownMs: 7200, x: 1118, y: 72, rect: { x: 1071, y: 38, w: 94, h: 68 } },
    { label: "data sheet", tMs: 9200, x: 720, y: 760, rect: { x: 32, y: 160, w: 1376, h: 1203 }, content: { x: 32, y: 160, w: 1376, h: 1203 } },
  ],
};

test("kleiner Knopf: Zoom bis zur Obergrenze, nicht darüber", () => {
  const p = framePose({ x: 1071, y: 38, w: 94, h: 68 }, vp, stage);
  assert.equal(p.scale, S_MAX);
});

test("Inhalt breiter als das Bild: kein Zoom unter 1", () => {
  const p = framePose({ x: 0, y: 0, w: 1600, h: 1440 }, vp, stage);
  assert.equal(p.scale, 1);
});

test("Pose am Rand wird so geklemmt, dass das Panel das Bild seitlich füllt", () => {
  const p = clampPose({ scale: S_MAX, cx: 0.99, cy: 0.02 }, vp, stage);
  const r = placePanel(p, vp, stage);
  // Panel breiter als das Bild ⇒ rechter Panelrand darf nicht ins Bild rutschen
  assert.ok(r.left + r.width >= stage.frameW - 1e-6, `rechts Rand sichtbar: ${r.left + r.width}`);
  assert.ok(r.left <= 1e-6);
  // Panel niedriger als das Bild ⇒ bleibt vertikal ganz im Bild
  assert.ok(r.top >= -1e-6 && r.top + r.height <= stage.frameH + 1e-6, `oben/unten abgeschnitten: ${r.top}`);
});

test("Grundpose zeigt das ganze Panel mittig", () => {
  const r = placePanel(base, vp, stage);
  assert.ok(Math.abs(r.width - 1080 * 0.92) < 1e-6);
  assert.ok(Math.abs(r.left + r.width / 2 - 540) < 1e-6);
});

test("Spur beginnt in der Grundpose und endet auf dem Datenblatt", () => {
  const keys = buildTrack(log, stage);
  assert.deepEqual(sampleTrack(keys, 0), base);
  const ende = sampleTrack(keys, log.durationMs / 1000);
  assert.ok(Math.abs(ende.scale - framePose(log.clicks[3].content!, vp, stage).scale) < 1e-6);
});

test("beim Gruppen-Hover ist die Kamera eingezoomt, über beide Gruppen ohne Zwischenschwenk", () => {
  const keys = buildTrack(log, stage);
  const a = sampleTrack(keys, (2100 - 1000) / 1000 + 1.2);
  const b = sampleTrack(keys, (3600 - 1000) / 1000 + 0.2);
  assert.ok(a.scale > 1.2, `Hover nicht gezoomt: ${a.scale}`);
  assert.deepEqual(a, b);
});

test("Kamera steht still, bevor der Data-Klick drückt", () => {
  const keys = buildTrack(log, stage);
  const druck = (7200 - 1000) / 1000;
  const kurzVor = sampleTrack(keys, druck - 0.1);
  const amDruck = sampleTrack(keys, druck);
  assert.deepEqual(kurzVor, amDruck);
  assert.equal(amDruck.scale, S_MAX);
});

test("Ereignisse nach dem Schnittende bewegen die Kamera nicht", () => {
  const spaet = { ...log, clicks: [...log.clicks, { label: "structure", tDepartMs: 13500, tMs: 14250, tDownMs: 14200, x: 990, y: 72, rect: { x: 916, y: 38, w: 151, h: 68 } }] };
  const ende = log.durationMs / 1000;
  assert.deepEqual(sampleTrack(buildTrack(spaet, stage), ende), sampleTrack(buildTrack(log, stage), ende));
});

test("Spur bleibt stetig (kein Sprung zwischen zwei Frames)", () => {
  const keys = buildTrack(log, stage);
  let prev = sampleTrack(keys, 0);
  for (let t = 1 / 30; t < 10; t += 1 / 30) {
    const p = sampleTrack(keys, t);
    assert.ok(Math.abs(p.scale - prev.scale) < 0.08, `Sprung bei ${t.toFixed(2)} s`);
    assert.ok(Math.abs(p.cx - prev.cx) < 0.05 && Math.abs(p.cy - prev.cy) < 0.05, `Schwenk-Sprung bei ${t.toFixed(2)} s`);
    prev = p;
  }
});
