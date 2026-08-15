import React from "react";

// Segment-Control „Struktur ⇄ Daten" im Panel-Kopf.
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
// und weil `batch_generate` mehrere Molekuel-Panels nebeneinander rendert,
// muss er pro Panel eindeutig sein (React `useId`).
export default function ViewToggle({ view, onChange, loading = false, idPrefix }) {
  const tabId = (name) => (idPrefix ? `${idPrefix}-tab-${name}` : undefined);
  const panelId = (name) => (idPrefix ? `${idPrefix}-${name}` : undefined);

  return (
    <div className="seg" role="tablist" aria-label="Ansicht">
      <button
        type="button"
        role="tab"
        id={tabId("structure")}
        aria-controls={panelId("structure")}
        aria-selected={view === "structure"}
        onClick={() => onChange("structure")}
      >
        Struktur
      </button>
      <button
        type="button"
        role="tab"
        id={tabId("data")}
        aria-controls={panelId("data")}
        aria-selected={view === "data"}
        aria-busy={loading || undefined}
        onClick={() => onChange("data")}
      >
        {loading && <span className="seg-spinner" aria-hidden="true" />}
        Daten
      </button>
    </div>
  );
}
