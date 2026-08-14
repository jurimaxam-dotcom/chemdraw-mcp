import React from "react";
import SectionHeader from "./components/SectionHeader";

// Rf ist ein Verhältnis — im Protokoll immer zweistellig notiert.
const fmtRf = (rf) => (typeof rf === "number" ? rf.toFixed(2) : String(rf ?? ""));

function laneSummary(lane) {
  const spots = lane.spots || [];
  if (spots.length === 0) return "—";
  return spots
    .map((s) => (s.label ? `${fmtRf(s.rf)} ${s.label}` : fmtRf(s.rf)))
    .join(" · ");
}

export default function TlcView({ data }) {
  const conditions = [
    data.solvent && `Mobile phase: ${data.solvent}`,
    data.detection && `Detection: ${data.detection}`,
  ]
    .filter(Boolean)
    .join(" · ");
  const lanes = data.lanes || [];

  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No TLC data available.
      </div>
    );
  }

  return (
    <div
      style={{
        height: 520, // intrinsisch — der Host bemisst das iframe am Inhalt
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader
        title={data.name || "TLC plate"}
        subtitle={
          conditions || "Schematic plate, drawn from the given Rf values"
        }
      />
      <div
        className="tlc-svg"
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          overflow: "hidden",
          padding: 8,
          flex: 1,
          minHeight: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        dangerouslySetInnerHTML={{ __html: data.svg }}
      />
      {/* matplotlib emits fixed pt dimensions — scale to the panel width */}
      <style>{`.tlc-svg svg { max-width: 100%; max-height: 100%; width: auto; height: auto; display: block; }`}</style>
      {lanes.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "4px 14px",
            marginTop: 8,
            fontSize: 11,
            color: "var(--fg-muted)",
          }}
        >
          {lanes.map((lane, i) => (
            <span key={lane.name || i}>
              <span style={{ color: "var(--fg)", fontWeight: 600 }}>
                {lane.name}
              </span>
              {": "}
              <span style={{ fontFamily: "ui-monospace, monospace" }}>
                {laneSummary(lane)}
              </span>
            </span>
          ))}
        </div>
      )}
      {data.files?.png && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 6,
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
          }}
        >
          PNG: {data.files.png}
        </div>
      )}
    </div>
  );
}
