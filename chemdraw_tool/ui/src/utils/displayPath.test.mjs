import test from "node:test";
import assert from "node:assert/strict";
import { displayPath } from "./displayPath.js";

test("macOS-Home wird zu ~", () => {
  assert.equal(displayPath("/Users/tom/ChemDraw-Output/diagramme/x.png"), "~/ChemDraw-Output/diagramme/x.png");
});
test("Linux-Home wird zu ~", () => {
  assert.equal(displayPath("/home/anna/ChemDraw-Output/scope/y.png"), "~/ChemDraw-Output/scope/y.png");
});
test("Windows-Home wird zu ~", () => {
  assert.equal(displayPath("C:\\Users\\Jay\\ChemDraw-Output\\3d\\c.sdf"), "~\\ChemDraw-Output\\3d\\c.sdf");
});
test("fremde Pfade, leere und fehlende Werte bleiben unverändert", () => {
  assert.equal(displayPath("/var/folders/ab/T/x.png"), "/var/folders/ab/T/x.png");
  assert.equal(displayPath(""), "");
  assert.equal(displayPath(undefined), "");
});
