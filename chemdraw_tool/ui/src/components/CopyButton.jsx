import React, { useState, useEffect, useRef } from "react";

// quiet (Etappe 4, 16.11.2026): der Knopf tritt zurück — ohne Rahmen, erst bei Hover/Fokus
// der Zeile voll sichtbar, ohne Hover-Gerät dezent. Nur Deckkraft, nie display/visibility:
// er bleibt im Bedienungshilfen-Baum und per Tab erreichbar (Desktop-Probe sucht „Copy value“).
// Aussehen über Klassen statt inline, damit die Hover-Regeln in styles.css greifen.
export default function CopyButton({ text, size, label = "Copy value", quiet = false }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);
  const sizeClass = size === "xs" ? " is-xs" : size === "sm" ? " is-sm" : "";

  // Clear any pending timer if the component unmounts before it fires.
  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  function flashCopied() {
    setCopied(true);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setCopied(false), 1500);
  }

  // Älterer Weg über ein verstecktes Textfeld. Meldet Erfolg nur, wenn der
  // Browser ihn bestätigt — sonst bliebe der Haken eine Behauptung.
  function copyViaTextarea() {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand("copy") !== false;
    } catch {
      ok = false;
    }
    document.body.removeChild(ta);
    if (ok) flashCopied();
  }

  function handleCopy() {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Im sandboxed iframe kann die Zwischenablage-API ablehnen; ohne
      // Rückfall passierte dann sichtbar nichts.
      navigator.clipboard.writeText(text).then(flashCopied, copyViaTextarea);
    } else {
      copyViaTextarea();
    }
  }

  return (
    <button
      type="button"
      aria-label={label}
      onClick={handleCopy}
      title="Copy"
      className={`copy-button${sizeClass}${quiet ? " is-quiet" : ""}${copied ? " is-copied" : ""}`}
    >
      {/* Panel-Umbau A (§4): derselbe Strich-Satz wie Panel.jsx (16er-Raster, 1,5 px); „kopiert“ = Haken in --success. */}
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
        {copied ? <path d="m3 8.5 3 3 7-7" /> : <>
          <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
          <path d="M10.5 3.5V3A1.5 1.5 0 0 0 9 1.5H3A1.5 1.5 0 0 0 1.5 3v6A1.5 1.5 0 0 0 3 10.5h.5" />
        </>}
      </svg>
    </button>
  );
}
