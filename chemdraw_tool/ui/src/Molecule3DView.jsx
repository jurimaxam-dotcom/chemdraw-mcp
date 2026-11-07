import React from "react";
import Ball3DCanvas from "./components/Ball3DCanvas";
import SectionHeader from "./components/SectionHeader";
import { displayPath } from "./utils/displayPath";

// Chat-Einstieg für generate_3d: Kopfzeile + Viewer + SDF-Pfad. Der Viewer
// selbst (Ball3DCanvas) ist derselbe wie hinter dem 3D-Knopf im Molekülpanel.
// Layout-Vertrag: füllt IMMER den Panel-Viewport (100vh, kein Scrollen);
// das Modell skaliert proportional in die verfügbare Fläche.

export default function Molecule3DView({ data }) {
  return (
    <div
      style={{
        height: 500,  // intrinsisch — der Host bemisst das iframe am Inhalt
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader
        title={data.name}
        subtitle="3D conformer (ETKDG + force field) · drag to rotate"
      />
      <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
        <Ball3DCanvas atoms={data.atoms || []} bonds={data.bonds || []} />
      </div>
      {data.files?.sdf && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 8,
            fontFamily: "ui-monospace, monospace",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            flexShrink: 0,
          }}
        >
          SDF: <span title={data.files.sdf}>{displayPath(data.files.sdf)}</span>
        </div>
      )}
    </div>
  );
}
