// Demo-Short 9:16: Hook → Eingabezeile (Kamera fährt aufs Feld) → Schwenk aufs echte
// Panel (Aufnahme aus demo.record.mjs, Kamera aus dem Click-Log) → Abspann.
// Bewusst keine Nachbildung der Claude-Oberfläche: die Eingabezeile ist eine eigene,
// schlichte Zeile; echt ist nur das Panel.
import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CAMERA_BEZIER } from "./lib/camera.ts";
import type { ClickLog } from "./lib/click-log.ts";
import { buildTrack, placePanel, sampleTrack, type Stage } from "./lib/track.ts";
import { HOOK_TEXT, PROMPT_TEXT, T, enterAt, outroStart, panStart, panelStart, typeEnd } from "./lib/timeline.ts";

export type ShortProps = { video: string; log: ClickLog };

// Palette in vier Ebenen, aus dem Dunkelmodus des Panels abgeleitet (styles.css):
// Papier, Tinte, Neutrale mit Grünstich, EIN Akzent (--accent des Panels, aufgehellt).
const C = {
  paper: "#141b18",
  ink: "#e6ede8",
  muted: "#9fb0a6",
  line: "#34413a",
  field: "#1d2622",
  accent: "#3a9e8f",
};
// Systemschrift mit Absicht: das Panel rendert in der Host-Schrift, also spricht
// das Video dieselbe Type wie das Gefilmte.
const FONT = '-apple-system, "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif';
const MONO = '"SF Mono", Menlo, ui-monospace, monospace';

const STAGE: Stage = { frameW: 1080, frameH: 1920, fit: 0.92 };

const ease = (t: number, a: number, b: number) => CAMERA_BEZIER(Math.min(1, Math.max(0, (t - a) / (b - a))));
const fade = (t: number, a: number, b: number) => interpolate(t, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

const Hook: React.FC<{ t: number }> = ({ t }) => {
  const words = HOOK_TEXT.split(" ");
  const out = 1 - fade(t, T.hookOut - 0.25, T.hookOut);
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: "0 96px", opacity: out }}>
      <div style={{ fontFamily: FONT, fontSize: 112, lineHeight: 1.05, fontWeight: 700, color: C.ink, letterSpacing: -2 }}>
        {words.map((w, i) => {
          const p = ease(t, 0.12 + i * 0.09, 0.62 + i * 0.09);
          return (
            <span key={i} style={{ display: "inline-block", marginRight: 26, opacity: p, transform: `translateY(${(1 - p) * 40}px)` }}>
              {w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const PromptField: React.FC<{ t: number }> = ({ t }) => {
  const n = Math.max(0, Math.min(PROMPT_TEXT.length, Math.floor((t - T.typeStart) / T.charS) + 1));
  const typed = t < T.typeStart ? "" : PROMPT_TEXT.slice(0, n);
  const typing = t >= T.typeStart && t < typeEnd();
  const caretOn = typing || Math.floor(t / 0.5) % 2 === 0;
  const pressed = t >= enterAt() && t < enterAt() + 0.16;
  const sent = t >= enterAt();
  return (
    <div style={{ width: 780, height: 140, borderRadius: 30, background: C.field, border: `2px solid ${sent ? C.accent : C.line}`, display: "flex", alignItems: "center", padding: "0 18px 0 44px", boxSizing: "border-box", boxShadow: "0 30px 80px rgba(0,0,0,.45)" }}>
      <div style={{ flex: 1, fontFamily: FONT, fontSize: 54, color: typed ? C.ink : C.muted, whiteSpace: "pre" }}>
        {typed || "Ask for a structure…"}
        {caretOn && typed !== "" && <span style={{ display: "inline-block", width: 4, height: 62, background: C.accent, marginLeft: 4, verticalAlign: -10 }} />}
      </div>
      {/* Senden: eigenes Strich-Icon (SVG), keine OS-Glyphe */}
      <div style={{ width: 112, height: 112, borderRadius: 22, background: typed ? C.accent : C.line, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${pressed ? 0.88 : 1})` }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke={C.paper} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" />
        </svg>
      </div>
    </div>
  );
};

const Outro: React.FC<{ t: number; start: number }> = ({ t, start }) => {
  // Erst deckt der Grund das Panel ab, dann kommt die Schrift — nie Schrift über Panel
  const p = ease(t, start + 0.3, start + 1.0);
  const q = ease(t, start + 0.55, start + 1.25);
  return (
    <AbsoluteFill style={{ background: C.paper, opacity: fade(t, start, start + 0.35), justifyContent: "center", alignItems: "center", fontFamily: FONT, color: C.ink }}>
      <div style={{ transform: `translateY(${(1 - p) * 30}px)`, opacity: p, fontSize: 120, fontWeight: 700, letterSpacing: -3 }}>chemdraw-mcp</div>
      <div style={{ opacity: q, marginTop: 28, fontSize: 56, color: C.muted }}>free &amp; open source</div>
      <div style={{ opacity: q, marginTop: 120, fontFamily: MONO, fontSize: 40, color: C.ink, borderBottom: `3px solid ${C.accent}`, paddingBottom: 10 }}>
        github.com/jurimaxam-dotcom/chemdraw-mcp
      </div>
    </AbsoluteFill>
  );
};

export const Short: React.FC<ShortProps> = ({ video, log }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  const keys = React.useMemo(() => buildTrack(log, STAGE), [log]);

  // Schwenk: Eingabe und Panel liegen untereinander auf einer hohen Bühne
  const pan = ease(t, panStart(), panStart() + T.panS);
  const promptZoom = 1 + 0.26 * ease(t, T.zoomIn, T.typeStart + 0.6);
  const panelPose = sampleTrack(keys, Math.max(0, t - panelStart()));
  const panel = placePanel(panelPose, log.viewport, STAGE);
  const trimFrames = Math.round(((log.trimBeforeMs ?? 0) + (log.offsetMs ?? 0)) / 1000 * fps);
  const promptOn = fade(t, T.promptIn - 0.1, T.promptIn + 0.3);
  const oStart = outroStart(log);

  return (
    <AbsoluteFill style={{ background: C.paper }}>
      {t < T.hookOut + 0.05 && <Hook t={t} />}

      {t >= T.promptIn - 0.1 && t < panStart() + T.panS + 0.1 && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: promptOn, transform: `translateY(${-pan * height}px) scale(${promptZoom})` }}>
          <PromptField t={t} />
        </AbsoluteFill>
      )}

      {/* Sequence: Videozeit 0 (= trimBefore) liegt auf panelStart, wie die Kameraspur */}
      <Sequence from={Math.round(panelStart() * fps)} durationInFrames={Math.round((oStart + 0.5 - panelStart()) * fps)} layout="none">
        <AbsoluteFill style={{ transform: `translateY(${(1 - pan) * height}px)` }}>
          <div style={{ position: "absolute", left: panel.left, top: panel.top, width: panel.width, height: panel.height, borderRadius: 24 * panelPose.scale, overflow: "hidden", boxShadow: "0 40px 120px rgba(0,0,0,.5)", background: "#fafbf9" }}>
            <OffthreadVideo src={staticFile(video)} trimBefore={trimFrames} muted style={{ width: "100%", height: "100%", display: "block" }} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {t >= oStart && <Outro t={t} start={oStart} />}
    </AbsoluteFill>
  );
};
