import React from "react";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import PlotFigure from "./components/PlotFigure";
import { Panel, PanelFoot, PanelHead, PanelState } from "./components/Panel";
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
  const canExpand = useCanExpand();
  const title = data.name || `${typeLabel} spectrum`;
  const subtitle = `${typeLabel} · schematic, drawn from the given peak list`;

  if (!data.svg) {
    return (
      <Panel kind="spectrum" className="plot-panel">
        <PanelHead title={title} subtitle={subtitle} />
        <PanelState kind="empty" message="No spectrum data available." />
      </Panel>
    );
  }

  return (
    <Panel kind="spectrum" fill className="plot-panel">
      <PanelHead title={title} subtitle={subtitle} expand={canExpand ? <ExpandButton /> : null} />
      <PlotFigure svg={data.svg} kind="spectrum" />
      <ContinueRow actions={spectrumFollowUps(data)} flush={flush} />
      <PanelFoot files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "spectrum"} size="sm" />
      </PanelFoot>
    </Panel>
  );
}
