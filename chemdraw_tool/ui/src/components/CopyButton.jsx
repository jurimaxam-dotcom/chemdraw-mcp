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
      {copied ? (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <rect x="4" y="1" width="7" height="8" rx="1" stroke="currentColor" strokeWidth="1.2" />
          <path d="M1 4h2v6a1 1 0 001 1h5v1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      )}
    </button>
  );
}
