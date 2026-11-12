import React, { useRef } from "react";
import Ball3DCanvas from "./components/Ball3DCanvas";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import { useModelContextReport } from "./ModelContext";
import { genericContext } from "./utils/modelContext.js";
import { panelBackground, serializeLiveSvg } from "./utils/serializeSvg";

// Chat-Einstieg für generate_3d: Kopfzeile + Viewer + SDF-Pfad. Der Viewer
// selbst (Ball3DCanvas) ist derselbe wie hinter dem 3D-Knopf im Molekülpanel.
// Layout-Vertrag: füllt IMMER den Panel-Viewport (100vh, kein Scrollen);
// das Modell skaliert proportional in die verfügbare Fläche.

export default function Molecule3DView({ data }) {
  useModelContextReport(genericContext("molecule3d", data), data.name || "molecule3d");
  const viewer = useRef(null);
  return (
    <div
      className="m3d-panel"
      style={{
        // Höhe 500 px steht in styles.css (.m3d-panel): intrinsisch — der Host
        // bemisst das iframe am Inhalt; bei gemeldeter fester Höhe füllt sie den Bereich.
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
