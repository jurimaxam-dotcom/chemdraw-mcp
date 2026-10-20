// Zeitplan des Shorts (Sekunden). Ein Ort für alle Schnittpunkte, damit Root
// (Länge der Komposition) und Short (wann was zu sehen ist) nicht auseinanderlaufen.
import type { ClickLog } from "./click-log.ts";

export const FPS = 30;
export const SIZE = { width: 1080, height: 1920 };

export const PROMPT_TEXT = "draw aspirin";
export const HOOK_TEXT = "Still drawing molecules by hand?";

export const T = {
  hookOut: 1.75, // Hook blendet aus …
  promptIn: 1.8, // … Eingabezeile blendet ein
  zoomIn: 2.0, // Kamera fährt aufs Feld
  typeStart: 2.45,
  charS: 0.075, // Tippgeschwindigkeit
  enterAfter: 0.35, // Pause nach dem letzten Zeichen, dann „Enter"
  panAfterEnter: 0.35, // Schwenk aufs Panel
  panS: 1.1,
  outroS: 2.8,
  outroOverlap: 0.35,
};

export const typeEnd = () => T.typeStart + PROMPT_TEXT.length * T.charS;
export const enterAt = () => typeEnd() + T.enterAfter;
export const panStart = () => enterAt() + T.panAfterEnter;
/** Ab hier läuft die Panel-Aufnahme (Schnittanfang des Click-Logs). */
export const panelStart = () => panStart();
export const panelEnd = (log: ClickLog) => panelStart() + log.durationMs / 1000;
export const outroStart = (log: ClickLog) => panelEnd(log) - T.outroOverlap;
export const totalSeconds = (log: ClickLog) => outroStart(log) + T.outroS;
