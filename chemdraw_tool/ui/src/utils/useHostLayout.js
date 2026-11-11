import { useCallback, useState } from "react";

// Layout nach dem, was der Host meldet (U2, M10 — docs/anthropic/abgleich.md Abschnitt 6).
// Claude Desktop meldet im Chat `inline` mit containerDimensions {width, maxHeight},
// im Seitenpanel und im Vollbild `fullscreen` mit {width, height}. Entschieden wird
// nach den Maßen, nicht nach dem Modus: nur eine gemeldete feste Höhe lässt das
// Panel die Fläche füllen. Ohne sie (Chat, alte Hosts, gar kein Kontext) bleibt
// alles inhaltsgroß wie bisher — das CSS greift nur unter [data-host-height].

const INSETS = ["top", "right", "bottom", "left"];

/** Feste Höhe in px, wenn der Host eine meldet; sonst null (Chat-Weg). */
export function fixedHeightOf(ctx) {
  const h = ctx?.containerDimensions?.height;
  return typeof h === "number" && Number.isFinite(h) && h > 0 ? h : null;
}

/** Darf das Panel einen eigenen Vergrößern-Knopf zeigen? */
export function canRequestFullscreen(ctx) {
  // Wortlaut des Auftrags: nur im Modus `inline`. Ein Host ohne displayMode
  // bekommt keinen Knopf (das Doku-Beispiel zeigte ihn dort).
  return Boolean(ctx?.availableDisplayModes?.includes?.("fullscreen")) && ctx?.displayMode === "inline";
}

/** Spiegelt den Host-Kontext an <html>: Datenattribute und CSS-Variablen. */
export function applyHostLayout(ctx, root = typeof document !== "undefined" ? document.documentElement : null) {
  if (!root) return;
  const dims = ctx?.containerDimensions || {};
  const height = fixedHeightOf(ctx);
  if (height != null) {
    root.setAttribute("data-host-height", "");
    root.style.setProperty("--host-height", `${height}px`);
  } else {
    root.removeAttribute("data-host-height");
    root.style.removeProperty("--host-height");
  }
  if (typeof dims.width === "number" && dims.width > 0) root.style.setProperty("--host-width", `${dims.width}px`);
  else root.style.removeProperty("--host-width");
  if (ctx?.displayMode) root.setAttribute("data-display-mode", String(ctx.displayMode));
  else root.removeAttribute("data-display-mode");
  // Sichere Ränder (Seitenpanel: die Kante zum Chat). Nur wenn einer > 0 ist,
  // sonst bleibt der Innenabstand exakt wie heute.
  const insets = ctx?.safeAreaInsets || {};
  const any = INSETS.some((k) => Number(insets[k]) > 0);
  for (const k of INSETS) {
    if (any) root.style.setProperty(`--safe-${k}`, `${Math.max(0, Number(insets[k]) || 0)}px`);
    else root.style.removeProperty(`--safe-${k}`);
  }
  if (any) root.setAttribute("data-safe-area", "");
  else root.removeAttribute("data-safe-area");
}

/**
 * Hook für main.jsx. `attach(app)` gehört in onAppCreated (vor connect): erst ein
 * registrierter Listener lässt das SDK die Änderungen in getHostContext() mischen.
 * `sync(app)` nach dem Verbinden liest den Anfangskontext. Gelesen wird immer der
 * gemischte Gesamtkontext, nie die Teil-Parameter des Ereignisses.
 */
export function useHostLayout() {
  const [hostContext, setHostContext] = useState(null);
  const sync = useCallback((app) => {
    const ctx = app?.getHostContext?.() ?? null;
    applyHostLayout(ctx);
    setHostContext(ctx ? { ...ctx } : null);
  }, []);
  const attach = useCallback((app) => {
    app?.addEventListener?.("hostcontextchanged", () => sync(app));
  }, [sync]);
  return { hostContext, attach, sync };
}
