import { createContext, useContext } from "react";

// Holds the ext-apps `app` instance so deep components (ExportPngButton)
// can call app.callServerTool without prop-threading through every view.
export const AppContext = createContext(null);

export function useAppBridge() {
  return useContext(AppContext);
}
