import React from "react";
import { getSvgTransform, viewBoxToScreen } from "../utils/svgCoords";
import { groupBonds } from "../utils/groupInfo";

// Glow statt Kreisen: die Bindungen der Gruppe leuchten weich in ihrer Farbe.
// Ein Atom ohne Bindungspartner in der Gruppe (z. B. ein einzelnes Halogen)
// bekommt einen weichen Fleck, damit es nicht unsichtbar bleibt.
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

  const bonds = groupBonds(atoms, group.atomIndices);
  const bonded = new Set(bonds.flat().map((a) => a.idx));
  const lone = atoms.filter((a) => group.atomIndices.includes(a.idx) && !bonded.has(a.idx));
  const screen = (a) => viewBoxToScreen(t, a.x, a.y);

  return (
    <svg className="group-glow" aria-hidden="true" style={{ "--group-color": group.color }}>
      {bonds.map(([a, b]) => {
        const p = screen(a);
        const q = screen(b);
        return <line key={`${a.idx}-${b.idx}`} x1={p.x} y1={p.y} x2={q.x} y2={q.y} />;
      })}
      {lone.map((a) => {
        const p = screen(a);
        return <circle key={a.idx} cx={p.x} cy={p.y} r={9} />;
      })}
    </svg>
  );
}
