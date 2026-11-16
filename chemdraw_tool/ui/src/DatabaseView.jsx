import React, { useMemo } from "react";
import MoleculeView from "./MoleculeView";
import SectionHeader from "./components/SectionHeader";
import PanelFooter from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import SourceList from "./components/SourceList";
import { useModelContextReport } from "./ModelContext";
import { moleculeFollowUps } from "./utils/followUps.js";
import { databaseContext } from "./utils/modelContext.js";
import { databaseAsMolecule } from "./utils/databaseSheet.js";

// Datenblatt aus lookup_molecule_data (Etappe 3, 16.11.2026): dieselbe Molekül-Ansicht
// wie generate_molecule mit offenem Data-Reiter — gleiche Anordnung (Kernwerte neben,
// Gruppen unter der Zeichnung), gleiche Bedienelemente (Structure/Data/Study, 2D/3D,
// Expand, Export, Anki). Der Weg zur Struktur bleibt lokal: Atomliste und Gruppen
// reisen im Payload mit; das Datenblatt liegt schon vor und wird nicht nachgeladen.
// Study geht ohne Namensleck: im Lernmodus zeigt MoleculeView weder Datenblatt noch
// Dateinamen; Formel, Masse und CAS sind wie dort verdeckt.
export default function DatabaseView({ data }) {
  const molecule = useMemo(() => databaseAsMolecule(data), [data]);
  if (!data.molecule_svg) return <SheetOnly data={data} />;
  return <MoleculeView data={molecule} initialSheet={data} />;
}

// Ohne Strukturbild gibt es nichts umzuschalten: nur das Datenblatt.
function SheetOnly({ data }) {
  const { flush } = useModelContextReport(databaseContext(data, { view: "data" }), data.name || data.smiles || "data sheet");
  return (
    <article className="molecule-panel">
      {data.name && <header className="panel-header"><SectionHeader title={data.name} subtitle={data.formula} foundAs={data.foundAs} /></header>}
      <div className="data-panel" data-view="data">
        <SourceList sources={data.sources} />
      </div>
      {(data.name || data.smiles) && <ContinueRow flush={flush}
        actions={moleculeFollowUps({ name: data.name, smiles: data.smiles, groups: [], atoms: [], pinned: null })} />}
      <PanelFooter />
    </article>
  );
}
