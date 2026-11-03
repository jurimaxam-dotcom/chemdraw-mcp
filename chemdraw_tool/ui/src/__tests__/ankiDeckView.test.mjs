// Anki-Vorschau: Kartenvorderseiten dürfen Anki-HTML tragen (<i>, <b>, <br>),
// die Vorschau zeigt sie als Text — nicht als wörtliche Tags.
//
// Desktop-Befund 02.11.2026 (Codex, Abnahme 0.7.0): „Was passiert, wenn man
// Ibuprofen kurz <i>vor</i> Low-Dose-ASS nimmt?" stand mit Tags im Panel.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import AnkiDeckView from "../AnkiDeckView";
import { render } from "./harness.mjs";

test("Vorschau zeigt Anki-HTML als Text, ohne wörtliche Tags", () => {
  const data = {
    type: "anki_deck", name: "Deck", cards: 2, media: 0,
    fronts: ["Ibuprofen kurz <i>vor</i> ASS?", "Zeile 1<br>Zeile 2 &amp; mehr"],
    files: { apkg: "/Users/x/ChemDraw-Output/anki/deck.apkg" },
  };
  const { container, unmount } = render(React.createElement(AnkiDeckView, { data }));
  const items = [...container.querySelectorAll("li")].map((li) => li.textContent);
  assert.equal(items[0], "Ibuprofen kurz vor ASS?");
  assert.equal(items[1], "Zeile 1 Zeile 2 & mehr");
  assert.ok(!container.innerHTML.includes("&lt;i&gt;"), "Tag wörtlich im Panel");
  unmount();
});
