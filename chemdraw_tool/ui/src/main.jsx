import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { useApp, useHostStyleVariables } from "@modelcontextprotocol/ext-apps/react";
import App from "./App";
import { AppContext, HostContext } from "./AppContext";
import HostDiagnostics from "./components/HostDiagnostics";
import ToolError from "./components/ToolError";
import ToolPlaceholder from "./components/ToolPlaceholder";
import { ModelContextProvider } from "./ModelContext";
import { extractToolData, extractToolError, loadToolData } from "./utils/toolData";
import { useHostLayout } from "./utils/useHostLayout";
import "./styles.css";

function Root() {
  const [data, setData] = useState(null);
  // Meldung des letzten Tool-Fehlers. Ein Fehler ersetzt das alte Ergebnis:
  // stehen bliebe sonst ein Bild, das zur neuen Anfrage nicht gehört.
  const [toolError, setToolError] = useState(null);
  // Argumente vor dem Ergebnis (toolinput) → Platzhalter statt „Waiting for data…“;
  // toolcancelled beendet den Ladezustand. Ein Ergebnis hat immer Vorrang.
  const [pendingInput, setPendingInput] = useState(null);
  const [cancelled, setCancelled] = useState(null);
  // Host-Kontext (U2): Größe und Modus → Attribute/Variablen an <html>.
  const { hostContext, attach, sync } = useHostLayout();
  // Nummer des jüngsten Ergebnisses: lädt ein großes Ergebnis noch nach (M2),
  // darf es ein danach eingetroffenes nicht überschreiben.
  const latest = useRef(0);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "Chem-MCP", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (app) => {
      // Vor connect registrieren: nur dann mischt das SDK Kontextänderungen ein.
      attach(app);
      app.addEventListener("toolinput", (params) => {
        setCancelled(null);
        setPendingInput(params?.arguments || {});
      });
      app.addEventListener("toolcancelled", (params) => {
        setCancelled({ reason: params?.reason });
      });
      app.addEventListener("toolresult", (params) => {
        const mine = ++latest.current;
        setCancelled(null);
        const message = extractToolError(params);
        if (message) {
          setData(null);
          setToolError(message);
          return;
        }
        const shown = (payload) => {
          if (mine !== latest.current || !payload) return;
          setToolError(null);
          setData(payload);
        };
        const payload = extractToolData(params);
        if (!payload?._deferred) {
          shown(payload);
          return;
        }
        // Großes Ergebnis: Bilder nachladen, bis dahin bleibt der Platzhalter.
        // Scheitert das, nennt die Meldung die schon geschriebenen Dateien —
        // nie eine leere Fläche.
        setData(null);
        loadToolData(app, params).then(shown, (err) => {
          if (mine !== latest.current) return;
          const files = Object.values(payload.files || {});
          setToolError([err.message, ...(files.length ? ["Files:", ...files] : [])].join("\n"));
        });
      });
    },
  });

  useHostStyleVariables(app, app?.getHostContext());
  useEffect(() => {
    if (app && isConnected) sync(app);
  }, [app, isConnected, sync]);

  if (data)
    return (
      <AppContext.Provider value={app}>
        <HostContext.Provider value={hostContext}>
          {/* Einziger Sender von updateModelContext (U4b): die Views melden nur. */}
          <ModelContextProvider app={app}>
            <HostDiagnostics app={app} hostContext={hostContext}>
              <App data={data} />
            </HostDiagnostics>
          </ModelContextProvider>
        </HostContext.Provider>
      </AppContext.Provider>
    );
  if (toolError) return <ToolError message={toolError} />;
  if (error) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connection error</div>;
  if (!isConnected) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connecting…</div>;
  if (pendingInput || cancelled) return <ToolPlaceholder args={pendingInput} cancelled={cancelled} />;
  return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Waiting for data…</div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root />);
