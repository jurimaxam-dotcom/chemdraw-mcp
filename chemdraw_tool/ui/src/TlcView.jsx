import React from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import PlotFigure from "./components/PlotFigure";
import { useModelContextReport } from "./ModelContext";
import { tlcFollowUps } from "./utils/followUps.js";
import { genericContext } from "./utils/modelContext.js";

// Rf ist ein Verhältnis — im Protokoll immer zweistellig notiert.
const fmtRf = (rf) => (typeof rf === "number" ? rf.toFixed(2) : String(rf ?? ""));

// Ein Fleck, der wie seine Bahn heißt („Edukt“ auf der Bahn „Edukt“), braucht den
// Namen nicht noch einmal — sonst „Edukt: 0.30 Edukt“ (Desktop-Befund 14.11.2026).
const same = (a, b) => String(a ?? "").trim().toLowerCase() === String(b ?? "").trim().toLowerCase();

function laneSummary(lane) {
  const spots = lane.spots || [];
  if (spots.length === 0) return "—";
  return spots
    .map((s) => (s.label && !same(s.label, lane.name) ? `${fmtRf(s.rf)} ${s.label}` : fmtRf(s.rf)))
    .join(" · ");
}

export default function TlcView({ data }) {
  const { flush } = useModelContextReport(genericContext("tlc", data), data.name || "tlc");
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
    <div className="plot-panel">
      <SectionHeader
        title={data.name || "TLC plate"}
        subtitle={
          conditions || "Schematic plate, drawn from the given Rf values"
        }
      />
      <PlotFigure svg={data.svg} kind="tlc" />
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
      <ContinueRow actions={tlcFollowUps(data)} flush={flush} />
      <PanelFooter files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "tlc"} size="sm" />
      </PanelFooter>
    </div>
  );
}
