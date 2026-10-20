import React, { useEffect, useRef, useState } from "react";
import { useAppBridge } from "../AppContext";
import { extractToolData } from "../utils/toolData";

// Fester Deckname: gleicher Name aktualisiert statt dupliziert (GUID = Deck +
// Vorderseite), so sammeln sich alle Klicks in einem Anki-Deck.
export const ANKI_DECK = "ChemDraw";

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Rückseite als Anki-HTML: Name fett, darunter die Formel mit tiefgestellten
// Zahlen. Anki-Felder werden nicht escaped, also hier selbst escapen.
function backText(name, formula) {
  const parts = [`<b>${escapeHtml(name || "Molecule")}</b>`];
  if (formula) parts.push(escapeHtml(formula).replace(/(\d+)/g, "<sub>$1</sub>"));
  return parts.join("<br>");
}

// idle → busy (deaktiviert) → (added | saved | error); Erfolg blinkt kurz,
// ein Fehler bleibt stehen, bis der nächste Klick ihn neu versucht.
export default function AddToAnkiButton({ smiles, name, formula, size }) {
  const app = useAppBridge();
  const [status, setStatus] = useState("idle");
  const [file, setFile] = useState("");
  const timeoutRef = useRef(null);
  const busyRef = useRef(false); // blockiert den re-entranten Doppelklick
  const dim = size === "sm" ? 32 : 40;
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
          cards: [{ front: { structure: smiles }, back: { text: backText(name, formula) } }],
          deliver: "open",
        },
      });
      const payload = extractToolData(result);
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

  const borderColor = ok ? "var(--copy-success)" : status === "error" ? "#e74c3c" : "var(--border)";
  const fg = ok ? "var(--copy-success)" : status === "error" ? "#e74c3c" : "var(--fg-muted)";
  const label = busy
    ? "Adding…"
    : status === "added"
    ? "Added"
    : status === "saved"
    ? "Saved"
    : status === "error"
    ? "Retry Anki"
    : "Add to Anki";

  return (
    <button
      type="button"
      className="add-to-anki"
      aria-label={title}
      title={title}
      onClick={handleAdd}
      disabled={busy}
      aria-busy={busy}
      style={{
        minWidth: dim,
        height: dim,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: ok ? "var(--copy-success-bg)" : "transparent",
        border: `1px solid ${borderColor}`,
        borderRadius: "var(--border-radius-sm, 6px)",
        cursor: busy ? "progress" : "pointer",
        opacity: busy ? 0.6 : 1,
        color: fg,
        padding: "0 10px",
        gap: 7,
        flexShrink: 0,
      }}
    >
      {ok ? (
        <svg width="13" height="13" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <rect x="1.5" y="3" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.1" />
          <path d="M4 1.5h7a1.5 1.5 0 0 1 1.5 1.5v7" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
          <path d="M6 5.5v4M4 7.5h4" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
        </svg>
      )}
      <span aria-live="polite">{label}</span>
    </button>
  );
}
