import React, { useEffect, useRef, useState } from "react";

// Diagnose für den Desktop-Handtest (U2): Was meldet der Host wirklich?
// Kein sichtbarer Knopf — ein Dreifachklick auf den Panel-Titel blendet einen
// ruhigen Block mit den Host-Fähigkeiten und den Layout-Feldern des Kontexts
// ein und wieder aus. Gilt für jede View, weil alle `.panel-title` tragen.
const FIELDS = ["displayMode", "availableDisplayModes", "containerDimensions", "safeAreaInsets", "platform"];

export function diagnosticsText(app, hostContext) {
  const ctx = hostContext || {};
  const picked = Object.fromEntries(FIELDS.map((k) => [k, ctx[k] ?? null]));
  let caps = null;
  try {
    caps = app?.getHostCapabilities?.() ?? null;
  } catch {
    caps = null;
  }
  return `hostCapabilities: ${JSON.stringify(caps, null, 2)}\nhostContext: ${JSON.stringify(picked, null, 2)}`;
}

export default function HostDiagnostics({ app, hostContext, children }) {
  const [open, setOpen] = useState(false);
  const wrap = useRef(null);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return undefined;
    const onClick = (e) => {
      if (e.detail !== 3) return;
      if (!e.target?.closest?.(".panel-title")) return;
      setOpen((o) => !o);
    };
    el.addEventListener("click", onClick);
    return () => el.removeEventListener("click", onClick);
  }, []);

  return (
    <div ref={wrap} className="panel-root">
      {children}
      {open && (
        <pre data-testid="host-diagnostics" className="host-diagnostics" aria-label="Host diagnostics">
          {diagnosticsText(app, hostContext)}
        </pre>
      )}
    </div>
  );
}
