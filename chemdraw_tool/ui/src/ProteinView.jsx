import React, { useEffect, useMemo, useRef, useState } from "react";
import BackboneCanvas from "./components/BackboneCanvas";
import SectionHeader from "./components/SectionHeader";
import ExportPngButton from "./components/ExportPngButton";
import IgGScheme, { SCHEME_LEGEND } from "./components/IgGScheme";
import PanelFooter, { fileEntries } from "./components/PanelFooter";
import { panelBackground, serializeLiveSvg } from "./utils/serializeSvg";
import { loadEngine } from "./protein/loadEngine";
import { layout, ligandMmcif, proteinMmcif, decodeLigands } from "./protein/proteinData";
import { ELEMENT_COLOR, PLDDT_COLOR, PLDDT_NAME, SS_COLOR, SS_NAME, rainbow, residueColorer } from "./protein/colors";

// Chat-Einstieg für Proteine (E8, Cartoon seit E13): generate_molecule und
// generate_3d liefern type "protein". Kopf = Protein, Organismus, Quelle.
// Zeichenfläche: Cartoon über die Mol*-Engine (WebGL, erst hier geladen —
// protein/loadEngine.js). Startet sie nicht (kein WebGL-Kontext, Script
// blockiert, Engine wirft), bleibt die SVG-Spur stehen, die während des
// Ladens ohnehin schon zu sehen ist — nie eine leere Fläche.
// Umschalter: Farbe nach Sekundärstruktur / Kette / Regenbogen N→C /
// Konfidenz (nur AlphaFold); Darstellung Cartoon / Spur; Ansicht zurücksetzen.

const MODES = [
  ["ss", "Secondary"],
  ["chain", "Chain"],
  ["rainbow", "Rainbow N→C"],
  ["plddt", "Confidence"],
];
const STYLES = [
  ["cartoon", "Cartoon"],
  ["trace", "Trace"],
];
// Einblend-Drehung wie der Molekül-3D-Viewer (Ball3DCanvas): ~40° um y, 1,2 s
const INTRO_TURN = 0.7;
const INTRO_MS = 1200;

// Austauschbare Naht für die DOM-Tests (jsdom hat kein WebGL).
export const viewerDeps = { loadEngine };

function introWanted() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function legendFor(mode, protein) {
  if (mode === "chain") return protein.chains.map((c) => [c.color, `${c.label} (${c.id})`]);
  if (mode === "plddt") return ["4", "3", "2", "1"].map((k) => [PLDDT_COLOR[k], PLDDT_NAME[k]]);
  if (mode === "rainbow") return [[rainbow(0), "N-terminus"], [rainbow(1), "C-terminus"]];
  return ["H", "E", "C"].map((k) => [SS_COLOR[k], SS_NAME[k]]);
}

/** „heme b (HEM) ×4“, „Zn²⁺“ — gleiche Gruppen zusammengefasst. */
export function ligandLegend(ligands = []) {
  const groups = new Map();
  for (const l of decodeLigands(ligands)) {
    const key = `${l.name}|${l.code}`;
    const g = groups.get(key) || { ...l, count: 0 };
    g.count += 1;
    groups.set(key, g);
  }
  return [...groups.values()].map((g) => {
    // Ion: Elementfarbe der Kugel; organische Gruppe (auch Häm mit Fe): grau wie
    // ihre Kohlenstoff-Stäbe — Fe-Orange läse sich sonst wie eine Kettenfarbe
    const ion = g.elements.length === 1;
    const label = g.code.length <= 2 || g.name === g.code ? g.name : `${g.name} (${g.code})`;
    return { color: ion ? ELEMENT_COLOR[g.elements[0]] || ELEMENT_COLOR.C : ELEMENT_COLOR.C, text: label + (g.count > 1 ? ` ×${g.count}` : "") };
  });
}

/** CSS-Farbe → "#rrggbb" (die Engine braucht Hex; der Host liefert rgb()). */
export function cssHex(color, doc = typeof document !== "undefined" ? document : null) {
  if (/^#[0-9a-f]{6}$/i.test(color || "")) return color;
  const m = /rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/i.exec(color || "");
  if (m) return "#" + m.slice(1, 4).map((v) => Number(v).toString(16).padStart(2, "0")).join("");
  return "#ffffff";
}

/** Halbe Ausdehnung in x/y (Å) um den Mittelpunkt der Box — für die Ruhekamera. */
export function frameOf(segs, ligands = []) {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  const take = ([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); };
  for (const s of segs) s.ca.forEach(take);
  for (const l of decodeLigands(ligands)) l.xyz.forEach(take);
  if (!Number.isFinite(x0)) return { cx: 0, cy: 0, halfW: 10, halfH: 10 };
  return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, halfW: (x1 - x0) / 2 + 2.5, halfH: (y1 - y0) / 2 + 2.5 };
}

function sceneColors(segs, mode) {
  const colorOf = residueColorer(segs, mode);
  const colors = new Map();
  for (const seg of segs) seg.ca.forEach((_, i) => colors.set(`${seg.chain.id}:${seg.seq0 + i}`, colorOf(seg, i)));
  return colors;
}

export default function ProteinView({ data }) {
  const protein = data.protein || { chains: [] };
  const viewer = useRef(null);
  const host = useRef(null);
  const ctl = useRef(null);
  const [mode, setMode] = useState(protein.colorBy === "chain" ? "chain" : "ss");
  const [style, setStyle] = useState("cartoon");
  const [engine, setEngine] = useState("loading"); // loading | ready | failed
  const [resetKey, setResetKey] = useState(0);
  // Antikörper: Struktur | Schema; allgemeiner Fall öffnet auf dem Schema
  const scheme = protein.scheme || null;
  const [pane, setPane] = useState(scheme?.start === "scheme" ? "scheme" : "structure");
  const onScheme = scheme && pane === "scheme";
  const isModel = protein.source === "alphafold";
  const modes = MODES.filter(([key]) => (key !== "plddt" || isModel) && (key !== "chain" || protein.chains.length > 1));
  const segs = useMemo(() => layout(protein), [protein]);
  const ligands = useMemo(() => ligandLegend(protein.ligands), [protein.ligands]);
  const ready = engine === "ready";
  const hint = ready
    ? "drag to rotate · pinch or ⌘/Ctrl+scroll to zoom · right-drag to move"
    : "drag to rotate";
  const subtitle = `${protein.subtitle || ""}${isModel && !(protein.subtitle || "").includes("predicted") ? " · predicted" : ""} · ${hint}`;

  // Engine starten — einmal je Datensatz; Fehlschlag = SVG-Spur bleibt.
  useEffect(() => {
    let alive = true;
    let made = null;
    setEngine("loading");
    (async () => {
      try {
        if (!segs.length) throw new Error("no backbone");
        const api = await viewerDeps.loadEngine();
        if (!alive || !host.current) return;
        made = await api.create(host.current, {
          protein: proteinMmcif(segs),
          ligands: ligandMmcif(protein.ligands),
          colors: sceneColors(segs, mode),
          fallback: SS_COLOR.C,
        }, { background: cssHex(panelBackground(host.current)), style, frame: frameOf(segs, protein.ligands) });
        if (!alive) {
          made.dispose();
          return;
        }
        ctl.current = made;
        setEngine("ready");
      } catch (err) {
        if (alive) setEngine("failed");
        if (typeof console !== "undefined") console.warn("protein cartoon unavailable, showing the backbone trace:", err?.message || err);
      }
    })();
    return () => {
      alive = false;
      ctl.current = null;
      made?.dispose();
    };
    // Farbe/Darstellung folgen per eigenem Effekt, ohne Neuaufbau
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [segs, protein.ligands]);

  // Einblend-Drehung erst nach dem Umschalten auf „ready“: dann stehen Leisten
  // und Hinweis, und die Ruhelage passt zur endgültigen Fläche
  useEffect(() => {
    if (!ready || !introWanted()) return undefined;
    const id = requestAnimationFrame(() => ctl.current?.intro?.(INTRO_TURN, INTRO_MS));
    return () => cancelAnimationFrame(id);
  }, [ready]);

  useEffect(() => {
    if (ready) ctl.current?.setColors(sceneColors(segs, mode)).catch(() => setEngine("failed"));
  }, [mode, ready, segs]);
  useEffect(() => {
    if (ready) ctl.current?.setStyle(style).catch(() => setEngine("failed"));
  }, [style, ready]);

  // Hell/dunkel folgt dem Host auch nach dem Start (Desktop schaltet live um)
  useEffect(() => {
    if (!ready || typeof window.matchMedia !== "function") return undefined;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const follow = () => ctl.current?.setBackground?.(cssHex(panelBackground(host.current)));
    mq.addEventListener?.("change", follow);
    return () => mq.removeEventListener?.("change", follow);
  }, [ready]);

  // Maß der Bildfläche für die SVG-Spur: viewBox = Pixel der Fläche, damit der
  // Rückfall sie ausfüllt wie der Cartoon (sonst 480 × 330 mit Briefkasten).
  // Ohne Layout (jsdom) bleibt es beim Vorgabemaß der Spur.
  const [stageSize, setStageSize] = useState({});
  useEffect(() => {
    const el = viewer.current;
    if (!el || typeof ResizeObserver === "undefined") return undefined;
    const measure = () => {
      const w = Math.round(el.clientWidth), h = Math.round(el.clientHeight);
      if (w > 0 && h > 0) setStageSize((s) => (s.width === w && s.height === h ? s : { width: w, height: h }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const resetView = () => {
    if (ready) ctl.current?.resetView();
    else setResetKey((k) => k + 1);
  };

  async function exportSource() {
    if (onScheme) return serializeLiveSvg(viewer.current?.querySelector("svg[data-igg-scheme]"));
    if (ready && ctl.current) {
      const box = host.current.getBoundingClientRect();
      const w = Math.round(box.width), h = Math.round(box.height);
      const snap = await ctl.current.snapshot(3);
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`
        + `<image href="${snap.url}" width="${w}" height="${h}"/></svg>`;
    }
    return serializeLiveSvg(viewer.current?.querySelector("svg[data-backbone]"));
  }

  return (
    <div
      className="protein-panel"
      style={{
        // keine feste Höhe (E19): die Bildfläche bemisst sich selbst
        // (.protein-stage), der Host bemisst das iframe am Inhalt
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader title={protein.title || data.name} subtitle={subtitle} />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center", marginBottom: 6 }}>
        {scheme && (
          <div className="seg" role="tablist" aria-label="View">
            {[["structure", "Structure"], ["scheme", "Scheme"]].map(([key, text]) => (
              <button key={key} type="button" role="tab" aria-selected={pane === key} onClick={() => setPane(key)}>
                {text}
              </button>
            ))}
          </div>
        )}
        {!onScheme && modes.length > 1 && (
          <div className="seg" role="tablist" aria-label="Colour by">
            {modes.map(([key, text]) => (
              <button key={key} type="button" role="tab" aria-selected={mode === key} onClick={() => setMode(key)}>
                {text}
              </button>
            ))}
          </div>
        )}
        {ready && !onScheme && (
          <div className="seg" role="tablist" aria-label="Representation">
            {STYLES.map(([key, text]) => (
              <button key={key} type="button" role="tab" aria-selected={style === key} onClick={() => setStyle(key)}>
                {text}
              </button>
            ))}
          </div>
        )}
        {!onScheme && <div className="seg">
          <button type="button" onClick={resetView} title="Back to the starting view">Reset</button>
        </div>}
      </div>
      <div ref={viewer} data-protein-viewer={engine} className="protein-stage">
        {!ready && <BackboneCanvas key={resetKey} chains={protein.chains} colorBy={mode} {...stageSize} />}
        <div
          ref={host}
          data-cartoon-host=""
          style={{ position: "absolute", inset: 0, visibility: ready && !onScheme ? "visible" : "hidden" }}
        />
        {onScheme && (
          <div style={{ position: "absolute", inset: 0, background: "var(--bg)" }}>
            <IgGScheme highlight={scheme.highlight} caption={scheme.caption} />
          </div>
        )}
      </div>
      {engine === "failed" && (
        <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>
          3D cartoon unavailable here (no WebGL) — showing the backbone trace.
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 14px", fontSize: 12, color: "var(--fg-muted)", margin: "6px 0 2px" }}>
        {(onScheme ? SCHEME_LEGEND : legendFor(mode, protein)).map(([color, text]) => (
          <span key={text} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 16, height: 5, borderRadius: 3, background: color }} />
            {text}
          </span>
        ))}
        {!onScheme && ligands.map(({ color, text }) => (
          <span key={`lig-${text}`} data-ligand="" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: 4, background: color }} />
            {text}
          </span>
        ))}
      </div>
      {scheme?.caption && (
        <div data-scheme-caption="" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{scheme.caption}</div>
      )}
      {protein.citation && (
        <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>{protein.citation}</div>
      )}
      <PanelFooter files={fileEntries(data.files)}>
        <ExportPngButton size="sm" filename={`${data.name || "protein"}-cartoon`}
          getSvg={exportSource}
          background={() => panelBackground(viewer.current)} />
      </PanelFooter>
    </div>
  );
}
