# Messung: schmale vs. breite Chemie-MCP-Server (12.09.2026)

Erhoben von einem Scout-Lauf gegen die GitHub-Suche und die MCP-Registry.
Anlass war Jays Vermutung, praezise zugeschnittene Tools bekaemen auf GitHub
mehr Aufmerksamkeit als breite Werkzeugkaesten. Kurzfassung des Verdikts:
**nein — Breite korreliert in dieser Stichprobe eher positiv mit Sternen,**
**und der sichtbare Hebel ist der Absender (Organisation, Paper, Awesome-Liste),**
**nicht der Zuschnitt.** Der PubChem-Cluster ist der sauberste Test: zwoelf
Repos, die exakt eine Datenbank bedienen, Median 0 Sterne.

```
MESSUNG 2026-09-12 — Schmale vs. breite Chemie-MCP-Server auf GitHub
Methode Toolzahl: grep '^\s*@[A-Za-z_.]*tool\b' (py) / README-Zaehlung (R) / Serverordner (S)
Kalibriert an chemdraw-mcp: 22 Dekoratoren, 2 bedingt (Vault aus) = 20 aktive = Handshake-Assertion.

Repo | ⭐ | 1. Commit | Alter Mo | ⭐/Mo | Tools | Org | Paper | Awesome
patsnap/mcp | 111 | 2026-04-14 | 4.9 | 22.6 | ~30 Server (S) | ja | ja | nein
ChatMol/molecule-mcp | 96 | 2025-03-19 | 17.8 | 5.4 | 29 | ja | nein | nein
OSU-NLP-Group/ChemMCP | 71 | 2025-04-24 | 16.6 | 4.3 | 32 | ja | ja | nein
tandemai-inc/rdkit-mcp-server | 42 | 2025-04-30 | 16.4 | 2.6 | ~75 | ja | nein | nein
longevity-genie/gget-mcp | 31 | 2025-06-06 | 15.2 | 2.0 | 25 | ja | nein | JA
ToxMCP/toxmcp | 27 | 2026-02-11 | 7.0 | 3.9 | 0 Code (Hub) | ja | ja(bioRxiv) | nein
globus-labs/science-mcps | 14 | 2025-06-03 | 15.3 | 0.9 | 40 / 5 Server | ja | nein | nein
[REF] jurimaxam-dotcom/chemdraw-mcp | 13 | 2026-06-10 | 3.1 | 4.2 | 20 | nein | nein | nein
qgeng1465/bio-mcp | 11 | 2026-08-11 | 1.0 | 11.0 | ~83 / 43 DBs | nein | ja | nein
sssjiang/pubchem_mcp_server | 11 | 2025-03-26 | 17.6 | 0.6 | 3 | nein | nein | nein
cyanheads/pubchem-mcp-server | 9 | 2025-06-29 | 14.5 | 0.6 | 10 (R) | nein | nein | nein
echelonts/flavormancer | 8 | 2026-06-24 | 2.6 | 3.1 | 18 | ja | nein | nein
ZiChenWang114514/chemdraw-skill | 8 | 2026-07-14 | 2.0 | 4.0 | 7 | nein | nein | nein
sinagilassi/mozichem-hub | 6 | 2025-06-16 | 15.0 | 0.4 | Framework | nein | nein | nein
leehiufung911/cdxml-toolkit | 6 | 2026-03-03 | 6.3 | 1.0 | 15 | nein | nein | nein
PabloPauling/posebusters-mcp-server | 5 | 2025-07-12 | 14.0 | 0.36 | 1 | nein | ja | nein
gvmfhy/smiles2iupac | 2 | 2026-05-02 | 4.3 | 0.46 | 4 | nein | nein | nein
leelasd/molecule_mcp | 2 | 2025-04-24 | 16.6 | 0.12 | 4 | nein | nein | nein
cyanheads/chembl-mcp-server | 1 | 2026-06-23 | 2.7 | 0.37 | 8 (R) | nein | nein | nein
oliverkraft93-ops/covasyn-mcp-examples | 0 | 2026-05-07 | 4.2 | 0 | 130+ (Registry) | nein | nein | nein

AUSGESCHLOSSEN: sebotic/cdk_pywrapper (2016, Pre-MCP-Sterne), epam/ketcher, awesome-Listen,
EnterOS-AI/* (Spiegel), wen2zhou/openscience-mcp (Marktplatz).

PUBCHEM-CLUSTER (12 Repos, alle schmal = eine Datenbank):
11, 9, 7, 2, 1, 0, 0, 0, 0, 0, 0, 0  -> 10 von 12 bei <=2 Sterne. Median 0.
PAAR-KONTROLLE cyanheads: pubchem (2025-06, 9⭐) vs chembl (2026-06, 1⭐) — gleicher Autor,
gleiche Form, 12 Monate spaeter = 9x weniger. Alterseffekt, nicht Breiteneffekt.

TOP-5 nach Sternen: 5/5 Organisation, 3/5 Paper/Preprint, Tools 25/29/32/~75/~30-Server.
SCHMALSTE 3 (1, 4, 4 Tools): 5, 2, 2 Sterne.

CONFOUND 3 — echte ChemDraw-App-Steuerung:
AppleScript ('tell application "ChemDraw"', gh search code): NUR Jays eigene Repos
(chemdraw-mcp/tests, chemdraw-companion, Chem-draw-addon) + metamolecular/chembot
(5⭐, letzter Push 2011-07-18, tot, .scpt).
Windows-COM ('ChemDraw.Application' + win32com) — die lebende Nische:
  leehiufung911/cdxml-toolkit 6⭐ (2026-03, 15 Tools, MIT)
  ZiChenWang114514/chemdraw-skill 8⭐ (2026-07, 7 Tools, MIT, 4.0 ⭐/Mo)
  ZiChenWang114514/cdxml-toolkit-community 1⭐ (2026-08, 15 @mcp.tool, MIT)
Keines davon steuert ChemDraw auf macOS.

TRAFFIC jurimaxam-dotcom/chemdraw-mcp (14 Tage):
Views 123 / 58 uniq. Pfade: 93/57 uniq auf "/" — 57 von 58 uniques sehen nur die Landing.
Tree/chemdraw_tool: 5 uniq. LICENSE: 1. README-Blobs: 1.
Referrer: Google 38/23, github.com 31/12, chatgpt.com 7/3, Bing 4/2, yandex 1/1.
Clones 223/75 — Achtung: 12 Actions-Laeufe in 14 Tagen zaehlen als Clones, Zahl unbrauchbar.
Release-Assets: v0.4.x zusammen 3 Downloads.

REGISTRY: registry.modelcontextprotocol.io HTTP 200, Suche "chem" matcht auch "schema"
(unbrauchbar als Zaehlung). Einziger echter Chemie-Treffer: com.covasyn/chemistry
"130+ tools across 17 suites" -> GitHub covasyn-mcp-examples 0⭐.

VERDIKT: unentscheidbar, tendiert zu NEIN. Breite korreliert in dieser Stichprobe
POSITIV mit Sternen, aber 5/5 Top-Repos tragen Organisations-/Paper-Flag.
Staerkster sichtbarer Hebel: Absender-Reputation + Alter, nicht Toolzahl.
Zweitstaerkster: Jays Name/Produkt-Luecke (macOS-ChemDraw-Steuerung existiert NIRGENDS).

NACHTRAG (Advisor-Korrekturen):
- PyPI chemdraw-mcp: last_day 25, last_week 56, last_month 321 (pypistats /recent).
  Gegen 123 Views / 58 uniq in 14 Tagen (~260 Views/Monat) => Downloads ~1.2x Views.
  Gleiche Groessenordnung, nicht dominierend. Abspring-These weder belegt noch widerlegt.
- Landing-Page-Anteil ist KEIN Bounce-Beleg (gilt fuer jedes Repo) — gestrichen.
- Windows-COM-Nische ist EINE Linie: leehiufung911/cdxml-toolkit und
  ZiChenWang114514/cdxml-toolkit-community haben identischen Root-Commit
  2363e7f28bd052a805134dd54eff1393e76669c0 (104 bzw. 122 Commits).
  Summe der Linie: 6+1 = 7⭐, plus chemdraw-skill 8⭐ (gleicher Autor wie community).
- chemdraw-skill (echte ChemDraw-Steuerung) 4.0 ⭐/Mo vs chemdraw-mcp 4.2 ⭐/Mo — kein Nachteil.
- Referrer: Google 23 von 58 uniques = 40%, nicht "fast nur Google".
- OHNE-ORG-TEILGRUPPE (Sterne / Tools): chemdraw-mcp 13/20, bio-mcp 11/83, sssjiang 11/3,
  cyanheads-pubchem 9/10, chemdraw-skill 8/7, cdxml-toolkit 6/15, posebusters 5/1,
  smiles2iupac 2/4, molecule_mcp 2/4, chembl 1/8, covasyn 0/130+.
  => chemdraw-mcp ist das sternstaerkste unbeworbene Chemie-MCP-Repo im Pool.
```
