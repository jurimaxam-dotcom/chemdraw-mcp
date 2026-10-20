// Herkunft: github.com/ashrafchowdury/programatic-demo, src/lib/camera.ts
// Commit 5104336d21edec84c78c1a35964e7d08b93703bf, MIT-Lizenz (Kopie: ../../LICENSE-programatic-demo).
// Unverändert bis auf den Import-Pfad (.ts-Endung für node --test).
import { Easing } from "remotion";
import { DESIGN_WIDTH } from "./click-log.ts";

/**
 * Single camera interpolator.
 *
 * Measured from Screen Studio-style refs: long decaying tail, 0% overshoot,
 * progress ~0.89 at 0.50 T. Those refs put 0.19 of the move in the first
 * 0.10 T, which was matched with cubic-bezier(0.2, 0.2, 0.15, 1) — and that
 * curve starts at slope 1.0, i.e. at full AVERAGE speed on the first frame.
 * Replayed through every public/*.clicks.json at 1.25x, the first frame of a
 * move ran at 26-100% of that move's peak speed (median 53%): one frame still,
 * the next smeared into eight stacked motion-blur copies. That lurch is the
 * "jerk" in the demos, and it is the one thing the reference fit got wrong.
 *
 * cubic-bezier(0.3, 0, 0.1, 1) keeps the tail and fixes the start:
 *
 *                     0.10T   0.50T   0.70T   98% at   peak speed   start slope
 *   (0.2, 0.2, 0.15, 1)  0.183   0.863   0.959   0.78T    2.84x @0.13T   1.0
 *   (0.3, 0, 0.1, 1)     0.052   0.838   0.953   0.80T    3.13x @0.21T   0
 *
 * The first frame of a 17-frame move now covers 8% of the peak frame's
 * distance instead of 52%. The price is the early 0.10T sample (0.05 vs the
 * reference's 0.19): a zero-slope start cannot also be that far along, and the
 * start is the part that read as a fault.
 */
export const CAMERA_BEZIER = Easing.bezier(0.3, 0, 0.1, 1);

/**
 * Entrance/exit interpolator for the full-bleed look's push envelope.
 *
 * Measured off the Cursor "Agent UX improvements" film: every decelerating
 * entrance there is a decaying exponential, ~0.78 of the remaining distance
 * retained per frame at 30fps (tau ~134ms). Fitting a cubic to the sampled
 * remaining-distance table gives cubic-bezier(0.15, 0.90, 0.75, 0.95) at
 * RMS 0.005; the camera's old cubic-bezier(0.2, 0.2, 0.15, 1) was the closest
 * standard curve at RMS 0.066 but is measurably too slow off the mark — the
 * reference covers 28% of the distance in frame ONE.
 *
 * Kept separate from CAMERA_BEZIER on purpose: that one drives the demo camera
 * and every reel's zoom track, and starts from rest by design (see above) —
 * the opposite of this entrance.
 */
export const PUSH_BEZIER = Easing.bezier(0.15, 0.9, 0.75, 0.95);

export type CameraPose = {
  scale: number;
  /** Focal point in *content* space (0..1), not CSS transform-origin. */
  cx: number;
  cy: number;
};

/**
 * The whole window, centred. `cy` is 0.5 of the CONTENT, which is the centre of
 * the window group only when there is no chrome strip; the track uses
 * basePose(chromeFrac) so its base keys sit exactly on the group centre. (This
 * was 0.48, an approximation of that for the default chrome — at render it was
 * always clamped to the centre anyway, so nothing that was drawn changes.)
 */
export const BASE_POSE: CameraPose = { scale: 1, cx: 0.5, cy: 0.5 };

export const clamp = (v: number, lo: number, hi: number): number =>
  Math.min(hi, Math.max(lo, v));
export const mix = (a: number, b: number, t: number): number => a + (b - a) * t;

export function cameraEase(t01: number): number {
  return CAMERA_BEZIER(clamp(t01, 0, 1));
}

/** Content-space Y of window-group point `g` (the group adds a chrome strip on top). */
export const groupToContentY = (g: number, chromeFrac: number): number =>
  chromeFrac > 0 ? (g - chromeFrac) / (1 - chromeFrac) : g;

/** BASE_POSE for a window group whose top `chromeFrac` is chrome. */
export function basePose(chromeFrac = 0): CameraPose {
  return { scale: 1, cx: 0.5, cy: groupToContentY(0.5, chromeFrac) };
}

/**
 * THE pan clamp: how far the focal point may sit from the group centre, as a
 * fraction of the group, at a given scale. |C - 0.5| <= 0.5 - 1 / (2 S).
 *
 * Called with the POSE scale it is the render-time safety in poseToCss: never
 * show more backdrop past an edge than the base shot does (at fit 1: never show
 * past the footage). Called with the EFFECTIVE scale (fit * S) it is the stricter
 * framing rule frameFor holds keyframes to: once the window is bigger than the
 * frame, keep its edges out of shot. See poseToCss for why it is the same curve
 * and why keyframes inside it keep every in-between frame inside it too.
 */
export function panLimit(scale: number): number {
  return scale > 1 ? 0.5 - 1 / (2 * scale) : 0;
}

/**
 * The camera between two poses, `e` of the way along (e already eased).
 *
 * Scale moves in LOG space: equal ratios per unit of progress, so the frame
 * edge moves at the speed the easing says rather than front-loading the zoom
 * (linear S spends its largest ratio change first, on top of an easing that
 * already does). The focal point is then derived FROM the current scale: it
 * runs along the straight line between the endpoints in (C, 1/S), which is
 * exactly the family of moves that hold one screen point still. For a punch
 * from base that point is the subject frameFor zoomed about, so the clicked
 * control stays pinned while the frame grows around it — linear mixing only
 * pinned it at the endpoints and swung an edge subject ~90px out and back at
 * S 1.74. For a pan (no scale change) the line degenerates to a plain mix.
 *
 * The same property keeps a move inside the pan clamp: the clamp's bound
 * 0.5 - 1/(2S) is linear in 1/S, so if both endpoints satisfy it, every point
 * on the line between them does. No move can wander into the render clamp.
 */
export function poseAlong(a: CameraPose, b: CameraPose, e: number): CameraPose {
  const scale = Math.exp(mix(Math.log(a.scale), Math.log(b.scale), e));
  const ua = 1 / a.scale;
  const ub = 1 / b.scale;
  const w = Math.abs(ub - ua) > 1e-6 ? (1 / scale - ua) / (ub - ua) : e;
  return { scale, cx: mix(a.cx, b.cx, w), cy: mix(a.cy, b.cy, w) };
}

/**
 * Progress slopes at the two ends of a move that does NOT start or end at rest
 * (d progress / d u, u the move's own 0..1 time). See carryProgress.
 */
export type MoveSlopes = { from: number; to: number };

/**
 * Progress for a move that carries speed through one or both of its ends: the
 * cubic Hermite from 0 to 1 with slopes `from` and `to`.
 *
 * Only junction moves use it (a move that ends exactly as the next begins, see
 * carryThrough in zoom.ts); every move that starts and ends at rest keeps
 * CAMERA_BEZIER, so their tracks are unchanged. Both slopes stay below 2 by
 * construction, inside the Fritsch-Carlson bound (s0^2 + s1^2 <= 9), so this is
 * monotone and stays in 0..1 — the pose never leaves the line between its keys,
 * which is what keeps it inside the pan clamp (see poseAlong).
 */
export function carryProgress(u: number, s: MoveSlopes): number {
  const x = clamp(u, 0, 1);
  const x2 = x * x;
  const x3 = x2 * x;
  return (
    3 * x2 - 2 * x3 + s.from * (x3 - 2 * x2 + x) + s.to * (x3 - x2)
  );
}

/**
 * One eased progress value drives scale and centre. Convert to CSS *after* this.
 * With `slopes` the move carries speed through its ends instead of starting and
 * stopping at rest (see carryProgress).
 */
export function interpolatePose(
  a: CameraPose,
  b: CameraPose,
  t01: number,
  slopes?: MoveSlopes,
): CameraPose {
  return poseAlong(a, b, slopes ? carryProgress(t01, slopes) : cameraEase(t01));
}

/**
 * One move from `a` to `b` bent toward `via`, eased once end to end.
 *
 * Used where the track would otherwise trail to base and punch straight back in
 * with no rest between (a far pan inside a cluster, back-to-back clusters).
 * Two moves there meant the camera decelerated to a dead stop at base and
 * kicked off again — the velocity fell to zero and re-launched. This is a
 * quadratic Bezier in (C, 1/S) with `via` as its control point: it starts and
 * ends at rest, but carries its speed through the middle, dipping to a middle
 * scale (for via = base between two 1.6x poses, ~1.23x) instead of stopping at
 * the whole window. The curve lies in the convex hull of its three points, and
 * the pan clamp is convex in (C, 1/S), so it stays inside the clamp too.
 */
export function interpolateVia(
  a: CameraPose,
  via: CameraPose,
  b: CameraPose,
  t01: number,
): CameraPose {
  const e = cameraEase(t01);
  const k0 = (1 - e) * (1 - e);
  const k1 = 2 * e * (1 - e);
  const k2 = e * e;
  const at = (x: number, y: number, z: number) => k0 * x + k1 * y + k2 * z;
  return {
    scale: 1 / at(1 / a.scale, 1 / via.scale, 1 / b.scale),
    cx: at(a.cx, via.cx, b.cx),
    cy: at(a.cy, via.cy, b.cy),
  };
}

export function posesNearlyEqual(a: CameraPose, b: CameraPose): boolean {
  return (
    Math.abs(a.scale - b.scale) < 0.008 &&
    Math.abs(a.cx - b.cx) < 0.01 &&
    Math.abs(a.cy - b.cy) < 0.01
  );
}

/**
 * Distance-aware move duration.
 *
 * The windows below are what the viewer should SEE (refs: ~750–1100 ms for a
 * zoom-in, zoom-out ~1.25x that). The camera track, however, runs on the click
 * log's clock, which the composition replays at `speed` — so a duration authored
 * here is divided by `speed` on screen. We therefore clamp in output time and
 * return log time, multiplying the result back up. Without this every measured
 * constant lands ~20% short at the default 1.25x.
 *
 * @param speed Composition playback rate vs the shoot. 1 = realtime.
 * @returns Seconds on the click-log clock.
 */
export function moveDuration(
  from: CameraPose,
  to: CameraPose,
  kind: "in" | "out" | "pan",
  vp: { width: number; height: number },
  speed = 1,
): number {
  const dS = Math.abs(to.scale - from.scale);
  // Priced by what the VIEWER sees move: focal travel times the magnification
  // it is seen at. Priced by focal travel alone, a re-frame at 1.74x crossed
  // ~750 px of screen in 0.71 s (skills-launch, 4.6 s), ~1 px/ms, about twice
  // the reference glides' ~0.5 px/ms, and read as a snap.
  const dPx = poseTravelPx(from, to, vp) * Math.max(from.scale, to.scale);
  const ms = 480 + 420 * dS + 0.5 * dPx;
  const onScreen =
    kind === "out"
      ? clamp(ms * 1.25, 650, 1450)
      : kind === "pan"
        ? clamp(ms, 700, 1400)
        : clamp(ms, 550, 1250);
  return (onScreen * speed) / 1000;
}

/**
 * Focal travel of a move, in DESIGN px (i.e. at DESIGN_WIDTH), not viewport px.
 *
 * Reference camera moves travel 31–501 px. A repositioning much larger than that
 * is not a pan any camera operator would make at magnification — it should pass
 * through a wider framing instead. Used by the track builder to decide between
 * panning and routing via base, and by moveDuration to price a move.
 *
 * NORMALISED ON PURPOSE. The poses are fractions of the frame, so multiplying by
 * a raw viewport gives a number that doubles when the same shot is captured at
 * CAPTURE_SCALE=2 — and MAX_PAN_PX below is a fixed 500. Measured: the API-key
 * to Harnesses pan priced 645px at 1920 and 1290px at 3840, so the 3840 cut
 * routed through base where the 1920 cut panned, adding a full zoom-out and
 * back that the 1x film never had. Dividing by k makes both price the same move
 * identically, and is exact (k = 1) for every 1x log.
 */
export function poseTravelPx(
  from: CameraPose,
  to: CameraPose,
  vp: { width: number; height: number },
): number {
  const k = vp.width > 0 ? vp.width / DESIGN_WIDTH : 1;
  return (
    Math.hypot(
      (to.cx - from.cx) * vp.width,
      (to.cy - from.cy) * vp.height,
    ) / k
  );
}

/** Above this focal travel, route through base rather than panning across. */
export const MAX_PAN_PX = 500;

/**
 * Map a content-space point into the window group that includes a top chrome strip.
 */
export function contentToWindow(
  cx: number,
  cy: number,
  chromeFrac: number,
): { cx: number; cy: number } {
  if (chromeFrac <= 0) return { cx, cy };
  return { cx, cy: chromeFrac + cy * (1 - chromeFrac) };
}

/**
 * Convert an interpolated content-space pose into the CSS transform DemoClip
 * applies to the window group: a translate (fractions of the group's own size,
 * for `translate(%)`) plus a scale, about the group's centre.
 *
 * Pan is expressed as a TRANSLATE, not a transform-origin, and that matters.
 * The origin form needs `(0.5 - C*S) / (1 - S)`, which is singular at S = 1: on
 * the way out of a zoom the origin runs away to +/-infinity, clips against a pad,
 * mis-frames the last ~10 frames of the move, then snaps back the instant S hits
 * exactly 1. That read as a shake at the end of every zoom-out. The translate
 * form below is linear in scale, so it stays continuous through S = 1 and needs
 * no clamping at all.
 *
 * @param fit Base shrink of the window on the backdrop (WINDOW_FIT).
 */
export function poseToCss(
  pose: CameraPose,
  chromeFrac: number,
  fit = 1,
): { scale: number; translateX: number; translateY: number } {
  const S = pose.scale;
  const effective = fit * S;
  const mapped = contentToWindow(pose.cx, pose.cy, chromeFrac);
  // A SAFETY, not a framing rule, and a no-op on every track buildCameraTrack
  // makes. The bound is panLimit on the POSE scale: never show more backdrop past
  // an edge than the base shot does (at fit 1, never reveal past the footage).
  //
  // The framing rule lives in frameFor. An earlier version clamped here on the
  // EFFECTIVE scale (half = 1 / (2 fit S), centred until fit * S > 1). That fixed
  // a real defect — at S 1.18-1.26 (effective 1.02-1.09) keyframes clamped on
  // 1 / S let the window slide until its edge sat at the base margin with the
  // far 13% cut off: a window inflating from its corner, not a camera punching
  // in. But as a RENDER clamp it fought every move: it pinned translate to 0
  // until fit * S passed 1 (pose scale 1.163 at 0.86), so the first third of
  // every punch zoomed about the window centre and then swerved 50-63px in a
  // frame, and pans whose keyframes sat outside it stopped dead against it
  // mid-move (model-providers f444 -> f445, -31.6 -> -1.5 px/frame).
  //
  // frameFor now applies that same effective-scale rule to the KEYFRAMES, so a
  // hold still keeps the window's edges out of shot (the corner case stays
  // fixed), and the moves between keyframes are inside this looser bound by
  // construction (see poseAlong), so it never engages.
  const lim = panLimit(S);
  const Cx = clamp(mapped.cx, 0.5 - lim, 0.5 + lim);
  const Cy = clamp(mapped.cy, 0.5 - lim, 0.5 + lim);
  return {
    scale: effective,
    translateX: effective * (0.5 - Cx),
    translateY: effective * (0.5 - Cy),
  };
}
