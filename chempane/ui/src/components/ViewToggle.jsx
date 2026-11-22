import React from "react";
import Tabs from "./Tabs";

// Segment-Control „Struktur ⇄ Daten" im Panel-Kopf — seit Etappe 3 eine dünne Hülle
// um das gemeinsame Reiter-Bauteil (Tabs.jsx).
//
// Die Optik steckt in styles.css (.seg), nicht in inline-styles: Fokus-Ring
// (:focus-visible), Spinner-Keyframes und die reduced-motion-Variante lassen
// sich als style-Objekt gar nicht ausdruecken.
//
// `loading` gehoert bewusst nur an den Daten-Knopf — die Gegenrichtung ist
// immer lokal und kann per Definition nicht laden.
//
// `idPrefix` verknuepft Reiter und Ansicht (aria-controls ⇄ aria-labelledby).
// Er kommt von aussen, weil das Panel-Element dem aufrufenden View gehoert —
// und weil ein Dokument mehrere solcher Panels tragen kann,
// muss er pro Panel eindeutig sein (React `useId`).
// `study` (opt-in, U4b): dritter Reiter „Study“ — nur MoleculeView setzt ihn.
export default function ViewToggle({ view, onChange, loading = false, idPrefix, study = false }) {
  const tab = (key, label, extra = {}) => ({
    key, label,
    id: idPrefix ? `${idPrefix}-tab-${key}` : undefined,
    controls: idPrefix ? `${idPrefix}-${key}` : undefined,
    ...extra,
  });
  const tabs = [tab("structure", "Structure"), tab("data", "Data", { busy: loading }), ...(study ? [tab("study", "Study")] : [])];
  return <Tabs label="View" tabs={tabs} value={view} onChange={onChange} />;
}
