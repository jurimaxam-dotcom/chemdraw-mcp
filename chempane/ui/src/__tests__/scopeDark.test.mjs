// Scope im Dunkelmodus: die Figur liegt auf fester weißer Platte. Die globale
// RDKit-Umfärbung (schwarz → --atom-c, im Dunkeln hell) darf sie nicht
// treffen, sonst wird das Gerüst hell auf Weiß (Design-Kritik 07.11.2026, F2).
// Gemessen an den echten Selektoren aus styles.css gegen das echte DOM.
import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";

import React from "react";

import ScopeView from "../ScopeView";
import { render } from "./harness.mjs";

const CSS = readFileSync(new URL("../styles.css", import.meta.url), "utf8");
// Alle Umfärbe-Regeln für schwarze Striche/Glyphen (auch #191919 der Kürzel), beide Dunkel-Varianten.
const SELECTORS = [
  ...CSS.matchAll(/^\s*(:root[^{\n]*svg:not\([^{\n]*?(?:path|text)\[[^\]]*(?:000000|191919)[^\]]*\])\s*\{/gm),
].map((m) => m[1].trim());

const FIGURE =
  '<svg viewBox="0 0 10 10"><path style="stroke:#000000" d="M0 0L5 5"/>' +
  '<path fill="#000000" d="M1 1"/><text fill="#000000">R</text>' +
  '<path style="stroke:#191919" d="M0 5L5 5"/><path fill="#191919" d="M2 2"/></svg>';

test("Umfärbe-Selektoren gefunden (sonst prüft der Test nichts)", () => {
  assert.ok(SELECTORS.length >= 10, `nur ${SELECTORS.length} Selektoren`);
});

test("Scope-SVG trägt die Ausnahme-Klasse und bleibt von der Dunkel-Umfärbung unberührt", () => {
  document.documentElement.setAttribute("data-theme", "dark");
  const { container, unmount } = render(
    React.createElement(ScopeView, { data: { type: "scope", svg: FIGURE, entries: [] } })
  );
  // Gegenprobe: ein freies RDKit-SVG (wie die Molekülansicht) wird umgefärbt.
  const control = document.createElement("div");
  control.innerHTML = FIGURE;
  document.body.appendChild(control);
  try {
    const scopeSvg = container.querySelector("svg");
    assert.ok(scopeSvg.closest(".scope-svg"), "Scope-SVG steckt nicht in .scope-svg");
    for (const sel of SELECTORS) {
      const hits = [...document.querySelectorAll(sel)];
      assert.equal(
        hits.some((el) => container.contains(el)),
        false,
        `Scope wird umgefärbt von: ${sel}`
      );
    }
    const controlHits = SELECTORS.flatMap((sel) => [...document.querySelectorAll(sel)]).filter(
      (el) => control.contains(el)
    );
    assert.ok(controlHits.length > 0, "Gegenprobe: freies SVG wird nicht umgefärbt — Selektor-Test kaputt");
  } finally {
    control.remove();
    unmount();
    document.documentElement.removeAttribute("data-theme");
  }
});
