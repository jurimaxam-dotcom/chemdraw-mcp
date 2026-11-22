// Was der Glow ueber der Struktur gerade zeigt: eine explizite Atomliste
// (Stereo-Hinweis), die angezeigte Gruppe (Hover-Vorschau, sonst die
// festgehaltene) oder ein festgehaltenes Atom ohne Gruppe (U4). Eine Stelle
// entscheidet, AtomHighlights zeichnet nur noch {atomIndices, color}.

/** Farbe fuer unbestimmte Stereoelemente — keine der Gruppenfarben. */
export const STEREO_COLOR = "#d6336c";
/** Festgehaltenes Einzelatom: Akzent des Panels (Theme-Variable). */
export const PIN_COLOR = "var(--accent)";

export function resolveHighlight({ groups, hoveredGroup, atomIndices, pinnedAtom }) {
  if (atomIndices?.length) return { atomIndices, color: STEREO_COLOR };
  const group = hoveredGroup && groups ? groups.find((g) => g.name === hoveredGroup) : null;
  if (group) return { atomIndices: group.atomIndices, color: group.color };
  if (Number.isInteger(pinnedAtom)) return { atomIndices: [pinnedAtom], color: PIN_COLOR };
  return null;
}
