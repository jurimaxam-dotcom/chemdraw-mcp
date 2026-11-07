import React, { useRef } from "react";
import Ball3DCanvas from "./components/Ball3DCanvas";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import { panelBackground, serializeLiveSvg } from "./utils/serializeSvg";

// Chat-Einstieg für generate_3d: Kopfzeile + Viewer + SDF-Pfad. Der Viewer
// selbst (Ball3DCanvas) ist derselbe wie hinter dem 3D-Knopf im Molekülpanel.
// Layout-Vertrag: füllt IMMER den Panel-Viewport (100vh, kein Scrollen);
// das Modell skaliert proportional in die verfügbare Fläche.

export default function Molecule3DView({ data }) {
  const viewer = useRef(null);
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
      <div ref={viewer} style={{ flex: 1, minHeight: 0, display: "flex" }}>
        <Ball3DCanvas atoms={data.atoms || []} bonds={data.bonds || []} />
      </div>
      {/* Fußzeile (E3): SDF links, Export der aktuellen Drehlage rechts. */}
      <PanelFooter files={fileEntries(data.files)}>
        <ExportPngButton size="sm" filename={`${data.name || "molecule"}-3d`}
          getSvg={() => serializeLiveSvg(viewer.current?.querySelector("svg"))}
          background={() => panelBackground(viewer.current)} />
      </PanelFooter>
    </div>
  );
}
