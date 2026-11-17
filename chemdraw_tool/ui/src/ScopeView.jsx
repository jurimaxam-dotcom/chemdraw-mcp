import React from "react";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import { Facts, Hint, Panel, PanelFoot, PanelHead, PanelState, Stage } from "./components/Panel";
import { useModelContextReport } from "./ModelContext";
import { genericContext } from "./utils/modelContext.js";
import { naturalHeight, naturalWidth } from "./utils/svgSize";

// Ausbeute und Notiz eines Eintrags — der Bezeichner (1a, 1b …) ist das Etikett der Kernwert-Zeile.
function entrySummary(entry) {
  return [entry.yield_text, entry.notes].filter(Boolean).join(" · ");
}

export default function ScopeView({ data }) {
  useModelContextReport(genericContext("scope", data), data.name || "scope");
  const canExpand = useCanExpand();
  const entries = data.entries || [];
  const failed = data.failed || [];
  const title = data.name || "Substrate scope";
  const subtitle =
    data.conditions ||
    `${entries.length} ${entries.length === 1 ? "entry" : "entries"}` +
      (data.columns ? ` · ${data.columns} columns` : "");

  if (!data.svg) {
    return (
      <Panel kind="scope" className="scope-panel">
        <PanelHead title={title} subtitle={subtitle} />
        <PanelState kind="empty" message="No scope figure available." />
      </Panel>
    );
  }

  // Einträge ohne Ausbeute oder Notiz tragen nichts bei, das nicht schon in der Figur steht.
  const facts = entries
    .map((entry, i) => ({ key: `${i}:${entry.label}`, label: entry.label, value: entrySummary(entry) }))
    .filter((f) => f.label && f.value);
  // Seitenverhältnis der Figur: in Fill wird die Papierbühne höchstens so hoch wie die Figur bei voller
  // Breite (b-graphics.css) — sonst stünde im Seitenpanel ein 70 px hohes Raster auf 560 px Papier.
  const w = naturalWidth(data.svg), h = naturalHeight(data.svg);
  return (
    <Panel kind="scope" fill className="scope-panel">
      <PanelHead title={title} subtitle={subtitle} expand={canExpand ? <ExpandButton /> : null} />
      {/* Papierbühne (Spezifikation §5.10): die Figur ist eine Druckvorlage mit festem Weiß und bekommt
          eine bewusste Papierkante. scope-svg nimmt sie von der dunklen RDKit-Umfärbung aus (styles.css). */}
      <Stage variant="paper" className="scope-svg"
        style={w && h ? { "--scope-aspect": (h / w).toFixed(4) } : undefined} dangerouslySetInnerHTML={{ __html: data.svg }} />
      <Facts items={facts} className="scope-entries" />
      {failed.length > 0 && (
        // Ausgelassene Einträge müssen sichtbar sein: die Figur sieht sonst
        // vollständig aus, obwohl ein Substrat fehlt.
        <Hint tone="warn" className="scope-failed">
          Not resolved, left out of the figure: {failed.join(", ")}
        </Hint>
      )}
      <PanelFoot files={fileEntries(data.files)}>
        <ExportPngButton svg={data.svg} filename={data.name || "scope"} size="sm" />
      </PanelFoot>
    </Panel>
  );
}
