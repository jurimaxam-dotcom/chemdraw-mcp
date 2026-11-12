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

// M2 (12.11.2026): Claude Desktop zeigt ein Panel nicht mehr, wenn das
// Tool-Ergebnis rund 150.000 Zeichen überschreitet. Der Server hält deshalb bei
// großen Ergebnissen die größten Teile (SVGs, notfalls Listen) zurück, setzt
// leere Platzhalter ein und vermerkt sie unter `_deferred`
// (chemdraw_tool/result_budget.py). Hier holt das Panel sie stückweise über das
// interne Tool load_panel_part und setzt sie rückwärts ein — eine zurückgehaltene
// Liste zuerst, die in ihr zurückgehaltenen Texte danach.
export const PART_LOAD_FAILED = "The images of this large result could not be loaded.";

// Alle zurückgehaltenen Teile eines Ergebnisses liegen beim Server als ein
// JSON-Array (Reihenfolge wie `_deferred.paths`) und kommen in Stücken.
async function loadParts(app, token) {
  let block = "";
  let offset = 0;
  while (offset !== null && offset !== undefined) {
    const result = await app.callServerTool({ name: "load_panel_part", arguments: { token, offset } });
    const error = extractToolError(result);
    if (error) throw new Error(error);
    const text = (result?.content ?? []).find((b) => b?.type === "text" && typeof b.text === "string");
    const piece = text ? JSON.parse(text.text) : null;
    if (!piece || typeof piece.text !== "string") throw new Error("empty answer");
    block += piece.text;
    offset = piece.next;
  }
  return JSON.parse(block);
}

export async function loadToolData(app, params) {
  const data = extractToolData(params);
  const deferred = data?._deferred;
  if (!deferred) return data;
  const { token, paths } = deferred;
  let parts;
  try {
    if (!app?.callServerTool) throw new Error("no app bridge");
    parts = await loadParts(app, token);
    if (!Array.isArray(parts) || parts.length !== paths.length) throw new Error("incomplete answer");
  } catch (err) {
    throw new Error(`${PART_LOAD_FAILED} ${err?.message || ""}`.trim());
  }
  const full = structuredClone(data);
  delete full._deferred;
  for (let i = paths.length - 1; i >= 0; i--) {
    const path = paths[i];
    let target = full;
    for (const step of path.slice(0, -1)) target = target[step];
    const key = path[path.length - 1];
    target[key] = typeof target[key] === "string" ? parts[i] : JSON.parse(parts[i]);
  }
  return full;
}

// Alle Dateipfade eines Ergebnisses, auch aus den Karten eines Stapels: scheitert
// das Nachladen, nennt das Panel sie statt eine leere Fläche zu zeigen.
export function writtenFiles(node) {
  if (Array.isArray(node)) return node.flatMap(writtenFiles);
  if (!node || typeof node !== "object") return [];
  return Object.entries(node).flatMap(([key, value]) =>
    key === "files" && value && typeof value === "object" && !Array.isArray(value)
      ? Object.values(value).filter((v) => typeof v === "string")
      : writtenFiles(value),
  );
}
