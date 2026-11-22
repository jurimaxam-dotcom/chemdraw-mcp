/**
 * Compute the transform from SVG viewBox coordinates to container-relative
 * pixel coordinates, accounting for preserveAspectRatio="xMidYMid meet".
 *
 * Returns null if the SVG/viewBox can't be read.
 */
export function getSvgTransform(svgContainerRef) {
  const container = svgContainerRef.current;
  if (!container) return null;
  const svgEl = container.querySelector("svg");
  if (!svgEl) return null;

  const vb = svgEl.viewBox?.baseVal;
  if (!vb || vb.width === 0 || vb.height === 0) return null;

  const containerRect = container.getBoundingClientRect();
  const svgRect = svgEl.getBoundingClientRect();

  // preserveAspectRatio="xMidYMid meet" uses uniform scale
  const scaleX = svgRect.width / vb.width;
  const scaleY = svgRect.height / vb.height;
  const scale = Math.min(scaleX, scaleY);
  // A collapsed/hidden container (width or height 0) yields scale 0,
  // which would make later coordinate math divide by zero (NaN/Infinity).
  if (!Number.isFinite(scale) || scale <= 0) return null;

  // content is centered within the SVG element
  const contentOffsetX = (svgRect.width - vb.width * scale) / 2;
  const contentOffsetY = (svgRect.height - vb.height * scale) / 2;

  const originX = svgRect.left - containerRect.left + contentOffsetX;
  const originY = svgRect.top - containerRect.top + contentOffsetY;

  return { vb, scale, originX, originY, svgRect, containerRect };
}

/** Map a viewBox-space point to container-relative pixel coords. */
export function viewBoxToScreen(t, x, y) {
  return {
    x: (x - t.vb.x) * t.scale + t.originX,
    y: (y - t.vb.y) * t.scale + t.originY,
  };
}

/** Map a client-space mouse event to viewBox coordinates. */
export function clientToViewBox(t, clientX, clientY) {
  const px = clientX - t.svgRect.left - (t.svgRect.width - t.vb.width * t.scale) / 2;
  const py = clientY - t.svgRect.top - (t.svgRect.height - t.vb.height * t.scale) / 2;
  return {
    x: px / t.scale + t.vb.x,
    y: py / t.scale + t.vb.y,
  };
}
