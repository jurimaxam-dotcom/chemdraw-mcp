// Lädt die Cartoon-Engine erst, wenn ein Protein gezeigt wird. Der gebaute
// Mol*-Code steht als Textblock <script type="text/plain"
// id="chem-cartoon-engine"> in der HTML-Datei (vite.config.js) und wird hier
// als Inline-Script ausgeführt (CSP der ext-apps-Sandbox: script-src
// 'unsafe-inline' — kein eval, kein Blob, kein Worker nötig). Fehlt der Block
// (Node-Tests) oder blockiert der Host das Script, fehlt danach die Engine —
// dann lehnt das Promise ab und das Panel bleibt bei der SVG-Spur.
export const ENGINE_ID = "chem-cartoon-engine";
export const engineDeps = { win: () => window };

let pending = null;

export function loadEngine() {
  const win = engineDeps.win();
  if (win.__chemCartoon) return Promise.resolve(win.__chemCartoon);
  if (pending) return pending;
  pending = new Promise((resolve, reject) => {
    const source = win.document.getElementById(ENGINE_ID)?.textContent || "";
    if (!source) {
      reject(new Error("cartoon engine not bundled"));
      return;
    }
    try {
      const script = win.document.createElement("script");
      script.textContent = source;
      win.document.head.appendChild(script);
      script.remove();
    } catch (err) {
      reject(err);
      return;
    }
    if (win.__chemCartoon) resolve(win.__chemCartoon);
    else reject(new Error("cartoon engine blocked (no script execution)"));
  });
  // Ein Fehlschlag bleibt nicht hängen: der nächste Versuch darf neu laden
  pending.catch(() => { pending = null; });
  return pending;
}

/** Nur für Tests: Zwischenspeicher leeren. */
export function resetEngine() {
  pending = null;
}
