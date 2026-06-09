import React from "react";

export default function SectionHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "var(--fg)",
          letterSpacing: "0.02em",
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 2 }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
