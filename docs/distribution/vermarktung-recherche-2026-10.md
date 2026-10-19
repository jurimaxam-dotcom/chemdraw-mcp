# Vermarktung: Recherche 19.10.2026

Zwei Recherche-Agenten (Opus), nur gelesen. Rohdaten des Teardowns lagen im Session-Scratchpad.

## Teil 1 – Wie erfolgreiche Repos ihre GitHub-Seite bauen

# Teardown: GitHub-Landingpages erfolgreicher Repos → Checkliste für chemdraw-mcp

Stand 19.10.2026. Erhoben per `gh api graphql` (Sterne, Topics, Homepage, `usesCustomOpenGraphImage`, Releases/Assets), `gh api repos/X/community/profile`, `gh api repos/X/contents/.github/ISSUE_TEMPLATE`, `gh api repos/X/readme` (erste 30 Zeilen per grep ausgewertet) und HN-Algolia. Rohdaten: `scratchpad/td/`.

## 1. Messdaten (13 Vergleichsrepos + chemdraw-mcp)

| Repo | ⭐ | angelegt | Hero in Z. 1–30 | Install-Weg | Topics | Homepage | Social Preview | Releases (Assets) |
|---|---|---|---|---|---|---|---|---|
| [upstash/context7](https://github.com/upstash/context7) | 63 295 | 03/2025 | Cover-Bild, Cursor-Install-Button, 34 Badges, „❌ Without / ✅ With" | Cursor-Deeplink, npx | 4 | context7.com | nein | 158 |
| [pocketbase/pocketbase](https://github.com/pocketbase/pocketbase) | 61 489 | 07/2022 | Logo, Einzeiler, 4 Bullets | Binary-Download | 4 | pocketbase.io | **ja** | 294 (8–10 Binaries) |
| [Textualize/rich](https://github.com/Textualize/rich) | 57 575 | 11/2019 | Badges, Logo, 10+ Übersetzungen, dann Screenshot | pip | 16 | readthedocs | **ja** | 177 |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | 46 908 | 02/2026 | 15 Badges, Zahlen-Claim („~120× fewer tokens") | Binary, curl | 20 | GitHub Pages | **ja** | 49 (49 Assets) |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 38 361 | 03/2025 | nur Text, „MCP vs CLI"-Abgrenzung | VS-Code-/Cursor-/Goose-Install-Buttons, npx | 2 | npm | nein | 73 |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | 33 756 | 03/2025 | Text, Use-Case-Liste | Install-Buttons (VS Code) | 3 | – | nein | 85 (9) |
| [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) | 28 135 | 11/2024 | Logo (dark/light), Slogan, Docs/Discord-Badges | pip/uv | 9 | gofastmcp.com | nein | 132 |
| [GLips/Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) (Solo) | 16 008 | 02/2025 | Header-Bild (dark/light), H1 + Nutzen-Satz, Downloads-/Discord-/Twitter-Badges | npx | 5 | framelink.ai | nein | 29 |
| [ankimcp/anki-mcp-server](https://github.com/ankimcp/anki-mcp-server) | 520 | 09/2025 | Logo-Bild, Nutzen-Satz, Tutorials-Abschnitt ab Z. 30 | **.mcpb** + npx | 6 | ankimcp.ai | nein | 57 (.mcpb: 441 / 496 / 186 Downloads) |
| [JimLiu/science-skills](https://github.com/JimLiu/science-skills) | 228 | 07/2026 | Text, Tabelle | – | 0 | – | nein | 0 |
| [ChatMol/molecule-mcp](https://github.com/ChatMol/molecule-mcp) | 97 | 03/2025 | 1 Screenshot, dann JSON-Config | manuelle JSON | 0 | – | nein | 0 |
| [OSU-NLP-Group/ChemMCP](https://github.com/OSU-NLP-Group/ChemMCP) | 73 | 04/2025 | kleines Logo, Verweis auf Website | manuell | 8 | GitHub Pages | nein | 1 |
| [tandemai-inc/rdkit-mcp-server](https://github.com/tandemai-inc/rdkit-mcp-server) | 42 | 04/2025 | nur Text + TOC | git clone | 7 | Firmenseite | nein | 0 |
| **[chemdraw-mcp](https://github.com/jurimaxam-dotcom/chemdraw-mcp)** | **21** | 06/2026 | 5 Badges, Text über **MVP-/Full-Profil**; Demo-GIF erst **Z. 51** | .mcpb, uvx, install.sh | 16 | **PyPI** | **nein** | 13 (.mcpb: 15 / 3 / 2) |

Weitere Messungen:
- **Contributing/Issue-Templates** (Community-Profil + `.github/ISSUE_TEMPLATE`): Großrepos haben CONTRIBUTING (playwright, github, fastmcp, rich, pocketbase, DeusData, GLips); die vier schwachen Chemie-Repos haben weder CONTRIBUTING noch Templates. chemdraw-mcp hat Issue-Forms (bug/feature/config), aber kein CONTRIBUTING (Health 42 %).
- **Star-History-Chart**: nur 1 von 13 ([GLips, README Z. 91](https://github.com/GLips/Figma-Context-MCP)). Kein Erfolgsmerkmal.
- **Vergleichstabelle/Abgrenzung**: als Tabelle nur DeusData; als Prosa-Abgrenzung oben: context7 („Without/With"), playwright („MCP vs CLI"), anki („Addon vs. dieses Repo").
- **GIF/Video in den ersten 30 Zeilen**: bei **0 von 13** gemessen. Es dominiert ein statisches Hero-Bild (context7, GLips, fastmcp, anki, rich, pocketbase = 6/13).
- **Viralität per Show HN**: PocketBase-Post 563 Punkte am 07.07.2022, zwei Tage nach Repo-Anlage ([HN 32013330](https://news.ycombinator.com/item?id=32013330)). Für rich, Figma-MCP und context7 fand die Algolia-Suche keinen großen Show-HN-Post → deren Reichweite kam aus anderen Kanälen (vermutet: X/Twitter, Cursor-Community, Firmenmarke).

## 2. Muster: was die Top-Repos haben, die schwachen nicht

**Gemessen:**
1. **Erster Bildschirm = Nutzen, nicht Interna.** Alle Top-Repos sagen in Z. 1–15, was man *bekommt* (context7: „Up-to-date Docs for AI Agents"; GLips: „Implement designs in any framework in one-shot"). chemdraw-mcp verbraucht Z. 15–50 auf Profil-Umschaltung und den Hinweis, dass PyPI/.mcpb noch altes Verhalten haben.
2. **Bild ganz oben.** 6/13 haben ein Hero-Bild vor dem ersten Abschnitt; alle 4 schwachen Chemie-Repos höchstens ein kleines Logo/Screenshot.
3. **Install in einem Klick oder einer Zeile.** Top-MCP-Repos: Install-Buttons (playwright, github, context7) oder `npx`. Die schwachen Chemie-Repos: manuelle JSON/git clone. ankimcp zeigt im Nachbarfeld, dass `.mcpb` im Release funktioniert: 441–496 Downloads pro Version gegen 15 bei chemdraw-mcp.
4. **Eigene Homepage/Doku statt Paketregistry** bei 9/13 (context7.com, pocketbase.io, gofastmcp.com, ankimcp.ai, framelink.ai …). chemdraw-mcp verlinkt PyPI.
5. **Regelmäßige Releases**: alle Repos ≥ 500 ⭐ haben ≥ 29 Releases; die vier schwachen 0–1. chemdraw-mcp (13) liegt hier schon gut.
6. **Topics ≠ Erfolg**: playwright 2, context7 4, github 3 Topics. chemdraw-mcp hat mit 16 bereits mehr als fast alle.

**Nicht verbreitet (also kein Muss):** Custom Social Preview (3/13), Star-History (1/13), Vergleichstabelle (1/13), GIF ganz oben (0/13).

**Vermutet (nicht gemessen):** Sterne folgen eher Absender und Kanal (Microsoft, GitHub, Upstash, Firmenmarke) als README-Details — das deckt sich mit der Memory-Messung vom 12.09.26 (PubChem-Cluster Median 0 ⭐). README-Arbeit erhöht die Umwandlung von Besuchern, bringt aber keine Besucher. Für Solo-Devs kam der Sprung bei PocketBase über Show HN.

## 3. Checkliste für chemdraw-mcp

**Jetzt (README-Oberkante, ~30 min):**
- [ ] Z. 15–50 (MVP-/Full-Profil, „Availability", „Switching profiles") aus dem Hero in einen Abschnitt weiter unten verschieben. Grund: 0/13 Vergleichsrepos zeigen Konfigurationsinterna oben.
- [ ] `assets/demo.gif` (heute Z. 51) oder ein statisches Hero-Bild (z. B. Koffein-Panel) direkt unter den Einzeiler setzen — vor jede Erklärung.
- [ ] Einzeiler + 3 Nutzen-Bullets (Name → Bild · offline RDKit · PNG/SVG für Protokoll/Folien) wie bei pocketbase.
- [ ] „Try it in 30 seconds" (heute Z. 53) als zweiten Block direkt nach dem Bild: großer Link „Download .mcpb → Doppelklick", darunter die `uvx`-Zeile.
- [ ] Eine Abgrenzungszeile nach context7-Vorbild: „Without: SMILES in ChemDraw abtippen · With: ‚Draw aspirin' im Chat". Optional eine Mini-Tabelle gegen [rdkit-mcp-server](https://github.com/tandemai-inc/rdkit-mcp-server)/[ChemMCP](https://github.com/OSU-NLP-Group/ChemMCP)/[molecule-mcp](https://github.com/ChatMol/molecule-mcp) (keins davon hat ein Panel oder `.mcpb`).

**Metadaten (5 min, in den Repo-Settings):**
- [ ] Homepage von PyPI auf eine eigene Seite umstellen (GitHub Pages oder der Release-Link), falls vorhanden; sonst auf `/releases/latest`.
- [ ] Social Preview setzen (1280×640, Koffein-Struktur + Einzeiler). Nicht verbreitet (3/13), aber billig, und jeder geteilte Link zeigt sonst das generische GitHub-Bild.
- [ ] Topics: Bestand (16) behalten; `claude-desktop`, `mcpb`, `mcp-apps` ergänzen (max. 20).

**Später:**
- [ ] CONTRIBUTING.md (Community-Health von 42 % hoch; haben 7/13).
- [ ] Release-Notes mit Bild/GIF der Neuerung — Releases sind schon da, Downloads 15 → Ziel: Release-Link ganz oben im README.
- [ ] Reichweite statt README: Show HN / r/chemistry / Claude-Discord-Post (Jays Hand, Außenkommunikation).
- Nicht nötig: Star-History-Chart, Badge-Wand, Übersetzungen.

## Teil 2 – Was Aufmerksamkeit bringt (Evidenz)

# Aufmerksamkeit für chemdraw-mcp: was belegt ist

Stand 19.10.2026. Nur gelesen, nichts gepostet. Kennzeichnung: **[B]** belegt (Studie), **[F]** Fallbericht, **[V]** Vermutung/Ableitung.

## 1. Forschung

| Befund | Quelle | Zahl |
|---|---|---|
| Sterne beeinflussen die Wahl | Borges & Valente 2018, *JSS* 146 | Umfrage mit 791 Entwicklern: 3 von 4 schauen vor Nutzung oder Mitarbeit auf die Sternzahl **[B]** |
| Wichtigste Werbekanäle populärer Repos | Borges & Valente 2019, *IEEE Computer* 52(8) | 100 Top-Projekte: Twitter, Nutzertreffen und Blogs am häufigsten; HN wichtiger Treiber. Bei erfolgreichen HN-Posts stieg der Median von 74 Sternen (3 Tage davor) auf 138 (3 Tage danach), mittlere Effektstärke **[B]** |
| HN wirkt kausal | Netsiwawichian, Mizuno et al., SNPD 2026 | Difference-in-Differences, 18.253 Repos: signifikant mehr Sterne und Forks; Effektgröße auf der Seite nicht angegeben **[B]** |
| HN-Launch-Größenordnung | Kraishan 2025, arXiv 2511.04453 | 138 KI-Tool-Launches: Mittelwert +121 Sterne nach 24 h, +289 nach 7 Tagen; der Median liegt „deutlich niedriger". Stärkster Prädiktor ist der **HN-Score**, danach die vorhandenen Sterne und die Uhrzeit (12–17 UTC am besten, rund +200 Sterne, unbereinigt). Das Präfix „Show HN" bringt bereinigt keinen Vorteil (−119, p = 0,39; Selektionseffekt durch Solo-Projekte) **[B]** |
| HN erhöht auch Forks und Mitwirkende | Meakpaiboonwattana et al. 2025, ICSME (arXiv 2506.12643) | 2.195 Stories, 1.814 Repos: signifikanter Anstieg **[B]** |
| Twitter wirkt | Fang, Lamba, Herbsleb, Vasilescu 2022, ICSE (Distinguished Paper) | 44.544 Tweets, 2.370 Repos, Kontrollgruppe: Tweets erhöhen Sterne „statistisch signifikant und praktisch relevant" (Pressezahl ca. +7 %), Mitwirkende nur ca. +2 %. Mehr Tweets bringen mehr Sterne **[B]** |
| README-Merkmale | Fan et al. 2021, *Empirical Software Engineering* 26(2) | 1.149 akademische KI-Repos: populäre und unpopuläre unterscheiden sich in 11 von 21 Merkmalen. Am stärksten trennen **Bilder im README**, Links auf andere Repos und eine Lizenz (Korrelation, nicht kausal) **[B]** |
| Gekaufte Sterne lohnen nicht | He, Vasilescu, Kästner et al. 2024/25, arXiv 2412.13459 | 4,5 Mio. Verdachtsfälle (bereinigt 3,1 Mio.); 15,8 % der Repos mit ≥ 50 Sternen hatten Kampagnen. Effekt: +0,08 % echte Sterne im Folgemonat, langfristig −0,05 %. Echte Sterne ziehen weitere nach (+0,36 % je 1 % im Vormonat) **[B]** |

Kernaussagen: Aufmerksamkeit entsteht in **Spitzen**, und eine Spitze erzeugt Folgesterne (Autoregression). Der HN-Score zählt, nicht das Präfix. Die Effekte gelten im Mittel; der Median ist klein.

## 2. Launch-Praxis

- **Show HN:** Regeln: Das Projekt muss sofort ausprobierbar sein, möglichst ohne Anmeldung. Wer um Upvotes bittet, verstößt gegen die Regeln **[B, Regelseite]**. Laut HN-FAQ ist ein Repost erlaubt, wenn der erste Post keine Beachtung fand. Das steht nicht auf der Show-HN-Seite und wurde nicht neu nachgelesen **[V]**. BookStack bekam durch einen Show HN (Jan. 2022) ca. 13.000 Besucher an einem Tag statt sonst ca. 700 und 736 Sterne in dem Monat statt bisher maximal 244 **[F]**. Für Jay: Der Juni-Post hat 1 Punkt; ein neuer Show HN mit GIF/Demo, ohne Installationshürde und um 12–17 UTC ist der direkte Folgeversuch.
- **Reddit:** r/chemistry (ca. 3,9 Mio. Mitglieder) verlangt seit März 2026 nach Regel 10 eine **Modmail vor jeder Werbung**; eigene Paper dürfen immer geteilt werden. Inoffizielle Schwelle: 100 Karma und 30 Tage Kontoalter **[B, Regeltext]**. Ein Chemiestudent kam dort im Februar 2026 mit „free client-side tools I built" auf 34 Punkte **[F]**. Bei r/ClaudeAI gilt Regel 7: selbst mit/für Claude gebaut, erklären, *wie* Claude geholfen hat, kostenlos testbar, wenig Werbesprache, über 100 Karma **[B]**. r/mcp (ca. 115.000 Mitglieder) erlaubt Eigenwerbung mit Offenlegung und dem Tag „showcase" **[B]**. Die Regeln von r/Chempros, r/OrganicChemistry und r/pharmacy wurden nicht geprüft (Reddit blockt den Abruf). Infisical: Reddit war Hauptkanal für 3.000 Sterne in 2 Monaten, ein Newsletter griff es am Folgetag auf (Mitgründer hatte über 2.000 Karma) **[F]**. Lago: 8 Wochen Social Sharing brachten nur ca. 300 Sterne, ein HN-Treffer ließ sich nicht wiederholen **[F]**.
- **GitHub Trending:** Es gibt keinen veröffentlichten Schwellenwert. Gezählt wird die Geschwindigkeit relativ zu anderen Repos (Sterne, Forks, Aufrufe, zeitgewichtet) **[V, Sekundärquellen]**. Für das Python-Ranking reicht vermutlich ein HN- oder Reddit-Tag mit dreistelligen Sternzahlen **[V]**.
- **X/Bluesky, LinkedIn, YouTube, Product Hunt, Dev.to:** Für Twitter ist der Effekt belegt (Fang 2022); Bluesky und #chemtwitter sind nicht untersucht **[V]**. Für YouTube, LinkedIn und Product Hunt wurde keine Studie zu Repo-Sternen gefunden. Product Hunt zielt auf Endkunden-SaaS, die eigene Zielgruppe ist dort klein **[V]**.

## 3. Fachspezifische Kanäle

- **JOSS:** Peer-Review-Paper mit DOI. Voraussetzungen: etwa 3 Monate Arbeit, eine „obvious research application" und OSI-Lizenz. Die neuen Kriterien (2026) fragen nach „research impact / scholarly significance", etwa ob andere Gruppen die Software nutzen **[B, JOSS-Doku]**. Für ein Werkzeug zum Zeichnen für Lehre und Folien ist die Annahme unsicher **[V]**.
- **Journal of Chemical Education:** Lehrwerkzeuge erscheinen dort; cDraw (2D-Editor, Griffith) ist ein Präzedenzfall **[F]**. Dieser Kanal trifft die Zielgruppe „Lehrende" am besten **[V]**.
- **Zenodo-DOI + CITATION.cff:** Kein Reichweiteneffekt belegt. Der Gewinn ist die Zitierbarkeit in Protokollen und Papern **[V]**.
- **ChemRxiv / J. Cheminform. Software Note / RDKit UGM:** Das sind die üblichen Wege in der Cheminformatik-Community. Borges & Valente nennen „Nutzertreffen" als häufigen Kanal **[B allgemein, V fachspezifisch]**. Das UGM verlangt einen Vortrag oder ein Poster, also Reise und Termin.
- **Anthropic:** Seit dem 25.09.2026 gibt es ein Einreichungsportal für Plugins und Connectors. Eigenständige MCPB-Einträge werden laut Sekundärquelle nicht mehr angenommen; ein lokaler Server muss in einem Plugin stecken **[V, vor Nutzung Primärdoku prüfen]**. Der Wettbewerb „Built with Claude" lief im August 2025 über die r/ClaudeAI-Flair **[F]**.

## 4. Priorisierte Hebel für chemdraw-mcp (Evidenz × Aufwand)

1. **README mit Bildern und GIF oben: Molekülname → Panel → PNG, plus Lizenz-Badge.** Aufwand ca. 1 h. Wirkung: höhere Umwandlung *aller* Besucher (Google und GitHub-Suche liefern schon Traffic). **[B: Fan 2021, Korrelation]**
2. **Show HN, zweiter Versuch:** Titel „Show HN: …" mit Funktion statt Produktname, 12–17 UTC Di–Do, kurzer Ersterklärungs-Kommentar, ein Weg ohne Installation (Demo-GIF, ideal ein Web-Preview). Wirkung im Mittel +100–300 Sterne, Median deutlich kleiner, abhängig vom Score. **[B: Kraishan 2025, Mizuno 2026, Borges 2019]**
3. **r/ClaudeAI (Flair Showcase) und r/mcp (Tag showcase):** Build-Log „wie Claude Code das gebaut hat". Die Regeln passen genau auf das Projekt. Hürde: über 100 Karma. **[B: Regeln; F: Infisical, Open Interface]**
4. **r/chemistry über Modmail-Freigabe, Ton „Student baut Werkzeug für Protokolle":** Zielgruppe direkt, aber Freigabe nötig. **[B: Regel 10; F: Post mit 34 Punkten]**
5. **Bluesky/X-Thread mit 3 Bildern, RDKit erwähnen** (das Projekt nutzt RDKit, die Community teilt Anwendungen gern). **[B: Fang 2022 für Twitter; V für Bluesky/#chemtwitter]**
6. **Plugin-Einreichung im neuen Anthropic-Portal** (lokaler Server als Plugin). Wirkung unbekannt, aber dauerhaft sichtbar dort, wo Desktop-Nutzer suchen. **[V; Verzeichnisse brachten bisher 0, das offizielle ist aber ein anderer Kanal]**
7. **Zenodo-DOI + CITATION.cff:** 15 Minuten, ermöglicht Zitate in Protokollen und Lehrmaterial. **[V]**
8. **Später: Technology Report in J. Chem. Educ. oder ein JOSS-Paper**, sobald Nutzung belegbar ist (Lehrende, Kurse). Hoher Aufwand, langfristige Glaubwürdigkeit. **[F: cDraw; B: JOSS-Kriterien]**

**Nicht tun:** Sterne kaufen oder Upvotes organisieren. Kurzfristig ist der Effekt nahe null, langfristig negativ, und auf HN/Reddit führt es zum Bann **[B: He 2024/25, Regelseiten]**.

## Quellen
- Borges & Valente 2018: https://arxiv.org/abs/1811.07643 · 2019: https://arxiv.org/abs/1908.04219
- Kraishan 2025: https://arxiv.org/abs/2511.04453 · Meakpaiboonwattana 2025: https://arxiv.org/abs/2506.12643 · Mizuno-Gruppe 2026: https://se.is.kit.ac.jp/pman4/en/detail/1044
- Fang et al. 2022: https://conf.researchr.org/details/icse-2022/icse-2022-papers/84/ · Fan et al. 2021: https://arxiv.org/abs/2010.02472 · He et al.: https://arxiv.org/abs/2412.13459
- Show HN: https://news.ycombinator.com/showhn.html · BookStack: https://www.bookstackapp.com/blog/9000-stars-and-the-effects-of-hacker-news/ · Infisical: https://infisical.com/blog/how-we-got-3000-github-stars-in-2-months · Lago: https://getlago.com/blog/how-we-got-our-first-1000-github-stars
- r/chemistry Regel 10: https://www.reddit.com/r/chemistry/comments/1s8p705/ · r/ClaudeAI/r/mcp Regeln: https://threadfox.vip/rules/claudeai, https://reddifier.com/free-subreddit-analysis-tool/r/mcp
- JOSS: https://joss.readthedocs.io/en/latest/submitting.html · Anthropic MCPB: https://claude.com/docs/connectors/building/mcpb
