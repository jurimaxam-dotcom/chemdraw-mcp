import React, { useState, useEffect, useRef } from "react";
import { useAppBridge } from "../AppContext";
import { svgToPngBlob, blobToBase64, copyPngToClipboard } from "../utils/svgToPng";

// idle → (copied | saved | error), auto-resets to idle after a flash.
export default function ExportPngButton({ svg, filename, size }) {
  const app = useAppBridge();
  const [status, setStatus] = useState("idle");
  const [savedPath, setSavedPath] = useState("");
  const timeoutRef = useRef(null);
  const busyRef = useRef(false); // in-flight guard: blocks a re-entrant double-click
  const dim = size === "sm" ? 22 : 26;
  const ok = status === "copied" || status === "saved";

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  function flash(next) {
    setStatus(next);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setStatus("idle"), 2500);
  }

  async function handleExport() {
    if (!svg || busyRef.current) return; // ignore re-entrant clicks while running
    busyRef.current = true;
    try {
      let blob;
      try {
        blob = await svgToPngBlob(svg, { scale: 3, background: "#fff" });
      } catch {
        flash("error");
        return;
      }
      // 1. Primary: image clipboard.
      try {
        await copyPngToClipboard(blob);
        flash("copied");
        return;
      } catch {
        // fall through to backend file save
      }
      // 2. Fallback: backend writes the file.
      try {
        if (!app?.callServerTool) throw new Error("No app bridge");
        const b64 = await blobToBase64(blob);
        const result = await app.callServerTool({
          name: "save_png",
          arguments: { png_base64: b64, filename: filename || "molekuel" },
        });
        const text = result?.content?.find((c) => c.type === "text")?.text;
        // result.isError is the SDK's hard-error flag (MCP-framework errors whose
        // text won't start with "Fehler:"); check it so they don't flash a false
        // green "Gespeichert". The "Fehler:" prefix covers the backend's own soft errors.
        if (result?.isError || !text || text.startsWith("Fehler:")) {
          throw new Error(text || "No path");
        }
        setSavedPath(text);
        flash("saved");
      } catch {
        flash("error");
      }
    } finally {
      busyRef.current = false;
    }
  }

  const title =
    status === "copied"
      ? "Copied as image"
      : status === "saved"
      ? `Saved: ${savedPath}`
      : status === "error"
      ? "Export failed"
      : "Export as PNG";

  const borderColor = ok
    ? "var(--copy-success)"
    : status === "error"
    ? "#e74c3c"
    : "var(--border)";
  const fg = ok
    ? "var(--copy-success)"
    : status === "error"
    ? "#e74c3c"
    : "var(--fg-muted)";

  return (
    <button
      onClick={handleExport}
      title={title}
      style={{
        width: dim,
        height: dim,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: ok ? "var(--copy-success-bg)" : "transparent",
        border: `1px solid ${borderColor}`,
        borderRadius: "var(--border-radius-sm, 6px)",
        cursor: "pointer",
        color: fg,
        padding: 0,
        flexShrink: 0,
      }}
    >
      {ok ? (
        <svg width="13" height="13" viewBox="0 0 12 12" fill="none">
          <path
            d="M2 6l3 3 5-5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
          <rect x="1.5" y="2" width="11" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.1" />
          <circle cx="5" cy="5.5" r="1" fill="currentColor" />
          <path d="M2 10l3-3 2.5 2.5L10 6l2 2" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}
