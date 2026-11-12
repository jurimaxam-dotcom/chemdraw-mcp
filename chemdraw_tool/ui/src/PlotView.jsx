import React from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import { useModelContextReport } from "./ModelContext";
import { plotFollowUps } from "./utils/followUps.js";
import { genericContext } from "./utils/modelContext.js";

export default function PlotView({ data }) {
  const { flush } = useModelContextReport(genericContext("plot", data), data.name || "plot");
  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No diagram data available.
      </div>
    );
  }

  return (
    <div className="plot-panel">
      <SectionHeader title={data.name} subtitle={data.subtitle} />
      <div className="plot-svg" dangerouslySetInnerHTML={{ __html: data.svg }} />
      {data.notes?.length > 0 && (
        <ul
          style={{
            fontSize: 11,
            color: "var(--fg-muted)",
            margin: "8px 0 0",
            paddingLeft: 18,
            lineHeight: 1.45,
          }}
        >
          {data.notes.map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
      )}
      <ContinueRow actions={plotFollowUps(data)} flush={flush} />
      <PanelFooter files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "plot"} size="sm" />
      </PanelFooter>
    </div>
  );
}
