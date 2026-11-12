import React, { useEffect, useRef, useState } from "react";
import { useAppBridge } from "../AppContext";
import { hostCan } from "../ModelContext";

// Zeile „Continue in chat“ (U3) über der Fußzeile. Jeder Knopf schreibt einen
// Satz als Nutzernachricht (app.sendMessage) — direkt im Klick-Handler, weil
// der Host Nachrichten nur nach einer Nutzeraktion annimmt (send-messages).
// Ohne Host-Fähigkeit `message` gibt es die Zeile gar nicht, auch keinen leeren Kasten.

export const MESSAGE_REJECTED = "Claude did not take the message. You can type it in the chat instead.";
export const MESSAGE_FAILED = "The message could not be sent. Try again or type it in the chat.";
// Desktop kann die Nachricht bis zur Bestätigung zurückhalten: die Sperre gegen
// Doppelklick fällt spätestens dann, damit kein Knopf dauerhaft blockiert bleibt.
const RELEASE_MS = 8000;

export default function ContinueRow({ actions, flush, hint = "Each button writes one message for Claude" }) {
  const app = useAppBridge();
  const [busy, setBusy] = useState(null);
  const [note, setNote] = useState("");
  const inFlight = useRef(false);
  const mounted = useRef(true);
  const releaseTimer = useRef(null);
  useEffect(() => () => {
    mounted.current = false;
    clearTimeout(releaseTimer.current);
  }, []);

  if (!actions?.length || !hostCan(app, "message") || typeof app?.sendMessage !== "function") return null;

  const release = () => {
    clearTimeout(releaseTimer.current);
    inFlight.current = false;
    if (mounted.current) setBusy(null);
  };

  function send(action) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(action.id);
    setNote("");
    releaseTimer.current = setTimeout(release, RELEASE_MS);
    // Kontext zuerst, ohne await dazwischen: beide Anfragen gehen in dieser
    // Reihenfolge raus, und die Nachricht bleibt Teil der Klick-Aktion.
    try { flush?.(); } catch { /* Kontext ist Beiwerk */ }
    let pending;
    try {
      pending = app.sendMessage({ role: "user", content: [{ type: "text", text: action.text }] });
    } catch (err) {
      pending = Promise.reject(err);
    }
    Promise.resolve(pending).then(
      (result) => { if (result?.isError && mounted.current) setNote(MESSAGE_REJECTED); },
      () => { if (mounted.current) setNote(MESSAGE_FAILED); },
    ).finally(release);
  }

  return (
    <section className="continue-row" data-testid="continue-row" aria-label="Continue in chat">
      <div className="continue-head">
        <h3 className="section-label">Continue in chat</h3>
        <span className="continue-hint">{hint}</span>
      </div>
      <div className="continue-actions">
        {actions.map((a) => (
          <button key={a.id} type="button" className={`continue-button${a.color ? " is-about" : ""}`}
            style={a.color ? { "--group-color": a.color } : undefined}
            aria-busy={busy === a.id} onClick={() => send(a)}>
            <span>{a.label}</span>
            <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor"
              strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M2 6h8M6.5 2.5L10 6l-3.5 3.5" /></svg>
          </button>
        ))}
      </div>
      {note && <p className="continue-note" role="status">{note}</p>}
    </section>
  );
}
