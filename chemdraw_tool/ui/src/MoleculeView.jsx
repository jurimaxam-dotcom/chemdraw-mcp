import React, { useState, useRef, useCallback } from "react";
import PropRow from "./components/PropRow";
import CopyButton from "./components/CopyButton";
import AtomTooltip from "./components/AtomTooltip";
import AtomHighlights from "./components/AtomHighlights";
import FunctionalGroupList from "./components/FunctionalGroupList";
import LipinskiBadge from "./components/LipinskiBadge";
import ExportPngButton from "./components/ExportPngButton";
import { getSvgTransform, viewBoxToScreen, clientToViewBox } from "./utils/svgCoords";

export default function MoleculeView({ data }) {
  const [hoveredAtom, setHoveredAtom] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [hoveredGroup, setHoveredGroup] = useState(null);
  const svgContainerRef = useRef(null);

  const handleMouseMove = useCallback(
    (e) => {
      if (!data.atoms || data.atoms.length === 0) return;
      const t = getSvgTransform(svgContainerRef);
      if (!t) return;

      const svg = clientToViewBox(t, e.clientX, e.clientY);

      let closest = null;
      let closestDist = Infinity;
      const THRESHOLD_SVG = 15 / t.scale;

      for (const atom of data.atoms) {
        const dx = atom.x - svg.x;
        const dy = atom.y - svg.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < closestDist) {
          closestDist = dist;
          closest = atom;
        }
      }

      if (closest && closestDist <= THRESHOLD_SVG) {
        const screen = viewBoxToScreen(t, closest.x, closest.y);
        setHoveredAtom(closest);
        setTooltipPos(screen);

        if (data.functionalGroups) {
          const group = data.functionalGroups.find((g) =>
            g.atomIndices.includes(closest.idx)
          );
          setHoveredGroup(group ? group.name : null);
        }
      } else {
        setHoveredAtom(null);
        setHoveredGroup(null);
      }
    },
    [data.atoms, data.functionalGroups]
  );

  const handleMouseLeave = useCallback(() => {
    setHoveredAtom(null);
  }, []);

  const props = data.properties || {};
  const groups = data.functionalGroups || [];
  const smiles = data.smiles ?? props.smiles;

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
        {data.svg && (
          <ExportPngButton svg={data.svg} filename={data.name || "molekuel"} />
        )}
      </div>

      <div style={{ display: "flex", gap: 10, flex: 1, minHeight: 0 }}>
        {/* SVG */}
        <div
          ref={svgContainerRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            position: "relative",
            flex: "1 1 70%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: 4,
            minWidth: 0,
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          {data.svg ? (
            <div
              dangerouslySetInnerHTML={{ __html: data.svg }}
              style={{
                width: "100%",
                height: "100%",
              }}
            />
          ) : (
            <div style={{ color: "var(--fg-muted)", fontSize: 11 }}>
              Kein SVG
            </div>
          )}
          <AtomHighlights
            atoms={data.atoms}
            groups={groups}
            hoveredGroup={hoveredGroup}
            svgContainerRef={svgContainerRef}
          />
          <AtomTooltip atom={hoveredAtom} position={tooltipPos} />
        </div>

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
