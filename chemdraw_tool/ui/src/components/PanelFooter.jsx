import React, { createContext, useState } from "react";
import CopyButton from "./CopyButton";
import { displayPath } from "../utils/displayPath";

// Gemeinsame Fußzeile (Design-Kritik 07.11.2026, Abschnitt 4, Rang 4): links die
// Dateien des Ergebnisses — gekürzt, voller Pfad im Tooltip, Kopierknopf —,
// rechts die Aktionen (Export PNG, Add to Anki). Ein Baustein, ein Ort: vorher
// standen Aktionen an drei Stellen und Pfade in vier verschiedenen Formen.
// Ohne Datei und ohne Aktion: keine Fußzeile, auch keine leere.
//
// Rückmeldungen einer Aktion (Export PNG: „Saved: …“) stehen für die Dauer des
// Flashes an der Stelle der Pfade — so wächst die Fußzeile nicht in die Höhe,
// und in den Panels mit fester Höhe wird nichts abgeschnitten.
export const FooterStatus = createContext(null);

const ORDER = ["png", "svg", "cdxml", "sdf", "apkg"];

/** files-Objekt eines Payloads → Zeilen für die Fußzeile, feste Reihenfolge. */
export function fileEntries(files) {
  const entries = Object.entries(files || {}).filter(([, path]) => typeof path === "string" && path);
  const rank = (key) => (ORDER.includes(key) ? ORDER.indexOf(key) : ORDER.length);
  return entries
    .sort(([a], [b]) => rank(a) - rank(b))
    .map(([key, path]) => ({ label: key.toUpperCase(), path }));
}

export default function PanelFooter({ files = [], children }) {
  const [status, setStatus] = useState(null);
  const rows = files.filter((f) => f && f.path);
  const actions = React.Children.toArray(children).filter(Boolean);
  if (rows.length === 0 && actions.length === 0) return null;

  return (
    <footer className="panel-footer" data-testid="panel-footer">
      <div className="panel-footer-files">
        {status ? (
          <span className={`export-feedback${status.kind === "error" ? " is-error" : ""}`} role="status">
            {status.text}
          </span>
        ) : (
          rows.map((f) => (
            <div className="panel-footer-file" key={`${f.label}:${f.path}`}>
              <span className="panel-footer-label">{f.label}</span>
              <span className="panel-footer-path" title={f.path}>{displayPath(f.path)}</span>
              <CopyButton text={f.path} size="xs" label="Copy path" />
            </div>
          ))
        )}
      </div>
      {actions.length > 0 && (
        <FooterStatus.Provider value={setStatus}>
          <div className="panel-footer-actions">{actions}</div>
        </FooterStatus.Provider>
      )}
    </footer>
  );
}
