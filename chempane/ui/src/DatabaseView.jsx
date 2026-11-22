import React, { useMemo } from "react";
import MoleculeView from "./MoleculeView";
import ContinueRow from "./components/ContinueRow";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import AddToAnkiButton from "./components/AddToAnkiButton";
import { Panel, PanelBody, PanelFoot, PanelHead } from "./components/Panel";
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

// Ohne Strukturbild gibt es nichts umzuschalten: nur das Datenblatt. Panel-Umbau A (§5.2):
// derselbe Rahmen wie das Molekül-Panel, Untertitel = PubChem-Datensatz statt Formel; ohne
// Datei und ohne Aktion entfällt der Fuß ganz.
function SheetOnly({ data }) {
  const { flush } = useModelContextReport(databaseContext(data, { view: "data" }), data.name || data.smiles || "data sheet");
  const canExpand = useCanExpand();
  const cid = databaseAsMolecule(data).properties.cid;
  return (
    <Panel kind="database" fill className="molecule-panel">
      <PanelHead title={data.name} subtitle={cid ? `PubChem CID ${cid}` : ""} foundAs={data.foundAs}
        expand={canExpand && <ExpandButton />} />
      <PanelBody className="data-panel" data-view="data">
        <SourceList sources={data.sources} />
      </PanelBody>
      {(data.name || data.smiles) && <ContinueRow flush={flush}
        actions={moleculeFollowUps({ name: data.name, smiles: data.smiles, groups: [], atoms: [], pinned: null })} />}
      {/* §5.2: Add to Anki im Fuß wie beim Molekül; Dateien gibt es beim Datenblatt keine. */}
      {data.smiles && <PanelFoot hideFiles>
        <AddToAnkiButton smiles={data.smiles} name={data.name} />
      </PanelFoot>}
    </Panel>
  );
}
