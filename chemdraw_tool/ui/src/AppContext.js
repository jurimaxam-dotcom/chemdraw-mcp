import { createContext, useContext } from "react";

// Holds the ext-apps `app` instance so deep components (ExportPngButton)
// can call app.callServerTool without prop-threading through every view.
export const AppContext = createContext(null);

export function useAppBridge() {
  return useContext(AppContext);
}

// Gemischter Host-Kontext (displayMode, containerDimensions, …) für Views, die
// danach etwas zeigen oder verbergen (Expand-Knopf). null = Host meldet nichts.
export const HostContext = createContext(null);

export function useHostContext() {
  return useContext(HostContext);
}
