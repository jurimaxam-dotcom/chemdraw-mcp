import React, { useState } from "react";
import CopyButton from "./CopyButton";
import NavTabs from "./NavTabs";

// Das Datenblatt: Reiter je Quelle + die Zeilen der aktiven Quelle.
//
// Aus DatabaseView herausgeloest, weil das Molekuel-Panel nach dem Nachladen
// exakt dieselbe Optik zeigen muss. Zwei Kopien waeren zwei Optiken, sobald
// eine davon einmal angefasst wird.
function DataTable({ rows }) {
  return <dl className="source-table">{rows.map(([key, value]) =>
    <div className="source-row" key={key}>
      <dt>{key}</dt><dd><span>{value != null ? String(value) : "—"}</span>{value != null && <CopyButton text={String(value)} size="sm" />}</dd>
    </div>
  )}</dl>;
}

function SourcePanel({ source, moleculeSvg }) {
  const rows = (source.rows || []).map((r) => [r.key, r.val]);
  return <section className="source-panel" aria-label={source.source || source.type || "Source"}>
    <div className="source-content">
      {moleculeSvg && <div className="source-structure" aria-hidden="true" dangerouslySetInnerHTML={{ __html: moleculeSvg }} />}
      <DataTable rows={rows} />
    </div>
    {source.url && <a className="source-link" href={source.url} target="_blank" rel="noopener noreferrer">{source.source || "View source"} →</a>}
  </section>;
}

export default function SourceList({ sources, moleculeSvg }) {
  const list = sources || [];
  const tabs = list.map((s) => s.type || "Source");
  const [activeTab, setActiveTab] = useState(tabs[0] || "");

  const activeSource =
    list.find((s) => (s.type || "Source") === activeTab) || list[0];

  if (!activeSource) {
    return (
      <div style={{ color: "var(--fg-muted)", fontSize: 13 }}>No data available</div>
    );
  }

  return (
    <>
      {tabs.length > 1 && (
        <NavTabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      )}
      <div className="source-sheet">
        <SourcePanel source={activeSource} moleculeSvg={moleculeSvg} />
      </div>
    </>
  );
}
