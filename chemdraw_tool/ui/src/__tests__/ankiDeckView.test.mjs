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

// Etappe 5 (16.11.2026): Vorschau mit Vorder- und Rückseite (Bild, wenn die Karte eines hat),
// bei vielen Karten die ersten und „+ n more“; Ablageort mit Kopierknopf.
const PNG = "data:image/png;base64,iVBORw0KGgo=";
const DECK = {
  type: "anki_deck", name: "Koffein und Paracetamol", cards: 8, media: 2, delivery: "apkg",
  fronts: Array.from({ length: 8 }, (_, i) => `F${i}`),
  file: "/Users/x/ChemDraw-Output/anki/koffein.apkg",
  previews: [
    { front: "", back: "<b>Koffein</b><br>Methylxanthin", front_image: PNG, back_image: "" },
    { front: "Welche Gruppe? <img src=x onerror=alert(1)>", back: "Ester", front_image: "", back_image: PNG },
    ...Array.from({ length: 4 }, (_, i) => ({ front: `F${i + 2}`, back: `B${i + 2}`, front_image: "", back_image: "" })),
  ],
};

test("Kartenvorschau: Vorder- und Rückseite je Karte, Bilder nur wo die Karte eines hat", () => {
  const { container, unmount } = render(React.createElement(AnkiDeckView, { data: DECK }));
  const cards = container.querySelectorAll("[data-anki-card]");
  assert.equal(cards.length, 4, "höchstens vier Karten (Spezifikation §5.13)");
  const [first, second] = cards;
  assert.ok(first.querySelector("[data-side='front'] img[src^='data:image/png']"), "Bild der Vorderseite fehlt");
  assert.equal(first.querySelector("[data-side='back'] img"), null);
  assert.equal(first.querySelector("[data-side='back'] .anki-side-text").textContent, "Koffein\nMethylxanthin");
  assert.ok(second.querySelector("[data-side='back'] img"), "Bild der Rückseite fehlt");
  assert.equal(container.querySelectorAll("img").length, 2, "Kartentext darf kein <img> einschleusen");
  assert.match(container.querySelector(".hint").textContent, /^\+ 4 more cards$/);
  unmount();
});

test("Kopf und Fußzeile: Kartenzahl im Untertitel, .apkg-Pfad sichtbar mit Kopierknopf", () => {
  const { container, unmount } = render(React.createElement(AnkiDeckView, { data: DECK }));
  const panel = container.firstElementChild;
  assert.ok(panel.matches("article.panel.anki-panel"));
  assert.match(container.querySelector(".panel-subtitle").textContent, /^8 cards · 2 images/);
  const footer = container.querySelector("[data-testid='panel-footer']");
  assert.equal(panel.lastElementChild, footer, "Fuß ist die letzte Zone");
  assert.ok(footer.matches("dl.panel-facts"), "die .apkg ist das Ergebnis: Kernwert-Zeile, kein Files-Schalter");
  assert.match(footer.textContent, /APKG/);
  const path = footer.querySelector(".panel-footer-path");
  assert.equal(path.textContent, "~/ChemDraw-Output/anki/koffein.apkg");
  assert.equal(path.getAttribute("title"), DECK.file);
  assert.equal(path.closest("[hidden]"), null, "Pfad sichtbar, nicht hinter „Files“");
  assert.equal(footer.querySelector("button[aria-expanded]"), null, "kein Files-Schalter");
  assert.ok(footer.querySelector("button[aria-label='Copy path']"), "Kopierknopf fehlt");
  unmount();
});

test("ältere Ergebnisse ohne previews: Vorderseiten wie bisher", () => {
  const data = { ...DECK, previews: undefined, cards: 2, fronts: ["Welcher Wirkstoff?", "Welcher Wirkstoff?"] };
  const { container, unmount } = render(React.createElement(AnkiDeckView, { data }));
  assert.equal(container.querySelectorAll("[data-anki-card]").length, 2);
  assert.match(container.textContent, /Welcher Wirkstoff\?/);
  unmount();
});
