import React from "react";
import { placeholderFromInput } from "../utils/placeholder.js";

// Ruhiges Skelett zwischen `toolinput` und `toolresult`: was die Argumente
// hergeben (Name, Namensliste), ohne Animation. `cancelled` beendet den
// Ladezustand mit einem Satz.
export default function ToolPlaceholder({ args, cancelled }) {
  const { title, items } = placeholderFromInput(args);
  if (cancelled) {
    const reason = typeof cancelled.reason === "string" && cancelled.reason.trim() ? ` (${cancelled.reason.trim()})` : "";
    return <div className="tool-placeholder is-cancelled" role="status" data-testid="tool-placeholder">
      <p className="placeholder-line">The request was cancelled{reason}. Nothing was drawn.</p>
    </div>;
  }
  return (
    <div className="tool-placeholder" role="status" aria-busy="true" data-testid="tool-placeholder">
      <div className="placeholder-head">
        {title && <p className="placeholder-title">{title}</p>}
        <p className="placeholder-line">Preparing the panel…</p>
      </div>
      {items.length > 0 ? (
        <ul className="placeholder-grid">
          {items.map((item, i) => <li key={`${item}-${i}`} className="placeholder-card">
            <span className="placeholder-box" aria-hidden="true" />
            <span className="placeholder-label">{item}</span>
          </li>)}
        </ul>
      ) : <div className="placeholder-canvas" aria-hidden="true" />}
    </div>
  );
}
