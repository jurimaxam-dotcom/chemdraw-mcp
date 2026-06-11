import React from "react";
import SectionHeader from "./components/SectionHeader";

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
    <div style={{ padding: 16 }}>
      <SectionHeader
        title={data.name || `${typeLabel} spectrum`}
        subtitle={`${typeLabel} · schematic, drawn from the given peak list`}
      />
      <div
        className="spectrum-svg"
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          overflow: "hidden",
          padding: 8,
        }}
        dangerouslySetInnerHTML={{ __html: data.svg }}
      />
      {/* matplotlib emits fixed pt dimensions — scale to the panel width */}
      <style>{`.spectrum-svg svg { width: 100%; height: auto; display: block; }`}</style>
      {pngPath && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 8,
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
          }}
        >
          PNG: {pngPath}
        </div>
      )}
    </div>
  );
}
