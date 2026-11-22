// Sichtbare Panel-Texte sind englisch (Projektregel: user-facing text English).
// Die Statuszeilen in main.jsx rendern beim Import und sind so nicht per DOM erreichbar,
// deshalb dort ein Quelltext-Abgleich; App selbst wird echt gerendert.
import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";

import React from "react";

import App from "../App";
import { render } from "./harness.mjs";

test("unbekannter Payload-Typ meldet sich englisch", () => {
  const { container, unmount } = render(React.createElement(App, { data: { type: "nope" } }));
  assert.match(container.textContent, /^Unknown type: nope$/);
  unmount();
});

test("Statuszeilen beim Verbinden sind englisch", () => {
  const src = readFileSync(new URL("../main.jsx", import.meta.url), "utf8");
  for (const de of ["Warte auf Daten", "Verbinde…", "Verbindungsfehler"]) assert.ok(!src.includes(de), de);
  for (const en of ["Waiting for data…", "Connecting…", "Connection error"]) assert.ok(src.includes(en), en);
});
