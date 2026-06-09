import React from "react";
import CopyButton from "./CopyButton";

export default function PropRow({ label, value, copyable, mono = true }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
        borderBottom: "1px solid var(--border)",
        padding: "5px 0",
      }}
    >
      <div style={{ fontSize: 10, color: "var(--fg-muted)", flexShrink: 0 }}>
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span
          style={{
            fontSize: 11,
            color: "var(--fg)",
            fontFamily: mono ? "var(--font-mono, 'SF Mono', ui-monospace, monospace)" : "var(--font)",
            wordBreak: "break-all",
            textAlign: "right",
          }}
        >
          {value ?? "—"}
        </span>
        {copyable && value != null && <CopyButton text={String(value)} size="sm" />}
      </div>
    </div>
  );
}
