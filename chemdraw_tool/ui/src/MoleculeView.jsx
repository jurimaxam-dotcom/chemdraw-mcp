import React, { useCallback, useId, useRef, useState } from "react";
import AmbiguousView from "./AmbiguousView";
import CopyButton from "./components/CopyButton";
import FunctionalGroupList, { GroupNote } from "./components/FunctionalGroupList";
import ExportPngButton from "./components/ExportPngButton";
import AddToAnkiButton from "./components/AddToAnkiButton";
import SourceList from "./components/SourceList";
import StereoNote, { useStereoHighlight } from "./components/StereoNote";
import StructureCanvas from "./components/StructureCanvas";
import ViewToggle from "./components/ViewToggle";
import { useAppBridge } from "./AppContext";
import { extractToolData } from "./utils/toolData";

// Ein ruhiger Satz statt eines Stacktrace: der Klick muss sichtbar landen,
// sonst sieht ein Fehlschlag aus wie ein toter Knopf.
export const DATA_LOAD_ERROR =
  "The data sheet could not be loaded. Click Data again to retry.";
export const VARIANTS_LOAD_ERROR =
  "The stereoisomers could not be loaded. Click Show variants again to retry.";

// Spiegel der Server-Grenze (generator.MAX_OPEN_STEREO): mehr offene Elemente
// waeren 16+ Bilder, der Server lehnt ab — dann gar kein Knopf.
const MAX_OPEN_STEREO = 3;

export default function MoleculeView({ data }) {
  const app = useAppBridge();
  const uid = useId();
  const [hoveredGroup, setHoveredGroup] = useState(null);
  const [view, setView] = useState("structure");
  // Skelettformel ⇄ alle H — eine eigene Achse neben Struktur/Daten. Beide
  // Zeichnungen liegen schon im Payload, der Klick bleibt lokal.
  const [allH, setAllH] = useState(false);
  // Gecachtes DatabasePayload. Nur Erfolge landen hier — ein Fehlschlag bleibt
  // wiederholbar, statt sich als leeres Datenblatt einzubrennen.
  const [sheet, setSheet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const inFlight = useRef(false); // blockiert den re-entranten Doppelklick
  // Zuletzt geaeusserter Wunsch des Nutzers. Waehrend das Datenblatt laedt,
  // kann er zurueck auf die Struktur klicken — das eintreffende Ergebnis darf
  // ihm die Ansicht dann nicht wieder wegziehen. Bei PubChem-Latenz ist das
  // kein Randfall.
  const wanted = useRef("structure");
  // Stereo-Varianten: einmal geholt, dann gecacht wie das Datenblatt.
  const [variants, setVariants] = useState(null);
  const [showVariants, setShowVariants] = useState(false);
  const [variantsLoading, setVariantsLoading] = useState(false);
  const [variantsFailed, setVariantsFailed] = useState(false);
  const variantsInFlight = useRef(false);

  const props = data.properties || {};
  // Welchen PubChem-Datensatz die Zahlen beschreiben. Steht im Kopf, weil ein
  // falsch aufgeloester Name sonst nirgends auffaellt: die Struktur passt dann
  // zu den Werten, nur eben zum falschen Stoff.
  const record = props.pubchemTitle
    ? `PubChem: ${props.pubchemTitle}${props.cid ? ` (CID ${props.cid})` : ""}`
    : "";
  const groups = data.functionalGroups || [];
  const stereo = useStereoHighlight(data.stereoWarnings || []);
  const formula = data.formula ?? props.formula;
  const smiles = data.smiles ?? props.smiles;
  // SMILES zuerst: die sind laut Tool-Doku immer aufloesbar, ein Name kann
  // danebengehen.
  const query = smiles || data.name || "";
  // Export folgt der Ansicht: der PNG-Knopf nimmt dieselbe Zeichnung wie die Flaeche.
  const showAllH = allH && Boolean(data.svgAllH);
  const svg = showAllH ? data.svgAllH : data.svg;
  const atoms = showAllH ? data.atomsAllH : data.atoms;

  const handleView = useCallback(
    async (next) => {
      wanted.current = next;
      if (next === "structure") {
        setView("structure");
        return;
      }
      if (sheet) {
        setView("data"); // schon geholt — kein zweiter Netzweg
        return;
      }
      if (inFlight.current) return;
      inFlight.current = true;
      setLoading(true);
      setFailed(false);
      try {
        if (!query) throw new Error("kein Stoff bekannt");
        if (!app?.callServerTool) throw new Error("keine App-Bruecke");
        const result = await app.callServerTool({
          name: "lookup_molecule_data",
          arguments: { name: query },
        });
        // extractToolData deckt beides ab: die harte isError-Flagge des SDK
        // und Claude Desktops gestripptes structuredContent.
        const payload = extractToolData(result);
        if (!payload) throw new Error("kein verwertbares Payload");
        setSheet(payload);
      } catch {
        setFailed(true);
      } finally {
        setLoading(false);
        inFlight.current = false;
        // Nur umschalten, wenn der Nutzer inzwischen nicht zurueckgewechselt
        // hat. Geholt ist trotzdem geholt — der Cache steht.
        if (wanted.current === "data") setView("data");
      }
    },
    [app, query, sheet]
  );

  const stereoCount = (data.stereoWarnings || []).length;
  const canShowVariants = Boolean(query) && stereoCount > 0 && stereoCount <= MAX_OPEN_STEREO;

  async function openVariants() {
    if (variants) {
      setShowVariants(true);
      return;
    }
    if (variantsInFlight.current) return;
    variantsInFlight.current = true;
    setVariantsLoading(true);
    setVariantsFailed(false);
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const args = { name_or_smiles: query, stereo_variants: true };
      // Ein SMILES als Name vor „(S)-“ waere unlesbar — dann nur der Deskriptor.
      if (data.name && data.name !== smiles) args.label = data.name;
      const result = await app.callServerTool({ name: "generate_molecule", arguments: args });
      const payload = extractToolData(result);
      if (!payload || payload.type !== "ambiguous") throw new Error("keine Varianten");
      setVariants(payload);
      setShowVariants(true);
    } catch {
      setVariantsFailed(true);
    } finally {
      setVariantsLoading(false);
      variantsInFlight.current = false;
    }
  }

  if (showVariants && variants) {
    return (
      <AmbiguousView data={variants}
        subtitle={`${variants.candidates.length} stereoisomers. Pick one to draw it with wedges.`}
        backBar={<button type="button" className="candidate-back" onClick={() => setShowVariants(false)}>
          Back to the structure
        </button>} />
    );
  }

  return (
    <article className="molecule-panel">
      <header className="panel-header">
        <div className="panel-heading">
          <h2 className="panel-title">{data.name || "Molecule"}</h2>
          {record && <p data-testid="pubchem-record" className="panel-record">{record}</p>}
        </div>
        <div className="panel-actions">
          {query && <ViewToggle view={view} onChange={handleView} loading={loading} idPrefix={uid} />}
          {svg && <ExportPngButton svg={svg} filename={data.name || "molecule"} />}
          {smiles && <AddToAnkiButton smiles={smiles} name={data.name} formula={formula} cas={props.cas} />}
        </div>
      </header>
      {view === "structure" ? (
        <div id={`${uid}-structure`} role="tabpanel" aria-labelledby={`${uid}-tab-structure`} data-view="structure">
          <div className="structure-layout">
            <StructureCanvas svg={svg} atoms={atoms} groups={groups} hoveredGroup={hoveredGroup} onHoverGroup={setHoveredGroup} highlightAtoms={stereo.highlightAtoms} />
            <dl className="key-facts" aria-label="Molecule details">
              <Fact label="Formula" value={formula && <Formula text={formula} />} copy={formula} />
              <Fact label="Molar mass" value={molarMass(props.mw)} />
              <Fact label="CAS" value={props.cas} copy={props.cas} />
            </dl>
          </div>
          {data.svgAllH && <div className="structure-tools">
            <button type="button" className="chip-toggle" aria-pressed={showAllH} onClick={() => setAllH((v) => !v)}
              title={showAllH ? "Back to the skeletal formula" : "Draw every hydrogen atom"}>All H</button>
          </div>}
          <StereoNote {...stereo.noteProps} onShowVariants={canShowVariants ? openVariants : undefined}
            variantsBusy={variantsLoading} />
          {variantsFailed && <Note>{VARIANTS_LOAD_ERROR}</Note>}
          {groups.length > 0 && <section className="group-section" aria-label="Functional groups">
            <h3 className="section-label">Functional groups</h3>
            <FunctionalGroupList groups={groups} hoveredGroup={hoveredGroup} onHoverGroup={setHoveredGroup} />
            <GroupNote groups={groups} hoveredGroup={hoveredGroup} />
          </section>}
        </div>
      ) : (
        <div id={`${uid}-data`} role="tabpanel" aria-labelledby={`${uid}-tab-data`} data-view="data" className="data-panel">
          {sheet ? <SourceList sources={sheet.sources} moleculeSvg={sheet.molecule_svg || data.svg} /> : <Note>{failed ? DATA_LOAD_ERROR : "Loading the data sheet…"}</Note>}
        </div>
      )}
    </article>
  );
}

function Note({ children }) {
  return <div className="panel-note" role="status">{children}</div>;
}

// Der Server liefert "233.31 g/mol", aeltere Payloads nur die Zahl.
function molarMass(mw) {
  if (mw == null || mw === "") return null;
  return /g\/mol/.test(String(mw)) ? String(mw) : `${mw} g/mol`;
}

// Zahlen in der Summenformel tiefgestellt: C9H8O4 → C₉H₈O₄.
function Formula({ text }) {
  return String(text).split(/(\d+)/).map((part, i) =>
    /^\d+$/.test(part) ? <sub key={i}>{part}</sub> : part);
}

function Fact({ label, value, copy }) {
  if (value == null || value === "") return null;
  return <div className="fact">
    <dt>{label}</dt>
    <dd><span>{value}</span>{copy && <CopyButton text={String(copy)} size="sm" />}</dd>
  </div>;
}
