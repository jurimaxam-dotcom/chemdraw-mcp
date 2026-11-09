import React from "react";

// Fehlermeldung eines Tools im Panel (Fund b, 09.11.): ohne sie blieb das Panel
// auf „Waiting for data…“ oder auf dem vorigen Ergebnis stehen, als hätte das
// Tool nichts gesagt. Kein eigener Payload-Typ — das Fehler-Ergebnis des SDK
// trägt die Meldung schon (utils/toolData.extractToolError).
export default function ToolError({ message }) {
  return (
    <div className="tool-error" role="alert" data-testid="tool-error">
      <div className="tool-error-title">The tool could not produce a result</div>
      <p className="tool-error-message">{message}</p>
    </div>
  );
}
