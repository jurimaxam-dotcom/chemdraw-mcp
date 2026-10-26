# Content-Werkzeuge: Kurzvideo, Animation, Design (Stand 27.10.2026)

Open-Source-Recherche für hochwertigen Content, lokal auf M1 Max / 32 GB. Metadaten per `gh api`,
README/Releases/Homebrew geprüft, nichts installiert. Qualität 1–5. Setup: gering = brew/npm/App,
mittel = venv + Modelle/Addon, hoch = experimentell/große Modelle. ★ = Top-Empfehlung der Kategorie.

## Kurzvideo

| Werkzeug | Repo | Qualität | M1 | Setup | Begründung |
|---|---|---|---|---|---|
| ★ Remotion | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 5 | nativ (Node + Chrome) | gering | Bleibt die Montagebasis der Shorts; Vorlage `remotion-dev/template-tiktok` bringt 9:16 und Wort-Untertitel per whisper.cpp mit. Lizenz frei für Einzelpersonen und Firmen bis 3 Mitarbeiter (LICENSE.md Z. 20–21). |
| Cap | [CapSoftware/Cap](https://github.com/CapSoftware/Cap) | 4 | nativ arm64 | gering | Nimmt das echte Claude Desktop auf (kann Playwright nicht), Studio Mode macht Zoom, Hintergrund, Captions. AGPL-3.0. |
| Recordly | [webadderallorg/Recordly](https://github.com/webadderallorg/Recordly) | 4 | arm64-DMG, ScreenCaptureKit | gering | Screen-Studio-Ersatz mit Auto-Zoom, Cursor-Glättung und gestyltem Rahmen, stärker als Cap. Vorsicht: 35k Sterne in 7 Monaten, Lizenz laut GitHub `NOASSERTION` — vor Einsatz LICENSE lesen. |
| whisper.cpp | [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 5 | Metal + Core ML | gering | Wortzeitstempel für animierte Untertitel direkt in Remotion, schneller als Echtzeit. MIT. |
| mlx-audio | [Blaizzy/mlx-audio](https://github.com/Blaizzy/mlx-audio) | 4 | MLX nativ | mittel | Lokales Voiceover (TTS) und Transkription in einem Paket. Deutsch nur über Chatterbox oder Qwen3-TTS, Kokoro hat kein Deutsch. |
| auto-editor | [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 4 | arm64-Bottle | gering | Schneidet Wartezeiten (Claude denkt) automatisch aus Rohaufnahmen. Exportiert auch Schnittlisten. |
| LosslessCut | [mifi/lossless-cut](https://github.com/mifi/lossless-cut) | 4 | arm64-DMG | gering | Rohaufnahmen ohne Neukodierung zuschneiden, bevor sie in Remotion gehen. |
| OBS Studio | [obsproject/obs-studio](https://github.com/obsproject/obs-studio) | 4 | nativ (`macOS-Apple.dmg`) | gering | Robuste Rohaufnahme mit hoher Bitrate, aber ohne Auto-Zoom — Fallback zu Cap/Recordly. |
| Screenize | [syi0808/screenize](https://github.com/syi0808/screenize) | 3 | macOS-only | gering–mittel | Auto-Zoom nach Cursor mit editierbaren Keyframes. Jung, seit Mai ohne Push. |
| Revideo | [midrender/revideo](https://github.com/midrender/revideo) | 3 | Node | mittel | Echte MIT-Alternative zu Remotion (Fork von Motion Canvas). Nur relevant, falls die Remotion-Lizenzschwelle greift. |
| mlx-video (LTX-2, Wan2.2) | [Blaizzy/mlx-video](https://github.com/Blaizzy/mlx-video) | 2–3 | MLX nativ | hoch | Einziger Weg zu LTX-2/Wan auf dem Mac ohne CUDA, für 5-s-Hook-Clips. Experimentell; LTX-2-Gewichte nicht OSS. |

## Animation

| Werkzeug | Repo | Qualität | M1 | Setup | Begründung |
|---|---|---|---|---|---|
| ★ Remotion + @remotion/three + react-three-fiber | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) · [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | 5 | WebGL über Chrome/Metal | gering | 3D-Moleküle framegenau per `useCurrentFrame`, direkt im bestehenden Short-Projekt. Keine zweite Timeline. |
| Blender + Molecular Nodes | [blender/blender](https://github.com/blender/blender) · [BradyAJohnston/MolecularNodes](https://github.com/BradyAJohnston/MolecularNodes) | 5 | nativ arm64, Cycles mit Metal-Backend | gering–mittel | Kinoqualität für Molekül-Kamerafahrten (liest SDF, PDB, PubChem), CI auf macOS. Als Clip mit Alpha rendern, per `<OffthreadVideo>` in Remotion. |
| Manim Community | [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | 5 | arm64-Bottle | gering–mittel | Bester Werkzeugsatz für Formel- und Reaktionsübergänge im 3Blue1Brown-Stil. Ausgabe als MOV mit Alpha. |
| RDKit | [rdkit/rdkit](https://github.com/rdkit/rdkit) | 4 (Datenquelle) | arm64-Wheels (2026.9.1) | gering | Liefert 2D-Koordinaten und 3D-Konformere für alle anderen Werkzeuge. Damit wird dieselbe Struktur nahtlos von der ChemDraw-Zeichnung zum 3D-Modell. |
| Mol* (molstar) | [molstar/molstar](https://github.com/molstar/molstar) | 4 | WebGL | gering–mittel | Bester Web-Viewer für große Strukturen, Animation über MolViewSpec. Für kleine Moleküle aufwendiger als 3Dmol. |
| 3Dmol.js | [3dmol/3Dmol.js](https://github.com/3dmol/3Dmol.js) | 3 | WebGL | gering | Leicht, liest SDF/MOL direkt. Schlichterer Look, Frame-Steuerung für Remotion selbst bauen. |
| Glaxnimate | [KDE/glaxnimate](https://github.com/KDE/glaxnimate) | 3 | arm64-DMG | gering | Vektor-Animation mit GUI, exportiert Lottie. ChemDraw-SVGs von Hand animieren, dann per `@remotion/lottie` einsetzen. |
| manim-Chemistry | [UnMolDeQuimica/manim-Chemistry](https://github.com/UnMolDeQuimica/manim-Chemistry) | 3 | wie Manim | mittel | Moleküle aus .mol, Orbitale, Periodensystem in Manim. Ein-Personen-Projekt mit bekannten .mol-Fallen. |
| PyMOL Open-Source | [schrodinger/pymol-open-source](https://github.com/schrodinger/pymol-open-source) | 3 | arm64-Bottle | gering | Skriptbare Movie-Befehle und Raytracing für schnelle Vorlagen. Look wirkt neben Blender veraltet. |
| lottie-web / dotlottie-web | [LottieFiles/dotlottie-web](https://github.com/LottieFiles/dotlottie-web) | 3 | Browser | gering | Logo-, Icon- und UI-Bausteine in Remotion. lottie-web selbst kaum noch gepflegt. |

## Oberflächen- und Produktdesign

| Werkzeug | Repo | Qualität | M1 | Setup | Begründung |
|---|---|---|---|---|---|
| ★ Blender + Molecular Nodes | [blender/blender](https://github.com/blender/blender) · [BradyAJohnston/MolecularNodes](https://github.com/BradyAJohnston/MolecularNodes) | 5 | nativ arm64, Metal | gering–mittel | Hero-Renders der ChemDraw-Moleküle in Studioqualität für README, Posts und Thumbnails. Dasselbe Setup wie in der Animation. |
| mflux | [mflux-community/mflux](https://github.com/mflux-community/mflux) | 5 | MLX nativ | gering–mittel | FLUX.2, Qwen Image, Ming-Image (Poster/UI, RGBA) und SeedVR2-Upscaler lokal. Hintergründe und Szenen ohne Cloud. |
| shadcn/ui | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 5 | plattformneutral | gering | Komponenten als Quellcode im Projekt — schnellster Weg zu einem Web-Panel, das auf Screenshots hochwertig aussieht. |
| Satori | [vercel/satori](https://github.com/vercel/satori) | 4 | plattformneutral | gering | JSX → SVG/PNG: OG- und Social-Karten erzeugt der MCP selbst, Molekül-SVG eingebettet. Nur Flexbox-CSS. |
| Penpot | [penpot/penpot](https://github.com/penpot/penpot) | 4 | Web; Docker selbst gehostet | gering (Web) / mittel | Figma-Ersatz mit Design-Tokens und offiziellem MCP-Server ([penpot/penpot-mcp](https://github.com/penpot/penpot-mcp)). Für Panel-Mockups und README-Komposition. |
| ComfyUI | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 5 | MPS (+ Desktop-App) | mittel | Knoten-Workflows für Komposition, Inpainting, Upscaling, auch KI-B-Roll für Shorts. Auf dem Mac langsamer als mflux. |
| Inkscape | [gitlab.com/inkscape/inkscape](https://gitlab.com/inkscape/inkscape) | 4 | arm64 (Cask) | gering | SVG-Feinschliff an ChemDraw-Strukturen, Banner, Logo; Batch-Export per CLI. |
| Krita | [KDE/krita](https://github.com/KDE/krita) | 4 | arm64 (Cask) | gering | Raster-Retusche der Renders, Thumbnails für Shorts. |
| Storybook | [storybookjs/storybook](https://github.com/storybookjs/storybook) | 4 | plattformneutral | gering | Panel-Komponenten in allen Zuständen, Quelle für einheitliche Marketing-Screenshots. Lohnt erst ab mehr Komponenten. |
| Excalidraw | [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | 3 | Web | gering | Handgezeichnete Erklärskizzen („Claude → MCP → Struktur“) für die README. |

Nicht aufgenommen: Hunyuan3D-2 (Lizenz schließt die EU aus), TRELLIS und WhisperX (CUDA), Wan/LTX direkt
(CUDA hartkodiert), Motion Canvas und Theatre.js (ruhen), Enve und DiffusionKit (archiviert), tldraw und GSAP
(keine OSS-Lizenz), Synfig und Kdenlive (arm64 nicht belegt).
