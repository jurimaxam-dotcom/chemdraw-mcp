import React, { useCallback, useId, useRef, useState } from "react";
import PropRow from "./components/PropRow";
import CopyButton from "./components/CopyButton";
import FunctionalGroupList from "./components/FunctionalGroupList";
import LipinskiBadge from "./components/LipinskiBadge";
import ExportPngButton from "./components/ExportPngButton";
import SourceList from "./components/SourceList";
import StructureCanvas from "./components/StructureCanvas";
import ViewToggle from "./components/ViewToggle";
import { useAppBridge } from "./AppContext";
import { extractToolData } from "./utils/toolData";

// Ein ruhiger Satz statt eines Stacktrace: der Klick muss sichtbar landen,
// sonst sieht ein Fehlschlag aus wie ein toter Knopf.
export const DATA_LOAD_ERROR =
  "The data sheet could not be loaded. Click Daten again to retry.";

export default function MoleculeView({ data }) {
  const app = useAppBridge();
  const uid = useId();
  const [hoveredGroup, setHoveredGroup] = useState(null);
  const [view, setView] = useState("structure");
  // Gecachtes DatabasePayload. Nur Erfolge landen hier — ein Fehlschlag bleibt
  // wiederholbar, statt sich als leeres Datenblatt einzubrennen.
  const [sheet, setSheet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const inFlight = useRef(false); // blockiert den re-entranten Doppelklick

  const props = data.properties || {};
  const groups = data.functionalGroups || [];
  const smiles = data.smiles ?? props.smiles;
  // SMILES zuerst: die sind laut Tool-Doku immer aufloesbar, ein Name kann
  // danebengehen.
  const query = smiles || data.name || "";

  const handleView = useCallback(
    async (next) => {
      if (next === "structure") {
        setView("structure");
        return;
      }
      if (sheet) {
        setView("data"); // schon geholt — kein zweiter Netzweg
        return;
      }
      if (inFlight.current) return;
      inFlight.current = true;
      setLoading(true);
      setFailed(false);
      try {
        if (!query) throw new Error("kein Stoff bekannt");
        if (!app?.callServerTool) throw new Error("keine App-Bruecke");
        const result = await app.callServerTool({
          name: "lookup_molecule_data",
          arguments: { name: query },
        });
        // extractToolData deckt beides ab: die harte isError-Flagge des SDK
        // und Claude Desktops gestripptes structuredContent.
        const payload = extractToolData(result);
        if (!payload) throw new Error("kein verwertbares Payload");
        setSheet(payload);
      } catch {
        setFailed(true);
      } finally {
        setLoading(false);
        inFlight.current = false;
        setView("data");
      }
    },
    [app, query, sheet]
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: 360, overflow: "hidden" }}>
      <div
        style={{
          marginBottom: 6,
          flexShrink: 0,
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--fg)" }}>
            {data.name || "Molecule"}
          </div>
          {data.subtitle && (
            <div style={{ fontSize: 10, color: "var(--fg-muted)", marginTop: 1 }}>
              {data.subtitle}
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
          {query && (
            <ViewToggle
              view={view}
              onChange={handleView}
              loading={loading}
              idPrefix={uid}
            />
          )}
          {data.svg && (
            <ExportPngButton svg={data.svg} filename={data.name || "molekuel"} />
          )}
        </div>
      </div>

      {view === "structure" ? (
        <div
          id={`${uid}-structure`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-structure`}
          data-view="structure"
          style={{ display: "flex", gap: 10, flex: 1, minHeight: 0 }}
        >
          <StructureCanvas
            svg={data.svg}
            atoms={data.atoms}
            groups={groups}
            hoveredGroup={hoveredGroup}
            onHoverGroup={setHoveredGroup}
          />

          {/* Panel */}
          <div
            style={{
              flex: "0 0 25%",
              borderLeft: "1px solid var(--border)",
              padding: "4px 8px",
              minWidth: 0,
              minHeight: 0,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {/* Steckbrief */}
            <div>
              <SectionLabel>Steckbrief</SectionLabel>
              <PropRow label="Formula" value={data.formula ?? props.formula} copyable mono={false} />
              <PropRow label="Mass" value={props.mw} copyable={false} mono={false} />
              <PropRow label="CAS" value={props.cas} copyable mono={false} />
            </div>

            {/* Functional groups */}
            {groups.length > 0 && (
              <div>
                <SectionLabel>Functional groups</SectionLabel>
                <FunctionalGroupList
                  groups={groups}
                  hoveredGroup={hoveredGroup}
                  onHoverGroup={setHoveredGroup}
                />
              </div>
            )}

            {/* Lipinski */}
            {data.lipinski && (
              <div>
                <SectionLabel>Rule of Five</SectionLabel>
                <LipinskiBadge lipinski={data.lipinski} />
              </div>
            )}

            {/* SMILES */}
            {smiles && (
              <div style={{
                marginTop: "auto",
                paddingTop: 4,
                borderTop: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}>
                <span style={{
                  fontSize: 9,
                  fontFamily: "var(--font-mono)",
                  color: "var(--fg-muted)",
                  wordBreak: "break-all",
                  flex: 1,
                  lineHeight: 1.3,
                }}>
                  {smiles}
                </span>
                <CopyButton text={smiles} size="sm" />
              </div>
            )}
          </div>
        </div>
      ) : (
        <div
          id={`${uid}-data`}
          role="tabpanel"
          aria-labelledby={`${uid}-tab-data`}
          data-view="data"
          style={{ flex: 1, minHeight: 0, overflowY: "auto" }}
        >
          {sheet ? (
            <SourceList
              sources={sheet.sources}
              moleculeSvg={sheet.molecule_svg || data.svg}
            />
          ) : (
            <Note>{failed ? DATA_LOAD_ERROR : "Loading the data sheet…"}</Note>
          )}
        </div>
      )}
    </div>
  );
}

function Note({ children }) {
  return (
    <div style={{ fontSize: 11, color: "var(--fg-muted)", padding: "8px 2px" }}>
      {children}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 9,
      fontWeight: 600,
      color: "var(--fg-muted)",
      marginBottom: 3,
      letterSpacing: "0.04em",
      textTransform: "uppercase",
    }}>
      {children}
    </div>
  );
}
