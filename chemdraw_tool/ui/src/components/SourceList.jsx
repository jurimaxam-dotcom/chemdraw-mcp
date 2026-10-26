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

// --- GHS je Quelle (Etappe 5) ---
// Eine Gruppe je PubChem-Referenz. Die Leitquelle (EU-harmonisiert, sonst
// ECHA-Aggregat) steht offen, alle anderen zugeklappt — vier Signalwoerter
// untereinander ohne Herkunft waren das Problem, das hier geloest wird.
// Prozente gelten nur innerhalb ihrer Quelle; ohne Prozent steht keiner da.
function fmtPct(p) {
  return `${Number(p).toString()}%`;
}

function ghsRows(group) {
  const findings = [];
  for (const h of group.hazards || []) {
    findings.push({
      pct: h.percent,
      row: [h.code, h.percent != null ? `${h.text} (${fmtPct(h.percent)} of reports with hazard codes)` : h.text],
    });
  }
  const nc = group.not_classified;
  if (nc) {
    const counts = nc.reports != null && nc.total ? ` (${nc.reports} of ${nc.total})` : "";
    findings.push({
      pct: nc.percent,
      row: ["Not classified", nc.percent != null ? `${fmtPct(nc.percent)} of all reports${counts}` : `Reported as not classified${counts}`],
    });
  }
  if (findings.some((f) => f.pct != null)) {
    findings.sort((a, b) => (b.pct ?? -1) - (a.pct ?? -1));
  }
  const rows = [];
  if (group.signal) rows.push(["Signal word", group.signal]);
  rows.push(...findings.map((f) => f.row));
  if (group.pictograms?.length) rows.push(["Pictograms", group.pictograms.join(", ")]);
  if (group.p_codes?.length) rows.push(["P-codes", group.p_codes.join(", ")]);
  if (group.reports_total) rows.push(["Company reports", String(group.reports_total)]);
  return rows;
}

function GhsGroup({ group, initiallyOpen }) {
  const [open, setOpen] = useState(initiallyOpen);
  const bodyId = `ghs-body-${group.id}`;
  const summary = [group.signal, ...(group.hazards || []).map((h) => h.code)].filter(Boolean).join(" · ");
  return <section className="ghs-group" data-ghs-id={group.id} aria-label={group.source}>
    <button type="button" className="ghs-toggle" aria-expanded={open} aria-controls={bodyId} onClick={() => setOpen((o) => !o)}>
      <span className="ghs-source">{group.source}</span>
      {group.lead && <span className="ghs-lead">Lead source</span>}
      {!open && summary && <span className="ghs-summary">{summary}</span>}
    </button>
    {group.note && <p className="ghs-note">{group.note}</p>}
    {open && <div id={bodyId}>
      <DataTable rows={ghsRows(group)} />
      {group.url && <a className="source-link" href={group.url} target="_blank" rel="noopener noreferrer">Source record →</a>}
    </div>}
  </section>;
}

function GhsGroups({ groups }) {
  return <div className="ghs-groups">
    {groups.map((g, i) => <GhsGroup key={g.id} group={g} initiallyOpen={i === 0} />)}
  </div>;
}

function SourcePanel({ source, moleculeSvg }) {
  const rows = (source.rows || []).map((r) => [r.key, r.val]);
  const groups = source.groups || [];
  return <section className="source-panel" aria-label={source.source || source.type || "Source"}>
    <div className="source-content">
      {moleculeSvg && <div className="source-structure" aria-hidden="true" dangerouslySetInnerHTML={{ __html: moleculeSvg }} />}
      <div className="source-body">
        {source.note && <p className="ghs-note">{source.note}</p>}
        {groups.length > 0 ? <GhsGroups groups={groups} /> : rows.length > 0 && <DataTable rows={rows} />}
      </div>
    </div>
    {source.url && <a className="source-link" href={source.url} target="_blank" rel="noopener noreferrer">{source.source || "View source"} →</a>}
  </section>;
}

export default function SourceList({ sources, moleculeSvg }) {
  const list = sources || [];
  // Ein Reiter je Typ, eindeutig: mehrere Quellen gleichen Typs (GHS) wohnen
  // als Gruppen in EINER Quelle — ein zweiter "GHS"-Reiter waere unanwaehlbar.
  const tabs = [...new Set(list.map((s) => s.type || "Source"))];
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
