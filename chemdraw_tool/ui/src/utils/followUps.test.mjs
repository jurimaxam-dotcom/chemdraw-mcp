// Knöpfe „Continue in chat“ (U3): welche Sätze das Panel für Claude schreibt.
// Reine Funktionen — kein DOM, kein React.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  mechanismFor,
  moleculeFollowUps,
  studyFollowUps,
  reactionFollowUps,
  mechanismFollowUps,
  spectrumFollowUps,
  tlcFollowUps,
  plotFollowUps,
  proteinFollowUps,
} from "./followUps.js";

// Atome im Bindungsabstand 10: C0–C1–X2 bzw. C0–C1–O2
const chain = (third, hOfMiddle) => [
  { idx: 0, el: "C", x: 0, y: 0, hCount: 3 },
  { idx: 1, el: "C", x: 10, y: 0, hCount: hOfMiddle },
  { idx: 2, el: third, x: 20, y: 0, hCount: third === "O" ? 1 : 0 },
];

const ASPIRIN_GROUPS = [
  { name: "Ester", atomIndices: [0, 1, 2], count: 1, color: "#d35400" },
  { name: "Carbonsäure", atomIndices: [3, 4, 5], count: 1, color: "#e74c3c" },
  { name: "Aromat", atomIndices: [6, 7, 8, 9, 10, 11], count: 1, color: "#2980b9" },
];

test("Mechanismus: Carbonsäure → Fischer-Veresterung", () => {
  assert.equal(mechanismFor(ASPIRIN_GROUPS, [])?.type, "fischer_ester");
});

test("Mechanismus: primärer/sekundärer Alkohol → Fischer, tertiärer nicht", () => {
  const groups = [{ name: "Hydroxyl", atomIndices: [1, 2], count: 1 }];
  assert.equal(mechanismFor(groups, chain("O", 2))?.type, "fischer_ester");
  assert.equal(mechanismFor(groups, chain("O", 0)), null);
});

test("Mechanismus: Phenol ist kein Alkohol für die Fischer-Veresterung", () => {
  assert.equal(mechanismFor([{ name: "Phenol", atomIndices: [1, 2], count: 1 }], chain("O", 0)), null);
});

test("Mechanismus: Alkylhalogenid → SN2 (C mit H) bzw. SN1 (tertiär)", () => {
  const halide = [{ name: "Halogenid", atomIndices: [1, 2], count: 1 }];
  assert.equal(mechanismFor(halide, chain("Br", 2))?.type, "sn2");
  assert.equal(mechanismFor(halide, chain("Cl", 0))?.type, "sn1");
});

test("Mechanismus: Fluorid und Arylhalogenid kann der Server nicht — kein Knopf", () => {
  const halide = [{ name: "Halogenid", atomIndices: [1, 2], count: 1 }];
  assert.equal(mechanismFor(halide, chain("F", 2)), null);
  const aryl = [...halide, { name: "Aromat", atomIndices: [0, 1], count: 1 }];
  assert.equal(mechanismFor(aryl, chain("Cl", 0)), null);
});

test("Mechanismus: ohne passende Gruppe kein Knopf", () => {
  assert.equal(mechanismFor([{ name: "Keton", atomIndices: [0, 1, 2], count: 1 }], chain("O", 0)), null);
  assert.equal(mechanismFor([], []), null);
});

test("Molekül ohne Auswahl: Struktur erklären, Mechanismus, IR, Vergleich, Quiz", () => {
  const actions = moleculeFollowUps({ name: "Aspirin", smiles: "CC(=O)Oc1ccccc1C(=O)O", groups: ASPIRIN_GROUPS, atoms: [] });
  assert.deepEqual(actions.map((a) => a.label), [
    "Explain the structure",
    "Fischer esterification mechanism",
    "Predict the IR bands",
    "Compare with a related compound",
    "Quiz me on Aspirin",
  ]);
  for (const a of actions) {
    assert.match(a.text, /Aspirin/, `Satz nennt den Stoff nicht: ${a.text}`);
    assert.match(a.text, /^[A-Z].*[.?]$/, `kein vollständiger Satz: ${a.text}`);
  }
  assert.match(actions[2].text, /IR/);
});

test("Molekül mit festgehaltener Gruppe: zwei Knöpfe zur Gruppe vorn, mit Gruppenfarbe", () => {
  const actions = moleculeFollowUps({
    name: "Aspirin", smiles: "x", groups: ASPIRIN_GROUPS, atoms: [], pinned: { kind: "group", name: "Ester" },
  });
  assert.equal(actions[0].label, "Explain this ester");
  assert.equal(actions[1].label, "Reactions of this group");
  assert.equal(actions[0].color, "#d35400");
  assert.match(actions[0].text, /ester group in Aspirin/);
  assert.match(actions[1].text, /reactions of the ester group in Aspirin/);
  assert.ok(!actions.some((a) => a.label === "Explain the structure"));
  assert.ok(actions.length <= 5);
});

test("Ohne Namen nennt der Satz das SMILES; langer Name nicht im Knopf", () => {
  const smiles = "CN1CCC23C4C1CC5=C2C(=C(C=C5)O)OC3C(C=C4)O";
  const actions = moleculeFollowUps({ name: "", smiles, groups: [], atoms: [] });
  assert.ok(actions.every((a) => a.text.includes(smiles)));
  assert.equal(actions.at(-1).label, "Quiz me on this compound");
});

test("Lernmodus: Sätze nennen das SMILES statt des verdeckten Namens", () => {
  const actions = studyFollowUps({ name: "Aspirin", smiles: "CC(=O)Oc1ccccc1C(=O)O", nameRevealed: false });
  assert.deepEqual(actions.map((a) => a.label), ["Give me a hint", "Quiz me on this compound", "Next: a similar compound"]);
  for (const a of actions) {
    assert.doesNotMatch(a.text, /Aspirin/i, `Satz verrät den Namen: ${a.text}`);
    assert.match(a.text, /CC\(=O\)Oc1ccccc1C\(=O\)O/);
    assert.match(a.text, /don't|do not/i, "Bitte, nichts vorwegzunehmen, fehlt");
  }
  const open = studyFollowUps({ name: "Aspirin", smiles: "x", nameRevealed: true });
  assert.match(open[0].text, /Aspirin/);
});

test("Reaktion: Mechanismus nur, wenn er aus dem Namen ableitbar ist", () => {
  const fischer = {
    name: "Fischer esterification",
    reactants: [{ name: "acetic acid" }, { name: "ethanol" }],
    products: [{ name: "ethyl acetate" }, { name: "water" }],
    conditions: "H2SO4",
  };
  const a = reactionFollowUps(fischer);
  assert.deepEqual(a.map((x) => x.label), ["Show the mechanism", "Explain this reaction"]);
  assert.match(a[0].text, /Fischer esterification mechanism for acetic acid and ethanol/);
  assert.match(a[1].text, /acetic acid \+ ethanol → ethyl acetate \+ water/);
  const plain = reactionFollowUps({ name: "", reactants: [{ name: "" }], products: [{ name: "" }], request: { reactants: ["CCO"], products: ["CC=O"] } });
  assert.deepEqual(plain.map((x) => x.label), ["Explain this reaction"]);
  assert.match(plain[0].text, /CCO → CC=O/);
});

test("Mechanismus: aktueller Schritt bzw. Übersicht, dazu Quiz", () => {
  const data = { name: "SN2: 2-bromobutane + cyanide", steps: [{ label: "Start" }, { label: "Transition state" }, { label: "Product" }] };
  const step = mechanismFollowUps(data, { mode: "step", step: 1 });
  assert.equal(step[0].label, "Explain this step");
  assert.match(step[0].text, /step 2 of 3/);
  assert.match(step[0].text, /Transition state/);
  assert.equal(step[1].label, "Quiz me on this mechanism");
  const overview = mechanismFollowUps(data, { mode: "overview", step: 0 });
  assert.equal(overview[0].label, "Explain this mechanism");
});

test("Spektrum, DC, Diagramm, Protein: je ein schlichter Knopf", () => {
  assert.match(spectrumFollowUps({ spectrum_type: "IR", name: "Aspirin" })[0].text, /IR spectrum of Aspirin/);
  assert.match(tlcFollowUps({ name: "Reaction control", lanes: [{ name: "SM" }, { name: "P" }] })[0].text, /TLC/);
  assert.match(plotFollowUps({ name: "Titration of acetic acid" })[0].text, /Titration of acetic acid/);
  assert.match(proteinFollowUps({ name: "Trastuzumab" })[0].text, /Trastuzumab/);
  assert.deepEqual(proteinFollowUps({ name: "" }), []);
});
