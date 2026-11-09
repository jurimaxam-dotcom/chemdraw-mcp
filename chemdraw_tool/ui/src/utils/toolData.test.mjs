import { test } from "node:test";
import assert from "node:assert/strict";
import { extractToolData, extractToolError } from "./toolData.js";

const PAYLOAD = { type: "molecule", name: "caffeine", svg: "<svg/>" };

test("bevorzugt structuredContent, wenn vorhanden", () => {
  const params = {
    structuredContent: PAYLOAD,
    content: [{ type: "text", text: JSON.stringify({ type: "anders" }) }],
    isError: false,
  };
  assert.deepEqual(extractToolData(params), PAYLOAD);
});

test("fällt auf JSON im content-Textblock zurück (Claude Desktop strippt structuredContent)", () => {
  const params = {
    content: [{ type: "text", text: JSON.stringify(PAYLOAD) }],
    isError: false,
  };
  assert.deepEqual(extractToolData(params), PAYLOAD);
});

test("überspringt Nicht-Text-Blöcke und Nicht-JSON-Text", () => {
  const params = {
    content: [
      { type: "image", data: "abc", mimeType: "image/png" },
      { type: "text", text: "kein JSON" },
      { type: "text", text: JSON.stringify(PAYLOAD) },
    ],
    isError: false,
  };
  assert.deepEqual(extractToolData(params), PAYLOAD);
});

test("liefert null bei Fehler-Ergebnissen", () => {
  const params = {
    content: [{ type: "text", text: JSON.stringify(PAYLOAD) }],
    isError: true,
  };
  assert.equal(extractToolData(params), null);
});

test("liefert null ohne verwertbare Daten", () => {
  assert.equal(extractToolData({ content: [{ type: "text", text: "hi" }], isError: false }), null);
  assert.equal(extractToolData({ content: [], isError: false }), null);
  assert.equal(extractToolData(undefined), null);
  assert.equal(extractToolData({}), null);
});

test("JSON-Text, der kein Objekt ist, zählt nicht als Payload", () => {
  const params = { content: [{ type: "text", text: '"nur ein String"' }], isError: false };
  assert.equal(extractToolData(params), null);
});

// Fund (b), Durchsicht 09.11.: das Panel verwarf Tool-Fehler still und blieb
// auf „Waiting for data…“ bzw. dem alten Ergebnis stehen.
test("extractToolError liefert die Meldung eines Fehler-Ergebnisses, ohne SDK-Präfix", () => {
  const params = {
    isError: true,
    content: [{ type: "text", text: "Error executing tool generate_molecule: Could not parse 'C1CC' as SMILES." }],
  };
  assert.equal(extractToolError(params), "Could not parse 'C1CC' as SMILES.");
});

test("extractToolError fügt mehrere Textblöcke zusammen und überspringt Nicht-Text", () => {
  const params = {
    isError: true,
    content: [{ type: "image", data: "x", mimeType: "image/png" }, { type: "text", text: "first" }, { type: "text", text: "second" }],
  };
  assert.equal(extractToolError(params), "first\nsecond");
});

test("extractToolError hat einen Satz, wenn der Fehler keinen Text trägt", () => {
  assert.match(extractToolError({ isError: true, content: [] }), /error/i);
  assert.match(extractToolError({ isError: true }), /error/i);
});

test("extractToolError ist null für Erfolge und Unsinn", () => {
  assert.equal(extractToolError({ isError: false, content: [{ type: "text", text: "x" }] }), null);
  assert.equal(extractToolError({ structuredContent: PAYLOAD }), null);
  assert.equal(extractToolError(undefined), null);
});
