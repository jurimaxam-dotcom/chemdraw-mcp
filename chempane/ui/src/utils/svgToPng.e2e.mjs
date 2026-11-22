// End-to-end render tests for the PNG-export pipeline in a REAL headless browser.
//
// Why this exists: the pure size-parsing (svgToPng.test.mjs) and the backend
// file writer (pytest) are unit-covered, but the part that actually matters —
// does SVG → <canvas> → toBlob produce a real, non-blank, visually-stable PNG? —
// only runs in a browser. Playwright drives headless Chromium so this is
// automated, not manual.
//
// It loads the ACTUAL svgToPng.js source (via a data: module import) so the
// tests exercise the shipped code, not a copy. The fixture is a REAL RDKit
// fill_container SVG (width=100% + viewBox) captured from the production
// pipeline — the exact case that can silently render blank/mis-scaled.
//
// Two layers:
//   1. structural — PNG magic bytes, dimensions, center-non-white (catches the
//      documented "blank white page" silent-degradation failure).
//   2. snapshot — EXACT pixel match against a committed reference PNG. This is
//      only safe because the bundled Chromium is PINNED (playwright "1.60.0",
//      no caret) and 2D-canvas rendering is deterministic for identical input
//      (verified: two renders are byte-identical *on this machine*). A Chromium
//      bump can shift anti-aliasing; so can a different host/OS/arch (determinism
//      is only proven same-machine). Either way, regenerate the reference with:
//      npm run test:e2e:update — but NEVER inside an autonomous loop to make a
//      diff vanish (that defeats the regression check; see loop guardrails).

import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { chromium } from "playwright";
import { extractSvgPixelSize } from "./svgToPng.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SVG = readFileSync(
  join(__dirname, "__fixtures__", "aspirin.fill.svg"),
  "utf8",
);
const MODULE_SRC = readFileSync(join(__dirname, "svgToPng.js"), "utf8");
// Rasterization is only deterministic per platform (anti-aliasing differs
// across OS/arch), so each platform gets its own golden file. darwin keeps
// the original un-suffixed reference from before multi-platform CI.
const SNAPSHOT =
  process.platform === "darwin"
    ? join(__dirname, "__fixtures__", "aspirin.expected.png")
    : join(__dirname, "__fixtures__", `aspirin.expected.${process.platform}.png`);
const UPDATE = process.env.UPDATE_SNAPSHOTS === "1";
const SCALE = 3;
const PNG_MAGIC = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const MODULE_URL =
  "data:text/javascript;base64," + Buffer.from(MODULE_SRC).toString("base64");

let browser;
before(async () => {
  browser = await chromium.launch();
});
after(async () => {
  await browser?.close();
});

test("svgToPngBlob rasters a real RDKit SVG to a non-blank PNG in a real browser", async () => {
  const expected = extractSvgPixelSize(SVG); // computed in Node from the same source
  const page = await browser.newPage();
  try {
    const result = await page.evaluate(
      async ({ moduleUrl, svg, scale }) => {
        const mod = await import(moduleUrl); // the real shipped module
        const blob = await mod.svgToPngBlob(svg, { scale, background: "#fff" });
        const bytes = new Uint8Array(await blob.arrayBuffer());

        // Decode the produced PNG back to pixels — proves it's a real, openable
        // image, and lets us inspect whether the structure actually rendered.
        const bmp = await createImageBitmap(blob);
        const canvas = document.createElement("canvas");
        canvas.width = bmp.width;
        canvas.height = bmp.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(bmp, 0, 0);

        // Sample a centered region: a blank-white canvas (the silent-degradation
        // failure) would yield nonWhite === 0 even with valid magic bytes.
        const half = 60;
        const cx = Math.floor(bmp.width / 2) - half;
        const cy = Math.floor(bmp.height / 2) - half;
        const data = ctx.getImageData(cx, cy, half * 2, half * 2).data;
        let nonWhite = 0;
        for (let i = 0; i < data.length; i += 4) {
          if (data[i] < 250 || data[i + 1] < 250 || data[i + 2] < 250) {
            nonWhite++;
          }
        }
        return {
          magic: Array.from(bytes.slice(0, 8)),
          mime: blob.type,
          width: bmp.width,
          height: bmp.height,
          nonWhite,
        };
      },
      { moduleUrl: MODULE_URL, svg: SVG, scale: SCALE },
    );

    assert.deepEqual(result.magic, PNG_MAGIC, "output must be a real PNG (magic bytes)");
    assert.equal(result.mime, "image/png", "blob MIME type must be image/png");
    assert.equal(result.width, expected.w * SCALE, "PNG width = viewBox width × scale");
    assert.equal(result.height, expected.h * SCALE, "PNG height = viewBox height × scale");
    assert.ok(
      result.nonWhite > 50,
      `center region must contain the rendered structure, not blank white (nonWhite=${result.nonWhite})`,
    );
  } finally {
    await page.close();
  }
});

test("rendered PNG matches the committed pixel snapshot exactly", async () => {
  const page = await browser.newPage();
  try {
    // Render fresh and bring the (small, compressed) PNG bytes back as base64.
    const freshB64 = await page.evaluate(
      async ({ moduleUrl, svg, scale }) => {
        const mod = await import(moduleUrl);
        const blob = await mod.svgToPngBlob(svg, { scale, background: "#fff" });
        const bytes = new Uint8Array(await blob.arrayBuffer());
        let bin = "";
        for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
        return btoa(bin);
      },
      { moduleUrl: MODULE_URL, svg: SVG, scale: SCALE },
    );
    const freshBytes = Buffer.from(freshB64, "base64");

    // Refresh the reference ONLY on explicit UPDATE — never auto-seed on mere
    // absence. A missing committed reference must fail loudly: silently writing
    // it and returning green would disable the regression check exactly the way
    // this file's header (and the global loop guardrails) forbid.
    if (UPDATE) {
      writeFileSync(SNAPSHOT, freshBytes);
      console.log(`# snapshot updated: ${SNAPSHOT} (${freshBytes.length} bytes)`);
      return;
    }
    if (!existsSync(SNAPSHOT)) {
      assert.fail(
        `reference snapshot missing: ${SNAPSHOT} — generate it intentionally with ` +
          `'npm run test:e2e:update'. A missing reference is a test failure, not a free pass.`,
      );
    }

    const refB64 = readFileSync(SNAPSHOT).toString("base64");

    // Compare by DECODED PIXELS (robust against PNG-encoder quirks), in-browser
    // where the canvas APIs live. Tolerance is zero: rendering is deterministic
    // under the pinned Chromium (proven byte-identical across runs).
    const cmp = await page.evaluate(
      async ({ freshB64, refB64 }) => {
        function toBlob(b64) {
          const bin = atob(b64);
          const arr = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
          return new Blob([arr], { type: "image/png" });
        }
        async function pixels(b64) {
          const bmp = await createImageBitmap(toBlob(b64));
          const c = document.createElement("canvas");
          c.width = bmp.width;
          c.height = bmp.height;
          const ctx = c.getContext("2d");
          ctx.drawImage(bmp, 0, 0);
          return {
            d: ctx.getImageData(0, 0, bmp.width, bmp.height).data,
            w: bmp.width,
            h: bmp.height,
          };
        }
        const a = await pixels(freshB64);
        const b = await pixels(refB64);
        if (a.w !== b.w || a.h !== b.h) {
          return { sizeMismatch: true, fresh: [a.w, a.h], ref: [b.w, b.h] };
        }
        let nDiff = 0;
        let maxChan = 0;
        for (let i = 0; i < a.d.length; i++) {
          const dd = Math.abs(a.d[i] - b.d[i]);
          if (dd > 0) {
            nDiff++;
            if (dd > maxChan) maxChan = dd;
          }
        }
        return { nDiff, maxChan, w: a.w, h: a.h };
      },
      { freshB64, refB64 },
    );

    assert.ok(
      !cmp.sizeMismatch,
      `snapshot size differs: fresh ${cmp.fresh} vs reference ${cmp.ref} — regenerate with: npm run test:e2e:update`,
    );
    assert.equal(
      cmp.nDiff,
      0,
      `rendered PNG differs from snapshot (${cmp.nDiff} channel-bytes differ, maxChannel=${cmp.maxChan}). ` +
        `If this change is intended, refresh the reference: npm run test:e2e:update`,
    );
  } finally {
    await page.close();
  }
});
