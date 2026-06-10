import React, { useState, useEffect, useRef } from "react";

export default function CopyButton({ text, size }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);
  const dim = size === "sm" ? 22 : 26;

  // Clear any pending timer if the component unmounts before it fires.
  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  function flashCopied() {
    setCopied(true);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setCopied(false), 1500);
  }

  function handleCopy() {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(flashCopied);
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      flashCopied();
    }
  }

  return (
    <button
      onClick={handleCopy}
      title="Copy"
      style={{
        width: dim,
        height: dim,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: copied ? "var(--copy-success-bg)" : "transparent",
        border: `1px solid ${copied ? "var(--copy-success)" : "var(--border)"}`,
        borderRadius: "var(--border-radius-sm, 6px)",
        cursor: "pointer",
        color: copied ? "var(--copy-success)" : "var(--fg-muted)",
        padding: 0,
        flexShrink: 0,
      }}
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
