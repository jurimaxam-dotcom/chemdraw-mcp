import React, { useState } from "react";

// Hinweiszeile fuer unbestimmte Stereoelemente. Hover/Fokus/Klick meldet den
// Wunsch nach oben; die Hervorhebung selbst laeuft ueber denselben Glow wie
// die funktionellen Gruppen (StructureCanvas → AtomHighlights).
export function stereoSummary(warnings) {
  const centers = warnings.filter((w) => w.kind === "atom").length;
  const bonds = warnings.filter((w) => w.kind === "double_bond").length;
  const parts = [];
  if (centers) parts.push(`${centers} unspecified stereocenter${centers === 1 ? "" : "s"}`);
  if (bonds) parts.push(`${bonds} unspecified double bond${bonds === 1 ? "" : "s"} (E/Z)`);
  return parts.join(" · ");
}

/** Alle Atome, die markiert werden koennen — leer, wenn die Zeichnung sie nicht zeigt. */
export function stereoAtoms(warnings) {
  return [...new Set((warnings || []).flatMap((w) => w.atoms || []))];
}

/**
 * Zustand fuer Hinweis + Glow: Hover zeigt, Klick haelt fest. Liefert die
 * Props fuer StereoNote und die Atomliste fuer StructureCanvas.
 */
export function useStereoHighlight(warnings) {
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false);
  const active = hovered || pinned;
  return {
    noteProps: { warnings, hovered, pinned, onHover: setHovered, onTogglePin: () => setPinned((p) => !p) },
    highlightAtoms: active ? stereoAtoms(warnings) : [],
  };
}

// onShowVariants kommt nur vom Molekuel-Panel (das Datenblatt gibt keins);
// variantsBusy markiert den laufenden Aufruf.
export default function StereoNote({ warnings, hovered, pinned, onHover, onTogglePin, onShowVariants, variantsBusy }) {
  if (!warnings?.length) return null;
  const text = stereoSummary(warnings);
  const title = "The input does not specify these, so the drawing leaves their configuration open.";
  const note = (
    <div className="stereo-note" data-testid="stereo-note" role="note" title={title}>
      {stereoAtoms(warnings).length > 0 ? (
        <button type="button" className="stereo-note-button" aria-pressed={hovered || pinned}
          onMouseEnter={() => onHover(true)} onMouseLeave={() => onHover(false)}
          onFocus={() => onHover(true)} onBlur={() => onHover(false)}
          onClick={onTogglePin}>
          <span className="stereo-dot" aria-hidden="true" />{text}
        </button>
      ) : (
        <span><span className="stereo-dot" aria-hidden="true" />{text}</span>
      )}
    </div>
  );
  if (!onShowVariants) return note;
  // Neben dem Hinweis, nicht darin: der Hinweistext bleibt, was er war.
  return (
    <div className="stereo-row">
      {note}
      <button type="button" className="chip-toggle" aria-busy={Boolean(variantsBusy)} onClick={onShowVariants}
        title="Draw every stereoisomer and pick one">Show variants</button>
    </div>
  );
}
