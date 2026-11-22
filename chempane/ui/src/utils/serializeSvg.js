// Ein SVG, das gerade im Panel steht (die 3D-Kuhle), als eigenständiges
// Dokument für Export PNG. Drei Dinge fehlen dem Live-Element dafür:
//  1. xmlns — im HTML-Dokument trägt <svg> keins; ein <img> lädt es ohne nicht.
//     XMLSerializer setzt es selbst, der Rückfall ergänzt es.
//  2. Die Theme-Variablen — `var(--bowl-0)` usw. gelten nur unter dem Stylesheet
//     des Panels; im <img> gäbe es keine, die Kuhle würde schwarz. Deshalb mit
//     den berechneten Werten des Elements ersetzen (leer → unverändert lassen).
//  3. Feste Maße — die Kuhle hat nur eine viewBox und ein Inline-Style mit 100 %.
const NS = "http://www.w3.org/2000/svg";

export function serializeLiveSvg(el) {
  if (!el) return "";
  const win = el.ownerDocument?.defaultView;
  let text = win?.XMLSerializer ? new win.XMLSerializer().serializeToString(el) : el.outerHTML;
  const open = /^<svg\b[^>]*>/.exec(text);
  if (!open) return text;
  let tag = open[0].replace(/\sstyle=(["'])[^"']*\1/, "");
  if (!/\sxmlns=/.test(tag)) tag = tag.replace(/^<svg/, `<svg xmlns="${NS}"`);
  const vb = /\sviewBox=["']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)/.exec(tag);
  if (vb && !/\swidth=/.test(tag)) tag = tag.replace(/^<svg/, `<svg width="${vb[1]}" height="${vb[2]}"`);
  text = tag + text.slice(open[0].length);
  const style = win?.getComputedStyle ? win.getComputedStyle(el) : null;
  return text.replace(/var\((--[\w-]+)\)/g, (match, name) => {
    const value = style?.getPropertyValue(name)?.trim();
    return value || match;
  });
}

/** Hintergrundfarbe des Panels (für einen Export, der wie das Panel aussehen soll). */
export function panelBackground(el) {
  const doc = el?.ownerDocument ?? (typeof document !== "undefined" ? document : null);
  const win = doc?.defaultView;
  const bg = doc?.body && win?.getComputedStyle ? win.getComputedStyle(doc.body).backgroundColor : "";
  return bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent" ? bg : "#ffffff";
}
