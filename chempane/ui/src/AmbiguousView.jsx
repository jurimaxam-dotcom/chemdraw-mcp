import React, { useRef, useState } from "react";
import MoleculeView from "./MoleculeView";
import { useAppBridge } from "./AppContext";
import { useModelContextReport } from "./ModelContext";
import { genericContext } from "./utils/modelContext.js";
import { loadToolData } from "./utils/toolData";
import { Button, Hint, Panel, PanelHead } from "./components/Panel";

// Ein ruhiger Satz statt eines Stacktrace — wie beim Daten-Knopf.
export const CANDIDATE_LOAD_ERROR =
  "The structure could not be drawn. Click the candidate again to retry.";

// Familienname („Xylol", „Glucose"): der Server hat bewusst nichts gezeichnet
// und schickt alle Kandidaten mit fertigem SMILES. Der Klick ruft
// generate_molecule mit dem SMILES — der Name selbst waere wieder mehrdeutig.
// Das Ergebnis zeigt diese Ansicht selbst an: ein vom Panel ausgeloester
// Toolaufruf kommt nicht als toolresult-Notification zurueck.
// `subtitle` ersetzt den Satz unter dem Titel — die Stereo-Varianten sind
// keine verschiedenen Verbindungen, sondern Isomere einer. `backBar` ist ein
// Rueckweg des Aufrufers (Stereo-Varianten: „Back to the structure"); er steht
// mit „All candidates" in EINER Leiste statt in zwei Zeilen uebereinander.
export default function AmbiguousView({ data, subtitle, backBar }) {
  const app = useAppBridge();
  const candidates = data.candidates || [];
  const [drawn, setDrawn] = useState(null); // gezeichnetes MoleculePayload
  const [pending, setPending] = useState(""); // Label des laufenden Aufrufs
  const [failed, setFailed] = useState("");
  // Die Auswahl meldet sich selbst; ist ein Kandidat gezeichnet, spricht dessen MoleculeView.
  // Auch unter einer Zurück-Leiste (Stereo-Varianten): die Elternansicht schweigt
  // dort, und ohne eigene Meldung bliebe beim Host ihr letzter Text stehen.
  useModelContextReport(!drawn ? genericContext("ambiguous", data) : "", data.name || "isomers");
  const inFlight = useRef(false); // blockiert den re-entranten Doppelklick

  async function choose(candidate) {
    if (inFlight.current) return;
    inFlight.current = true;
    setPending(candidate.label);
    setFailed("");
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const result = await app.callServerTool({
        name: "generate_molecule",
        arguments: { name_or_smiles: candidate.smiles, label: candidate.label },
      });
      const payload = await loadToolData(app, result);
      if (!payload || payload.type !== "molecule") throw new Error("kein Molekuel-Payload");
      setDrawn(payload);
    } catch {
      setFailed(candidate.label);
    } finally {
      setPending("");
      inFlight.current = false;
    }
  }

  if (drawn) {
    return (
      <div className="ambiguous-chosen">
        <div className="back-bar">
          {backBar}
          <Button icon="chevron-left" className="candidate-back" onClick={() => setDrawn(null)}>
            All candidates
          </Button>
        </div>
        <MoleculeView key={drawn.properties?.smiles || drawn.name} data={drawn} />
      </div>
    );
  }

  // Panel-Umbau A (§5.4): Kopf wie überall, Kandidaten als Karten wie im Stapel (Etikett, Zeichnung,
  // Name), der Ladezustand bzw. Fehler als Hint unter dem Raster.
  return (
    <Panel kind="ambiguous" className="ambiguous-panel">
      {backBar && <div className="back-bar">{backBar}</div>}
      <PanelHead title={data.name}
        subtitle={subtitle || `This name covers ${candidates.length} different compounds. Pick one to draw it.`} />
      <ul className="candidate-grid" aria-label="Candidates">
        {candidates.map((c) => (
          <li key={c.smiles}>
            <button
              type="button"
              className="candidate"
              onClick={() => choose(c)}
              aria-busy={pending === c.label}
              title={c.smiles}
            >
              <span className="candidate-label">{c.label}</span>
              <span className="candidate-structure" dangerouslySetInnerHTML={{ __html: c.svg }} />
              {c.name && c.name !== c.label && <span className="candidate-name">{c.name}</span>}
            </button>
          </li>
        ))}
      </ul>
      {(pending || failed) && (
        <Hint tone={failed && !pending ? "warn" : "quiet"} className="panel-note" role="status">
          {pending ? `Drawing ${pending}…` : CANDIDATE_LOAD_ERROR}
        </Hint>
      )}
    </Panel>
  );
}
