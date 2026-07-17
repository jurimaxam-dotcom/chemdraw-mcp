# Repro-Harness: Panel gegen Referenz-Host

Testet `dist/index.html` gegen den offiziellen ext-apps-Referenz-Host (`AppBridge`)
in headless Chromium — unabhängig von Claude Desktop. Entstanden beim Debugging
des „Warte auf Daten…"-Bugs (Juli 2026), als Desktop nach einem Update
`structuredContent` nicht mehr ans iframe durchreichte.

```bash
# aus chemdraw_tool/ui/:
npx esbuild .repro-harness/host-src.mjs --bundle --format=iife --outfile=.repro-harness/host.bundle.js
node .repro-harness/run.mjs                          # Payload mit structuredContent
PAYLOAD=payload-desktop.json node .repro-harness/run.mjs  # Desktop-Verhalten: nur content+isError
```

- `host-src.mjs` — Minimal-Host (AppBridge + PostMessageTransport), sendet nach
  `initialized` das Payload als `sendToolResult`
- `payload.json` — echtes `generate_molecule`-Ergebnis (content + structuredContent)
- `payload-desktop.json` — dasselbe ohne `structuredContent` (Claude-Desktop-Verhalten ab v1.22209.0)
- `run.mjs` — Playwright-Runner; Urteil: „PANEL RENDERT: …" oder „TIMEOUT"
