import React from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import PlotFigure from "./components/PlotFigure";
import { useModelContextReport } from "./ModelContext";
import { spectrumFollowUps } from "./utils/followUps.js";
import { genericContext } from "./utils/modelContext.js";

const TYPE_LABELS = {
  ir: "IR",
  nir: "NIR",
  raman: "Raman",
  uv_vis: "UV/Vis",
  fluorescence: "Fluorescence",
  ord: "ORD",
  cd: "CD",
  nmr_1h: "¹H NMR",
  nmr_13c: "¹³C NMR",
  ms: "MS",
};

export default function SpectrumView({ data }) {
  const { flush } = useModelContextReport(genericContext("spectrum", data), data.name || "spectrum");
  const typeLabel = TYPE_LABELS[data.spectrum_type] || data.spectrum_type;
  const pngPath = data.files?.png;

  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No spectrum data available.
      </div>
    );
  }

  return (
    <div className="plot-panel">
      <SectionHeader
        title={data.name || `${typeLabel} spectrum`}
        subtitle={`${typeLabel} · schematic, drawn from the given peak list`}
      />
      <PlotFigure svg={data.svg} kind="spectrum" />
      <ContinueRow actions={spectrumFollowUps(data)} flush={flush} />
      <PanelFooter files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "spectrum"} size="sm" />
      </PanelFooter>
    </div>
  );
}
