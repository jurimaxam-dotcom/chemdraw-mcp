// Kameraspur fürs Hochformat (eigener Code). Interpolation und Easing kommen aus
// camera.ts (programatic-demo); zoom.ts von dort ist für lange, ungeskriptete
// Klickfolgen gebaut und bewusst nicht übernommen — hier reichen wenige Beats.
//
// Raum: eine Pose ist (scale, cx, cy) mit cx/cy als Bruchteil des Panels (0..1),
// der in der Bildmitte liegt. scale 1 = Panel `fit` × Bildbreite breit.
import { clamp, interpolatePose, moveDuration, type CameraPose } from "./camera.ts";
import {
  CAMERA_LEAD_S,
  HOLD_MIN_S,
  LEAD_FALLBACK_S,
  SETTLE_BEFORE_PRESS_S,
  type ClickEvent,
  type ClickLog,
} from "./click-log.ts";

export type Box = { x: number; y: number; w: number; h: number };
export type Viewport = { width: number; height: number };
export type Stage = { frameW: number; frameH: number; fit: number };
export type Key = { t: number; pose: CameraPose };

/** Obergrenze wie upstream (zoom.ts S_MAX): darüber wird 2×-Footage weich. */
export const S_MAX = 1.74;
/** Inhalt füllt so viel der Bildbreite; der Rest ist Luft. */
const FILL = 0.94;
/** Planungswert für eine Kamerabewegung (Sekunden); die echte Dauer misst moveDuration. */
const MOVE_S = 0.85;
/** Unter dieser Lücke kehrt die Kamera nicht erst zur Grundpose zurück. */
const BACK_TO_BASE_GAP_S = 2 * MOVE_S + 0.6;

export const BASE_POSE: CameraPose = { scale: 1, cx: 0.5, cy: 0.5 };

/** Panelbreite in Bildpixeln bei `scale`. */
const panelW = (scale: number, stage: Stage) => stage.frameW * stage.fit * scale;

/**
 * Pro Achse: ist das Panel kleiner als das Bild, bleibt es ganz drin; ist es
 * größer, bleibt das Bild ganz im Panel. `half` = halbe Bildgröße in Panel-Bruchteilen.
 */
function clampAxis(c: number, half: number): number {
  return half >= 0.5 ? clamp(c, 1 - half, half) : clamp(c, half, 1 - half);
}

export function clampPose(pose: CameraPose, vp: Viewport, stage: Stage): CameraPose {
  const w = panelW(pose.scale, stage);
  const h = (w * vp.height) / vp.width;
  return {
    scale: pose.scale,
    cx: clampAxis(pose.cx, stage.frameW / (2 * w)),
    cy: clampAxis(pose.cy, stage.frameH / (2 * h)),
  };
}

/** Pose, die `box` (Viewport-px der Aufnahme) möglichst groß, aber ganz zeigt. */
export function framePose(box: Box, vp: Viewport, stage: Stage): CameraPose {
  const px = (stage.frameW * stage.fit) / vp.width; // Bildpixel pro Aufnahmepixel bei scale 1
  const sx = (stage.frameW * FILL) / (box.w * px);
  const sy = (stage.frameH * FILL) / ((box.h * px));
  const scale = clamp(Math.min(sx, sy), 1, S_MAX);
  return clampPose(
    { scale, cx: (box.x + box.w / 2) / vp.width, cy: (box.y + box.h / 2) / vp.height },
    vp,
    stage,
  );
}

/** Wo das Panel bei `pose` im Bild liegt (Bildpixel). */
export function placePanel(pose: CameraPose, vp: Viewport, stage: Stage) {
  const width = panelW(pose.scale, stage);
  const height = (width * vp.height) / vp.width;
  return {
    width,
    height,
    left: stage.frameW / 2 - pose.cx * width,
    top: stage.frameH / 2 - pose.cy * height,
  };
}

type Beat = { start: number; press?: number; end: number; pose: CameraPose };

const sameBox = (a?: Box, b?: Box) => !!a && !!b && a.x === b.x && a.y === b.y && a.w === b.w && a.h === b.h;

/** Log-Zeit (ms) → Sekunden ab Schnittanfang. */
const clock = (log: ClickLog) => (ms: number) => (ms - (log.trimBeforeMs ?? 0) + (log.offsetMs ?? 0)) / 1000;

/** Aufeinanderfolgende Ereignisse mit gleichem `content` sind EIN Beat (kein Zwischenschwenk). */
function beats(log: ClickLog, stage: Stage): Beat[] {
  const s = clock(log);
  const out: Beat[] = [];
  let prev: ClickEvent | null = null;
  for (const c of log.clicks) {
    // Hinter dem Schnitt (z. B. der Rückklick auf „Structure"): gehört nicht in den Clip
    if (s(c.tDepartMs ?? c.tMs) >= log.durationMs / 1000) continue;
    // Ein Beat ohne Zeigerweg und ohne Klick (Ergebnis erscheint) startet, wenn es da ist
    const depart = c.tDepartMs != null ? s(c.tDepartMs) : c.tDownMs != null ? s(c.tMs) - LEAD_FALLBACK_S : s(c.tMs) + CAMERA_LEAD_S;
    const press = c.tDownMs != null ? s(c.tDownMs) : undefined;
    if (prev && c.content && sameBox(c.content, prev.content)) {
      const b = out[out.length - 1];
      b.end = s(c.tMs);
      if (press != null) b.press ??= press;
    } else {
      out.push({ start: depart - CAMERA_LEAD_S, press, end: s(c.tMs), pose: framePose(c.content ?? c.rect!, log.viewport, stage) });
    }
    prev = c;
  }
  return out;
}

/** Halte- und Bewegungs-Keys: zwischen zwei Keys bewegt sich die Kamera, sonst steht sie. */
export function buildTrack(log: ClickLog, stage: Stage): Key[] {
  const keys: Key[] = [{ t: 0, pose: BASE_POSE }];
  const frame = { width: stage.frameW, height: stage.frameH };
  const dauer = (a: CameraPose, b: CameraPose) =>
    moveDuration(a, b, b.scale > a.scale + 1e-3 ? "in" : b.scale < a.scale - 1e-3 ? "out" : "pan", frame);
  const moveTo = (t: number, pose: CameraPose) => {
    const last = keys[keys.length - 1];
    const from = Math.max(t, last.t);
    keys.push({ t: from, pose: last.pose }, { t: from + dauer(last.pose, pose), pose });
  };
  const list = beats(log, stage);
  list.forEach((b, i) => {
    // Vor einem Klick muss die Kamera stehen, wenn gedrückt wird
    const prev = keys[keys.length - 1].pose;
    const start = b.press != null ? Math.min(b.start, b.press - SETTLE_BEFORE_PRESS_S - dauer(prev, b.pose)) : b.start;
    moveTo(start, b.pose);
    const next = list[i + 1];
    const holdEnd = b.end + HOLD_MIN_S;
    if (next && next.start - holdEnd > BACK_TO_BASE_GAP_S) moveTo(holdEnd, BASE_POSE);
  });
  return keys;
}

export function sampleTrack(keys: Key[], t: number): CameraPose {
  if (t <= keys[0].t) return keys[0].pose;
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (t < b.t) {
      if (a.pose === b.pose || b.t - a.t < 1e-9) return a.pose;
      return interpolatePose(a.pose, b.pose, (t - a.t) / (b.t - a.t));
    }
  }
  return keys[keys.length - 1].pose;
}
