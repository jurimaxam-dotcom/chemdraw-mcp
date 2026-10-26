import test from "node:test";
import assert from "node:assert/strict";
import { STEREO_COLOR, resolveHighlight } from "./highlight.js";

const GROUPS = [{ name: "Ester", atomIndices: [0, 1, 2], color: "#d35400" }];

test("ohne Hover und ohne Atomliste leuchtet nichts", () => {
  assert.equal(resolveHighlight({ groups: GROUPS, hoveredGroup: null }), null);
  assert.equal(resolveHighlight({ groups: GROUPS, hoveredGroup: "Gibtsnicht" }), null);
});

test("eine Gruppe liefert ihre Atome und ihre Farbe", () => {
  assert.deepEqual(resolveHighlight({ groups: GROUPS, hoveredGroup: "Ester" }), {
    atomIndices: [0, 1, 2],
    color: "#d35400",
  });
});

test("eine Atomliste (Stereo-Hinweis) schlaegt die Gruppe", () => {
  assert.deepEqual(
    resolveHighlight({ groups: GROUPS, hoveredGroup: "Ester", atomIndices: [4] }),
    { atomIndices: [4], color: STEREO_COLOR }
  );
});

test("eine leere Atomliste faellt auf die Gruppe zurueck", () => {
  assert.equal(resolveHighlight({ groups: GROUPS, hoveredGroup: "Ester", atomIndices: [] }).color, "#d35400");
});
