import React from "react";
import { getSvgTransform, viewBoxToScreen } from "../utils/svgCoords";

export default function AtomHighlights({
  atoms,
  groups,
  hoveredGroup,
  svgContainerRef,
}) {
  if (!hoveredGroup || !atoms || !groups) return null;

  const group = groups.find((g) => g.name === hoveredGroup);
  if (!group) return null;

  const t = getSvgTransform(svgContainerRef);
  if (!t) return null;

  const highlightAtoms = atoms.filter((a) =>
    group.atomIndices.includes(a.idx)
  );

  return (
    <>
      {highlightAtoms.map((atom) => {
        const pos = viewBoxToScreen(t, atom.x, atom.y);
        return (
          <div
            key={atom.idx}
            style={{
              position: "absolute",
              left: pos.x,
              top: pos.y,
              width: 20,
              height: 20,
              marginLeft: -10,
              marginTop: -10,
              borderRadius: "50%",
              background: `${group.color}30`,
              border: `2px solid ${group.color}`,
              pointerEvents: "none",
              transition: "opacity 0.15s",
            }}
          />
        );
      })}
    </>
  );
}
