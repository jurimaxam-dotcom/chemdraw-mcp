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
