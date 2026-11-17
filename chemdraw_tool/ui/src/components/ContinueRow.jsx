import React, { useEffect, useId, useRef, useState } from "react";
import { useAppBridge } from "../AppContext";
import { hostCan } from "../ModelContext";

// Zeile „Continue in chat“ (U3) über der Fußzeile. Jeder Knopf schreibt einen
// Satz als Nutzernachricht (app.sendMessage) — direkt im Klick-Handler, weil
// der Host Nachrichten nur nach einer Nutzeraktion annimmt (send-messages).
// Ohne Host-Fähigkeit `message` gibt es die Zeile gar nicht, auch keinen leeren Kasten.

export const MESSAGE_REJECTED = "Claude did not take the message. You can type it in the chat instead.";
// Abgelehnte Promise = das SDK hat aufgehört zu warten (Standard 60 s). Laut Anthropic
// (send-messages) kann Claude die Nachricht trotzdem haben: nie „nicht gesendet“ behaupten.
export const MESSAGE_FAILED = "No reply from Claude yet. If the text is not in your message box, try again or type it there.";
// Desktop kann die Nachricht bis zur Bestätigung zurückhalten: die Sperre gegen
// Doppelklick fällt spätestens dann, damit kein Knopf dauerhaft blockiert bleibt.
const RELEASE_MS = 8000;

export default function ContinueRow({ actions, flush, hint = "Each button writes one message for Claude" }) {
  const app = useAppBridge();
  const hintId = useId();
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
    // Etappe 4 (16.11.2026): eine kompakte Zeile statt eines Kastens mit Titel und Erklärzeile —
    // kleines Etikett vor den Knöpfen; die Erklärung bleibt als Tooltip am Etikett und als
    // Beschreibung der Gruppe (aria-describedby), sichtbar nur noch für Bedienungshilfen.
    // Panel-Umbau A (§4): Knöpfe ruhig mit Haarlinie, 28 hoch, ohne Pfeil (der war aria-hidden).
    <section className="continue-row" data-testid="continue-row" aria-label="Continue in chat" aria-describedby={hintId}>
      <span id={hintId} className="visually-hidden">{hint}</span>
      <div className="continue-actions">
        <span className="continue-label" title={hint} aria-hidden="true">Continue in chat</span>
        {actions.map((a) => (
          <button key={a.id} type="button" className={`continue-button${a.color ? " is-about" : ""}`}
            style={a.color ? { "--group-color": a.color } : undefined}
            aria-busy={busy === a.id} onClick={() => send(a)}>
            <span>{a.label}</span>
          </button>
        ))}
      </div>
      {note && <p className="continue-note" role="status">{note}</p>}
    </section>
  );
}
