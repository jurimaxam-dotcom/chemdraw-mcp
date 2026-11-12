import React, { createContext, useCallback, useContext, useEffect, useId, useMemo, useRef } from "react";
import { buildModelContext } from "./utils/modelContext.js";

// Genau ein Besitzer für app.updateModelContext (U4b). Der Host behält nur das
// letzte Update — senden mehrere Stellen, gewinnt zufällig eine. Deshalb melden
// die Views (je Karte eine Meldung) hier ihren Text, und nur dieser Provider
// sendet: entprellt, nur bei geändertem Text, nur mit Host-Fähigkeit, Fehler still.

/** Kann der Host diese Fähigkeit mit Text? `{}` ohne Modalitäten gilt als ja. */
export function hostCan(app, capability) {
  try {
    const cap = app?.getHostCapabilities?.()?.[capability];
    if (!cap || typeof cap !== "object") return false;
    return Object.keys(cap).length === 0 || Boolean(cap.text);
  } catch {
    return false;
  }
}

const Ctx = createContext(null);

export function ModelContextProvider({ app, delay = 300, children }) {
  const reports = useRef(new Map()); // id → { text, summary, focus }
  const lastSent = useRef(null);
  const timer = useRef(null);
  const focusCounter = useRef(0);

  const api = useMemo(() => {
    const send = () => {
      clearTimeout(timer.current);
      timer.current = null;
      if (!hostCan(app, "updateModelContext") || typeof app?.updateModelContext !== "function") return;
      const text = buildModelContext([...reports.current.values()]);
      if (!text || text === lastSent.current) return;
      lastSent.current = text;
      const forget = () => { if (lastSent.current === text) lastSent.current = null; };
      try {
        Promise.resolve(app.updateModelContext({ content: [{ type: "text", text }] })).catch(forget);
      } catch {
        forget();
      }
    };
    const schedule = () => {
      clearTimeout(timer.current);
      timer.current = setTimeout(send, delay);
    };
    return {
      canContext: hostCan(app, "updateModelContext"),
      // Für Hinweistexte: Knöpfe gibt es nur mit `message`. Der Kontext ist kein Versprechen —
      // Desktop meldet die Fähigkeit, das Modell sah den Text im Handtest U5b (12.11.2026) nicht.
      canAsk: hostCan(app, "message") && typeof app?.sendMessage === "function",
      report(id, entry, interacted) {
        if (!entry) {
          if (reports.current.delete(id)) schedule();
          return;
        }
        const prev = reports.current.get(id);
        const focus = interacted ? ++focusCounter.current : prev?.focus || 0;
        reports.current.set(id, { ...entry, focus });
        schedule();
      },
      remove(id) {
        if (reports.current.delete(id)) schedule();
      },
      // Sofort senden (vor sendMessage): Satz und Auswahl müssen zusammenpassen.
      flush(id) {
        const entry = id && reports.current.get(id);
        if (entry) entry.focus = ++focusCounter.current;
        send();
      },
    };
  }, [app, delay]);

  useEffect(() => () => clearTimeout(timer.current), []);

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

/**
 * Eine View meldet ihren Zustandstext. `text` = voller Text, `summary` = eine
 * Zeile für den Stapel-Überblick. Rückgabe: `flush` (vor sendMessage aufrufen)
 * ob der Host Kontext annimmt (`canContext`) und ob es Chat-Knöpfe gibt (`canAsk`, für Hinweistexte).
 */
export function useModelContextReport(text, summary = "") {
  const ctx = useContext(Ctx);
  const id = useId();
  const previous = useRef(null);
  useEffect(() => {
    if (!ctx) return;
    // Erste Meldung = Anfangszustand; jede Änderung danach kam vom Nutzer.
    const interacted = previous.current !== null && previous.current !== text;
    previous.current = text;
    ctx.report(id, text ? { text, summary } : null, interacted);
  }, [ctx, id, text, summary]);
  useEffect(() => () => ctx?.remove(id), [ctx, id]);
  const flush = useCallback(() => ctx?.flush(id), [ctx, id]);
  return { flush, canContext: Boolean(ctx?.canContext), canAsk: Boolean(ctx?.canAsk) };
}
