import React, { useState } from "react";
import CopyButton from "./CopyButton";
import NavTabs from "./NavTabs";

// Das Datenblatt: Reiter je Quelle + die Zeilen der aktiven Quelle.
//
// Aus DatabaseView herausgeloest, weil das Molekuel-Panel nach dem Nachladen
// exakt dieselbe Optik zeigen muss. Zwei Kopien waeren zwei Optiken, sobald
// eine davon einmal angefasst wird.
function DataTable({ rows }) {
  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      {rows.map(([key, value], i) => (
        <div
          key={key}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
            background: i % 2 === 1 ? "var(--bg-alt)" : "transparent",
            borderRadius: "var(--radius-sm)",
            padding: "4px 6px",
          }}
        >
          <span style={{ fontSize: 11, color: "var(--fg-muted)", flexShrink: 0 }}>
            {key}
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span
              style={{
                fontSize: 11,
                color: "var(--fg)",
                fontFamily: "var(--font-mono)",
                wordBreak: "break-all",
                textAlign: "right",
              }}
            >
              {value != null ? String(value) : "—"}
            </span>
            {value != null && <CopyButton text={String(value)} size="sm" />}
          </div>
        </div>
      ))}
    </div>
  );
}

function SourcePanel({ source, moleculeSvg }) {
  const rows = (source.rows || []).map((r) => [r.key, r.val]);
  const link = source.url || null;

  return (
    <div>
      <div style={{ display: "flex", gap: 12 }}>
        {moleculeSvg && (
          <div
            style={{
              width: 100,
              flexShrink: 0,
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "center",
              pointerEvents: "none",
            }}
            dangerouslySetInnerHTML={{ __html: moleculeSvg }}
          />
        )}
        <DataTable rows={rows} />
      </div>
      {link && (
        <div style={{ marginTop: 8 }}>
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 11,
              color: "var(--accent)",
              textDecoration: "none",
            }}
          >
            {source.source || "View source"} →
          </a>
        </div>
      )}
    </div>
  );
}

export default function SourceList({ sources, moleculeSvg }) {
  const list = sources || [];
  const tabs = list.map((s) => s.type || "Unbekannt");
  const [activeTab, setActiveTab] = useState(tabs[0] || "");

  const activeSource =
    list.find((s) => (s.type || "Unbekannt") === activeTab) || list[0];

  if (!activeSource) {
    return (
      <div style={{ color: "var(--fg-muted)", fontSize: 11 }}>No data available</div>
    );
  }

  return (
    <>
      {tabs.length > 1 && (
        <NavTabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      )}
      <div
        style={{
          background: "var(--bg-alt)",
          borderRadius: "var(--radius-md)",
          boxShadow: "var(--shadow-card)",
          padding: "10px 12px",
        }}
      >
        <SourcePanel source={activeSource} moleculeSvg={moleculeSvg} />
      </div>
    </>
  );
}
