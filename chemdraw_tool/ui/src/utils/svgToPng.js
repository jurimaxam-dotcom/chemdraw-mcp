// PNG export helpers. extractSvgPixelSize is pure (Node-testable);
// the rest touches browser APIs only inside their function bodies.

const VIEWBOX_RE =
  /viewBox=['"]\s*([-\d.eE]+)\s+([-\d.eE]+)\s+([-\d.eE]+)\s+([-\d.eE]+)\s*['"]/;
// Lookbehind excludes hyphen/word chars so `stroke-width` doesn't match `width`.
const WIDTH_RE = /(?<![-\w])width=['"]([\d.]+)(?:px)?['"]/;
const HEIGHT_RE = /(?<![-\w])height=['"]([\d.]+)(?:px)?['"]/;

/**
 * Intrinsic pixel size of an SVG string.
 * Prefers viewBox (robust for fill_container SVGs whose width/height is 100%).
 * Falls back to numeric width/height. Throws if neither yields a positive size.
 */
export function extractSvgPixelSize(svgString) {
  const vb = VIEWBOX_RE.exec(svgString);
  if (vb) {
    const w = Math.round(parseFloat(vb[3]));
    const h = Math.round(parseFloat(vb[4]));
    if (w > 0 && h > 0) return { w, h };
  }
  const wm = WIDTH_RE.exec(svgString);
  const hm = HEIGHT_RE.exec(svgString);
  if (wm && hm) {
    const w = Math.round(parseFloat(wm[1]));
    const h = Math.round(parseFloat(hm[1]));
    if (w > 0 && h > 0) return { w, h };
  }
  throw new Error("SVG ohne verwertbare Maße");
}

/**
 * Rasterize an SVG string to a PNG Blob via an offscreen canvas.
 * scale: DPI multiplier (3 = print-sharp). background: filled before drawing.
 */
export function svgToPngBlob(svgString, { scale = 3, background = "#fff" } = {}) {
  const { w, h } = extractSvgPixelSize(svgString);
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url =
      "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgString);
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = w * scale;
      canvas.height = h * scale;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas-Context nicht verfügbar"));
        return;
      }
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error("toBlob lieferte null"));
      }, "image/png");
    };
    img.onerror = () => reject(new Error("SVG konnte nicht geladen werden"));
    img.src = url;
  });
}

/** Read a Blob as bare base64 (no `data:` prefix). */
export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = String(reader.result);
      resolve(result.slice(result.indexOf(",") + 1));
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

/** Copy a PNG Blob to the clipboard. Throws if the API is missing or denied. */
export async function copyPngToClipboard(blob) {
  if (typeof ClipboardItem === "undefined" || !navigator.clipboard?.write) {
    throw new Error("Clipboard-Image-API nicht verfügbar");
  }
  await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
}
