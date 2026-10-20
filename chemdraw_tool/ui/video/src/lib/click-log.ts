// Herkunft: github.com/ashrafchowdury/programatic-demo, src/lib/click-log.ts
// Commit 5104336d21edec84c78c1a35964e7d08b93703bf, MIT-Lizenz (Kopie: ../../LICENSE-programatic-demo).
// Gekürzt auf Datenvertrag + die Konstanten, die camera.ts und track.ts brauchen; sonst unverändert.
/**
 * Shared click-log types and camera-timing constants.
 * Imported by Remotion (src/) and the Playwright recorders (scripts/).
 */

export type ClickEvent = {
  label?: string;
  tMs: number;
  /**
   * Elapsed ms when the cursor *started* travelling toward this target.
   * Used to start the camera just before the pointer leaves. Optional so
   * older logs still render (camera falls back to tMs − LEAD_FALLBACK_S).
   */
  tDepartMs?: number;
  /**
   * Elapsed ms of mousedown. Drives the click ripple and cursor squash when
   * Remotion draws the cursor. Absent on `focus()` beats, which place a zoom
   * keyframe without actually clicking — and on older logs.
   */
  tDownMs?: number;
  /**
   * Elapsed ms when typing into this target finished. Present only on `typeInto`
   * beats. Between `tMs` and this, the pointer is parked and the app is drawing
   * its own text caret, so the arrow is faded out — two cursors on screen reads
   * as a bug, and the arrow is not the thing to watch while text appears.
   */
  typeEndMs?: number;
  x: number;
  y: number;
  /** The clicked element's bounding rect (viewport CSS px). When present the zoom
   *  frames the whole control; otherwise it falls back to a small box around x/y. */
  rect?: { x: number; y: number; w: number; h: number };
  /**
   * The populated region around the target — the form, list or panel the
   * control belongs to — in the same viewport CSS px as `rect`. Optional: when
   * present, frameFor centres the zoom on target + content and tightens until
   * the frame is no more than BLANK_CAP empty page, so a small form on a tall,
   * sparse page is not framed with 60-70% blank below it. When absent, framing
   * follows the click alone, exactly as before.
   */
  content?: { x: number; y: number; w: number; h: number };
  /**
   * Where the text was going while this beat typed, sampled every ~250 ms from
   * the click to the last keystroke. Same space as `rect`. For a contenteditable
   * it is the caret itself; for an input or textarea (which expose no caret
   * geometry) it is the field, so a textarea that grows as it fills still shows
   * where the text is. Optional and unused by the camera today — logged so a
   * zoom can follow a growing field instead of letting it type out of frame.
   */
  caret?: { tMs: number; x: number; y: number; w: number; h: number }[];
  /** Explicit zoom cluster id. Same id → shared punch / hold / trail. */
  cluster?: string;
  /** When false, this event does not contribute to zoom (still in the video). */
  zoom?: boolean;
  /**
   * Force the camera to this scale on this beat, instead of fitting the framed
   * rect. For a WIDE target (a menu spanning most of the width) the fit maths
   * pulls back to S_MIN, which is the opposite of "zoom in on it"; setting this
   * frames the rect's centre at the requested magnification instead. Clamped to
   * the sharpness ceiling (S_MAX) so it can crop tight without upscaling past
   * native. See frameFor.
   */
  zoomScale?: number;
};

/** One recorded pointer position, on the click-log clock. */
export type CursorSample = {
  /** Elapsed ms. */
  t: number;
  /** Viewport CSS px. */
  x: number;
  y: number;
  /**
   * Wheel delta (px, +down) dispatched at this sample, on a `ctx.scroll` beat.
   * Absent everywhere else. Lets the render tell a scroll — the content moving
   * under a still pointer — from a still frame.
   */
  wheel?: number;
};

/**
 * A keyboard chord worth showing on screen.
 *
 * Separate from ClickEvent on purpose: a key press is not a pointer target, so
 * it must not feed the zoom camera, the cursor track, or the click SFX
 * detectors — all three key off ClickEvent and would misread it.
 *
 * The reference film is keyboard-first and has NO pointer anywhere; it
 * announces every interaction with a keycap pill instead. See src/KeycapHUD.tsx.
 */
export type KeyEvent = {
  /** Elapsed ms of the keydown, on the same clock as ClickEvent.tMs. */
  tMs: number;
  /** The chord as display glyphs, e.g. "⌥⏎". See chordGlyphs. */
  chord: string;
  /** What the chord did, for the log and for `atLabels` SFX cues. */
  label?: string;
};

/**
 * Playwright chord ("Alt+Enter") to the glyphs a viewer reads ("⌥⏎").
 *
 * Mac glyphs because the footage is shot on a Mac and the app draws its own
 * hints the same way — the reference's own affordance reads "⌥↵ to Use as Mode",
 * so a spelled-out "Alt+Enter" pill beside it would look like a different
 * product.
 */
const KEY_GLYPHS: Record<string, string> = {
  alt: "\u2325",
  option: "\u2325",
  meta: "\u2318",
  cmd: "\u2318",
  command: "\u2318",
  control: "\u2303",
  ctrl: "\u2303",
  shift: "\u21e7",
  enter: "\u23ce",
  return: "\u23ce",
  tab: "\u21e5",
  escape: "esc",
  esc: "esc",
  backspace: "\u232b",
  delete: "\u2326",
  arrowup: "\u2191",
  arrowdown: "\u2193",
  arrowleft: "\u2190",
  arrowright: "\u2192",
  space: "space",
};

export const chordGlyphs = (chord: string): string =>
  chord
    .split("+")
    .map((part) => {
      const key = part.trim();
      return KEY_GLYPHS[key.toLowerCase()] ?? key.toUpperCase();
    })
    .join("");

export type ClickLog = {
  name: string;
  viewport: { width: number; height: number };
  /**
   * Full pointer path emitted by the recorder's glide.
   *
   * When present, Remotion draws the cursor as vector at composition resolution
   * and the recorder does not bake one into the video. When absent (older
   * recordings) the cursor is already in the footage, so Remotion draws nothing
   * — which is what keeps those clips rendering correctly.
   */
  cursorTrack?: CursorSample[];
  /** Duration of the kept (demo) portion in ms; used to size the composition. */
  durationMs: number;
  /** Trim this many ms off the FRONT of the video (e.g. login) before the demo. */
  trimBeforeMs?: number;
  /** Manual nudge (ms) applied to every click time if video/log drift shows up. */
  offsetMs?: number;
  /**
   * The playback rate the shoot was PACED for — DEMO_SPEED at record time.
   *
   * The recorder times glides, the camera room it leaves before a press and
   * the cluster gap on the screen clock, i.e. recording ms = screen ms x this.
   * Rendering at another speed still works, but every one of those plays at
   * the wrong length, so render warns (see speedMismatch). Absent on logs
   * written before it was recorded; those were all paced for 1.25.
   */
  speed?: number;
  /**
   * Studio backdrop for this demo, copied from the flow at record time.
   *
   * It lives in the LOG rather than the flow because `pnpm render` never loads
   * a flow — it reads this file. See src/lib/backdrop.ts.
   */
  backdrop?: string;
  clicks: ClickEvent[];
  /**
   * Keyboard chords to surface as an on-screen keycap. Absent on every existing
   * log, and drawn only under the full-bleed look, so nothing already recorded
   * changes.
   */
  keys?: KeyEvent[];
};

export const EMPTY_LOG: ClickLog = {
  name: "",
  viewport: { width: 1920, height: 1080 },
  durationMs: 8000,
  offsetMs: 0,
  clicks: [],
};

/**
 * Width the look was tuned at. Every composition-pixel constant (cursor size,
 * shadow radii, corner radius, chrome height) is written for this width and
 * scaled by OUTPUT_WIDTH / DESIGN_WIDTH at render, so changing the output
 * resolution moves the whole design together instead of shrinking the details.
 */
export const DESIGN_WIDTH = 1920;

/** Fallback lead-in when a log has no tDepartMs (older recordings). */
export const LEAD_FALLBACK_S = 0.75;
/** Minimum still hold after the last click of a cluster. */
export const HOLD_MIN_S = 1.3;
/**
 * Still hold after the last KEYSTROKE of a typing beat, before trailing out.
 *
 * A click is instantaneous, so HOLD_MIN_S measured from `tMs` covers it. Typing
 * is not: 111 characters take ~4s, and a hold measured from the click expired
 * a third of the way through, trailing the camera to base while two thirds of
 * the text was still being typed — the one thing the demo exists to show, played
 * at the widest framing in the clip. The camera must not leave an action that is
 * still happening, so a typing beat holds until `typeEndMs` instead.
 *
 * Shorter than HOLD_MIN_S because the viewer has been reading throughout, and
 * the trail-out itself keeps the text legible for most of another second.
 */
export const TYPE_TAIL_S = 0.4;
/** Camera starts this many seconds before cursor departure. */
export const CAMERA_LEAD_S = 0.035;
/**
 * A camera move lands at least this long (screen seconds) before the press.
 *
 * The press is what the viewer is watching for; a ripple drawn on a frame that
 * is still gliding smears into the motion blur. Replayed over every public
 * click log at 1.25x, 12 of 118 presses landed mid-move — one 482ms before the
 * camera settled — because camera durations were scaled by playback speed and
 * the recorded cursor glide was not. Five frames at 30fps reads as "arrived,
 * then clicked" without a visible wait.
 */
export const SETTLE_BEFORE_PRESS_S = 0.15;
/**
 * Shortest a move may be squeezed to (screen seconds) to meet that deadline.
 * The reference moves run 750-1250ms; below ~450ms the zoom reads as a snap.
 */
export const MOVE_FLOOR_S = 0.45;
