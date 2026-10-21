import test from "node:test";
import assert from "node:assert/strict";
import { recordingOptions } from "../host/demo-options.mjs";

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
