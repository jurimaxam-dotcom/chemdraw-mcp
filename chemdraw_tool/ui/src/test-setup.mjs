// Testumgebung fuer die Panel-Komponenten.
//
// `node --test` kann zweierlei nicht, was React-Komponenten brauchen: JSX
// parsen und ein DOM anbieten. Beides wird hier nachgeruestet — und zwar in
// einem eigenen Einstiegspunkt, der per `--import` VOR der Testdatei laeuft.
// Der Test-Runner reicht `--import` an jeden Kindprozess weiter, das Setup
// gilt also pro Testdatei frisch.
//
// Bewusst NICHT im `test:unit`-Lauf: `src/utils/*.test.mjs` sind reine
// Rechen-Tests und laufen heute ohne DOM. Globale jsdom-Objekte in denselben
// Prozess zu kippen wuerde ihr Verhalten aendern, ohne dass sie es brauchen.
import { existsSync, readFileSync, statSync } from "node:fs";
import { registerHooks } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

import { transformSync } from "esbuild";
import { JSDOM } from "jsdom";

// --- 1. Modulaufloesung wie Vite ---------------------------------------------
// Der App-Code importiert erweiterungslos (`./components/PropRow`) und in JSX.
// Node ESM kann beides nicht; die Hooks holen genau das nach, mehr nicht.
const CANDIDATE_SUFFIXES = ["", ".jsx", ".js", "/index.jsx", "/index.js"];

function isFile(url) {
  if (url.protocol !== "file:") return false;
  const stat = statSync(fileURLToPath(url), { throwIfNoEntry: false });
  return Boolean(stat?.isFile());
}

registerHooks({
  resolve(specifier, context, nextResolve) {
    const parent = context.parentURL ?? pathToFileURL(`${process.cwd()}/`).href;
    // Nur eigener Quellcode. In node_modules loest Node selbst auf — dort
    // haengen CJS-Dateien an relativen Pfaden, die dieser Hook sonst faelsch-
    // lich zu ES-Modulen erklaeren wuerde.
    const ours = !parent.includes("/node_modules/");
    if (ours && (specifier.startsWith(".") || specifier.startsWith("/"))) {
      for (const suffix of CANDIDATE_SUFFIXES) {
        const url = new URL(specifier + suffix, parent);
        if (isFile(url)) return { url: url.href, shortCircuit: true };
      }
    }
    return nextResolve(specifier, context);
  },

  load(url, context, nextLoad) {
    if (url.endsWith(".jsx")) {
      const path = fileURLToPath(url);
      if (!existsSync(path)) return nextLoad(url, context);
      // Klassische Transformation (React.createElement) — jede Komponente
      // importiert React selbst, ein Runtime-Import waere ueberfluessig.
      const { code } = transformSync(readFileSync(path, "utf8"), {
        loader: "jsx",
        format: "esm",
        target: "esnext",
        sourcefile: path,
      });
      return { format: "module", source: code, shortCircuit: true };
    }
    return nextLoad(url, context);
  },
});

// --- 2. DOM ------------------------------------------------------------------
const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
  pretendToBeVisual: true, // liefert requestAnimationFrame, das React DOM erwartet
});

const GLOBALS = [
  "window",
  "document",
  "navigator",
  "Element",
  "HTMLElement",
  "SVGElement",
  "Node",
  "Event",
  "MouseEvent",
  "KeyboardEvent",
  "CustomEvent",
  "DOMRect",
  "NodeFilter",
  "MutationObserver",
  "getComputedStyle",
  "requestAnimationFrame",
  "cancelAnimationFrame",
];

for (const key of GLOBALS) {
  const raw = key === "window" ? dom.window : dom.window[key];
  if (raw === undefined) continue;
  // Freie Funktionen (getComputedStyle …) brauchen `window` als `this`;
  // Konstruktoren (Grossbuchstabe) duerfen nicht gebunden werden.
  const value =
    typeof raw === "function" && !/^[A-Z]/.test(key) ? raw.bind(dom.window) : raw;
  Object.defineProperty(globalThis, key, {
    value,
    configurable: true,
    writable: true,
  });
}

// React 18 verlangt diese Flagge, sonst warnt jedes act() in die Konsole.
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
