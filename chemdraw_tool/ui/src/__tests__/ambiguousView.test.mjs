// Mehrdeutiger Name („Xylol"): das Panel zeigt alle Kandidaten, ein Klick
// zeichnet den gewaehlten — ueber generate_molecule mit dessen SMILES, nicht
// noch einmal mit dem Namen (der waere wieder mehrdeutig).
import assert from "node:assert/strict";
import { test } from "node:test";

import React, { act } from "react";

import { AppContext } from "../AppContext";
import AmbiguousView, { CANDIDATE_LOAD_ERROR } from "../AmbiguousView";
import { AMBIGUOUS, MOLECULE, lookupFailure, lookupSuccess } from "./fixtures.mjs";
import { buttonByText, click, render, textOf } from "./harness.mjs";

function setup(respond = () => lookupSuccess(MOLECULE), data = AMBIGUOUS) {
  const calls = [];
  const app = {
    callServerTool: async (req) => {
      calls.push(req);
      return respond(req);
    },
  };
  const view = render(
    React.createElement(
      AppContext.Provider,
      { value: app },
      React.createElement(AmbiguousView, { data })
    )
  );
  const candidate = (label) =>
    [...view.container.querySelectorAll("button.candidate")].find((b) =>
      textOf(b).startsWith(label)
    );
  return { ...view, calls, candidate };
}

test("zeigt jeden Kandidaten mit Vorschaubild, ohne etwas nachzuladen", () => {
  const { container, calls, candidate, unmount } = setup();
  for (const c of AMBIGUOUS.candidates) {
    const button = candidate(c.label);
    assert.ok(button, `Kandidat ${c.label} fehlt`);
    assert.ok(button.querySelector("svg"), `${c.label} ohne Vorschaubild`);
  }
  assert.match(textOf(container), /Xylol/);
  assert.equal(calls.length, 0, "Toolaufruf ohne Klick");
  unmount();
});

test("Klick zeichnet den Kandidaten per SMILES und zeigt das Molekuel-Panel", async () => {
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  const drawn = { ...MOLECULE, name: "m-xylene", properties: { smiles: "Cc1cccc(C)c1" } };
  const { container, calls, candidate, unmount } = setup(async () => {
    await pending;
    return lookupSuccess(drawn);
  });

  await click(candidate("m-xylene"));
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], {
    name: "generate_molecule",
    arguments: { name_or_smiles: "Cc1cccc(C)c1", label: "m-xylene" },
  });
  assert.match(textOf(container), /Drawing m-xylene/);

  // In act() aufloesen — sonst bleibt das Folge-Render ungeflusht und der Test
  // waere gruen, ohne das Molekuel-Panel je gesehen zu haben.
  await act(async () => {
    release();
    await pending;
  });

  assert.ok(container.querySelector("[data-view='structure']"), "kein Molekuel-Panel");
  assert.equal(textOf(container.querySelector(".panel-title")), "m-xylene");
  assert.equal(candidate("o-xylene"), undefined, "Kandidaten haengen noch daneben");

  // Zurueck zur Auswahl ist lokal — kein zweiter Aufruf.
  await click(buttonByText(container, "All candidates"));
  assert.ok(candidate("o-xylene"), "Rueckweg zur Auswahl fehlt");
  assert.equal(calls.length, 1);
  unmount();
});

test("ein Fehlschlag bleibt sichtbar und wiederholbar", async () => {
  let fail = true;
  const { container, calls, candidate, unmount } = setup(() =>
    fail ? lookupFailure() : lookupSuccess(MOLECULE)
  );

  await click(candidate("p-xylene"));
  assert.match(textOf(container), new RegExp(CANDIDATE_LOAD_ERROR.slice(0, 30)));
  assert.ok(candidate("p-xylene"), "Auswahl nach Fehlschlag verschwunden");

  fail = false;
  await click(candidate("p-xylene"));
  assert.equal(calls.length, 2);
  assert.ok(container.querySelector("[data-view='structure']"), "Wiederholung zeichnet nicht");
  unmount();
});

test("ein Doppelklick schickt nur einen Aufruf", async () => {
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  const { calls, candidate, unmount } = setup(async () => {
    await pending;
    return lookupSuccess(MOLECULE);
  });
  await click(candidate("o-xylene"));
  await click(candidate("p-xylene"));
  assert.equal(calls.length, 1, "zweiter Aufruf waehrend der erste laeuft");
  await act(async () => {
    release();
    await pending;
  });
  unmount();
});

test("App leitet type=ambiguous auf die Auswahl", async () => {
  const { default: App } = await import("../App");
  const view = render(
    React.createElement(
      AppContext.Provider,
      { value: { callServerTool: async () => lookupFailure() } },
      React.createElement(App, { data: AMBIGUOUS })
    )
  );
  assert.equal(view.container.querySelectorAll("button.candidate").length, 3);
  view.unmount();
});
