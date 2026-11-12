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

// M2 (12.11.2026): Große Ergebnisse halten ihre größten Teile zurück
// (chemdraw_tool/result_budget.py); das Panel lädt sie per load_panel_part nach.
import { loadToolData, PART_LOAD_FAILED } from "./toolData.js";

function fakeApp(parts, { fail = false } = {}) {
  // Der Server hält alle Teile als ein JSON-Array bereit und gibt es in Stücken heraus.
  const block = JSON.stringify(parts);
  const calls = [];
  return {
    calls,
    async callServerTool({ name, arguments: args }) {
      calls.push({ name, ...args });
      if (fail) return { isError: true, content: [{ type: "text", text: "Error executing tool load_panel_part: gone" }] };
      const end = Math.min(args.offset + 7, block.length);
      return { content: [{ type: "text", text: JSON.stringify({ text: block.slice(args.offset, end), next: end < block.length ? end : null }) }] };
    },
  };
}

const DEFERRED = {
  type: "batch",
  molecules: [{ name: "a", svg: "" }, { name: "b", svg: "kurz" }],
  _deferred: { token: "t1", paths: [["molecules", 0, "svg"], ["molecules"]] },
};

test("loadToolData ohne Vermerk: dasselbe wie extractToolData, kein Serveraufruf", async () => {
  const app = fakeApp([]);
  assert.deepEqual(await loadToolData(app, { structuredContent: PAYLOAD }), PAYLOAD);
  assert.equal(app.calls.length, 0);
});

test("loadToolData setzt Teile stückweise und rückwärts ein (Liste vor Text in ihr)", async () => {
  // Teil 1 ist die zurückgehaltene Liste (mit leerem svg darin), Teil 0 das svg darin.
  const liste = JSON.stringify([{ name: "a", svg: "" }, { name: "b", svg: "kurz" }]);
  const app = fakeApp(["<svg>langes Bild</svg>", liste]);
  const params = { content: [{ type: "text", text: JSON.stringify({ ...DEFERRED, molecules: [] }) }] };
  const data = await loadToolData(app, params);
  assert.equal(data._deferred, undefined);
  assert.deepEqual(data.molecules, [{ name: "a", svg: "<svg>langes Bild</svg>" }, { name: "b", svg: "kurz" }]);
  assert.ok(app.calls.every((c) => c.name === "load_panel_part" && c.token === "t1"));
  assert.ok(app.calls.length > 1, "in Stücken geladen");
  assert.deepEqual(app.calls.map((c) => c.offset), app.calls.map((_, i) => i * 7), "Stück für Stück, ohne Lücke");
});

test("loadToolData verändert das Ergebnis des Hosts nicht", async () => {
  const sc = structuredClone(DEFERRED);
  const app = fakeApp(["<svg/>", JSON.stringify([{ name: "a", svg: "" }])]);
  await loadToolData(app, { structuredContent: sc });
  assert.deepEqual(sc, DEFERRED);
});

test("loadToolData: Nachladen scheitert → Fehler mit Meldung statt halber Daten", async () => {
  const app = fakeApp([], { fail: true });
  await assert.rejects(loadToolData(app, { structuredContent: DEFERRED }), (err) => {
    assert.ok(err.message.startsWith(PART_LOAD_FAILED));
    assert.ok(err.message.includes("gone"));
    return true;
  });
});
