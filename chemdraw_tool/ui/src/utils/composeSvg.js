// Ein SVG aus mehreren Teilen zusammensetzen — für Panels, deren Zeichnung im
// Panel aus mehreren Einzel-SVGs plus HTML besteht (Reaktion: Strukturen, „+“,
// Pfeil mit Bedingungen; Mechanismus-Übersicht: Schritte untereinander).
// Export PNG braucht genau ein SVG-Dokument; das baut diese reine Funktion.
//
// Teile:
//   { kind: "svg", svg, caption? }       eingebettete Struktur (eigene viewBox bleibt)
//   { kind: "text", text, size? }        „+“, Koeffizient, Platzhalter
//   { kind: "arrow", arrow?, above?, below?, reversible? }
//                                        Reihe: waagerechter Pfeil (forward/equilibrium/retro)
//                                        Spalte: senkrechter Pfeil, reversible = ⇌
import { extractSvgPixelSize } from "./svgToPng.js";

const NS = "http://www.w3.org/2000/svg";
const FONT = 'font-family="Helvetica, Arial, sans-serif"';
const INK = "#222222";
const MUTED = "#555555";
const CAPTION = 13;

const r2 = (n) => Math.round(n * 100) / 100;

function esc(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Grobe Textbreite ohne Canvas: reicht für Abstände, nicht für Satzspiegel.
const textWidth = (text, size) => (text ? String(text).length * size * 0.58 : 0);

function sizeOf(svg) {
  try {
    return extractSvgPixelSize(String(svg || ""));
  } catch {
    return null;
  }
}

// Struktur-SVG als verschachteltes <svg> an Position (x, y). Die XML-
// Deklaration von RDKit (<?xml …?>) mitten im Dokument wäre ein harter
// Parse-Fehler, also raus; Breite/Höhe ersetzen, viewBox behalten.
function embed(svg, x, y, w, h) {
  const s = String(svg).replace(/<\?xml[^>]*\?>/g, "").replace(/<!DOCTYPE[^>]*>/gi, "").trim();
  const open = /<svg\b[^>]*>/.exec(s);
  if (!open) return "";
  const hasViewBox = /\sviewBox=/.test(open[0]);
  const rest = open[0].replace(/\s(?:x|y|width|height)=(['"])[^'"]*\1/g, "");
  const attrs = ` x="${r2(x)}" y="${r2(y)}" width="${r2(w)}" height="${r2(h)}"` +
    (hasViewBox ? "" : ` viewBox="0 0 ${r2(w)} ${r2(h)}"`);
  return s.slice(0, open.index) + rest.replace(/^<svg/, `<svg${attrs}`) + s.slice(open.index + open[0].length);
}

function measure(part, direction) {
  if (part.kind === "svg") {
    const size = sizeOf(part.svg);
    if (!size) return null;
    const captionH = part.caption ? CAPTION + 8 : 0;
    return { ...part, w: Math.max(size.w, textWidth(part.caption, CAPTION)), h: size.h + captionH, inner: size };
  }
  if (part.kind === "text") {
    const size = part.size || 22;
    return { ...part, size, w: Math.max(14, textWidth(part.text, size)), h: size * 1.3 };
  }
  if (part.kind === "arrow") {
    if (direction === "column") return { ...part, w: 24, h: 34 };
    const w = Math.max(110, textWidth(part.above, CAPTION), textWidth(part.below, CAPTION)) + 16;
    return { ...part, w, h: 18 + (part.above ? 20 : 0) + (part.below ? 20 : 0) };
  }
  return null;
}

function text(x, y, value, size, color, anchor = "middle") {
  return `<text x="${r2(x)}" y="${r2(y)}" ${FONT} font-size="${size}" fill="${color}" text-anchor="${anchor}">${esc(value)}</text>`;
}

function drawArrowRow(p, x, y) {
  const cx = x + p.w / 2;
  const top = y + (p.above ? 20 : 0); // Oberkante des 18 px hohen Pfeilfelds
  const left = cx - (p.w - 16) / 2;
  const right = cx + (p.w - 16) / 2;
  const out = [];
  if (p.above) out.push(text(cx, top - 6, p.above, CAPTION, INK));
  const kind = p.arrow === "equilibrium" || p.arrow === "retro" ? p.arrow : "forward";
  const line = (x1, y1, x2, y2) =>
    `<line x1="${r2(x1)}" y1="${r2(y1)}" x2="${r2(x2)}" y2="${r2(y2)}" stroke="${MUTED}" stroke-width="1.6"/>`;
  if (kind === "equilibrium") {
    out.push(line(left, top + 6, right, top + 6));
    out.push(`<polygon points="${r2(right)},${r2(top + 6)} ${r2(right - 12)},${r2(top + 6)} ${r2(right - 12)},${r2(top + 1)}" fill="${MUTED}"/>`);
    out.push(line(left, top + 12, right, top + 12));
    out.push(`<polygon points="${r2(left)},${r2(top + 12)} ${r2(left + 12)},${r2(top + 12)} ${r2(left + 12)},${r2(top + 17)}" fill="${MUTED}"/>`);
  } else if (kind === "retro") {
    out.push(line(left, top + 6, right - 5, top + 6));
    out.push(line(left, top + 12, right - 5, top + 12));
    out.push(`<polyline points="${r2(right - 11)},${r2(top + 1)} ${r2(right)},${r2(top + 9)} ${r2(right - 11)},${r2(top + 17)}" fill="none" stroke="${MUTED}" stroke-width="1.6"/>`);
  } else {
    out.push(line(left, top + 9, right - 12, top + 9));
    out.push(`<polygon points="${r2(right - 12)},${r2(top + 4)} ${r2(right)},${r2(top + 9)} ${r2(right - 12)},${r2(top + 14)}" fill="${MUTED}"/>`);
  }
  if (p.below) out.push(text(cx, top + 18 + 15, p.below, CAPTION, INK));
  return out.join("");
}

function drawArrowColumn(p, x, y) {
  const cx = x + p.w / 2;
  const line = (x1, y1, x2, y2) =>
    `<line x1="${r2(x1)}" y1="${r2(y1)}" x2="${r2(x2)}" y2="${r2(y2)}" stroke="${MUTED}" stroke-width="1.5"/>`;
  if (p.reversible) {
    return line(cx - 3, y + 4, cx - 3, y + 30) +
      `<polyline points="${r2(cx - 7)},${r2(y + 24)} ${r2(cx - 3)},${r2(y + 30)}" fill="none" stroke="${MUTED}" stroke-width="1.5"/>` +
      line(cx + 3, y + 4, cx + 3, y + 30) +
      `<polyline points="${r2(cx + 7)},${r2(y + 10)} ${r2(cx + 3)},${r2(y + 4)}" fill="none" stroke="${MUTED}" stroke-width="1.5"/>`;
  }
  return line(cx, y + 4, cx, y + 22) +
    `<polygon points="${r2(cx - 4)},${r2(y + 22)} ${r2(cx)},${r2(y + 30)} ${r2(cx + 4)},${r2(y + 22)}" fill="${MUTED}"/>`;
}

function draw(p, x, y, direction) {
  if (p.kind === "svg") {
    const ix = x + (p.w - p.inner.w) / 2;
    let out = embed(p.svg, ix, y, p.inner.w, p.inner.h);
    if (p.caption) out += text(x + p.w / 2, y + p.inner.h + CAPTION + 2, p.caption, CAPTION, MUTED);
    return out;
  }
  if (p.kind === "text") return text(x + p.w / 2, y + p.size, p.text, p.size, INK);
  return direction === "column" ? drawArrowColumn(p, x, y) : drawArrowRow(p, x, y);
}

/** Teile zu einem eigenständigen SVG-Dokument mit weißem Grund zusammensetzen. */
export function composeSvg(parts, { direction = "row", gap = 10, padding = 16, background = "#ffffff" } = {}) {
  const items = (parts || []).map((p) => measure(p, direction)).filter(Boolean);
  const along = direction === "column" ? "h" : "w";
  const across = direction === "column" ? "w" : "h";
  const length = items.reduce((sum, p) => sum + p[along], 0) + gap * Math.max(0, items.length - 1);
  const thickness = Math.max(1, ...items.map((p) => p[across]));
  const W = r2((direction === "column" ? thickness : length) + 2 * padding);
  const H = r2((direction === "column" ? length : thickness) + 2 * padding);
  let cursor = padding;
  const body = items.map((p) => {
    const offset = padding + (thickness - p[across]) / 2;
    const [x, y] = direction === "column" ? [offset, cursor] : [cursor, offset];
    cursor += p[along] + gap;
    return draw(p, x, y, direction);
  });
  return `<svg xmlns="${NS}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
    `<rect width="${W}" height="${H}" fill="${background}"/>${body.join("")}</svg>`;
}
