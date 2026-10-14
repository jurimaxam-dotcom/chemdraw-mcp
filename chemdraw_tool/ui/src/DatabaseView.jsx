import React, { useId, useState } from "react";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import FunctionalGroupList from "./components/FunctionalGroupList";
import SourceList from "./components/SourceList";
import StructureCanvas from "./components/StructureCanvas";
import ViewToggle from "./components/ViewToggle";

export default function DatabaseView({ data }) {
  const uid = useId();
  const [view, setView] = useState("data");
  const [hoveredGroup, setHoveredGroup] = useState(null);

  const groups = data.functionalGroups || [];
  // Der Weg zur Struktur ist IMMER lokal: Atomliste und Gruppen reisen im
  // Payload mit (DatabasePayload), RDKit hat sie ohnehin gerechnet. Kein
  // Toolaufruf, kein Ladezustand — deshalb hat dieser View auch keinen.
  const hasStructure = Boolean(data.molecule_svg);

  return (
    <article className="molecule-panel">
      {(data.name || hasStructure) && (
        <header className="panel-header">
          {data.name ? (
            <SectionHeader title={data.name} subtitle={data.formula} />
          ) : (
            <div />
          )}
          <div className="panel-actions">
            {hasStructure && (
              <ViewToggle view={view} onChange={setView} idPrefix={uid} />
            )}
            {data.molecule_svg && (
              <ExportPngButton svg={data.molecule_svg} filename={data.name || "molekuel"} />
            )}
          </div>
        </header>
      )}

      {view === "structure" && hasStructure ? (
        <div
          id={`${uid}-structure`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-structure`}
          data-view="structure"
          className={groups.length ? "structure-layout" : "structure-layout structure-only"}
        >
          <StructureCanvas
            svg={data.molecule_svg}
            atoms={data.atoms}
            groups={groups}
            hoveredGroup={hoveredGroup}
            onHoverGroup={setHoveredGroup}
            style={groups.length > 0 ? undefined : { flex: "1 1 100%" }}
          />
          {groups.length > 0 && (
            <aside className="molecule-info">
              <h3 className="section-label">Functional groups</h3>
              <FunctionalGroupList
                groups={groups}
                hoveredGroup={hoveredGroup}
                onHoverGroup={setHoveredGroup}
              />
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
    </article>
  );
}
