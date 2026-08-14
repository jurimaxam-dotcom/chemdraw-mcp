import React from "react";
import SectionHeader from "./components/SectionHeader";

// Der Bezeichner ist die Angabe, nach der in einer Scope-Figur gesucht wird —
// er steht deshalb auch in der Liste vorn und fett.
function entrySummary(entry) {
  return [entry.yield_text, entry.notes].filter(Boolean).join(" · ");
}

export default function ScopeView({ data }) {
  const entries = data.entries || [];
  const failed = data.failed || [];

  if (!data.svg) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No scope figure available.
      </div>
    );
  }

  const subtitle =
    data.conditions ||
    `${entries.length} ${entries.length === 1 ? "entry" : "entries"}` +
      (data.columns ? ` · ${data.columns} columns` : "");

  return (
    <div
      style={{
        height: 560, // intrinsisch — der Host bemisst das iframe am Inhalt
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader title={data.name || "Substrate scope"} subtitle={subtitle} />
      <div
        className="scope-svg"
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          overflow: "hidden",
          padding: 8,
          flex: 1,
          minHeight: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        dangerouslySetInnerHTML={{ __html: data.svg }}
      />
      {/* RDKit liefert feste px-Maße — auf die Panelbreite herunterskalieren */}
      <style>{`.scope-svg svg { max-width: 100%; max-height: 100%; width: auto; height: auto; display: block; }`}</style>
      {entries.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "4px 14px",
            marginTop: 8,
            fontSize: 11,
            color: "var(--fg-muted)",
          }}
        >
          {entries.map((entry, i) => (
            <span key={entry.label || entry.structure || i}>
              <span style={{ color: "var(--fg)", fontWeight: 600 }}>
                {entry.label}
              </span>
              {entrySummary(entry) && (
                <>
                  {": "}
                  <span style={{ fontFamily: "ui-monospace, monospace" }}>
                    {entrySummary(entry)}
                  </span>
                </>
              )}
            </span>
          ))}
        </div>
      )}
      {failed.length > 0 && (
        // Ausgelassene Einträge müssen sichtbar sein: die Figur sieht sonst
        // vollständig aus, obwohl ein Substrat fehlt.
        <div style={{ fontSize: 11, color: "#c0392b", marginTop: 6 }}>
          Not resolved, left out of the figure: {failed.join(", ")}
        </div>
      )}
      {data.files?.png && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 6,
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
          }}
        >
          PNG: {data.files.png}
        </div>
      )}
    </div>
  );
}
