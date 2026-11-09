// Holt das Panel-Payload aus einer tool-result-Notification.
// Claude Desktop (ab v1.22209.0) reicht structuredContent nicht mehr ans
// iframe weiter, sendet aber weiterhin die JSON-Serialisierung des Payloads
// als content-Textblock (FastMCP legt structured output in beide Felder).
export function extractToolData(params) {
  if (!params || params.isError) return null;
  if (params.structuredContent && typeof params.structuredContent === "object") {
    return params.structuredContent;
  }
  for (const block of params.content ?? []) {
    if (block?.type !== "text" || typeof block.text !== "string") continue;
    try {
      const parsed = JSON.parse(block.text);
      if (parsed && typeof parsed === "object") return parsed;
    } catch {
      // kein JSON — nächster Block
    }
  }
  return null;
}

// Fund (b), 09.11.: Fehler-Ergebnisse verwarf das Panel still. Diese Funktion
// holt die Meldung heraus, damit das Panel sie zeigen kann. Das SDK stellt
// „Error executing tool <name>: “ voran — für den Nutzer ist das Rauschen.
export const TOOL_ERROR_FALLBACK = "The tool reported an error without a message.";

export function extractToolError(params) {
  if (!params?.isError) return null;
  const text = (params.content ?? [])
    .filter((block) => block?.type === "text" && typeof block.text === "string")
    .map((block) => block.text.replace(/^Error executing tool \S+: /, "").trim())
    .filter(Boolean)
    .join("\n");
  return text || TOOL_ERROR_FALLBACK;
}
