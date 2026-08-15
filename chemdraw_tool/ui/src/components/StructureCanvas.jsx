import React, { useCallback, useRef, useState } from "react";
import AtomHighlights from "./AtomHighlights";
import AtomTooltip from "./AtomTooltip";
import { clientToViewBox, getSvgTransform, viewBoxToScreen } from "../utils/svgCoords";

// Die Struktur mit Atom-Hover — aus MoleculeView herausgeloest, damit das
// Datenblatt-Panel dieselbe Flaeche zeigen kann statt einer zweiten Kopie.
//
// Aufgeteilt wird nach Besitz des Zustands: `hoveredAtom`/`tooltipPos` sieht
// nur diese Komponente, `hoveredGroup` teilt sie sich mit der Gruppenliste in
// der Seitenspalte — deshalb kommt der von aussen (kontrolliert).
const BASE_STYLE = {
  position: "relative",
  flex: "1 1 70%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  padding: 4,
  minWidth: 0,
  minHeight: 0,
  overflow: "hidden",
};

export default function StructureCanvas({
  svg,
  atoms,
  groups,
  hoveredGroup,
  onHoverGroup,
  style,
}) {
  const [hoveredAtom, setHoveredAtom] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const svgContainerRef = useRef(null);

  const handleMouseMove = useCallback(
    (e) => {
      if (!atoms || atoms.length === 0) return;
      const t = getSvgTransform(svgContainerRef);
      if (!t) return;

      const point = clientToViewBox(t, e.clientX, e.clientY);

      let closest = null;
      let closestDist = Infinity;
      const THRESHOLD_SVG = 15 / t.scale;

      for (const atom of atoms) {
        const dx = atom.x - point.x;
        const dy = atom.y - point.y;
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

        if (groups) {
          const group = groups.find((g) => g.atomIndices.includes(closest.idx));
          onHoverGroup?.(group ? group.name : null);
        }
      } else {
        setHoveredAtom(null);
        onHoverGroup?.(null);
      }
    },
    [atoms, groups, onHoverGroup]
  );

  // Bewusst NUR das Atom: die Gruppe kann auch von der Seitenspalte gesetzt
  // sein, und die verlaesst man beim Weg dorthin genau ueber diese Kante.
  const handleMouseLeave = useCallback(() => {
    setHoveredAtom(null);
  }, []);

  return (
    <div
      ref={svgContainerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style ? { ...BASE_STYLE, ...style } : BASE_STYLE}
    >
      {svg ? (
        <div
          dangerouslySetInnerHTML={{ __html: svg }}
          style={{
            width: "100%",
            height: "100%",
          }}
        />
      ) : (
        <div style={{ color: "var(--fg-muted)", fontSize: 11 }}>Kein SVG</div>
      )}
      <AtomHighlights
        atoms={atoms}
        groups={groups}
        hoveredGroup={hoveredGroup}
        svgContainerRef={svgContainerRef}
      />
      <AtomTooltip atom={hoveredAtom} position={tooltipPos} />
    </div>
  );
}
