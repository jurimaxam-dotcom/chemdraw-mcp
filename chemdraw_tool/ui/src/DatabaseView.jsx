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
    <div style={{ padding: "8px 0" }}>
      {(data.name || hasStructure) && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          {data.name ? (
            <SectionHeader title={data.name} subtitle={data.formula} />
          ) : (
            <div />
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
            {hasStructure && (
              <ViewToggle view={view} onChange={setView} idPrefix={uid} />
            )}
            {data.molecule_svg && (
              <ExportPngButton svg={data.molecule_svg} filename={data.name || "molekuel"} />
            )}
          </div>
        </div>
      )}

      {view === "structure" && hasStructure ? (
        <div
          id={`${uid}-structure`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-structure`}
          data-view="structure"
          style={{ display: "flex", gap: 10, height: 300, minHeight: 0 }}
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
            <div
              style={{
                flex: "0 0 25%",
                borderLeft: "1px solid var(--border)",
                padding: "4px 8px",
                minWidth: 0,
                minHeight: 0,
                overflowY: "auto",
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 600,
                  color: "var(--fg-muted)",
                  marginBottom: 3,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                }}
              >
                Functional groups
              </div>
              <FunctionalGroupList
                groups={groups}
                hoveredGroup={hoveredGroup}
                onHoverGroup={setHoveredGroup}
              />
            </div>
          )}
        </div>
      ) : (
        <div
          id={`${uid}-data`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-data`}
          data-view="data"
        >
          <SourceList sources={data.sources} moleculeSvg={data.molecule_svg} />
        </div>
      )}
    </div>
  );
}
