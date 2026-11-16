// Rauchtest der Testumgebung selbst.
//
// Grund: ohne ihn ist ein rot laufender Feature-Test nicht von einem kaputten
// JSX-Loader zu unterscheiden — beides sieht nach "Test schlaegt fehl" aus.
// Dieser Test benutzt bewusst eine ALTE, unveraenderte Komponente.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import Tabs from "../components/Tabs";
import { buttonByText, click, render } from "./harness.mjs";

test("jsdom + JSX-Loader: eine bestehende Komponente rendert und reagiert", async () => {
  let picked = null;
  const view = render(
    React.createElement(Tabs, {
      label: "Data sources",
      tabs: [{ key: "PubChem", label: "PubChem" }, { key: "ChEBI", label: "ChEBI" }],
      value: "PubChem",
      onChange: (t) => {
        picked = t;
      },
    })
  );

  const buttons = [...view.container.querySelectorAll("button")];
  assert.deepEqual(
    buttons.map((b) => b.textContent),
    ["PubChem", "ChEBI"]
  );

  await click(buttonByText(view.container, "ChEBI"));
  assert.equal(picked, "ChEBI");

  view.unmount();
});
