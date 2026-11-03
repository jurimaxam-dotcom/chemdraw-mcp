import React from "react";
import SectionHeader from "./components/SectionHeader";
import { displayPath } from "./utils/displayPath";

const MAX_FRONTS = 10;

// Kartenvorderseiten sind Anki-HTML (<i>, <br>, &amp;). Die Vorschau zeigt den
// Text, ohne das HTML einzusetzen: <template>-Inhalt ist inert — er lädt keine
// Bilder und führt keine Handler aus.
export function frontText(front) {
  const tpl = document.createElement("template");
  tpl.innerHTML = String(front ?? "").replace(/<br\s*\/?>/gi, " ");
  return (tpl.content.textContent || "").replace(/\s+/g, " ").trim();
}

export default function AnkiDeckView({ data }) {
  const fronts = data.fronts || [];
  const shown = fronts.slice(0, MAX_FRONTS);
  const hidden = fronts.length - shown.length;

  return (
    <div style={{ padding: 16 }}>
      <SectionHeader
        title={data.name || "Anki deck"}
        subtitle={`${data.cards} card${data.cards === 1 ? "" : "s"} · ${data.media} image${data.media === 1 ? "" : "s"} · ${
          data.delivery === "ankiconnect"
            ? "imported into Anki via AnkiConnect"
            : data.delivery?.startsWith("ankiconnect-")
            ? "AnkiConnect unreachable — import the .apkg manually"
            : "import the .apkg into Anki"
        }`}
      />
      <ol
        style={{
          margin: "0 0 12px",
          paddingLeft: 22,
          fontSize: 12,
          color: "var(--fg)",
          lineHeight: 1.7,
        }}
      >
        {shown.map((front, i) => (
          <li key={i}>{frontText(front)}</li>
        ))}
      </ol>
      {hidden > 0 && (
        <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 12 }}>
          … and {hidden} more card{hidden === 1 ? "" : "s"}
        </div>
      )}
      {data.file && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
            background: "var(--bg-alt)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            padding: "8px 10px",
          }}
        >
          <span title={data.file}>{displayPath(data.file)}</span>
        </div>
      )}
    </div>
  );
}
