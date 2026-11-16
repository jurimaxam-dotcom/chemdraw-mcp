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

// Wie frontText, aber Zeilenumbrüche bleiben (Rückseiten: Name<br>Klasse); Lücken eines
// Lückentexts ({{c1::Antwort::Hinweis}}) erscheinen als […] wie auf der Vorderseite in Anki.
export function cardText(html) {
  const tpl = document.createElement("template");
  tpl.innerHTML = String(html ?? "")
    .replace(/\{\{c\d+::.*?\}\}/g, "[…]")
    .replace(/<br\s*\/?>/gi, "\n");
  return (tpl.content.textContent || "")
    .split("\n").map((line) => line.replace(/\s+/g, " ").trim()).filter(Boolean).join("\n");
}

function delivered(delivery) {
  if (delivery === "ankiconnect") return "imported into Anki via AnkiConnect";
  if (delivery === "open") return "opened in Anki";
  if (delivery?.startsWith("ankiconnect-")) return "AnkiConnect unreachable — import the .apkg manually";
  return "import the .apkg into Anki";
}

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

function Side({ side, label, text, image }) {
  const shown = cardText(text);
  return (
    <div className="anki-side" data-side={side}>
      <span className="anki-side-label">{label}</span>
      {image && <img className="anki-thumb" src={image} alt={`${label} image`} />}
      {shown && <p className="anki-side-text" title={shown}>{shown}</p>}
    </div>
  );
}

// Etappe 5 (16.11.2026): Deckname, Kartenzahl, Vorschau der ersten Karten (Vorder- und
// Rückseite nebeneinander, mit dem Kartenbild), „+ n more“ und der Ablageort der .apkg.
// Vorher: Titel und die Vorderseiten als Liste — bei Strukturkarten zweimal dieselbe Frage.
// Bewusst keine Aktion hier: nichts startet Anki oder ändert dort etwas.
export default function AnkiDeckView({ data }) {
  useModelContextReport(genericContext("anki_deck", data), data.name || "anki_deck");
  const previews = data.previews || [];
  const fronts = data.fronts || [];
  const shown = previews.length ? previews.length : Math.min(fronts.length, MAX_FRONTS);
  const total = Math.max(data.cards ?? 0, previews.length ? fronts.length : 0, shown);
  const more = total - shown;

  return (
    <div className="anki-panel">
      <SectionHeader
        title={data.name || "Anki deck"}
        subtitle={`${plural(data.cards ?? 0, "card")} · ${plural(data.media ?? 0, "image")} · ${delivered(data.delivery)}`}
      />
      <ol className={previews.length ? "anki-cards" : "anki-cards is-fronts"} aria-label="Card preview">
        {previews.length
          ? previews.map((p, i) => (
              <li key={i} className="anki-card" data-anki-card="">
                <Side side="front" label="Front" text={p.front} image={p.front_image} />
                <Side side="back" label="Back" text={p.back} image={p.back_image} />
              </li>
            ))
          : fronts.slice(0, MAX_FRONTS).map((front, i) => (
              <li key={i} className="anki-front" data-anki-card="">{frontText(front)}</li>
            ))}
      </ol>
      {more > 0 && <p className="anki-more">+ {plural(more, "more card")}</p>}
      {/* Fußzeile (E3): die .apkg-Datei mit Präfix und Kopierknopf; eine Aktion gibt es hier nicht. */}
      <PanelFooter files={data.file ? [{ label: "APKG", path: data.file }] : []} />
    </div>
  );
}
