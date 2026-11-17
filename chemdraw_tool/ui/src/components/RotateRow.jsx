import React from "react";
import { Button } from "./Panel";

// Zeile direkt unter einem drehbaren 3D-Modell (Etappe 5, 16.11.2026): Bedienhinweis und
// „Reset view“ — im Chat-Einstieg (generate_3d) und hinter dem 3D-Knopf des Molekül-Panels
// an derselben Stelle und mit demselben Namen. Der Knopf enthält bewusst kein SVG: Aufrufer
// suchen das Modell als erstes SVG der Fläche.
// Panel-Umbau A: im Molekül-Panel geht die Zeile in der StageBar auf (Hinweis + Reset rechts über der
// Bühne); RotateRow bleibt für generate_3d (Paket C), der Knopf ist jetzt ein ruhiger .btn.
export default function RotateRow({ hint = "Drag to rotate · explicit hydrogens", onReset }) {
  return (
    <div className="rotate-row">
      <p className="panel-note-quiet">{hint}</p>
      <Button className="reset-view" onClick={onReset} title="Back to the starting rotation">Reset view</Button>
    </div>
  );
}
