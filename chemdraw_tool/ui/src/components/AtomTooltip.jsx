import React from "react";

const ELEMENT_NAMES_DE = {
  C: "Kohlenstoff",
  O: "Sauerstoff",
  N: "Stickstoff",
  S: "Schwefel",
  H: "Wasserstoff",
  Cl: "Chlor",
  F: "Fluor",
  Br: "Brom",
  P: "Phosphor",
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

  const name = ELEMENT_NAMES_DE[atom.el] || atom.el;
  const color = ELEMENT_COLORS[atom.el] || "var(--fg)";

  let chargeStr = "";
  if (atom.charge > 0) chargeStr = `+${atom.charge}`;
  else if (atom.charge < 0) chargeStr = `${atom.charge}`;

  return (
    <div
      style={{
        position: "absolute",
        left: position.x,
        top: position.y,
        transform: "translate(-50%, -100%) translateY(-10px)",
        background: "var(--bg-alt)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
        padding: "6px 10px",
        pointerEvents: "none",
        zIndex: 100,
        minWidth: 90,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--fg)" }}>
          {atom.el}
        </span>
        <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>{name}</span>
      </div>
      {atom.hCount != null && atom.hCount > 0 && (
        <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>
          H-Atome: {atom.hCount}
        </div>
      )}
      {chargeStr && (
        <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>
          Ladung: {chargeStr}
        </div>
      )}
    </div>
  );
}
