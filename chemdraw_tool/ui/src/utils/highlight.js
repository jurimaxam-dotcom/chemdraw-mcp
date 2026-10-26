// Was der Glow ueber der Struktur gerade zeigt: entweder eine explizite
// Atomliste (Stereo-Hinweis) oder die gehoverte funktionelle Gruppe. Eine
// Stelle entscheidet, AtomHighlights zeichnet nur noch {atomIndices, color}.

/** Farbe fuer unbestimmte Stereoelemente — keine der Gruppenfarben. */
export const STEREO_COLOR = "#d6336c";

export function resolveHighlight({ groups, hoveredGroup, atomIndices }) {
  if (atomIndices?.length) return { atomIndices, color: STEREO_COLOR };
  if (!hoveredGroup || !groups) return null;
  const group = groups.find((g) => g.name === hoveredGroup);
  return group ? { atomIndices: group.atomIndices, color: group.color } : null;
}
