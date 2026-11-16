import React from "react";

// Zeile direkt unter einem drehbaren 3D-Modell (Etappe 5, 16.11.2026): Bedienhinweis und
// „Reset view“ — im Chat-Einstieg (generate_3d) und hinter dem 3D-Knopf des Molekül-Panels
// an derselben Stelle und mit demselben Namen. Der Knopf enthält bewusst kein SVG: Aufrufer
// suchen das Modell als erstes SVG der Fläche.
export default function RotateRow({ hint = "Drag to rotate · explicit hydrogens", onReset }) {
  return (
    <div className="rotate-row">
      <p className="panel-note-quiet">{hint}</p>
      <button type="button" className="reset-view" onClick={onReset} title="Back to the starting rotation">Reset view</button>
    </div>
  );
}
