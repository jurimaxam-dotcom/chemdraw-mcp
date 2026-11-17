import React from "react";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import PlotFigure from "./components/PlotFigure";
import { Facts, Hint, Panel, PanelFoot, PanelHead, PanelState } from "./components/Panel";
import { useModelContextReport } from "./ModelContext";
import { plotFollowUps } from "./utils/followUps.js";
import { genericContext } from "./utils/modelContext.js";

// Notizen tragen Markdown-Fettdruck (**4.616**) — für Claude und die Exportdatei; das
// Panel setzt ihn als <strong> statt die Sterne zu zeigen (Etappe 5). Nur Paare, ein
// einzelnes Sternchen bleibt Text.
export function noteParts(note) {
  return String(note ?? "").split(/\*\*(.+?)\*\*/g)
    .map((text, i) => (i % 2 ? <strong key={i}>{text}</strong> : text));
}

// „t½ = 6 h · CL = 4.62 L/h“: jedes Stück „Name = Wert“ mit kurzem Namen ist ein Kernwert
// (Spezifikation §5.8: Notizen als Facts-Zeile). Ein Satz („Signal 0.47 → 4.616 (x = …)“,
// „90 % of steady state after …“) bleibt ganz — er wird ein Hinweis, nie halb zerlegt.
const FACT = /^([^=→()]{1,24}?)\s+=\s+(.+)$/;

/** Notizen → { facts: [{label, value}], sentences: [note] } */
export function splitNotes(notes) {
  const facts = [];
  const sentences = [];
  for (const note of notes || []) {
    const pieces = String(note ?? "").split(" · ").map((p) => FACT.exec(p.trim()));
    if (pieces.length > 0 && pieces.every(Boolean)) {
      for (const [, label, value] of pieces) facts.push({ label, value: noteParts(value), key: `${facts.length}:${label}` });
    } else {
      sentences.push(note);
    }
  }
  return { facts, sentences };
}

export default function PlotView({ data }) {
  const { flush } = useModelContextReport(genericContext("plot", data), data.name || "plot");
  const canExpand = useCanExpand();
  if (!data.svg) {
    return (
      <Panel kind="plot" className="plot-panel">
        <PanelHead title={data.name} subtitle={data.subtitle} />
        <PanelState kind="empty" message="No diagram data available." />
      </Panel>
    );
  }

  const { facts, sentences } = splitNotes(data.notes);
  // Jede Zeile unter der Figur (Kalibrierung, PK, Dosis-Wirkung) kostet Höhe — um so viel
  // wird die Figur im Chat flacher (b-graphics.css), damit das Panel in 700 px bleibt.
  const lines = (facts.length ? 1 : 0) + sentences.length;
  return (
    <Panel kind="plot" fill className="plot-panel" style={{ "--plot-notes": lines }}>
      <PanelHead title={data.name} subtitle={data.subtitle} expand={canExpand ? <ExpandButton /> : null} />
      <PlotFigure svg={data.svg} />
      <Facts items={facts} className="plot-notes" />
      {sentences.map((note, i) => <Hint key={i} className="plot-note">{noteParts(note)}</Hint>)}
      <ContinueRow actions={plotFollowUps(data)} flush={flush} />
      <PanelFoot files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "plot"} size="sm" />
      </PanelFoot>
    </Panel>
  );
}
