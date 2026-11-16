import React, { useLayoutEffect, useRef, useState } from "react";
import MoleculeView, { ExpandButton } from "./MoleculeView";
import ContinueRow from "./components/ContinueRow";
import PanelFooter from "./components/PanelFooter";
import { useAppBridge, useHostContext } from "./AppContext";
import { useModelContextReport } from "./ModelContext";
import { batchFollowUps } from "./utils/followUps.js";
import { batchContext, splitBatchFailure } from "./utils/modelContext.js";

// batch_generate (Etappe 2, 16.11.2026): Übersicht als Raster kompakter Karten,
// Klick öffnet die volle Molekül-Ansicht EINES Stoffs. Vorher standen n volle
// Karten untereinander, jede mit Reitern, Weiter-Zeile und Pfaden — schon drei
// Stoffe waren höher als das Fenster.
//
// Immer nur eine View meldet Kontext: die Übersicht, solange nichts offen ist,
// sonst die MoleculeView des geöffneten Stoffs (die Übersicht meldet dann "").
// Die Übersicht wird beim Öffnen abgebaut, nicht versteckt — so kann keine
// verdeckte Karte weitermelden, und der Lernmodus des Details hat keinen
// Nachbarn, der den Namen trägt.
export default function BatchView({ data }) {
  const app = useAppBridge();
  const hostContext = useHostContext();
  const molecules = data.molecules || [];
  const [open, setOpen] = useState(null); // Index des geöffneten Stoffs
  // Rollposition und zuletzt geöffnete Karte: beim Zurückgehen dorthin, wo der
  // Nutzer war. Greift, wo das Panel selbst rollt (feste Höhe: Seitenpanel,
  // Vollbild); im Chat rollt der Host, dort bleibt nur der Fokus.
  const savedScroll = useRef(0);
  const lastOpened = useRef(null);
  const backRef = useRef(null);
  const cardRefs = useRef([]);

  // Render und Meldung aus demselben Wert: ein Index ohne Stoff zeigt (und meldet) die Übersicht.
  const detail = open != null ? molecules[open] || null : null;
  const { flush } = useModelContextReport(detail ? "" : batchContext(data), "");

  function openCard(i) {
    savedScroll.current = currentScroll();
    lastOpened.current = i;
    setOpen(i);
  }

  useLayoutEffect(() => {
    if (open != null) {
      scrollToY(0);
      backRef.current?.focus({ preventScroll: true });
    } else if (lastOpened.current != null) {
      scrollToY(savedScroll.current);
      cardRefs.current[lastOpened.current]?.focus({ preventScroll: true });
    }
  }, [open]);

  if (detail) {
    const mol = detail;
    return (
      <div className="batch-detail">
        <div className="back-bar">
          {/* Kein Stoffname hier: im Lernmodus verriete die Leiste ihn. */}
          <button type="button" ref={backRef} className="candidate-back batch-back" onClick={() => setOpen(null)}>
            <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor"
              strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 6H2M5.5 2.5L2 6l3.5 3.5" /></svg>
            <span>Back to all structures</span>
          </button>
          <span className="batch-position" aria-hidden="true">{open + 1} / {molecules.length}</span>
        </div>
        <MoleculeView key={mol.properties?.smiles || mol.name || open} data={mol} />
      </div>
    );
  }

  const failed = data.failed || [];
  return (
    <article className="batch-panel">
      <header className="panel-header">
        <div className="panel-heading">
          <h2 className="panel-title">{molecules.length} {molecules.length === 1 ? "structure" : "structures"}</h2>
          <p className="panel-subtitle">Open a structure for its data sheet, functional groups and export.</p>
        </div>
        <div className="panel-actions"><ExpandButton app={app} hostContext={hostContext} /></div>
      </header>
      <ul className="batch-grid" aria-label="Structures">
        {molecules.map((mol, i) => {
          const props = mol.properties || {};
          const formula = mol.formula ?? props.formula;
          const mass = molarMass(props.mw);
          const name = mol.name || mol.smiles || props.smiles || "Molecule";
          return (
            <li key={props.smiles || mol.name || i}>
              <button type="button" className="batch-card" ref={(el) => { cardRefs.current[i] = el; }}
                onClick={() => openCard(i)}
                aria-label={[name, formula, mass].filter(Boolean).join(", ")}>
                <span className="batch-card-structure" aria-hidden="true" dangerouslySetInnerHTML={{ __html: mol.svg || "" }} />
                <span className="batch-card-name">{name}</span>
                {(formula || mass) && <span className="batch-card-facts">
                  {formula && <span className="batch-card-formula"><Formula text={formula} /></span>}
                  {mass && <span>{mass}</span>}
                </span>}
              </button>
            </li>
          );
        })}
      </ul>
      <BatchFailedList failed={failed} />
      <ContinueRow actions={batchFollowUps(molecules)} flush={flush} />
      {/* Ein Ordner statt n×2 Pfaden: die Dateien eines Stapels liegen zusammen.
          Jeder Einzelpfad steht in der Fußzeile seiner Detailansicht. */}
      <PanelFooter files={folderEntries(data)} />
    </article>
  );
}

// Fehlschläge unter dem Raster — sonst sieht der Batch vollständig aus, obwohl ein Name fehlt.
function BatchFailedList({ failed }) {
  if (failed.length === 0) return null;
  return (
    <div data-testid="batch-failed" role="status" className="batch-failed">
      <span className="batch-failed-head">Not drawn ({failed.length})</span>
      <ul>
        {failed.map((entry, i) => {
          const { input, reason } = splitBatchFailure(entry);
          return (
            <li key={`${entry}-${i}`}>
              <span className="batch-failed-input">{input}</span>
              {` — ${reason}`}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function dirOf(path) {
  const i = path.lastIndexOf("/");
  return i > 0 ? path.slice(0, i) : path;
}

/** Ordner aller geschriebenen Dateien des Stapels (meist einer), für die Fußzeile. */
export function folderEntries(data) {
  const paths = [];
  for (const m of data.molecules || []) {
    for (const p of Object.values(m.files || {})) if (typeof p === "string" && p) paths.push(p);
  }
  for (const p of data.cdxml_paths || []) if (typeof p === "string" && p) paths.push(p);
  const dirs = [...new Set(paths.map(dirOf))];
  return dirs.map((path) => ({ label: "FOLDER", path }));
}

function currentScroll() {
  try {
    return window.scrollY || document.scrollingElement?.scrollTop || 0;
  } catch {
    return 0;
  }
}

function scrollToY(y) {
  try {
    if (typeof window.scrollTo === "function" && currentScroll() !== y) window.scrollTo(0, y);
  } catch {
    /* Rollen ist Beiwerk */
  }
}

function molarMass(mw) {
  if (mw == null || mw === "") return "";
  return /g\/mol/.test(String(mw)) ? String(mw) : `${mw} g/mol`;
}

function Formula({ text }) {
  return String(text).split(/(\d+)/).map((part, i) =>
    /^\d+$/.test(part) ? <sub key={i}>{part}</sub> : part);
}

