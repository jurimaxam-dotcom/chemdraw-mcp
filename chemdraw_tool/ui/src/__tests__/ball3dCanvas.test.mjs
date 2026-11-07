// Das Molekül füllt die Kuhle: der Maßstab richtet sich nach dem
// Bindungsradius (Abstand vom Ursprung), nicht nach dem größten Achsenwert —
// sonst ragt ein diagonal liegendes Molekül aus der Kuhle, und ein flaches
// verschenkt die halbe Fläche (Jay 07.11.: „3D ist der Hebel — größer“).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import React from "react";

import Ball3DCanvas from "../components/Ball3DCanvas";
import { render } from "./harness.mjs";

function circles(container) {
  return [...container.querySelectorAll("circle[fill^='url(#atom-']")].map((c) => ({
    cx: Number(c.getAttribute("cx")), cy: Number(c.getAttribute("cy")), r: Number(c.getAttribute("r")),
  }));
}

function bowl(container) {
  const svg = container.querySelector("svg");
  const size = Number(svg.getAttribute("viewBox").split(" ")[3]);
  const b = container.querySelector("circle[fill='url(#bowl)']");
  return { size, cx: Number(b.getAttribute("cx")), cy: Number(b.getAttribute("cy")), R: Number(b.getAttribute("r")) };
}

const DIAGONAL = {
  atoms: [{ symbol: "C", x: -2, y: -2, z: -2 }, { symbol: "C", x: 2, y: 2, z: 2 }, { symbol: "O", x: 0, y: 0, z: 0 }],
  bonds: [{ a: 0, b: 2, order: 1 }, { a: 2, b: 1, order: 1 }],
};

test("ein diagonal liegendes Molekül bleibt in jeder Drehlage innerhalb der Kuhle", () => {
  const { container, unmount } = render(React.createElement(Ball3DCanvas, DIAGONAL));
  const { cx, cy, R } = bowl(container);
  for (const c of circles(container)) {
    const d = Math.hypot(c.cx - cx, c.cy - cy) + c.r;
    assert.ok(d <= R, `Atom ragt aus der Kuhle: Abstand+Radius ${d.toFixed(1)} > ${R}`);
  }
  unmount();
});

test("das Molekül nutzt die Kuhle: der äußerste Atomrand liegt nahe am Kuhlenrand", () => {
  const { container, unmount } = render(React.createElement(Ball3DCanvas, DIAGONAL));
  const { cx, cy, R } = bowl(container);
  const outer = Math.max(...circles(container).map((c) => Math.hypot(c.cx - cx, c.cy - cy) + c.r));
  assert.ok(outer >= 0.8 * R, `Molekül füllt die Kuhle nicht: ${outer.toFixed(1)} von ${R}`);
  unmount();
});

// --- E1 (Design-Kritik 07.11., Rang 1 und 2): Kuhle je Theme, Bindungen mit Chemie ---

const draw = (props) => render(React.createElement(Ball3DCanvas, props));
const bondGroups = (container, order) =>
  [...container.querySelectorAll(`g[data-bond-order='${order}']`)];
const linesOf = (g) => [...g.querySelectorAll("line")].map((l) => ({
  el: l.getAttribute("data-element"),
  x1: Number(l.getAttribute("x1")), y1: Number(l.getAttribute("y1")),
  x2: Number(l.getAttribute("x2")), y2: Number(l.getAttribute("y2")),
  w: Number(l.getAttribute("stroke-width")),
  dashed: l.hasAttribute("stroke-dasharray"),
  stroke: l.style.stroke,
}));

// Linien derselben Bindungshälfte: parallel und senkrecht zueinander versetzt.
function assertParallelOffset(lines, n, label) {
  assert.equal(lines.length, n, `${label}: ${n} Linien je Hälfte erwartet, ${lines.length} bekommen`);
  const [a] = lines;
  const dx = a.x2 - a.x1, dy = a.y2 - a.y1, len = Math.hypot(dx, dy);
  for (const l of lines.slice(1)) {
    const cross = (dx * (l.y2 - l.y1) - dy * (l.x2 - l.x1)) / (len * Math.hypot(l.x2 - l.x1, l.y2 - l.y1));
    assert.ok(Math.abs(cross) < 1e-6, `${label}: Linien nicht parallel`);
    const off = Math.abs(dx * (l.y1 - a.y1) - dy * (l.x1 - a.x1)) / len;
    assert.ok(off >= 1.5, `${label}: Linien liegen aufeinander (Versatz ${off.toFixed(2)})`);
  }
}

const FORMALDEHYDE = {
  atoms: [{ symbol: "C", x: -0.6, y: 0, z: 0 }, { symbol: "O", x: 0.6, y: 0, z: 0 }],
  bonds: [{ a: 0, b: 1, order: 2 }],
};

test("Kuhle ohne helles Quadrat: kein fester Hintergrund, kein innerer Rahmen", () => {
  const { container, unmount } = draw(DIAGONAL);
  const svg = container.querySelector("svg");
  assert.equal(svg.style.background, "", "SVG trägt einen festen Hintergrund");
  assert.equal(svg.style.border, "", "SVG trägt einen eigenen Rahmen");
  assert.ok(!container.innerHTML.toLowerCase().includes("#f4f5f8"), "helles Quadrat #f4f5f8 noch da");
  unmount();
});

test("Kuhlenverlauf und Kontaktschatten kommen aus Theme-Variablen", () => {
  const { container, unmount } = draw(DIAGONAL);
  const stops = (id) => [...container.querySelectorAll(`#${id} stop`)].map((s) => s.style.stopColor);
  assert.ok(stops("bowl").length >= 3);
  for (const c of stops("bowl")) assert.match(c, /^var\(--bowl-/, `Kuhlen-Stopp ohne Variable: ${c}`);
  for (const c of stops("contact-shadow")) assert.match(c, /^var\(--bowl-shadow/, `Schatten-Stopp ohne Variable: ${c}`);
  assert.match(container.querySelector("circle[fill='url(#bowl)']").style.stroke, /^var\(--bowl-rim/);
  unmount();
});

test("Kohlenstoff und Wasserstoff färben sich nach dem Theme", () => {
  const { container, unmount } = draw({
    atoms: [{ symbol: "C", x: 0, y: 0, z: 0 }, { symbol: "H", x: 1, y: 0, z: 0 }], bonds: [{ a: 0, b: 1, order: 1 }],
  });
  for (const [el, v] of [["C", "--atom3d-c"], ["H", "--atom3d-h"]]) {
    const stops = [...container.querySelectorAll(`#atom-${el} stop`)].map((s) => s.style.stopColor);
    assert.ok(stops.length >= 3 && stops.every((c) => c.startsWith(`var(${v}`)), `${el}-Kugel ohne Theme-Farbe: ${stops}`);
  }
  unmount();
});

test("styles.css definiert Kuhle und C/H-Farben in Hell und in beiden Dunkel-Blöcken", () => {
  const css = readFileSync(new URL("../styles.css", import.meta.url), "utf8");
  for (const v of ["--bowl-0", "--bowl-1", "--bowl-2", "--bowl-3", "--bowl-rim", "--bowl-shadow", "--atom3d-c", "--atom3d-h"]) {
    const n = css.split(`${v}:`).length - 1;
    assert.ok(n >= 3, `${v} nur ${n}× definiert (:root + zwei Dunkel-Blöcke erwartet)`);
  }
  const rule = css.match(/\.structure-3d\s*\{[^}]*\}/g)?.join(" ") ?? "";
  assert.match(rule, /border:\s*0/, ".structure-3d behält den Rahmen der Zeichenfläche");
});

test("jede Bindungshälfte trägt die Farbe ihres Atoms", () => {
  const { container, unmount } = draw({
    atoms: [{ symbol: "C", x: -0.7, y: 0, z: 0 }, { symbol: "O", x: 0.7, y: 0, z: 0 }], bonds: [{ a: 0, b: 1, order: 1 }],
  });
  const [g] = bondGroups(container, 1);
  assert.ok(g, "keine Gruppe für die Einfachbindung");
  const lines = linesOf(g);
  assert.deepEqual(lines.map((l) => l.el).sort(), ["C", "O"]);
  const c = lines.find((l) => l.el === "C"), o = lines.find((l) => l.el === "O");
  assert.match(c.stroke, /^var\(--atom3d-c/);
  assert.notEqual(o.stroke, c.stroke, "O-Hälfte trägt dieselbe Farbe wie C");
  assert.ok(o.stroke && !o.stroke.includes("5a5a5a"), `O-Hälfte grau: ${o.stroke}`);
  unmount();
});

test("Doppelbindung: zwei parallele Linien je Hälfte (Formaldehyd C=O)", () => {
  const { container, unmount } = draw(FORMALDEHYDE);
  const [g] = bondGroups(container, 2);
  assert.ok(g, "keine Gruppe für die Doppelbindung");
  const lines = linesOf(g);
  assertParallelOffset(lines.filter((l) => l.el === "C"), 2, "C-Hälfte");
  assertParallelOffset(lines.filter((l) => l.el === "O"), 2, "O-Hälfte");
  assert.ok(lines.every((l) => !l.dashed), "Doppelbindung gestrichelt");
  unmount();
});

test("Dreifachbindung: drei parallele Linien je Hälfte (Nitril C#N)", () => {
  const { container, unmount } = draw({
    atoms: [{ symbol: "C", x: -0.6, y: 0, z: 0 }, { symbol: "N", x: 0.6, y: 0, z: 0 }], bonds: [{ a: 0, b: 1, order: 3 }],
  });
  const [g] = bondGroups(container, 3);
  assert.ok(g, "keine Gruppe für die Dreifachbindung");
  assertParallelOffset(linesOf(g).filter((l) => l.el === "N"), 3, "N-Hälfte");
  unmount();
});

const BENZENE = {
  atoms: Array.from({ length: 6 }, (_, i) => ({
    symbol: "C", x: 1.4 * Math.cos((i * Math.PI) / 3), y: 1.4 * Math.sin((i * Math.PI) / 3), z: 0,
  })),
  bonds: Array.from({ length: 6 }, (_, i) => ({ a: i, b: (i + 1) % 6, order: 1.5 })),
};

test("aromatische Bindung (Ordnung 1.5): eine volle und eine gestrichelte Linie", () => {
  const { container, unmount } = draw(BENZENE);
  const groups = bondGroups(container, "aromatic");
  assert.equal(groups.length, 6, "Benzol: sechs aromatische Bindungen erwartet");
  for (const g of groups) {
    const lines = linesOf(g);
    assert.ok(lines.some((l) => l.dashed) && lines.some((l) => !l.dashed), "aromatisch braucht voll + gestrichelt");
    // Beide Hälften sind C — eine Hälfte = Linien, die am selben Atom beginnen.
    const half = lines.filter((l) => Math.hypot(l.x1 - lines[0].x1, l.y1 - lines[0].y1) < 6);
    assertParallelOffset(half, 2, "aromatische Hälfte");
  }
  unmount();
});

test("aromatic-Flag zählt wie Ordnung 1.5", () => {
  const { container, unmount } = draw({ ...BENZENE, bonds: BENZENE.bonds.map((b) => ({ ...b, order: 1, aromatic: true })) });
  assert.equal(bondGroups(container, "aromatic").length, 6);
  unmount();
});

test("Strichstärke nimmt mit der Tiefe ab: vordere Bindung dicker als hintere", () => {
  const { container, unmount } = draw({
    atoms: [
      { symbol: "C", x: -1, y: 0, z: 2 }, { symbol: "C", x: 1, y: 0, z: 2 },
      { symbol: "C", x: -1, y: 0, z: -2 }, { symbol: "C", x: 1, y: 0, z: -2 },
    ],
    bonds: [{ a: 0, b: 1, order: 1 }, { a: 2, b: 3, order: 1 }],
  });
  const groups = bondGroups(container, 1);
  assert.equal(groups.length, 2, "zwei Bindungsgruppen erwartet");
  // Gezeichnet in Tiefenreihenfolge: hinten zuerst, vorn zuletzt.
  const back = linesOf(groups[0])[0].w, front = linesOf(groups[1])[0].w;
  assert.ok(front > back * 1.15, `vorn ${front} nicht deutlich dicker als hinten ${back}`);
  unmount();
});

test("Atomradien folgen den Kovalenzradien: Cl > C > O > H", () => {
  const atoms = ["Cl", "C", "O", "H"].map((symbol) => ({ symbol, x: 0, y: 0, z: 0 }));
  const { container, unmount } = draw({ atoms, bonds: [] });
  const r = (el) => Number(container.querySelector(`circle[fill='url(#atom-${el})']`).getAttribute("r"));
  assert.ok(r("Cl") > r("C") && r("C") > r("O") && r("O") > r("H"),
    `Radien Cl ${r("Cl")}, C ${r("C")}, O ${r("O")}, H ${r("H")}`);
  unmount();
});

test("Kontaktschatten sitzt unter dem tiefsten Atom und bleibt in der Kuhle", () => {
  const { container, unmount } = draw({
    atoms: [{ symbol: "C", x: 0, y: -3, z: 0 }, { symbol: "C", x: 0, y: 3, z: 0 }], bonds: [{ a: 0, b: 1, order: 1 }],
  });
  const { cy, R } = bowl(container);
  const sh = container.querySelector("ellipse[fill='url(#contact-shadow)']");
  const shCy = Number(sh.getAttribute("cy")), shRy = Number(sh.getAttribute("ry"));
  const lowest = Math.max(...circles(container).map((c) => c.cy));
  assert.ok(shCy > lowest, `Schatten (${shCy.toFixed(0)}) liegt über dem tiefsten Atom (${lowest.toFixed(0)})`);
  assert.ok(shCy + shRy <= cy + R, "Schatten ragt aus der Kuhle");
  unmount();
});
