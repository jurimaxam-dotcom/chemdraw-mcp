import React, { useCallback, useRef, useState } from "react";
import AtomHighlights from "./AtomHighlights";
import AtomTooltip from "./AtomTooltip";
import { resolveHighlight } from "../utils/highlight";
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
  // Explizite Atomliste (Stereo-Hinweis) — schlaegt die gehoverte Gruppe.
  highlightAtoms,
  // Festgehaltenes Einzelatom (Index) und Klick-Rückruf (U4).
  pinnedAtom,
  onPickAtom,
  style,
}) {
  const [hoveredAtom, setHoveredAtom] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const svgContainerRef = useRef(null);

  // Nächstes Atom unter dem Zeiger (15 px Fangradius) — Hover und Klick teilen
  // dieselbe Rechnung; der Klick trifft per eigener Koordinate, nicht über den Hover-Zustand.
  const atomAt = useCallback(
    (clientX, clientY) => {
      if (!atoms || atoms.length === 0) return null;
      const t = getSvgTransform(svgContainerRef);
      if (!t) return null;
      const point = clientToViewBox(t, clientX, clientY);
      let closest = null;
      let closestDist = Infinity;
      for (const atom of atoms) {
        const dist = Math.hypot(atom.x - point.x, atom.y - point.y);
        if (dist < closestDist) {
          closestDist = dist;
          closest = atom;
        }
      }
      return closest && closestDist <= 15 / t.scale ? { atom: closest, t } : null;
    },
    [atoms]
  );

  const handleMouseMove = useCallback(
    (e) => {
      const hit = atomAt(e.clientX, e.clientY);
      if (hit) {
        setHoveredAtom(hit.atom);
        setTooltipPos(viewBoxToScreen(hit.t, hit.atom.x, hit.atom.y));
        if (groups) {
          const group = groups.find((g) => g.atomIndices.includes(hit.atom.idx));
          onHoverGroup?.(group ? group.name : null);
        }
      } else {
        setHoveredAtom(null);
        // Nur die Vorschau: eine festgehaltene Auswahl (pinned) bleibt davon unberührt.
        onHoverGroup?.(null);
      }
    },
    [atomAt, groups, onHoverGroup]
  );

  // U4: Klick auf ein Atom hält seine Gruppe fest (oder das Atom selbst).
  const handleClick = useCallback(
    (e) => {
      if (!onPickAtom) return;
      const hit = atomAt(e.clientX, e.clientY);
      if (!hit) return;
      const group = groups?.find((g) => g.atomIndices.includes(hit.atom.idx));
      onPickAtom(hit.atom, group || null);
    },
    [atomAt, groups, onPickAtom]
  );

  // Bewusst NUR das Atom: die Gruppe kann auch von der Seitenspalte gesetzt
  // sein, und die verlaesst man beim Weg dorthin genau ueber diese Kante.
  const handleMouseLeave = useCallback(() => {
    setHoveredAtom(null);
  }, []);

  return (
    <div
      className="structure-canvas"
      ref={svgContainerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      data-pickable={onPickAtom ? "" : undefined}
      style={{ ...BASE_STYLE, ...style, ...(onPickAtom && hoveredAtom ? { cursor: "pointer" } : null) }}
    >
      {svg ? (
        <div
          className="structure-drawing"
          dangerouslySetInnerHTML={{ __html: svg }}
          style={{
            width: "100%",
            height: "100%",
          }}
        />
      ) : (
        <div style={{ color: "var(--fg-muted)", fontSize: 11 }}>No structure available</div>
      )}
      <AtomHighlights
        atoms={atoms}
        highlight={resolveHighlight({ groups, hoveredGroup, atomIndices: highlightAtoms, pinnedAtom })}
        svgContainerRef={svgContainerRef}
      />
      <AtomTooltip atom={hoveredAtom} position={tooltipPos} />
    </div>
  );
}
