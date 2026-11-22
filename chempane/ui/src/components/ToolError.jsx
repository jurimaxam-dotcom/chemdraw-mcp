import React from "react";

// Fehlermeldung eines Tools im Panel (Fund b, 09.11.): ohne sie blieb das Panel
// auf „Waiting for data…“ oder auf dem vorigen Ergebnis stehen, als hätte das
// Tool nichts gesagt. Kein eigener Payload-Typ — das Fehler-Ergebnis des SDK
// trägt die Meldung schon (utils/toolData.extractToolError).
// Panel-Umbau A (§5.14): PanelState „error“ — ruhige Fläche, Titel 600, Satz in --text-2, kein Rot.
// Abweichung von §5.14: ohne PanelHead mit Tool-Titel. main.jsx kennt den Toolnamen hier nicht, und
// host.e2e prüft, dass ein Fehler kein .panel-title zeigt (sonst sähe er aus wie ein Ergebnis).
import { PanelState } from "./Panel";

export default function ToolError({ message }) {
  return (
    <article className="panel tool-error" data-panel="error" role="alert" data-testid="tool-error">
      <PanelState kind="error" title="The tool could not produce a result" message={message} />
    </article>
  );
}
