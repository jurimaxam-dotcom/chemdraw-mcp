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
