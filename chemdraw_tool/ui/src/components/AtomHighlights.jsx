import React from "react";
import { getSvgTransform, viewBoxToScreen } from "../utils/svgCoords";
import { groupBonds } from "../utils/groupInfo";

// Glow statt Kreisen: die Bindungen zwischen den markierten Atomen leuchten
// weich in ihrer Farbe. Ein Atom ohne markierten Bindungspartner (ein
// einzelnes Halogen, ein Stereozentrum) bekommt einen weichen Fleck, damit es
// nicht unsichtbar bleibt. Was markiert ist, entscheidet resolveHighlight.
export default function AtomHighlights({ atoms, highlight, svgContainerRef }) {
  if (!highlight || !atoms?.length || !highlight.atomIndices?.length) return null;

  const t = getSvgTransform(svgContainerRef);
  if (!t) return null;

  const { atomIndices, color } = highlight;
  const bonds = groupBonds(atoms, atomIndices);
  const bonded = new Set(bonds.flat().map((a) => a.idx));
  const lone = atoms.filter((a) => atomIndices.includes(a.idx) && !bonded.has(a.idx));
  const screen = (a) => viewBoxToScreen(t, a.x, a.y);

  return (
    <svg className="group-glow" aria-hidden="true" style={{ "--group-color": color }}>
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
