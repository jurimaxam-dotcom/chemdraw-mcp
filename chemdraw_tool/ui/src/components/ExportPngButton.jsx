import React, { useContext, useEffect, useRef, useState } from "react";
import { useAppBridge } from "../AppContext";
import { svgToPngBlob, blobToBase64, copyPngToClipboard } from "../utils/svgToPng";
import { displayPath } from "../utils/displayPath";
import { FooterStatus } from "./PanelFooter";

// Austauschbare Naht für die DOM-Tests: jsdom hat kein Canvas und Node kein
// FileReader. Im Panel sind es immer die echten Funktionen.
export const exportDeps = { svgToPngBlob, blobToBase64, copyPngToClipboard };

const OK_MS = 4000;
const ERROR_MS = 8000;

// idle → (copied | saved | error), zurück nach einem Flash.
// Die Rückmeldung ist sichtbar (Desktop-Handtest 07.11.2026: die Datei landete
// still in ~/ChemDraw-Output/png/, das Panel zeigte nichts): in der Fußzeile an
// der Stelle der Pfade, außerhalb einer Fußzeile direkt neben dem Knopf.
//
// svg: fertiger SVG-String · getSvg: liefert ihn erst beim Klick (3D: die
// aktuelle Drehlage) · background: Farbe oder Funktion, die sie beim Klick liefert.
export default function ExportPngButton({ svg, getSvg, filename, size, background = "#fff" }) {
  const app = useAppBridge();
  const report = useContext(FooterStatus);
  const [status, setStatus] = useState("idle");
  const [savedPath, setSavedPath] = useState("");
  const [reason, setReason] = useState("");
  const timeoutRef = useRef(null);
  const busyRef = useRef(false); // in-flight guard: blocks a re-entrant double-click
  const dim = size === "sm" ? 32 : 40;
  const ok = status === "copied" || status === "saved";

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  const message =
    status === "copied"
      ? "Copied to clipboard"
      : status === "saved"
      ? `Saved: ${displayPath(savedPath)}`
      : status === "error"
      ? `Export failed: ${reason}`
      : "";

  // Rückmeldung an die Fußzeile melden, solange sie gilt.
  useEffect(() => {
    if (!report) return undefined;
    report(message ? { text: message, kind: status === "error" ? "error" : "ok" } : null);
    return undefined;
  }, [report, message, status]);
  useEffect(() => () => report?.(null), [report]);

  function flash(next, ms = OK_MS) {
    setStatus(next);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setStatus("idle"), ms);
  }

  function fail(why) {
    setReason(why);
    flash("error", ERROR_MS);
  }

  async function handleExport() {
    if (busyRef.current) return; // ignore re-entrant clicks while running
    busyRef.current = true;
    try {
      let source = "";
      try {
        // 3D-Cartoon (WebGL): getSvg liefert ein Promise (Bild erst rendern)
        source = getSvg ? await getSvg() : svg;
      } catch {
        source = "";
      }
      if (!source) {
        fail("there is no drawing to export");
        return;
      }
      let blob;
      try {
        const bg = typeof background === "function" ? background() : background;
        blob = await exportDeps.svgToPngBlob(source, { scale: 3, background: bg });
      } catch {
        fail("the drawing could not be rendered as an image");
        return;
      }
      // 1. Primary: image clipboard.
      try {
        await exportDeps.copyPngToClipboard(blob);
        flash("copied");
        return;
      } catch {
        // fall through to backend file save
      }
      // 2. Fallback: backend writes the file.
      if (!app?.callServerTool) {
        fail("the clipboard is blocked here and there is no connection to the server");
        return;
      }
      try {
        const b64 = await exportDeps.blobToBase64(blob);
        const result = await app.callServerTool({
          name: "save_png",
          arguments: { png_base64: b64, filename: filename || "molekuel" },
        });
        const text = result?.content?.find((c) => c.type === "text")?.text;
        // result.isError is the SDK's hard-error flag (MCP-framework errors whose
        // text won't start with "Fehler:"); the "Fehler:" prefix covers the
        // backend's own soft errors. Both carry the reason in the text.
        if (result?.isError || !text || text.startsWith("Fehler:")) {
          fail(text ? text.replace(/^Fehler:\s*/, "") : "the server did not return a file path");
          return;
        }
        setSavedPath(text);
        flash("saved");
      } catch (err) {
        fail(err?.message ? `the server call failed (${err.message})` : "the server call failed");
      }
    } finally {
      busyRef.current = false;
    }
  }

  // title/aria-label tragen den vollen Pfad (Host-Test liest ihn dort);
  // sichtbar ist der gekürzte in der Rückmeldung.
  const title =
    status === "copied"
      ? "Copied as image"
      : status === "saved"
      ? `Saved: ${savedPath}`
      : status === "error"
      ? `Export failed: ${reason}`
      : "Export as PNG";

  const borderColor = ok ? "var(--copy-success)" : status === "error" ? "var(--danger, #c0392b)" : "var(--border)";
  const fg = ok ? "var(--copy-success)" : status === "error" ? "var(--danger, #c0392b)" : "var(--fg-muted)";

  const button = (
    <button
      type="button"
      className="export-png"
      aria-label={title}
      onClick={handleExport}
      title={title}
      style={{
        minWidth: dim,
        height: dim,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: ok ? "var(--copy-success-bg)" : "transparent",
        border: `1px solid ${borderColor}`,
        borderRadius: "var(--border-radius-sm, 6px)",
        cursor: "pointer",
        color: fg,
        padding: "0 10px",
        gap: 7,
        flexShrink: 0,
      }}
    >
      {ok ? (
        <svg width="13" height="13" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <rect x="1.5" y="2" width="11" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.1" />
          <circle cx="5" cy="5.5" r="1" fill="currentColor" />
          <path d="M2 10l3-3 2.5 2.5L10 6l2 2" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      <span>{ok ? (status === "copied" ? "Copied" : "Saved") : status === "error" ? "Retry PNG" : "Export PNG"}</span>
    </button>
  );

  if (report || !message) return button;
  return (
    <>
      <span className={`export-feedback${status === "error" ? " is-error" : ""}`} role="status">{message}</span>
      {button}
    </>
  );
}
