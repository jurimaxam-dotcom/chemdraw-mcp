// „found as": Hat der Server den Namen ueber eine andere Schreibweise
// gefunden (deutsche Regel, Transliteration, Salzform), steht sie im Kopf —
// so faellt ein falscher Treffer auf. Woertliche Treffer zeigen nichts.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import { AppContext } from "../AppContext";
import DatabaseView from "../DatabaseView";
import MoleculeView from "../MoleculeView";
import { DATABASE, MOLECULE } from "./fixtures.mjs";
import { render, textOf } from "./harness.mjs";

function renderIn(View, data) {
  return render(React.createElement(AppContext.Provider, { value: {} }, React.createElement(View, { data })));
}

const line = (container) => container.querySelector("[data-testid='found-as']");

for (const [label, View, base] of [["Molekuel", MoleculeView, MOLECULE], ["Datenblatt", DatabaseView, DATABASE]]) {
  test(`${label}: zeigt die Schreibweise, unter der gefunden wurde`, () => {
    const { container, unmount } = renderIn(View, { ...base, name: "Dexamethason", foundAs: "Dexamethasone" });
    assert.equal(textOf(line(container)), "Found as “Dexamethasone”");
    unmount();
  });

  test(`${label}: woertlicher Treffer ohne Zeile`, () => {
    const { container, unmount } = renderIn(View, { ...base, foundAs: "" });
    assert.equal(line(container), null);
    unmount();
  });
}
