import React, { useRef, useState } from "react";
import Ball3DCanvas from "./components/Ball3DCanvas";
import Formula from "./components/Formula";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import { Button, Facts, Panel, PanelFoot, PanelHead, Stage, StageBar } from "./components/Panel";
import { useModelContextReport } from "./ModelContext";
import { genericContext } from "./utils/modelContext.js";
import { panelBackground, serializeLiveSvg } from "./utils/serializeSvg";
import { formulaOfAtoms, massOfAtoms } from "./utils/atoms3d.js";

// Chat-Einstieg für generate_3d (Spezifikation §5.11, Umbau C 17.11.2026): Kopf → StageBar
// (Hinweis, Reset view) → 3D-Bühne in voller Inhaltsbreite → Formel und Molmasse als Kernwerte
// → Fuß (SDF hinter „Files“, Export der aktuellen Drehlage). Der Viewer selbst (Ball3DCanvas)
// ist derselbe wie hinter dem 3D-Knopf im Molekülpanel. Maße: frame.css (.stage-3d) und
// styles/c-protein-3d-anki.css (.m3d-*): im Chat volle Breite × bis 720, in Fill der Rest,
// aber nie höher als breit — der übrige Platz fällt unter den Fuß, nicht neben die Kuhle.

export default function Molecule3DView({ data }) {
  useModelContextReport(genericContext("molecule3d", data), data.name || "molecule3d");
  const viewer = useRef(null);
  const canExpand = useCanExpand();
  // Reset view: neu einhängen stellt die Ausgangsdrehung wieder her (samt Einblend-Drehung).
  const [turn, setTurn] = useState(0);
  // Formel und Molmasse liefert der Server aus dem RDKit-Molekül (Isotope, Ladung). Die Atomliste
  // trägt nur Elementsymbole; aus ihr wird nur noch für alte Ergebnisse ohne diese Felder gerechnet.
  const atoms = data.atoms || [];
  const formula = data.formula || formulaOfAtoms(atoms);
  const mass = typeof data.molar_mass === "number" ? data.molar_mass : massOfAtoms(atoms);
  return (
    <Panel kind="molecule3d" fill className="m3d-panel">
      <PanelHead
        title={data.name}
        subtitle="3D conformer (ETKDG + force field)"
        expand={canExpand ? <ExpandButton /> : null}
      />
      {/* Der Knopf trägt bewusst kein SVG: Aufrufer suchen das Modell als erstes SVG der Bühne. */}
      <StageBar
        hint="Drag to rotate · explicit hydrogens"
        right={<Button className="reset-view" onClick={() => setTurn((t) => t + 1)} title="Back to the starting rotation">Reset view</Button>}
      />
      <Stage variant="3d" ref={viewer} className="m3d-stage">
        <Ball3DCanvas key={turn} atoms={atoms} bonds={data.bonds || []} />
      </Stage>
      <Facts items={[
        { label: "Formula", value: formula ? <Formula text={formula} /> : null },
        { label: "Molar mass", value: mass != null ? `${mass.toFixed(2)} g/mol` : null },
      ]} />
      <PanelFoot files={fileEntries(data.files)}>
        <ExportPngButton size="sm" filename={`${data.name || "molecule"}-3d`}
          getSvg={() => serializeLiveSvg(viewer.current?.querySelector("svg"))}
          background={() => panelBackground(viewer.current)} />
      </PanelFoot>
    </Panel>
  );
}
