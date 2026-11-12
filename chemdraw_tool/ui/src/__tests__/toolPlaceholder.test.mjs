// Platzhalter aus `toolinput` (statt „Waiting for data…“) und der Satz nach `toolcancelled`.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import ToolPlaceholder from "../components/ToolPlaceholder";
import { render, textOf } from "./harness.mjs";

test("Molekül: Titel aus den Argumenten, ruhiges Skelett, als Status markiert", () => {
  const { container, unmount } = render(React.createElement(ToolPlaceholder, { args: { name_or_smiles: "aspirin" } }));
  const box = container.querySelector("[data-testid='tool-placeholder']");
  assert.ok(box);
  assert.equal(box.getAttribute("role"), "status");
  assert.equal(box.getAttribute("aria-busy"), "true");
  assert.match(textOf(box), /aspirin/);
  assert.doesNotMatch(textOf(box), /Waiting for data/);
  assert.ok(box.querySelector(".placeholder-canvas"));
  unmount();
});

test("Stapel: je Name ein beschrifteter Platzhalter", () => {
  const { container, unmount } = render(React.createElement(ToolPlaceholder, { args: { molecules: ["aspirin", "caffeine"] } }));
  const cards = [...container.querySelectorAll(".placeholder-card")].map((c) => textOf(c));
  assert.deepEqual(cards, ["aspirin", "caffeine"]);
  unmount();
});

test("abgebrochen: ein Satz statt Ladezustand", () => {
  const { container, unmount } = render(React.createElement(ToolPlaceholder, { args: { name_or_smiles: "aspirin" }, cancelled: { reason: "user action" } }));
  assert.match(textOf(container), /The request was cancelled/);
  assert.equal(container.querySelector("[aria-busy='true']"), null);
  unmount();
});
