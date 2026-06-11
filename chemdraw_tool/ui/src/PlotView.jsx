import React from "react";
import SectionHeader from "./components/SectionHeader";

export default function PlotView({ data }) {
  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No diagram data available.
      </div>
    );
  }

  return (
    <div style={{ padding: 16 }}>
      <SectionHeader title={data.name} subtitle={data.subtitle} />
      <div
        className="plot-svg"
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          overflow: "hidden",
          padding: 8,
        }}
        dangerouslySetInnerHTML={{ __html: data.svg }}
      />
      <style>{`.plot-svg svg { width: 100%; height: auto; display: block; }`}</style>
      {data.files?.png && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 8,
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
