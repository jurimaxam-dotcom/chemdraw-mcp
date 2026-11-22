// Panel-Format der Proteine (E13): dieselben Bytes wie protein_view.py.
import assert from "node:assert/strict";
import { test } from "node:test";

import { decodeOffsets, decodeXyz, layout, proteinMmcif } from "../protein/proteinData.js";
import { rainbow, residueColorer } from "../protein/colors.js";

// Erzeugt mit protein_view.encode_xyz / encode_offsets (Python)
const CA = "DADe/zgA6AMAAP//";
const O = "C+kEAAAA";

test("liest Cα und O genau so, wie der Server sie schreibt", () => {
  assert.deepEqual(decodeXyz(CA), [[1.2, -3.4, 5.6], [100, 0, -0.1]]);
  assert.deepEqual(decodeOffsets(O), [[1.1, -2.3, 0.4], null], "0,0,0 heißt: kein O");
});

test("mmCIF: Lücke zwischen Segmenten einer Kette, Helix- und Strangbereiche", () => {
  const chain = { id: "A", color: "#0072B2" };
  const segs = layout({ chains: [{ ...chain, segments: [{ ca: CA, o: O, ss: "HH" }, { ca: CA, o: O, ss: "EE" }] }] });
  assert.deepEqual(segs.map((s) => s.seq0), [1, 12], "zweites Segment springt um 10");
  const cif = proteinMmcif(segs);
  assert.equal((cif.match(/^ATOM /gm) || []).length, 4 + 2 - 1 + 1, "je Rest CA, O nur wo vorhanden");
  assert.ok(!cif.includes("HELX_P HELX_P1"), "Helix unter 3 Resten wird kein Band");
  assert.ok(cif.includes("S1 1 ALA A 12 ALA A 13"));
});

test("Regenbogen läuft je Kette von Blau nach Rot", () => {
  assert.equal(rainbow(0), "#2424db");
  assert.equal(rainbow(1), "#db2424");
  const segs = layout({ chains: [{ id: "A", segments: [{ ca: CA, o: O, ss: "HH" }] }] });
  const color = residueColorer(segs, "rainbow");
  assert.equal(color(segs[0], 0), rainbow(0));
  assert.equal(color(segs[0], 1), rainbow(1));
});
