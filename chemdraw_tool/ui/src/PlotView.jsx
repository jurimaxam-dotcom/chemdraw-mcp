import React from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import { displayPath } from "./utils/displayPath";

export default function PlotView({ data }) {
  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No diagram data available.
      </div>
    );
  }

  return (
    <div
      style={{
        height: 480,  // intrinsisch — der Host bemisst das iframe am Inhalt
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader title={data.name} subtitle={data.subtitle} />
      <div
        className="plot-svg"
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
      <style>{`.plot-svg svg { max-width: 100%; max-height: 100%; width: auto; height: auto; display: block; }`}</style>
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
      {/* Exportknopf wie im Molekül-Panel (Desktop-Befund 30.10.2026) */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          marginTop: 8,
        }}
      >
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
            minWidth: 0,
          }}
        >
          {data.files?.png && (
            <>
              PNG: <span title={data.files.png}>{displayPath(data.files.png)}</span>
            </>
          )}
        </div>
        <ExportPngButton svg={data.svg} filename={data.name || "plot"} size="sm" />
      </div>
    </div>
  );
}
