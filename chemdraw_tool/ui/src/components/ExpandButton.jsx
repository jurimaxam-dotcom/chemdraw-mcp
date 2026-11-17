import React from "react";
import { useAppBridge, useHostContext } from "../AppContext";
import { Icon } from "./Panel";
import { canRequestFullscreen } from "../utils/useHostLayout";

// Eigener Vergrößern-Knopf (U2, M10; seit Etappe 3 in jeder View mit Bildfläche, immer
// rechts im Kopf): nur wenn der Host `fullscreen` anbietet und das Panel im Chat steht.
// requestDisplayMode direkt im Klick-Handler — Claude lehnt die Anfrage ohne frische
// Nutzeraktion ab. Nach dem Wechsel meldet der Host displayMode "fullscreen", der Knopf
// verschwindet von selbst. app/hostContext dürfen von außen kommen, sonst aus dem Kontext.
export function useCanExpand() {
  const app = useAppBridge();
  const hostContext = useHostContext();
  return canRequestFullscreen(hostContext) && Boolean(app?.requestDisplayMode);
}

export default function ExpandButton({ app: appProp, hostContext: ctxProp }) {
  const appCtx = useAppBridge();
  const hostCtx = useHostContext();
  const app = appProp ?? appCtx;
  const hostContext = ctxProp ?? hostCtx;
  if (!canRequestFullscreen(hostContext) || !app?.requestDisplayMode) return null;
  const expand = () => {
    app.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
  };
  // Panel-Umbau A (§4): 32 × 32, ruhig, nur Symbol (zwei Diagonalpfeile); der Name bleibt „Expand“ über aria-label.
  return <button type="button" className="expand-button" onClick={expand} aria-label="Expand"
    title="Open in the side panel"><Icon name="expand" size={16} /></button>;
}
