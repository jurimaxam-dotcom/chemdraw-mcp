// Das Molekül füllt die Kuhle: der Maßstab richtet sich nach dem
// Bindungsradius (Abstand vom Ursprung), nicht nach dem größten Achsenwert —
// sonst ragt ein diagonal liegendes Molekül aus der Kuhle, und ein flaches
// verschenkt die halbe Fläche (Jay 07.11.: „3D ist der Hebel — größer“).
import assert from "node:assert/strict";
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
