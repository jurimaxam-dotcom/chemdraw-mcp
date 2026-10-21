import test from "node:test";
import assert from "node:assert/strict";
import { recordingOptions, demoEditFilter } from "../host/demo-options.mjs";

test("Demo kürzt nur lange Ladepausen; Klick und fertiges Datenblatt bleiben stehen", () => {
  assert.equal(demoEditFilter(1000, 5000), "select='not(between(t,1.350,4.850))',setpts='PTS-if(gte(T,4.850),3.500,0)/TB'");
  assert.equal(demoEditFilter(1000, 1400), "null");
  assert.equal(demoEditFilter(null, null), "null");
});

test("Aufnahme ohne Optionen behält Standardgröße und Standardszene", () => {
  assert.deepEqual(recordingOptions([]), {
    mitKlicks: false, zoom: 1, width: 720, height: 560, szenen: ["molecule"],
  });
});

test("--hires verdoppelt die Aufnahme ohne Click-Log oder Layoutänderung", () => {
  assert.deepEqual(recordingOptions(["compare", "--hires", "reaction"]), {
    mitKlicks: false, zoom: 2, width: 720, height: 560, szenen: ["compare", "reaction"],
  });
});

test("--clicks behält die höhere Shorts-Aufnahme; --hires skaliert nicht doppelt", () => {
  const erwartet = {
    mitKlicks: true, zoom: 2, width: 720, height: 720, szenen: ["molecule"],
  };
  assert.deepEqual(recordingOptions(["--clicks"]), erwartet);
  assert.deepEqual(recordingOptions(["--clicks", "--hires"]), erwartet);
});
