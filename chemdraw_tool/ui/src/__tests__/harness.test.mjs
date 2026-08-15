// Rauchtest der Testumgebung selbst.
//
// Grund: ohne ihn ist ein rot laufender Feature-Test nicht von einem kaputten
// JSX-Loader zu unterscheiden — beides sieht nach "Test schlaegt fehl" aus.
// Dieser Test benutzt bewusst eine ALTE, unveraenderte Komponente.
import assert from "node:assert/strict";
import { test } from "node:test";

import React from "react";

import NavTabs from "../components/NavTabs";
import { buttonByText, click, render } from "./harness.mjs";

test("jsdom + JSX-Loader: eine bestehende Komponente rendert und reagiert", async () => {
  let picked = null;
  const view = render(
    React.createElement(NavTabs, {
      tabs: ["PubChem", "ChEBI"],
      activeTab: "PubChem",
      onTabChange: (t) => {
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
