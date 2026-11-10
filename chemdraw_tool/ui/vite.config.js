import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const ENGINE = here("./src/protein/cartoonEngine.js");

// Cartoon-Engine (E13): Mol* als eigener IIFE-Build, in der HTML-Datei als
// `<script type="text/plain" id="chem-cartoon-engine">` — der Browser liest den
// Block nur als Text und führt ihn erst aus, wenn ein Protein gezeigt wird
// (src/protein/loadEngine.js). Gemessen 10.11.2026 (Panel-Start im iframe,
// Median aus 7): ohne Engine 30 ms; als gewöhnlicher Import 210 ms (der Browser
// wertet die 2,4 MB jedes Mal aus); als JS-Zeichenkette 77 ms; als Textblock
// 55 ms. esbuild ist exakt gepinnt (package.json) — der Gate-Vergleich der
// dist-Bytes verlangt einen deterministischen Build. Lizenztexte der
// gebündelten Pakete stehen als Kopfkommentar im Engine-Code
// (THIRD_PARTY_LICENSES im Repo).
function cartoonEngine() {
  return {
    name: "cartoon-engine",
    apply: "build",
    transformIndexHtml() {
      const notice = readFileSync(here("../../THIRD_PARTY_LICENSES"), "utf8").replaceAll("*/", "* /");
      const out = buildSync({
        entryPoints: [ENGINE],
        bundle: true,
        minify: true,
        format: "iife",
        target: "es2020",
        legalComments: "none",
        banner: { js: `/*!\n${notice}*/` },
        write: false,
        logLevel: "error",
      });
      const code = out.outputFiles[0].text;
      // Ein "</script" im Code beendete den Block vorzeitig — dann lieber scheitern
      if (/<\/script/i.test(code)) throw new Error("cartoon engine contains </script");
      return [{ tag: "script", attrs: { type: "text/plain", id: "chem-cartoon-engine" }, children: code, injectTo: "body" }];
    },
  };
}

export default defineConfig({
  plugins: [cartoonEngine(), react(), viteSingleFile()],
  build: {
    target: "esnext",
    outDir: "dist",
  },
});
