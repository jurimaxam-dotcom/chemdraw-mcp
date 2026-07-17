import { test } from "node:test";
import assert from "node:assert/strict";
import { extractToolData } from "./toolData.js";

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
