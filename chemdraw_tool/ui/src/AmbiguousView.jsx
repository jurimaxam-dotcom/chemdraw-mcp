import React, { useRef, useState } from "react";
import MoleculeView from "./MoleculeView";
import { useAppBridge } from "./AppContext";
import { extractToolData } from "./utils/toolData";

// Ein ruhiger Satz statt eines Stacktrace — wie beim Daten-Knopf.
export const CANDIDATE_LOAD_ERROR =
  "The structure could not be drawn. Click the candidate again to retry.";

// Familienname („Xylol", „Glucose"): der Server hat bewusst nichts gezeichnet
// und schickt alle Kandidaten mit fertigem SMILES. Der Klick ruft
// generate_molecule mit dem SMILES — der Name selbst waere wieder mehrdeutig.
// Das Ergebnis zeigt diese Ansicht selbst an: ein vom Panel ausgeloester
// Toolaufruf kommt nicht als toolresult-Notification zurueck.
export default function AmbiguousView({ data }) {
  const app = useAppBridge();
  const candidates = data.candidates || [];
  const [drawn, setDrawn] = useState(null); // gezeichnetes MoleculePayload
  const [pending, setPending] = useState(""); // Label des laufenden Aufrufs
  const [failed, setFailed] = useState("");
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
      const payload = extractToolData(result);
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
        <button type="button" className="candidate-back" onClick={() => setDrawn(null)}>
          All candidates
        </button>
        <MoleculeView key={drawn.properties?.smiles || drawn.name} data={drawn} />
      </div>
    );
  }

  return (
    <article className="ambiguous-panel">
      <header className="panel-header">
        <div className="panel-heading">
          <h2 className="panel-title">{data.name}</h2>
          <p className="panel-subtitle">
            This name covers {candidates.length} different compounds. Pick one to draw it.
          </p>
        </div>
      </header>
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
        <div className="panel-note" role="status">
          {pending ? `Drawing ${pending}…` : CANDIDATE_LOAD_ERROR}
        </div>
      )}
    </article>
  );
}
