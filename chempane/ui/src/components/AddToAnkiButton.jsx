import React, { useEffect, useRef, useState } from "react";
import { useAppBridge } from "../AppContext";
import { loadToolData } from "../utils/toolData";
import { Icon } from "./Panel";

// Fester Deckname: gleicher Name aktualisiert statt dupliziert (GUID = Deck +
// Vorderseite), so sammeln sich alle Klicks in einem Anki-Deck.
export const ANKI_DECK = "ChemDraw";

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Rückseite als Anki-HTML nach dem Design-Entwurf: Name, Formel mit
// tiefgestellten Zahlen, graue CAS-Zeile; die Klassen gestaltet das Karten-CSS
// in anki_export.py. Anki-Felder werden nicht escaped, also hier selbst escapen.
function backText(name, formula, cas) {
  const parts = [`<div class='name'>${escapeHtml(name || "Molecule")}</div>`];
  if (formula) parts.push(`<div class='formula'>${escapeHtml(formula).replace(/(\d+)/g, "<sub>$1</sub>")}</div>`);
  if (cas) parts.push(`<div class='meta'>CAS ${escapeHtml(cas)}</div>`);
  return parts.join("");
}

// idle → busy (deaktiviert) → (added | saved | error); Erfolg blinkt kurz,
// ein Fehler bleibt stehen, bis der nächste Klick ihn neu versucht.
export default function AddToAnkiButton({ smiles, name, formula, cas, size }) {
  const app = useAppBridge();
  const [status, setStatus] = useState("idle");
  const [file, setFile] = useState("");
  const timeoutRef = useRef(null);
  const busyRef = useRef(false); // blockiert den re-entranten Doppelklick
  const busy = status === "busy";
  const ok = status === "added" || status === "saved";

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  async function handleAdd() {
    if (!smiles || busyRef.current) return;
    busyRef.current = true;
    clearTimeout(timeoutRef.current);
    setStatus("busy");
    let next = "error";
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const result = await app.callServerTool({
        name: "export_anki_deck",
        arguments: {
          deck_name: ANKI_DECK,
          // SMILES statt Name: kein Netz nötig, und die Karte hängt am Molekül.
          cards: [{ front: { structure: smiles }, back: { text: backText(name, formula, cas) } }],
          deliver: "open",
        },
      });
      const payload = await loadToolData(app, result);
      if (payload?.type !== "anki_deck") throw new Error("kein Anki-Payload");
      setFile(payload.file || "");
      // "open" heißt: Anki hat die Datei bekommen. Sonst liegt sie nur auf der Platte.
      next = payload.delivery === "open" ? "added" : "saved";
    } catch {
      next = "error";
    } finally {
      busyRef.current = false;
      setStatus(next);
      if (next !== "error") {
        timeoutRef.current = setTimeout(() => setStatus("idle"), 2500);
      }
    }
  }

  const title =
    status === "busy"
      ? "Adding to Anki…"
      : status === "added"
      ? `Opened in Anki: ${file}`
      : status === "saved"
      ? `Saved: ${file}`
      : status === "error"
      ? "Adding to Anki failed — click to retry"
      : `Add a flashcard to the Anki deck "${ANKI_DECK}"`;

  const label = busy
    ? "Adding…"
    : status === "added"
    ? "Added"
    : status === "saved"
    ? "Saved"
    : status === "error"
    ? "Retry Anki"
    : "Add to Anki";

  // Panel-Umbau A (§4 Button): ruhiger Knopf ohne Kante; Erfolg in --success, Fehler in --danger (vorher #e74c3c inline).
  const state = ok ? " is-ok" : status === "error" ? " is-error" : "";
  return (
    <button
      type="button"
      className={`btn btn-quiet add-to-anki${state}`}
      aria-label={title}
      title={title}
      onClick={handleAdd}
      disabled={busy}
      aria-busy={busy}
    >
      <Icon name={ok ? "check" : "card-plus"} />
      <span aria-live="polite">{label}</span>
    </button>
  );
}
