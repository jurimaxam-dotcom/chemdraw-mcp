# Sicherheitsreview chemdraw-mcp (manuell, nur lesend)

Stand: Branch `main`, Code-Review auf `5cd30ee`. Die Abhängigkeits-Audits wurden auf HEAD `e5e7fac` (chore(deps): Sicherheitsupdates) wiederholt; `uv.lock` und `chemdraw_tool/ui/package-lock.json` im Arbeitsbaum sind dort identisch mit HEAD (`git diff --quiet HEAD -- …`). `d.html` ist inzwischen gelöscht. 29.10.2026.

**Im Standardprofil `mvp` registriert** (`server.py:258-264`): generate_molecule, batch_generate, compare_molecules, generate_reaction, lookup_molecule_data, save_png, export_anki_deck. Jeder Befund trägt unten die Angabe „MVP: ja/nein“.

Bedrohungsmodell: Eingaben der MCP-Werkzeuge setzt das Modell. Angreifer ist realistisch eine Prompt-Injection aus Inhalten, die das Modell liest (PubChem-/KEGG-/Webtexte, geteilte Dokumente, Projektdateien). Das Panel bekommt Daten ausschließlich vom eigenen Server. Release-Angreifer: kompromittierte Drittanbieter-Action oder Download-Quelle.

**Ergebnis kurz:** Keine kritischen oder hohen Befunde. Pfad-Traversal, Befehls-Injection, XXE und Panel-XSS sind sauber abgefangen. Die relevanten Punkte liegen in der Lieferkette (ungepinnte Actions, ungeprüfte Downloads, `curl | sh` im Bundle-Starter) und in ungefiltertem HTML in Anki-Karten.

---

## Befunde

### B1 – Anki-Kartentext wird bewusst unescaped als HTML übernommen
- **Ort:** `chemdraw_tool/anki_export.py:183-184` (`f"<div class='text'>{side.text}</div>"`), erreichbar über `export_anki_deck` (`chemdraw_tool/server.py:1116 ff.`, im MVP-Profil registriert), Auslieferung per `deliver="open"` (`anki_export.py:274`) oder `deliver="ankiconnect"` (`anki_export.py:244-262`, Import ohne Rückfrage).
- **Schwere:** mittel · **Sicherheit:** plausibel (Codepfad bestätigt; die Ausführung in Anki ist nicht gemessen) · **MVP:** ja
- **Szenario:** Eine Prompt-Injection (z. B. in einem PubChem-Beschreibungstext oder einem geteilten Lernskript) bringt das Modell dazu, eine Karte mit `<script>…</script>` oder `<img onerror=…>` im Feld `front.text`/`back.text` anzulegen. Anki Desktop rendert Kartenfelder als HTML in einem Chromium-Webview und führt dort JavaScript aus. Mit `deliver="ankiconnect"` landet die Karte ohne Import-Dialog in der Sammlung und läuft bei jeder Wiederholung. Folgen: Inhalte der Lernsammlung manipulieren und Anfragen an lokale Dienste stellen (AnkiConnect auf `127.0.0.1:8765`; ob dessen Origin-Prüfung das abfängt, ist ungeprüft).
- **Fix:** `side.text` per `html.escape` übernehmen und nur eine kleine Allowlist an Formatierung zulassen (`<b>`, `<i>`, `<sub>`, `<sup>`, `<br>`), z. B. mit `nh3`/`bleach` oder einem eigenen Mini-Sanitizer. Mindestens `<script>`, `on*=`-Attribute, `javascript:` und `<iframe>` entfernen. `deliver="ankiconnect"` nur nach Klick im Panel zulassen, nie direkt vom Modell.

### B2 – GitHub Actions über Tag/Branch statt Commit-SHA eingebunden
- **Ort:** `.github/workflows/ci.yml:20,23,28,60`; `.github/workflows/publish.yml:17,18,20,31,35,48,49,67`. Besonders `pypa/gh-action-pypi-publish@release/v1` (Branch-Referenz) in einem Job mit `id-token: write` (`publish.yml:28-35`).
- **Schwere:** mittel · **Sicherheit:** bestätigt (Konfiguration), Ausnutzung setzt eine Kompromittierung des Upstream voraus
- **Szenario:** Wird ein Upstream-Tag oder -Branch umgebogen (Muster tj-actions/changed-files, März 2025), läuft fremder Code im Publish-Job. Er kann mit dem OIDC-Token eine manipulierte Version von `chemdraw-mcp` auf PyPI veröffentlichen. Der Bundle-Starter (`mcpb/server/run.sh`) installiert genau diese Version automatisch bei allen Nutzern.
- **Fix:** Alle `uses:` auf die volle Commit-SHA pinnen (Tag als Kommentar dahinter) und Dependabot bzw. Renovate für `github-actions` aktivieren. Für den Publish-Job ein GitHub-Environment mit Required Reviewer anlegen und den Trusted Publisher auf dieses Environment einschränken.

### B3 – `mcp-publisher` wird als „latest“ ohne Prüfsumme geladen und mit OIDC-Rechten ausgeführt
- **Ort:** `.github/workflows/publish.yml:80-89` (`curl …/releases/latest/download/…tar.gz | tar xz`, dann `mcp-publisher login github-oidc`; Job hat `id-token: write`)
- **Schwere:** mittel · **Sicherheit:** bestätigt (Konfiguration)
- **Szenario:** Ein kompromittiertes oder neues Release des Registry-Repos läuft ungeprüft mit dem OIDC-Token. Damit lässt sich der Registry-Eintrag `io.github.jurimaxam-dotcom/…` umschreiben, etwa auf ein anderes Paket. Außerdem kann ein Breaking Change den Publish still verändern.
- **Fix:** Eine feste Version pinnen und die SHA-256 gegen einen im Repo hinterlegten Wert prüfen (`sha256sum -c`).

### B4 – Bundle-Starter installiert uv per `curl | sh` und zieht Abhängigkeiten ungelockt von PyPI
- **Ort:** `mcpb/server/run.sh:36-43` (`curl -LsSf https://astral.sh/uv/install.sh | sh`), `run.sh:138` (`uv tool install … "chemdraw-mcp==$VERSION"`) sowie Fallback `run.sh:149` (`uv tool run`); ebenso `install.sh:22-24`.
- **Schwere:** mittel · **Sicherheit:** bestätigt (Verhalten)
- **Szenario:** (a) Beim ersten Start in Claude Desktop lädt das Bundle **ohne Rückfrage** ein Shellskript aus dem Netz und führt es aus; wer astral.sh oder die TLS-Strecke kontrolliert, bekommt Codeausführung beim Nutzer. (b) Gepinnt ist nur `chemdraw-mcp`. `pyproject.toml` nennt `rdkit`, `lxml`, `requests`, `Pillow` ganz ohne Versionsgrenze und den Rest nur mit Untergrenzen (`mcp>=2.3,<3`, `matplotlib>=3.10.9` …). Alle direkten und transitiven Abhängigkeiten (rdkit, lxml, requests, mcp …) löst uv beim Nutzer frisch auf. Eine bösartige Neuversion einer Abhängigkeit, die zur Spezifikation in `pyproject.toml` passt, wird so automatisch installiert. `uv.lock` greift hier nicht.
- **Fix:** (a) uv nicht still installieren, sondern mit klarer Fehlermeldung abbrechen. Alternativ eine gepinnte uv-Version per Prüfsumme laden. (b) Beim Release eine Constraints- bzw. Hash-Datei aus `uv.lock` erzeugen (`uv export --format requirements-txt --hashes`), ins Bundle legen und mit `uv tool install --constraints …` verwenden. Oder im Bundle `uv pip install --require-hashes` nutzen.

### B5 – Release-Tag wird per `${{ }}` direkt in ein Shell-Kommando interpoliert
- **Ort:** `.github/workflows/publish.yml:53` (`gh release upload "${{ github.event.release.tag_name }}" …`)
- **Schwere:** niedrig · **Sicherheit:** plausibel
- **Szenario:** Git-Refnamen dürfen `$`, `(`, `)` und Backticks enthalten. Ein Tag wie `v1$(curl …|sh)` würde innerhalb der doppelten Anführungszeichen ausgeführt, und zwar in einem Job mit `contents: write`. Releases kann aber nur anlegen, wer Schreibrechte hat. Real bleibt das Risiko gering; es geht um Hygiene.
- **Fix:** `env: TAG: ${{ github.event.release.tag_name }}` setzen und dann `gh release upload "$TAG" …` aufrufen.

### B6 – Build-Downloads ohne Integritätsprüfung; Schriftart auf Major-Version „@5“
- **Ort:** `scripts/build-web.sh:23-27` (Pyodide-Tarball von GitHub-Releases, kein Hash), `build-web.sh:33` (`@fontsource/$fam@5`, gleitende Version); die Seite lädt das Ergebnis als `vendor/pyodide/pyodide.js` (`web/praktikumsrechner/index.html:213-226`). Im Entwicklungsmodus lädt sie zusätzlich `cdn.jsdelivr.net` ohne SRI (`index.html:211`, nur auf localhost).
- **Schwere:** niedrig · **Sicherheit:** bestätigt (Verhalten)
- **Szenario:** Ein manipulierter Tarball (auch einer, der im Cache unter `~/.cache/chemdraw-web` liegen bleibt) wird mit GitHub Pages an alle Besucher ausgeliefert. Der Service Worker cached ihn danach dauerhaft offline.
- **Fix:** Die SHA-256 des Pyodide-Tarballs und der Schriftdateien im Skript hinterlegen und prüfen. Fontsource auf eine exakte Version pinnen.

### B7 – Panel-Links aus PubChem-Metadaten ohne Schema-Prüfung
- **Ort:** `chemdraw_tool/ui/src/components/SourceList.jsx:68,90` (`href={group.url}`, `href={source.url}`). Die Quelle ist `meta.get("URL")` aus der PubChem-PUG-View-Referenz (`chemdraw_tool/databases.py:236`), weitergereicht über `server.py:2784`. React ist Version 18 (`package.json`), dort werden `javascript:`-URLs nur gewarnt, nicht blockiert.
- **Schwere:** niedrig · **Sicherheit:** plausibel · **MVP:** ja (Datenblatt über lookup_molecule_data)
- **Szenario:** Die Referenz-URL kommt von einem PubChem-Depositor, also von Dritten. Stünde dort `javascript:…`, liefe der Code beim Klick im Panel-iframe. Die Wirkung ist begrenzt: srcdoc-Sandbox mit `allow-scripts`, Zugriff nur auf die AppBridge, also `callServerTool` auf eigene Werkzeuge wie `save_png` oder `export_anki_deck` (siehe B1). Wegen `target="_blank"` blockiert die Sandbox ohne `allow-popups` den Klick wahrscheinlich ohnehin.
- **Fix:** Im Server oder im Panel nur `http:`/`https:` zulassen (`new URL(u).protocol`), sonst den Link weglassen.

### B8 – Keine Größen- oder Mengenbegrenzung für Werkzeugeingaben
- **MVP:** ja für batch_generate/compare_molecules/save_png/_slugify; generate_scope_table und generate_3d nur im Profil `full`.
- **Ort:** u. a. `batch_generate`/`compare_molecules` (MVP) und `generate_scope_table` (full) mit unbegrenzter Listenlänge, `generate_3d` (full, Konformer-Einbettung), `_slugify` ohne Längenkappung (`server.py:509-513`), `save_png` (je Aufruf 8 MB, Aufrufzahl unbegrenzt; `png_writer.py:15,73-80`).
- **Schwere:** niedrig · **Sicherheit:** bestätigt (fehlende Limits); die Wirkung wurde nicht gemessen
- **Szenario:** Per Prompt-Injection ruft das Modell Werkzeuge mit Tausenden Strukturen oder Riesenmolekülen auf. Der stdio-Server blockiert dann (der Hauptthread rechnet), `~/ChemDraw-Output` füllt sich, oder ein Titel über ~255 Byte führt zu `OSError: File name too long` statt zu einer sauberen Meldung. `FindMCS` hat einen Timeout (`image_export.py:465`, 10 s), der Rest nicht.
- **Fix:** Listen auf z. B. 50 Einträge kappen (Pydantic `max_length`), SMILES/Namen auf z. B. 2 000 Zeichen, Atomzahl vor `EmbedMolecule` begrenzen, Slugs auf 120 Zeichen kürzen (wie `png_writer._safe_stem`), und für `save_png` ein Tages- oder Ordnerlimit setzen.

### B9 – Werkzeuge überschreiben vorhandene Ausgabedateien mit gleichem Slug
- **Ort:** `chemdraw_tool/image_export.py:429-445` (`write_files`, Überschreiben ist Absicht), Anki `server.py:1175`, 3D `server.py:1660-1663`
- **Schwere:** info · **Sicherheit:** bestätigt
- **Szenario:** Das Modell kann über `title`/`name`/`deck_name` jede Datei **innerhalb** des jeweiligen Unterordners von `~/ChemDraw-Output` überschreiben, etwa eine früher erzeugte `aspirin.png` mit anderem Inhalt. Ein Schreiben außerhalb ist nicht möglich (siehe „Geprüft“).
- **MVP:** ja (Molekül, Vergleich, Reaktion, Anki); 3D nur `full`.
- **Fix:** So belassen (dokumentierte Absicht) oder bei Titel-Kollision mit anderem Fingerabdruck ein Suffix anhängen.

### B10 – AppleScript-Exportpfad ohne Escaping (toter Code)
- **Ort:** `chemdraw_tool/chemdraw.py:46-62` – `build_export_svg_script` setzt `output_path` ungeescaped in `keystroke "{output_path}"` ein. Pfad und App-Name in `build_open_script` werden escaped (`chemdraw.py:19-27`).
- **Schwere:** info · **Sicherheit:** bestätigt (Code), nicht erreichbar: kein MCP-Werkzeug und kein Skript ruft `export_to_svg`/`open_in_chemdraw` auf (grep ohne Treffer außerhalb von `chemdraw.py`).
- **Szenario:** Würde der Export wieder an ein Werkzeug gehängt und der Pfad käme aus einem Titel, könnte ein `"` gefolgt von AppleScript-Code (`do shell script`) ausgeführt werden.
- **Fix:** `_escape_applescript(output_path)` auch hier anwenden oder das Modul entfernen.

### B11 – Kleinere Hygiene-Punkte
- Bandit B324 (SHA-1): `anki_export.py:187` und `server.py:505` nutzen `hashlib.sha1` nur für kurze Inhalts-Kürzel in Dateinamen, nicht für Integrität oder Authentisierung. Eine Kollision würde höchstens eine Datei im eigenen Ausgabeordner überschreiben (vgl. B9). **info.** Optional `usedforsecurity=False` setzen oder SHA-256 nehmen, damit Scanner schweigen.
- `.github/workflows/ci.yml`: kein `permissions:`-Block, es gelten also die Repo-Standardrechte für `GITHUB_TOKEN` (bei Fork-PRs ohnehin read-only). Außerdem `npm install` statt `npm ci` (`ci.yml:36`), womit die CI das Lockfile nicht erzwingt. **niedrig, bestätigt.** Fix: `permissions: contents: read` und `npm ci`.
- `actions/checkout` ohne `persist-credentials: false` in `publish.yml:48,67` (Token bleibt in `.git/config`, solange der Job läuft). **info.**
- `chemdraw_tool/desktop_config.py:181-197`: schreibt `claude_desktop_config.json` nicht atomar. Das `.bak` kopiert die Env-Blöcke **anderer** MCP-Server (dort stehen oft API-Tokens) in eine zweite Datei mit Standard-umask. **info.** Fix: in eine Temp-Datei schreiben, dann `os.replace`, und die Rechte des Originals auf `.bak` übernehmen.
- `chemdraw_tool/vault.py:24,40,79-90`: `rglob` über `CHEMDRAW_VAULT_PATH`. Kein Pfad aus Modell-Eingaben, also keine Traversal. Ob Symlinks im Vault nach außen verfolgt werden, hängt von der Python-Version ab (ungeprüft). Nur aktiv, wenn die Variable gesetzt ist; `search_vault` steht nicht in `MVP_TOOLS`, ist also nur im Profil `full` registriert. **info.**
- Datenabfluss: Substanznamen und SMILES aus dem Chat gehen an PubChem, NCI CIR, ChEBI, KEGG und UniProt (`databases.py`, `resolver.py`). So beschrieben im Manifest. **info.**
- `web/praktikumsrechner/index.html:330,381,410`: `innerHTML` mit Template-Strings. Nutzereingaben und Aufgabentexte laufen durch `esc()` (`index.html:245`, escapt `& < > "`, aber nicht `'`; alle betroffenen Attribute stehen in doppelten Anführungszeichen, damit reicht das). Nicht escaped sind nur `loesungText(a)` (`:286-289`, `:344-347`) und der Platzhalter `ph` im Attribut `placeholder="${ph}"` (`:298-299`); beide kommen aus dem eigenen Pyodide-Rechenkern bzw. einer Konstantentabelle (`BEISPIEL`), nicht vom Nutzer. Es gibt keine CSP-Meta. **info.**
- `web/praktikumsrechner/sw.js`: Cache-first mit `ignoreSearch: true`, nur Same-Origin-GET, Cache-Version pro Build. Scope ist der Ordner der Seite. Unauffällig bis auf das Risiko, eine einmal vergiftete Datei (siehe B6) bis zum nächsten Build offline auszuliefern. **info.**

---

## Geprüft, unauffällig

**Pfade / Schreiben außerhalb `~/ChemDraw-Output`**
- `_slugify` (`server.py:509-513`): `re.sub(r"[^\w\s-]", "", …)` entfernt `/`, `\`, `.`, `~`. `..` und absolute Pfade sind nicht möglich. Das gilt für alle Aufrufer: Spektrum `:869`, DC `:944`, Scope `:1100`, Anki `:1175`, Titration `:1247`, Kalibrierung `:1348`, Spezies `:1400`, PK `:1466`, Dosis-Wirkung `:1551`, Vergleich `:1623`, 3D `:1660`, Reaktion `:3205`, Molekül `_molecule_slug` `:516`.
- `write_files` (`image_export.py:429`): Format-Endungen sind feste Schlüssel (`png`/`svg`), kein Modell-String.
- `save_png` → `png_writer._safe_stem` (`png_writer.py:21-28`): schneidet Verzeichnisanteile ab, Allowlist `[A-Za-z0-9._-]`, entfernt `.` am Rand, max. 200 Zeichen. Base64 wird validiert, PNG-Magic geprüft, 8-MB-Grenze gilt schon vor dem Dekodieren, und es gibt keinen Überschreibschutz-Bypass (Suffix `-2`).
- Anki-Mediendateien: Namen aus dem SHA-1 des Inhalts (`anki_export.py:187`), das Tempverzeichnis per `tempfile`.
- `vault.py`: Einträge werden über `stem`-Vergleich gesucht, nie per Pfad-Join aus der Eingabe.

**Befehle / Injection**
- Alle `subprocess`-Aufrufe nutzen Argument-Listen, nie `shell=True` (`chemdraw.py`, `anki_export.py:274` mit festem Pfad, `resolver.py:218` `java -version`, `resolver.py:266` OPSIN-JVM).
- OPSIN-stdin-Protokoll: Namen mit `\n`/`\r` werden vorher abgewiesen (`resolver.py:447`). Das Namens-Echo wird verglichen (`resolver.py:310`), eine Desynchronisierung ist deshalb nicht möglich.
- Kein `pickle`, kein `yaml.load`, kein `eval`/`exec` im Paket (grep über `chemdraw_tool/*.py`).

**ReDoS**
- Alle Regexe in `resolver.py` (`:27-29`, `:574-580`), `server.py:511-512`, `databases.py:121-288` und `png_writer.py:18-19` geprüft: Zeichenklassen, verankerte Muster und lineare Wiederholungen ohne verschachtelte, sich überlappende Quantoren. `_FORMULA = (?:[A-Z][a-z]?\d*)+` ist eindeutig zerlegbar (jedes Glied beginnt mit einem Großbuchstaben), also kein katastrophales Backtracking. Die GHS-Regexe laufen auf PubChem-Text, nicht auf Modelleingaben. Unauffällig.

**XML**
- `validator.py:104` `etree.fromstring` parst nur selbst erzeugtes CDXML (`server.py:207-208`), keine externen Dateien. Es gibt kein Werkzeug, das CDXML einliest, daher keine XXE-Fläche. CDXML-Texte entstehen über `lxml`-Elemente, die automatisch escapen.

**Netz / SSRF**
- Alle Datenbank-URLs haben feste Hosts (`databases.py:17-61,428,458-460,512`, `resolver.py:56,61`). Namen gehen über `quote(name, safe="")` in den Pfad. SMILES werden per POST-Formular übertragen. `kegg_id` (`databases.py:481,498`) ist nicht gequotet, stammt aber aus der KEGG-Antwort und kann nur den Pfad auf `rest.kegg.jp` verändern. AnkiConnect ist fest auf `127.0.0.1:8765` gesetzt (`anki_export.py:33`).

**Panel (`chemdraw_tool/ui/src`)**
- `dangerouslySetInnerHTML` in Reaction/Plot/Scope/Spectrum/Mechanism/Ambiguous/Tlc/SourceList/StructureCanvas gibt nur SVG vom eigenen Server aus. Für jeden Text-Pfad in diese SVGs wurde geprüft, ob er escaped wird:
  - RDKit-Legenden: Mit FreeType werden sie als Pfade gezeichnet, ohne FreeType als escaptes `<text>`. Messung mit RDKit 2026.03.6: Legende `<img src=x onerror=alert(1)>&` landet nicht roh im SVG (Befehl unten).
  - matplotlib (`svg.fonttype: none`) escapt Text selbst.
  - `scope.py:653` und `image_export.py:423` nutzen `xml.sax.saxutils.escape`.
  - `projection.py:471-508` setzt nur Formel-Labels ein, die aus dem Molekül berechnet werden (`_hetero_label`/`_end_label`), keine Freitexte.
- Kein `postMessage`-Handler und kein `fetch`/WebSocket im eigenen Code (Kommunikation nur über die SDK-AppBridge). `_UI_META` (`server.py:364`) deklariert keine CSP-Ausnahmen oder `connectDomains`, also gilt die restriktive Standard-CSP des Hosts. `dist/index.html` lädt keine externen Ressourcen; die gefundenen URLs sind nur Namespaces und Schema-IDs.
- Externe Links mit `rel="noopener noreferrer"` (Schema siehe B7).

**CI**
- Kein `pull_request_target`, kein `workflow_run`. Der CI-Job hat keine Secrets. Publish per Trusted Publishing (OIDC) ohne gespeicherten Token, `id-token: write` nur in `publish`/`registry`.

**Skripte**
- `scripts/*.sh` quoten Variablen durchgehend und laden nichts per `curl | sh` (nur `build-web.sh` lädt Dateien, siehe B6). `handshake.sh` führt den Befehl aus der lokalen Desktop-Config aus, das ist beabsichtigt und lokal. `traffic-snapshot.sh` nutzt absolute Pfade (`/bin/rm`, `/usr/bin/mktemp`). `deploy-pages.sh` bricht ab, solange im Impressum Platzhalter stehen.

**`d.html`**
- War beim ersten Lesen eine untracked, gespeicherte GitHub-Docs-Seite („About GitHub Sponsors“, 128 KB) ohne Secrets. Inzwischen gelöscht (`ls d.html` → No such file).

---

## Abhängigkeiten (gegen HEAD `e5e7fac`)

```
$ git log -1 --oneline
e5e7fac chore(deps): Sicherheitsupdates – starlette, urllib3, pillow, cryptography, pyjwt, zod u. a.
$ git diff --quiet HEAD -- uv.lock chemdraw_tool/ui/package-lock.json && echo "Lockfiles = HEAD"
Lockfiles = HEAD
$ which pip-audit osv-scanner trivy grype
pip-audit not found / osv-scanner not found / trivy not found / grype not found
```
Python-Audit ersatzweise über die OSV-API (nur Abfrage, nichts installiert). Das Skript las `git show HEAD:uv.lock` und lief mit dem vorhandenen `.venv`-Python `-I` im Scratchpad:
```
64 Registry-Pakete per POST https://api.osv.dev/v1/querybatch
64 Pakete abgefragt; Treffer: 0
```
Versionen in HEAD:uv.lock: rdkit 2026.3.6 · lxml 6.1.0 · requests 2.34.2 · Pillow 13.0.0 · mcp 2.3.0 · genanki 0.13.1 · matplotlib 3.10.9 · urllib3 2.8.0 · certifi 2026.10.23 · starlette 1.10.0 · cryptography 50.0.2 · pyjwt 2.15.1 · python-multipart 0.0.32 · pydantic 2.13.4 · idna 3.20 · py2opsin 1.2.0 · molmass 2026.1.8. OSV meldet für keine davon eine bekannte Schwachstelle. Wie aktuell genanki gepflegt wird, wurde nicht nachgeschlagen.

```
$ npm audit --prefix chemdraw_tool/ui --package-lock-only        (HEAD-Stand)
found 0 vulnerabilities
$ npm audit --prefix chemdraw_tool/ui --package-lock-only --omit=dev
found 0 vulnerabilities
```

**Gemeldet von der parallelen Session, nicht selbst geprüft:** `pip-audit --no-deps` → 0 Befunde, `gitleaks` über 290 Commits → nichts gefunden. (Die eigene Secret-Suche unten deckt sich damit.)

Dependabot/Renovate: nicht konfiguriert (kein `.github/dependabot.yml`). Hinweis zu B4: Die Lockfile-Updates schützen Bundle-Nutzer nicht, weil `run.sh` die Abhängigkeiten ohne `uv.lock` frisch auflöst.

## Secret-Suche in der Git-Historie

297 Commits (`git rev-list --all | wc -l`, Stand vor `e5e7fac`; der neue Commit ändert nur Lockfiles und Versionsangaben).

```
$ git log -p --all | grep -nE "sk-ant-…|ghp_…|gho_…|github_pat_…|AKIA[0-9A-Z]{16}|BEGIN … PRIVATE KEY|pypi-[A-Za-z0-9_-]{30}|xox[baprs]-…|AIza…"
(keine Treffer)

$ git log -p --all | grep -Ei '^\+.*(api[_-]?key|token|password|passwd|secret)["'\'' ]*[:=]["'\'' ]*[A-Za-z0-9_-]{12,}'  (ohne id-token/GH_TOKEN-Referenzen)
(keine Treffer)

$ git log -p --all | grep -cE "Bearer [A-Za-z0-9._-]{20,}|ANTHROPIC_API_KEY=[^ $]{8,}|OPENAI_API_KEY=[^ $]{8,}"
0
$ git log -p --all | grep -n ANTHROPIC_API_KEY
nur Doku-Zeilen ("braucht `ANTHROPIC_API_KEY`", "export ANTHROPIC_API_KEY=…" mit Auslassungszeichen) — kein Wert

$ git log --all --name-only | grep -iE '(^|/)\.env|secret|credential|\.pem$|\.key$|id_rsa|\.npmrc|\.pypirc|netrc'
(keine Treffer)

$ git log --all --diff-filter=D --name-only | sort -u   → 40 gelöschte Pfade
Bilder/GIFs, .repro-harness, alte UI-Komponenten, docs/produkt/*, docs/distribution/*, plans/*, Tests,
ein Worktree-Gitlink (.claude/worktrees/agent-…). Keine .env-, Schlüssel- oder Credential-Dateien.

$ git ls-files | grep -iE '\.env|secret|\.pem|\.key$'   → leer
.gitignore enthält .env und .env.*
```
Ergebnis: Keine Secrets in der Historie gefunden. Nicht geprüft wurden personenbezogene Inhalte in den gelöschten `docs/produkt/*`-Dateien (z. B. Anschrift); das ist kein Secret im engeren Sinn.

## Verwendete Prüfbefehle (Auswahl)
- `grep -rnE "subprocess|osascript|os\.system|Popen|shell=True|pickle|yaml\.load|eval\(|exec\(|etree\.|urlopen|requests\.(get|post)|quote\(" chemdraw_tool`
- `grep -rnE "dangerouslySetInnerHTML|innerHTML|postMessage|fetch\(|href=\{" chemdraw_tool/ui/src`
- RDKit-Escaping-Test: `MolDraw2DSVG(300,300[, -1,-1, noFreetype=True])` + `PrepareAndDrawMolecule(…, legend='<img src=x onerror=alert(1)>&')` → `'<img' in svg == False` in beiden Modi

---

## Nachtrag: Plugin-Scan Claude Security (ganzes Repo, medium, Revision e5e7fac)

Jay hat den Scan in der Session freigegeben. Er lief 26 Minuten mit 78 Agenten: 36 Researcher, alle zurückgekehrt. Die Vollständigkeitsprüfung meldet `checked`. Stempel: `verification.status: verified`. Der Report liegt unter `CLAUDE-SECURITY-20261029-200326/CLAUDE-SECURITY-RESULTS.md` (eigene .gitignore, wird nicht committet).

| ID | Schwere | Ort | Kern | Gremium |
|---|---|---|---|---|
| F1 | mittel | .github/workflows/publish.yml:82 | mcp-publisher wird als `latest` ohne Prüfsumme in einem Job mit `id-token: write` geladen. Weil der Trusted Publisher kein Environment verlangt, kann das Binary auch auf PyPI veröffentlichen. | 2/3 |
| F2 | mittel | evals/tool-routing/run_claude.py:47 | `claude -p` läuft mit `cwd=tempfile.gettempdir()` und `--setting-sources project`. Auf Linux kann ein Mitnutzer über `/tmp/.claude/settings.json` Hooks einschleusen; auf macOS ist TMPDIR je Nutzer getrennt. | 3/3 |
| F3 | niedrig | tests/gallery_ui.py:62 | Ein vorab angelegter Symlink `/tmp/chem-gallery` führt dazu, dass alle Dateien im Zielordner gelöscht werden. | 3/3 |
| F4 | niedrig | tests/screenshot_ui.py:107 | Fester Dateiname in `/tmp`: Ein Symlink lässt den Screenshot eine fremde Datei überschreiben. | 3/3 |

Abgleich mit der manuellen Durchsicht:
- F1 deckt sich mit B3 und ergänzt ihn um die PyPI-Ausweitung.
- F2, F3 und F4 sind neu.
- Für B1 (Anki-HTML), B2, B4 und B5–B11 liegt kein Plugin-Befund vor. Diese bleiben als Befunde der manuellen Durchsicht offen.

Nicht gelesen hat der Scan:
- das minifizierte Bundle `ui/dist/index.html` (nur den Kopf)
- `tests/`, `docs/`, `plans/` und `assets/` als Komponenten (F3 und F4 kamen trotzdem zustande)
- die Vendor-Dateien unter `web/dist/vendor`

---

## Umsetzung 30.10.2026 (Tisch-Faden 20261030-073542-sicherheitsfixes)

| Befund | Status | Commit | Beleg |
|---|---|---|---|
| B2 | behoben | 3e13f17 | Alle `uses:` auf Commit-SHA, Tag als Kommentar (ohne Major-Sprung); `.github/dependabot.yml` für `github-actions`. `actionlint` grün. |
| B3/F1 | behoben (Workflow), Rest Jay | f910a4d | mcp-publisher fest `v1.8.6`, `sha256sum -c` gegen `1fbe93fc…` — lokal gegen das Asset und `registry_1.8.6_checksums.txt` verifiziert. `id-token: write` war schon job-scoped, feiner geht nicht. PyPI-Job läuft in `environment: pypi`; Sperre braucht Jays zwei Klicks (PyPI-Publisher + Required Reviewer), Haken in `plans/vermarktung.md`. |
| B5 | behoben | 4815ed8 | `TAG` über `env:`, kein `${{ }}` mehr in `run:`-Zeilen. |
| B1 | behoben (Text), Rest offen | 6004d11 | `_safe_text`: `html.escape`, Allowlist `<b> <i> <sub> <sup> <br>` ohne Attribute, Entities bleiben, Cloze bleibt. 4 Tests, 2 davon vorher rot. `deliver="ankiconnect"` nur per Klick: offen im Plan. |
| F2 | behoben | 644c17f | `claude -p` läuft in eigenem `mkdtemp`-Ordner (0700), danach entfernt; Rauchtest mit Attrappe. |
| F3/F4 | behoben | 7e6ab6e | Galerie und Screenshots je Lauf in frischem `mkdtemp`-Ordner, kein Löschen in festen `/tmp`-Pfaden. |
| B7 | behoben | 5c1d989 | `safeHref`: nur `http:`/`https:` werden verlinkt. DOM-Test vorher rot; Bundle neu gebaut. |
| B4 | offen (Jays Entscheidung) | — | Optionen (a)–(c) in `plans/vermarktung.md`. |
| B6, B8–B11 | offen | — | Nicht im Auftrag. |

Gate nach allen Fixes: `./test.sh` rc=0 (ruff grün, 7343 passed / 16 skipped, Bundle aktuell, Frontend 31 + 82 + 2 pass); `npm run test:host` rc=0.
