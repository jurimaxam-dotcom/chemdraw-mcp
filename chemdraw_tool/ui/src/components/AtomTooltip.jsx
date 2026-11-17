import React from "react";

const ELEMENT_NAMES = {
  C: "Carbon",
  O: "Oxygen",
  N: "Nitrogen",
  S: "Sulfur",
  H: "Hydrogen",
  Cl: "Chlorine",
  F: "Fluorine",
  Br: "Bromine",
  P: "Phosphorus",
};

const ELEMENT_COLORS = {
  O: "#ff6b6b",
  N: "#4a9eff",
  S: "#c8c800",
  Cl: "#008000",
  F: "#008000",
  Br: "#8B4513",
  P: "#FFA500",
};

export default function AtomTooltip({ atom, position }) {
  if (!atom) return null;

  const name = ELEMENT_NAMES[atom.el] || atom.el;
  const color = ELEMENT_COLORS[atom.el] || "var(--fg)";

  let chargeStr = "";
  if (atom.charge > 0) chargeStr = `+${atom.charge}`;
  else if (atom.charge < 0) chargeStr = `${atom.charge}`;

  // Panel-Umbau A: Aussehen in frame.css (.atom-tooltip) statt inline; Haarlinie statt Schatten (§3).
  // Die Punktfarbe ist eine Datenfarbe (Element) und bleibt hier. Texte englisch (vorher „H-Atome“, „Ladung“).
  return (
    <div className="atom-tooltip" style={{ left: position.x, top: position.y }}>
      <div className="atom-tooltip-head">
        <span className="atom-tooltip-dot" style={{ background: color }} />
        <span className="atom-tooltip-el">{atom.el}</span>
        <span className="atom-tooltip-name">{name}</span>
      </div>
      {atom.hCount != null && atom.hCount > 0 && <div className="atom-tooltip-line">Hydrogens: {atom.hCount}</div>}
      {chargeStr && <div className="atom-tooltip-line">Charge: {chargeStr}</div>}
    </div>
  );
}
