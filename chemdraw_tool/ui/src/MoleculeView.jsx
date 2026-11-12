import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import AmbiguousView from "./AmbiguousView";
import CopyButton from "./components/CopyButton";
import FoundAs from "./components/FoundAs";
import FunctionalGroupList, { GroupNote } from "./components/FunctionalGroupList";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import AddToAnkiButton from "./components/AddToAnkiButton";
import SourceList from "./components/SourceList";
import StereoNote, { useStereoHighlight } from "./components/StereoNote";
import Ball3DCanvas from "./components/Ball3DCanvas";
import StructureCanvas from "./components/StructureCanvas";
import ViewToggle from "./components/ViewToggle";
import ContinueRow from "./components/ContinueRow";
import StudyPanel from "./components/StudyPanel";
import { useModelContextReport } from "./ModelContext";
import { moleculeFollowUps, studyFollowUps } from "./utils/followUps.js";
import { moleculeContext, moleculeSummary, studyItems } from "./utils/modelContext.js";
import { useAppBridge, useHostContext } from "./AppContext";
import { canRequestFullscreen } from "./utils/useHostLayout";
import { panelBackground, serializeLiveSvg } from "./utils/serializeSvg";
import { loadToolData } from "./utils/toolData";

// Ein ruhiger Satz statt eines Stacktrace: der Klick muss sichtbar landen,
// sonst sieht ein Fehlschlag aus wie ein toter Knopf.
export const DATA_LOAD_ERROR =
  "The data sheet could not be loaded. Click Data again to retry.";
export const VIEW_LOAD_ERROR =
  "This drawing could not be loaded. Click the button again to retry.";
export const VARIANTS_LOAD_ERROR =
  "The stereoisomers could not be loaded. Click Show variants again to retry.";
export const CONFORMER_LOAD_ERROR =
  "The 3D model could not be loaded. Click 3D again to retry.";

// Spiegel der Server-Grenze (generator.MAX_OPEN_STEREO): mehr offene Elemente
// waeren 16+ Bilder, der Server lehnt ab — dann gar kein Knopf.
const MAX_OPEN_STEREO = 3;

export default function MoleculeView({ data, expandable = true }) {
  const app = useAppBridge();
  const hostContext = useHostContext();
  const uid = useId();
  // Hover = Vorschau, pinned = festgehaltene Auswahl (U4): getrennt, damit das
  // Verlassen eines Atoms oder Chips die Auswahl nie löscht. Angezeigt wird der
  // Hover, sonst die Auswahl. pinned: {kind:"group",name} | {kind:"atom",idx,el} | null.
  const [hoveredGroup, setHoveredGroup] = useState(null);
  const [pinned, setPinned] = useState(null);
  const [view, setView] = useState("structure");
  // Lernmodus (U4b): Schlüssel der aufgedeckten Stücke ("name", "formula",
  // "mass", "cas", "group:<Name>") und die Gruppe, die gerade leuchtet.
  const [revealed, setRevealed] = useState([]);
  const [studyFocus, setStudyFocus] = useState(null);
  // Skelettformel ⇄ alle H ⇄ Fischer ⇄ Haworth — eine eigene Achse neben
  // Struktur/Daten. Das Payload sagt nur, welche Ansichten es gibt; der erste
  // Klick holt die Zeichnung, danach Cache wie beim Datenblatt (Jay 26.10.:
  // eager waren sie mehr als die Hälfte jeder Antwort). Ein zweiter Klick auf
  // denselben Knopf führt zur Skelettformel zurück.
  // Hat das Modell eine Ansicht selbst angefordert (view=…), liegt sie schon
  // im Payload: das Panel startet dort und lädt sie nicht noch einmal.
  const [drawing, setDrawing] = useState(() => (data.initialView && data.viewSvg ? data.initialView : "skeletal"));
  const [drawingCache, setDrawingCache] = useState(() => (data.initialView && data.viewSvg
    ? { [data.initialView]: { svg: data.viewSvg, atoms: data.viewAtoms || [] } } : {}));
  const [drawingBusy, setDrawingBusy] = useState("");
  const [drawingFailed, setDrawingFailed] = useState(false);
  // Je Ansicht ein eigener Flug: ein zweiter Klick auf eine andere Ansicht,
  // während die erste lädt, holt seine Zeichnung selbst — der zuletzt gewählte
  // Zustand gewinnt (Fund d, 09.11.). Nur derselbe Knopf doppelt wird geblockt.
  const drawingInFlight = useRef(new Set());
  const wantedDrawing = useRef(drawing);
  // 3D-Knopf: dieselbe Achse wie All H, nur ein anderes Werkzeug dahinter
  // (generate_3d, lazy, dann Cache). Zeigt er, weicht die 2D-Zeichnung —
  // eine Zeichenfläche, nie zwei. Ein 2D-Knopf holt sie zurück.
  const [conformer, setConformer] = useState(null);
  const [show3d, setShow3d] = useState(false);
  const [conformerBusy, setConformerBusy] = useState(false);
  const [conformerFailed, setConformerFailed] = useState(false);
  const conformerInFlight = useRef(false);
  const wanted3d = useRef(false);
  const viewer3d = useRef(null); // Fläche der Kuhle: Export PNG liest dort das aktuelle SVG
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
  // Projektionen tragen keine Atomliste — dort gibt es keine Overlays.
  const views = data.viewRequest ? data.views || [] : [];
  const shown = drawingCache[drawing] ? drawing : "skeletal";
  const { svg, atoms } = drawingCache[shown] || { svg: data.svg, atoms: data.atoms };

  // „2D“: zurück zur Skelettformel — sie steckt im Payload, nichts zu laden.
  function showSkeletal() {
    wanted3d.current = false;
    setShow3d(false);
    wantedDrawing.current = "skeletal";
    setDrawing("skeletal");
    // Der Hinweis galt dem fehlgeschlagenen Laden, nicht der Skelettformel.
    setDrawingFailed(false);
    setConformerFailed(false);
  }

  async function toggleDrawing(next) {
    // Aus 3D heraus holt der Klick die Zeichnung zurück — auch wenn ihr Knopf
    // vor dem 3D-Klick schon gedrückt war; erst der nächste Klick geht zur Skelettformel.
    const was3d = show3d;
    wanted3d.current = false;
    setShow3d(false);
    if (shown === next && !was3d) {
      wantedDrawing.current = "skeletal";
      setDrawing("skeletal");
      return;
    }
    wantedDrawing.current = next;
    if (drawingCache[next]) {
      setDrawing(next);
      setDrawingFailed(false);
      return;
    }
    if (drawingInFlight.current.has(next)) return;
    drawingInFlight.current.add(next);
    setDrawingBusy(next);
    setDrawingFailed(false);
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const result = await app.callServerTool({
        name: "generate_molecule",
        arguments: { ...data.viewRequest, view: next },
      });
      const payload = await loadToolData(app, result);
      if (!payload?.viewSvg) throw new Error("keine Zeichnung");
      setDrawingCache((c) => ({ ...c, [next]: { svg: payload.viewSvg, atoms: payload.viewAtoms || [] } }));
      // Wer inzwischen anderswohin geklickt hat, behält seine Ansicht.
      if (wantedDrawing.current === next) setDrawing(next);
    } catch {
      // Der Hinweis gilt nur der Ansicht, die der Nutzer noch will.
      if (wantedDrawing.current === next) setDrawingFailed(true);
    } finally {
      drawingInFlight.current.delete(next);
      const still = wantedDrawing.current;
      setDrawingBusy(drawingInFlight.current.has(still) ? still : "");
    }
  }

  async function toggle3d() {
    if (show3d) {
      wanted3d.current = false;
      setShow3d(false);
      return;
    }
    wanted3d.current = true;
    if (conformer) {
      setShow3d(true);
      return;
    }
    if (conformerInFlight.current) return;
    conformerInFlight.current = true;
    setConformerBusy(true);
    setConformerFailed(false);
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const args = { name_or_smiles: query };
      if (data.name && data.name !== smiles) args.label = data.name;
      const result = await app.callServerTool({ name: "generate_3d", arguments: args });
      const payload = await loadToolData(app, result);
      if (!payload?.atoms?.length) throw new Error("kein Konformer");
      setConformer(payload);
      if (wanted3d.current) setShow3d(true);
    } catch {
      setConformerFailed(true);
    } finally {
      setConformerBusy(false);
      conformerInFlight.current = false;
    }
  }

  const handleView = useCallback(
    async (next) => {
      wanted.current = next;
      // Struktur und Lernmodus sind lokal — kein Toolaufruf.
      if (next === "structure" || next === "study") {
        setView(next);
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
        // loadToolData deckt alles ab: die harte isError-Flagge des SDK,
        // Claude Desktops gestripptes structuredContent und (M2) die
        // zurückgehaltenen Bilder eines großen Datenblatts.
        const payload = await loadToolData(app, result);
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

  const is3d = show3d && Boolean(conformer);
  // Die Datenseite zeigt keine Kuhle — dort exportiert die Fußzeile die 2D-Zeichnung.
  const footer3d = is3d && view === "structure";
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
      const payload = await loadToolData(app, result);
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

  // Ein Atom-Index gilt nur für die Zeichnung, in der er angeklickt wurde.
  useEffect(() => {
    setPinned((p) => (p?.kind === "atom" ? null : p));
  }, [shown, show3d]);

  function pinGroup(name) {
    setPinned((p) => (p?.kind === "group" && p.name === name ? null : { kind: "group", name }));
  }
  function pickAtom(atom, group) {
    if (group) return pinGroup(group.name);
    setPinned((p) => (p?.kind === "atom" && p.idx === atom.idx ? null : { kind: "atom", idx: atom.idx, el: atom.el }));
  }
  const clearPin = () => setPinned(null);

  const items = studyItems(data);
  const reveal = (key) => {
    setRevealed((r) => (r.includes(key) ? r : [...r, key]));
    if (key.startsWith("group:")) setStudyFocus(key.slice(6));
  };
  const nameOpen = revealed.includes("name") || !data.name;
  const left = items.filter((i) => !revealed.includes(i.key)).length;
  const counter = left === 0 ? "Everything revealed" : `${left} of ${items.length} still covered`;

  // Zeigt das Panel die Stereo-Varianten, ist diese Struktur verdeckt: dann meldet
  // sie nichts — sonst läse Claude die Ausgangsstruktur samt alter Auswahl.
  const hiddenByVariants = showVariants && Boolean(variants);
  const { flush, canAsk } = useModelContextReport(
    hiddenByVariants ? "" : moleculeContext(data, { view, drawing: shown, is3d: show3d && Boolean(conformer), pinned, revealed }),
    hiddenByVariants ? "" : moleculeSummary(data),
  );
  const followUps = view === "study"
    ? studyFollowUps({ name: data.name, smiles, nameRevealed: nameOpen })
    : moleculeFollowUps({ name: data.name, smiles, groups, atoms: data.atoms, pinned });

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
          {view === "study" && !nameOpen
            ? <button type="button" className="study-name" onClick={() => reveal("name")}>Which compound is this? Show name</button>
            : <>
              <h2 className="panel-title">{data.name || "Molecule"}</h2>
              {record && <p data-testid="pubchem-record" className="panel-record">{record}</p>}
              <FoundAs value={data.foundAs} />
            </>}
          {view === "study" && <p className="panel-record study-counter" role="status">{counter}</p>}
        </div>
        {(query || (expandable && canRequestFullscreen(hostContext))) && <div className="panel-actions">
          {query && <ViewToggle view={view} onChange={handleView} loading={loading} idPrefix={uid} study />}
          {/* Im Stapel (batch) vergrößert man das Panel, nicht eine Karte: dort kein Knopf. */}
          {expandable && <ExpandButton app={app} hostContext={hostContext} />}
        </div>}
      </header>
      {view === "study" ? (
        <StudyPanel uid={uid} svg={data.svg} atoms={data.atoms} groups={groups} revealed={revealed}
          focusGroup={studyFocus} onReveal={reveal} onFocusGroup={setStudyFocus}
          facts={[
            formula && { key: "formula", label: "Formula", value: <Formula text={formula} /> },
            props.mw && { key: "mass", label: "Molar mass", value: molarMass(props.mw) },
            props.cas && { key: "cas", label: "CAS", value: props.cas },
          ].filter(Boolean)}
          onRevealAll={() => setRevealed(items.map((i) => i.key))}
          onCover={() => { setRevealed([]); setStudyFocus(null); }} />
      ) : view === "structure" ? (
        <div id={`${uid}-structure`} role="tabpanel" aria-labelledby={`${uid}-tab-structure`} data-view="structure">
          <div className="structure-layout" data-layout-3d={is3d ? "" : undefined}>
            {/* Zeichenfläche und Ansicht-Achse als eine Spalte: die Achse sitzt direkt
                unter Zeichnung oder Kuhle, vor den Kernwerten (Design-Kritik Rang 3). */}
            <div className="structure-main">
              {is3d
                ? <div className="structure-canvas structure-3d" data-view-3d="" ref={viewer3d}>
                    <Ball3DCanvas atoms={conformer.atoms} bonds={conformer.bonds || []} />
                  </div>
                : <StructureCanvas svg={svg} atoms={atoms} groups={groups}
                    hoveredGroup={hoveredGroup || (pinned?.kind === "group" ? pinned.name : null)}
                    pinnedAtom={pinned?.kind === "atom" ? pinned.idx : undefined}
                    onHoverGroup={setHoveredGroup} onPickAtom={pickAtom} highlightAtoms={stereo.highlightAtoms} />}
              {(views.length > 0 || query) && <div className="seg view-axis" data-view-axis="" role="group" aria-label="Drawing">
                <AxisButton pressed={!show3d && shown === "skeletal"} onClick={showSkeletal}
                  title="Skeletal formula">2D</AxisButton>
                {DRAWING_TOGGLES.filter((t) => views.includes(t.key)).map((t) =>
                  <AxisButton key={t.key} pressed={!show3d && shown === t.key} busy={drawingBusy === t.key}
                    onClick={() => toggleDrawing(t.key)}
                    title={!show3d && shown === t.key ? "Back to the skeletal formula" : t.title}>{t.label}</AxisButton>)}
                {query && <AxisButton pressed={show3d} busy={conformerBusy} onClick={toggle3d}
                  title={show3d ? "Back to the 2D drawing" : "Rotatable 3D model (ETKDG + force field)"}>3D</AxisButton>}
              </div>}
            </div>
            <dl className="key-facts" aria-label="Molecule details">
              <Fact label="Formula" value={formula && <Formula text={formula} />} copy={formula} />
              <Fact label="Molar mass" value={molarMass(props.mw)} />
              <Fact label="CAS" value={props.cas} copy={props.cas} />
            </dl>
          </div>
          {drawingFailed && <Note>{VIEW_LOAD_ERROR}</Note>}
          {conformerFailed && <Note>{CONFORMER_LOAD_ERROR}</Note>}
          {is3d && <p className="panel-note-quiet">Drag to rotate · explicit hydrogens</p>}
          {/* Stereo, Gruppen und der Projektionssatz beziehen sich auf die 2D-Zeichnung — in 3D aus.
              Der Satz steht dort, wo er etwas erklärt: mit Fischer-Knopf unter Fischer (offene
              Kette), ohne ihn unter Haworth (Glykosid: warum es keine Fischer-Projektion gibt). */}
          {!is3d && <>
            {shown === (views.includes("fischer") ? "fischer" : "haworth") && data.projectionNote
              && <Note>{data.projectionNote}</Note>}
            <StereoNote {...stereo.noteProps} onShowVariants={canShowVariants ? openVariants : undefined}
              variantsBusy={variantsLoading} />
            {variantsFailed && <Note>{VARIANTS_LOAD_ERROR}</Note>}
            {/* Fischer eines Ringzuckers zeigt die offene Kette; die Gruppen stammen aus der
                Ringform (Halbacetal statt Aldehyd) und stünden dort falsch. */}
            {groups.length > 0 && !(shown === "fischer" && data.projectionNote)
              && <section className="group-section" aria-label="Functional groups">
              <h3 className="section-label">Functional groups</h3>
              <FunctionalGroupList groups={groups} pinnedGroup={pinned?.kind === "group" ? pinned.name : null}
                onHoverGroup={setHoveredGroup} onPin={pinGroup} />
              <GroupNote groups={groups} hoveredGroup={hoveredGroup} pinned={pinned} canAsk={canAsk} onClear={clearPin} />
            </section>}
          </>}
        </div>
      ) : (
        <div id={`${uid}-data`} role="tabpanel" aria-labelledby={`${uid}-tab-data`} data-view="data" className="data-panel">
          {sheet ? <SourceList sources={sheet.sources} moleculeSvg={sheet.molecule_svg || data.svg} /> : <Note>{failed ? DATA_LOAD_ERROR : "Loading the data sheet…"}</Note>}
        </div>
      )}
      <ContinueRow actions={followUps} flush={flush} />
      {/* Fußzeile (E3): Dateien links, Aktionen rechts. In 3D die SDF-Datei des
          Konformers und Export der aktuellen Drehlage — die Kuhle ist reines SVG.
          Im Lernmodus ohne Pfade und ohne Export: beide tragen den Namen. */}
      <PanelFooter files={view === "study" ? [] : footer3d ? fileEntries(conformer.files) : fileEntries(data.files)}>
        {view === "study" ? null : footer3d
          ? <ExportPngButton size="sm" filename={`${data.name || "molecule"}-3d`}
              getSvg={() => serializeLiveSvg(viewer3d.current?.querySelector("svg"))}
              background={() => panelBackground(viewer3d.current)} />
          : svg && <ExportPngButton size="sm" svg={svg} filename={data.name || "molecule"} />}
        {smiles && <AddToAnkiButton size="sm" smiles={smiles} name={data.name} formula={formula} cas={props.cas} />}
      </PanelFooter>
    </article>
  );
}

// Eigener Vergrößern-Knopf (U2, M10): nur wenn der Host `fullscreen` anbietet und
// das Panel im Chat steht. requestDisplayMode direkt im Klick-Handler — Claude
// lehnt die Anfrage ohne frische Nutzeraktion ab. Nach dem Wechsel meldet der Host
// displayMode "fullscreen", der Knopf verschwindet von selbst.
function ExpandButton({ app, hostContext }) {
  if (!canRequestFullscreen(hostContext) || !app?.requestDisplayMode) return null;
  const expand = () => {
    app.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
  };
  return <button type="button" className="expand-button" onClick={expand}
    title="Open in the side panel">Expand</button>;
}

const DRAWING_TOGGLES = [
  { key: "all_h", label: "All H", title: "Draw every hydrogen atom" },
  { key: "fischer", label: "Fischer", title: "Fischer projection" },
  { key: "haworth", label: "Haworth", title: "Haworth projection" },
  { key: "chair", label: "Chair", title: "Chair conformation" },
];

// Ein Knopf der Ansicht-Achse. Lädt er, dreht sich derselbe Spinner wie am
// Daten-Reiter — aria-busy allein sähe aus wie ein toter Klick.
function AxisButton({ pressed, busy = false, onClick, title, children }) {
  return <button type="button" aria-pressed={pressed} aria-busy={busy}
    onClick={onClick} title={title}>
    {busy && <span className="seg-spinner" aria-hidden="true" />}{children}
  </button>;
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
