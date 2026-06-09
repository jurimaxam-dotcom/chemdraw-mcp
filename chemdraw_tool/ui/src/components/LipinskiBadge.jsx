import React from "react";

const RULES = [
  { key: "mw", label: "MW", limit: "≤ 500", check: (v) => v != null && v <= 500 },
  { key: "logP", label: "LogP", limit: "≤ 5", check: (v) => v != null && v <= 5 },
  { key: "hbd", label: "HBD", limit: "≤ 5", check: (v) => v != null && v <= 5 },
  { key: "hba", label: "HBA", limit: "≤ 10", check: (v) => v != null && v <= 10 },
];

export default function LipinskiBadge({ lipinski }) {
  if (!lipinski) return null;

  const passColor = "var(--copy-success)";
  const failColor = "#e74c3c";

  return (
    <div>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        marginBottom: 4,
      }}>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          color: lipinski.passes ? passColor : failColor,
        }}>
          {lipinski.passes ? "✓" : "✗"}
        </span>
        <span style={{ fontSize: 10, fontWeight: 600, color: "var(--fg)" }}>
          Lipinski
        </span>
        <span style={{ fontSize: 9, color: "var(--fg-muted)" }}>
          {lipinski.violations === 0
            ? "0 Verletzungen"
            : `${lipinski.violations} Verletzung${lipinski.violations > 1 ? "en" : ""}`}
        </span>
      </div>
      <div style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        {RULES.map(({ key, label, limit, check }) => {
          const val = lipinski[key];
          const ok = check(val);
          return (
            <div
              key={key}
              title={`${label} ${limit}`}
              style={{
                fontSize: 9,
                padding: "1px 5px",
                borderRadius: 4,
                border: `1px solid ${ok ? passColor : failColor}`,
                color: ok ? passColor : failColor,
                background: ok ? "rgba(22,163,74,0.06)" : "rgba(231,76,60,0.06)",
              }}
            >
              {label} {val != null ? (typeof val === "number" && !Number.isInteger(val) ? val.toFixed(1) : val) : "—"}
            </div>
          );
        })}
      </div>
    </div>
  );
}
