import React from "react";
import SectionHeader from "./components/SectionHeader";
import PanelFooter from "./components/PanelFooter";
import { useModelContextReport } from "./ModelContext";
import { genericContext } from "./utils/modelContext.js";

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
  useModelContextReport(genericContext("anki_deck", data), data.name || "anki_deck");
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
            : data.delivery === "open"
            ? "opened in Anki"
            : data.delivery?.startsWith("ankiconnect-")
            ? "AnkiConnect unreachable — import the .apkg manually"
            : "import the .apkg into Anki"
        }`}
      />
      <ol
        style={{
          margin: 0,
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
        <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 4 }}>
          … and {hidden} more card{hidden === 1 ? "" : "s"}
        </div>
      )}
      {/* Fußzeile (E3): die .apkg-Datei mit Präfix; eine Aktion gibt es hier nicht. */}
      <PanelFooter files={data.file ? [{ label: "APKG", path: data.file }] : []} />
    </div>
  );
}
