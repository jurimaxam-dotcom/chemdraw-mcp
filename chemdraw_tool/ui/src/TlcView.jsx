import React from "react";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import PlotFigure from "./components/PlotFigure";
import { Facts, Panel, PanelFoot, PanelHead, PanelState } from "./components/Panel";
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
    .map((s) => (s.label && !same(s.label, lane.name) ? `${fmtRf(s.rf)} ${String(s.label).trim()}` : fmtRf(s.rf)))
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
  const canExpand = useCanExpand();
  const title = data.name || "TLC plate";
  const subtitle = conditions || "Schematic plate, drawn from the given Rf values";

  if (!data.svg) {
    return (
      <Panel kind="tlc" className="plot-panel">
        <PanelHead title={title} subtitle={subtitle} />
        <PanelState kind="empty" message="No TLC data available." />
      </Panel>
    );
  }

  // Rf-Werte als Kernwert-Zeile (Spezifikation §5.9): Bahn als Etikett, Werte 15/400, keine Mono-Schrift.
  const rf = lanes.map((lane, i) => ({ key: `${i}:${lane.name}`, label: lane.name, value: laneSummary(lane) }));
  return (
    <Panel kind="tlc" fill className="plot-panel">
      <PanelHead title={title} subtitle={subtitle} expand={canExpand ? <ExpandButton /> : null} />
      <PlotFigure svg={data.svg} kind="tlc" />
      <Facts items={rf} className="tlc-rf" />
      <ContinueRow actions={tlcFollowUps(data)} flush={flush} />
      <PanelFoot files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "tlc"} size="sm" />
      </PanelFoot>
    </Panel>
  );
}
