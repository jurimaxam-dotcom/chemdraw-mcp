import React, { useId, useState } from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter from "./components/PanelFooter";
import FunctionalGroupList, { GroupNote } from "./components/FunctionalGroupList";
import ContinueRow from "./components/ContinueRow";
import { useModelContextReport } from "./ModelContext";
import { moleculeFollowUps } from "./utils/followUps.js";
import { databaseContext } from "./utils/modelContext.js";
import SourceList from "./components/SourceList";
import StereoNote, { useStereoHighlight } from "./components/StereoNote";
import StructureCanvas from "./components/StructureCanvas";
import ViewToggle from "./components/ViewToggle";

export default function DatabaseView({ data }) {
  const uid = useId();
  const [view, setView] = useState("data");
  // Hover = Vorschau, pinned = festgehaltene Auswahl (U4), wie in MoleculeView.
  const [hoveredGroup, setHoveredGroup] = useState(null);
  const [pinned, setPinned] = useState(null);

  const groups = data.functionalGroups || [];
  const stereoWarnings = data.stereoWarnings || [];
  const stereo = useStereoHighlight(stereoWarnings);
  // Der Weg zur Struktur ist IMMER lokal: Atomliste und Gruppen reisen im
  // Payload mit (DatabasePayload), RDKit hat sie ohnehin gerechnet. Kein
  // Toolaufruf, kein Ladezustand — deshalb hat dieser View auch keinen.
  const hasStructure = Boolean(data.molecule_svg);
  const pinGroup = (name) => setPinned((p) => (p?.kind === "group" && p.name === name ? null : { kind: "group", name }));
  const pickAtom = (atom, group) => (group ? pinGroup(group.name)
    : setPinned((p) => (p?.kind === "atom" && p.idx === atom.idx ? null : { kind: "atom", idx: atom.idx, el: atom.el })));
  const { flush, canContext } = useModelContextReport(
    databaseContext(data, { view: view === "structure" && hasStructure ? "structure" : "data", pinned }),
    data.name || data.smiles || "data sheet",
  );

  return (
    <article className="molecule-panel">
      {(data.name || hasStructure) && (
        <header className="panel-header">
          {data.name ? (
            <SectionHeader title={data.name} subtitle={data.formula} foundAs={data.foundAs} />
          ) : (
            <div />
          )}
          {hasStructure && (
            <div className="panel-actions">
              <ViewToggle view={view} onChange={setView} idPrefix={uid} />
            </div>
          )}
        </header>
      )}

      {view === "structure" && hasStructure ? (
        <div
          id={`${uid}-structure`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-structure`}
          data-view="structure"
          className={groups.length || stereoWarnings.length ? "structure-layout" : "structure-layout structure-only"}
        >
          <StructureCanvas
            svg={data.molecule_svg}
            atoms={data.atoms}
            groups={groups}
            hoveredGroup={hoveredGroup || (pinned?.kind === "group" ? pinned.name : null)}
            pinnedAtom={pinned?.kind === "atom" ? pinned.idx : undefined}
            onHoverGroup={setHoveredGroup}
            onPickAtom={pickAtom}
            highlightAtoms={stereo.highlightAtoms}
            style={groups.length > 0 || stereoWarnings.length > 0 ? undefined : { flex: "1 1 100%" }}
          />
          {(groups.length > 0 || stereoWarnings.length > 0) && (
            <aside className="molecule-info">
              <StereoNote {...stereo.noteProps} />
              {groups.length > 0 && <>
                <h3 className="section-label">Functional groups</h3>
                <FunctionalGroupList
                  groups={groups}
                  pinnedGroup={pinned?.kind === "group" ? pinned.name : null}
                  onHoverGroup={setHoveredGroup}
                  onPin={pinGroup}
                />
                <GroupNote groups={groups} hoveredGroup={hoveredGroup} pinned={pinned}
                  canContext={canContext} onClear={() => setPinned(null)} />
              </>}
            </aside>
          )}
        </div>
      ) : (
        <div
          id={`${uid}-data`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-data`}
          className="data-panel"
          data-view="data"
        >
          <SourceList sources={data.sources} moleculeSvg={data.molecule_svg} />
        </div>
      )}
      {(data.name || data.smiles) && <ContinueRow flush={flush}
        actions={moleculeFollowUps({ name: data.name, smiles: data.smiles, groups, atoms: data.atoms, pinned })} />}
      {/* Keine Dateien: lookup_molecule_data schreibt nichts auf die Platte. */}
      <PanelFooter>
        {data.molecule_svg && <ExportPngButton size="sm" svg={data.molecule_svg} filename={data.name || "molekuel"} />}
      </PanelFooter>
    </article>
  );
}
