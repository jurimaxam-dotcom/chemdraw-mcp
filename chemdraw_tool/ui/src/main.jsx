import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import App from "./App";
import { AppContext } from "./AppContext";
import "./styles.css";

function Root() {
  const [data, setData] = useState(null);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "Chem-MCP", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (app) => {
      app.ontoolresult = (params) => {
        if (params?.structuredContent) {
          setData(params.structuredContent);
        }
      };
    },
  });

  if (data)
    return (
      <AppContext.Provider value={app}>
        <App data={data} />
      </AppContext.Provider>
    );
  if (error) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Verbindungsfehler</div>;
  if (!isConnected) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Verbinde…</div>;
  return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Warte auf Daten…</div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root />);
