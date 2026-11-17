import React from "react";
import { placeholderFromInput } from "../utils/placeholder.js";
import { Panel, PanelHead, PanelState } from "./Panel";

// Ruhiges Skelett zwischen `toolinput` und `toolresult`: was die Argumente
// hergeben (Name, Namensliste), ohne Animation. `cancelled` beendet den
// Ladezustand mit einem Satz.
// Panel-Umbau A (§5.5): derselbe Rahmen wie das fertige Panel — Kopf aus dem toolinput, darunter die
// leere Bühne (bzw. das Kartenraster eines Stapels) mit ruhigem Ladezustand. Die Klassen
// .placeholder-canvas/.placeholder-card bleiben, Tests und host.e2e suchen danach.
export default function ToolPlaceholder({ args, cancelled }) {
  const { title, items } = placeholderFromInput(args);
  if (cancelled) {
    const reason = typeof cancelled.reason === "string" && cancelled.reason.trim() ? ` (${cancelled.reason.trim()})` : "";
    return <Panel kind="placeholder" className="tool-placeholder is-cancelled" role="status" data-testid="tool-placeholder">
      <PanelState kind="empty" className="placeholder-line"
        message={`The request was cancelled${reason}. Nothing was drawn.`} />
    </Panel>;
  }
  return (
    <Panel kind="placeholder" className="tool-placeholder" role="status" aria-busy="true" data-testid="tool-placeholder">
      <PanelHead heading={<>
        {title && <p className="placeholder-title">{title}</p>}
        <p className="placeholder-line panel-subtitle">Preparing the panel…</p>
      </>} />
      {items.length > 0 ? (
        <ul className="placeholder-grid">
          {items.map((item, i) => <li key={`${item}-${i}`} className="placeholder-card">
            <span className="placeholder-box" aria-hidden="true" />
            <span className="placeholder-label">{item}</span>
          </li>)}
        </ul>
      ) : <div className="stage stage-plain placeholder-canvas" aria-hidden="true" />}
    </Panel>
  );
}
