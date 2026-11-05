# MCP-Server: Panel, Werkzeuge, Releases

## Weiter bei — 0.8.0 veröffentlicht, Etappe F abgenommen (Claude-Hauptsession, 05.11.2026 17:05)

**Release 0.8.0 ist draußen (Jay 05.11. 16:15: „du darfst es machen“ — einmalige Freigabe für diesen Klick, keine Dauererlaubnis):**
`gh release create v0.8.0 --target 566a060…` → https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/tag/v0.8.0, Tag zeigt auf
`566a060309e61000f4805b508cf882aa09b559a1`. Workflow `publish.yml` Lauf 42053659782: Freigabe `pypi` per `pending_deployments`
(Environment 25767991480), Ergebnis build/publish/bundle/registry je `success`. Belege: PyPI-Index führt `chemdraw_mcp-0.8.0`
(whl sha256 `0506d628…`, sdist `95c05d4b…`), Release-Asset `chemdraw-mcp-0.8.0.mcpb`, MCP-Registry `isLatest` = 0.8.0.
Der frühere Befehl von Jays Hand war nicht gelaufen (weder Tag noch Draft vorhanden, 16:10 geprüft).

**Etappe F gestartet:** Tisch-Faden `20261105-162003-etappe-f-marketing-repo` (Claude-Session `edf9eeb9`, herdr `w4W:p4`, Split down),
Auftrag mit Vorab-Befund (**Korrektur 05.11.: `plans/vermarktung.md` war versioniert**, 24 Commits — nur `vermarktung/` und `docs/distribution/` waren unversioniert): `vermarktung/`, `plans/vermarktung.md`, `docs/distribution/` sind **unversioniert** (`.git/info/exclude`
seit 21.10.) → Kopie, kein `subtree split`; Historie hat nur Branch `worktree-agent-a89d4c26da6a9d6c2` (`chemdraw_tool/ui/video/`,
`scripts/demo-short.sh`). `vermarktung/out` 1,3 GB + `video/node_modules` bleiben draußen; `vermarktung/traffic` ist Symlink nach
`~/.local/share/chemdraw-mcp/traffic`. `ax-claude.swift`/`aufnahme-desktop.sh` gehören Codex → Abstimmung per Tisch im Auftrag.
**F abgenommen 17:05** (Faden geschlossen, Bericht #2 unabhängig geprüft: Repo PRIVATE, 62 getrackte Dateien ohne Videos/`out/`/`node_modules`,
Reste in chemdraw-mcp weg, `scripts/ax-claude.sh preflight` → `screen=1 ax=1`, `gate-f.log` grün; Haken mit Belegen unten bei „Etappe F erledigt“).

**Dependabot (17:12):** PR #8 (setup-uv 10.3.2→10.3.3, Checks grün) — Merge ist Jays Klick: `gh pr merge 8 --squash --delete-branch`
(Claude-Merge vom Auto-Modus verweigert). PR #7 (6 Python-Bumps, u. a. Playwright 1.60→1.64.1, CI rot) läuft in eigener Session,
Faden `20261105-163128-dependabot-pr-7-nach` (Session `8b06750a`); Bericht bringt die Merge-Zeile.
**PR #7 grün (05.11., 98e4342 auf dem PR-Branch):** Rot war `tests/test_render_golden.py:75` (Aspirin-Goldens), Ursache
rdkit 2026.9.1 — `Compute2DCoords` spiegelt Aspirin/Glucose, dreht Ibuprofen/Benzol (Gegenprobe: nur rdkit zurück → grün).
Fix: `rdkit<2026.9` in `pyproject.toml` (gilt auch für PyPI), Playwright npm-seitig auf 1.64.1 nachgezogen (Pixel-Snapshot hält,
Chromium 1248). Gate rc=0 (7542 passed), CI py3.11/py3.13 grün, Befund im PR-Kommentar. Merge = Jays Klick:
`gh pr merge 7 --squash --delete-branch`. Pin ist Zwischenstand, keine Lösung (kehrt bei jedem rdkit-Release wieder).
**Befund (Advisor + Messung 05.11.):** der Golden-Test misst Renderer UND RDKit-Layout zugleich. Mit eingefrorenen Aspirin-
Koordinaten rendert rdkit 2026.9.1 beide Goldens **byte-gleich** (Skript `scratchpad/frozen2.py`, Kontrolle unter 2026.3.6 ebenfalls
gleich; Molblock-Umweg verfälscht schon allein, daher Koordinaten direkt setzen). **Jay:** A) Test entkoppeln (Koordinaten als
committete Fixture, optional Layout-Wächter über paarweise Atomabstände, spiegelungsinvariant) + Pin weg + rdkit 2026.9 ·
B) Goldens jetzt neu, Pin weg · C) Pin behalten. **Entschieden: A** (Jay delegierte an den Advisor, 05.11.).
- [x] Schritt 1 auf main: `tests/__fixtures__/aspirin.coords.json` (aus rdkit 2026.3.6, Goldens unverändert), Golden-Test setzt
  die Koordinaten; Beleg: unter 2026.9.1 `4 passed`, eine Koordinate +0,3 → `2 failed`. `tests/test_dependency_pins.py` prüft
  Playwright pyproject ↔ package.json; Beleg: Mutation package.json 1.64.1 → `1 failed` „Playwright-Drift“. CLAUDE.md angepasst.
- [x] Layout-Wächter `tests/test_layout_guard.py` (Hinweis Nebenagent: ohne ihn rutscht ein gedrehtes/gespiegeltes Nutzerbild
  durch): 7 Proben, direkter Koordinatenvergleich (Spiegelung zählt), Bless `UPDATE_LAYOUT=1`. Beleg: ohne Referenz `8 failed`,
  unter rdkit 2026.9.1 genau aspirin/benzene/glucose/ibuprofen rot (`4 failed, 4 passed`), unter Lock `8 passed`.
- [ ] Schritt 2 (wartet auf Jays Merge von #7): `rdkit<2026.9` → `"rdkit"`, `uv lock`, Wächter rot → Vorher/Nachher-Bild der
  vier Proben ansehen, `UPDATE_LAYOUT=1` im selben Commit, Gate unter 2026.9.1, Kommentar im pyproject weg.
**Dependabot abgenommen (17:40, Hauptsession, Faden geschlossen):** PR #7 grün (py3.11/py3.13), Ursache des Rots war rdkit 2026.9.1
(Compute2DCoords spiegelt Aspirin/Glucose → Golden-SVGs rot), nicht Playwright; Fix `98e4342` auf dem PR-Branch: `rdkit<2026.9` mit
Begründung im pyproject, Playwright beidseitig 1.64.1, Goldens/Snapshots unverändert (Branch-Diff geprüft).
**Jay:** `gh pr merge 8 --squash --delete-branch && gh pr merge 7 --squash --delete-branch` · **Jay (später, nicht blockierend):**
rdkit-Pin behalten (Empfehlung: ja — Default-Rendering darf sich nicht still ändern) oder bei nächstem bewussten RDKit-Bump Goldens
mit Sichtprüfung neu und Pin weg?
**Nächster Schritt:** nach Jays Merges `git pull`, Gate einmal auf main · dann als eigene Etappe · Masse-Eval-Befunde (Abschnitt „Release-Klick 0.8.0“ unten)
· Geparkt: E2 Lehrbuch-Feinschliff (GELB-Liste im Abschnitt darunter).
**Fragen an Jay (unbeantwortet — nicht bauen):** Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

## Weiter bei — Release-Klick 0.8.0 (Jays Hand), Etappe E abgenommen (Claude-Hauptsession, 05.11.2026 16:25)

**Etappe E ist abgenommen — Beweiskette statt Jays Auge** (Jay 05.11.: „ich bin nicht vom Fach“): (1) `tests/test_mechanism_bookkeeping.py`
+ `tests/test_mechanism_lehrbuch.py` im Gate (`e744e73`); (2) blinder Opus-Gutachter Lauf 1 auf k2 → 4× ROT (R1–R4, Abschnitt darunter),
Runde 3 behoben (`8075634`…`dfe0cef`); Lauf 2 auf k3 → 32/33 grün oder gelb, 1× ROT (SN1 Allylkation ohne Resonanz/zweites Produkt)
→ SN1 lehnt allylische Halogenide jetzt mit Grund ab (`566a060`, Snapshot/README/CHANGELOG mit); (3) Codex-Desktop-Handtest Runde 3
grün (`056cb2a`: SN1 6 Schritte mit Oxonium + H⁺, SN2-ÜZ δ⁻, Screenshots `/tmp/chemdraw-desktop-test/etappe-e-r3/`); (4) Gate selbst:
rc=0, 7988 Tests (`scratchpad/gate-final.log`), Handshake 16/12 grün. **Die frühere „Abnahme 15:55 per Advisor-Sichtung“ (d9e7507)
ist damit überholt — sie hatte die vier systematischen Fehler nicht gesehen.**

**Nächster Schritt = Jay: Release-Klick 0.8.0, Ziel-SHA `566a060309e61000f4805b508cf882aa09b559a1`** (Spitze von main nach `566a060`):
```
gh release create v0.8.0 --target 566a060309e61000f4805b508cf882aa09b559a1 --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)
gh run list --workflow publish.yml --limit 1
gh api -X POST repos/jurimaxam-dotcom/chemdraw-mcp/actions/runs/<run-id>/pending_deployments -F 'environment_ids[]=25767991480' -f state=approved -f comment="0.8.0"
```
Jobs `bundle` und `registry` laufen im Workflow mit (Fallback `./scripts/publish-registry.sh`).

**Geparkt (GELB des Gutachters, nach dem Release, eigene Etappe „E2 Lehrbuch-Feinschliff“):** SN2-Pfeile an die Edukte statt in den ÜZ
(Clayden-Konvention) · Carbokation trigonal-planar (120°) statt T-förmig · E1/E2-Konkurrenzhinweis im Text (Isopropyliodid + OH⁻,
tBuI + iPrOH) · Deprotonierung über Lösungsmittel statt freies H⁺ · Fischer-Protonentransfer zweistufig · ⇌ bei Fischer · lange Ketten
(Stearin, Octan) abkürzen (R = C₁₇H₃₅) · Oxonium-Label „OH⁺ + H“ einheitlicher. Fachlich korrekt, nur Konvention/Lesbarkeit.

**Danach:** Etappe F Marketing-Repo (eigene Session) · Dependabot-Branches · Masse-Eval-Befunde (Abschnitt „Release-Klick 0.8.0“ unten).
**Fragen an Jay (unbeantwortet — nicht bauen):** Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

## Weiter bei — Etappe E Runde 3: Befunde der unabhängigen Sichtung (Claude-Hauptsession, 05.11.2026 15:40)

**Jay (05.11., zu den Kontaktbögen Runde 2):** „ich kann nicht verifizieren was richtig und falsch ist, da ich nicht vom Fach bin —
wie kompensieren wir das, dass wir mit Sicherheit sagen können, ob es stimmt?“ → **Jays Auge wird ersetzt, nicht übersprungen:**
1. **Maschinell:** `tests/test_mechanism_bookkeeping.py` (`e744e73`) — jeder gebogene Pfeil muss genau die Bindungs-/H-Änderung zum
   nächsten Schritt beschreiben, jede Änderung braucht ihren Pfeil; über die ganze Matrix, netzfrei an den gemappten SMILES.
   Benannte Ausnahmen im Docstring. Dazu `tests/test_mechanism_lehrbuch.py`: Ergebnis aus OpenStax 11.2/11.4 statt eigener Ableitung.
2. **Unabhängige Sichtung** (Opus-Gutachter, blind, ohne unsere Einschätzung, Kriterien aus Design-Notiz (g)) — Ergebnis Runde 2:
   Fischer GELB (nur Kosmetik), **SN2 und SN1 ROT mit je einem systematischen Fehler**:
   - **R2 SN2-ÜZ:** Nucleophil und Abgangsgruppe tragen volle Ladungen („N≡C⁻ ··· C ··· Br⁻“) → Gesamtladung −2 statt −1.
     Richtig: δ⁻ an beiden (oder ⁻ außen an der Klammer). Bestätigt am Bild.
   - **R4 SN1 mit H₂O/ROH:** Oxonium-Zwischenstufe (R–OH₂⁺ / R–O⁺(H)R′) und Deprotonierungspfeil fehlen; Produktzeile ROH + X⁻
     ohne H⁺ (Ladung 0 → −1). Bestätigt am Bild. Richtig: Schritt „Oxonium ion“ mit Pfeil O–H-Bindung → O, Produkte ROH + X⁻ + H⁺.
   - **R1 Azid:** Ladung am endständigen N liegt im SVG unter der Doppelbindungslinie (`sn2-1-chlorbutan-azid-0.svg` atom-7) → Leser
     sieht N=N⁺=N⁻ statt ⁻N=N⁺=N⁻. Renderfehler, Daten richtig.
   - **R3 Matrixfall sn1-tbubr-cyanid-salz:** tertiäres Halogenid + Cyanid ist kein Lehrbuch-SN1 (E2 überwiegt; am Kation Isonitril,
     Kornblum). Fall aus der Matrix nehmen (Ersatz: tBuCl + Azid, Azid-Abfang klassisch).
   - GELB, billig: Pfeilschwanz bei „HO“-Label (SN1 + Methanol, Schritt 4) sitzt am H statt am O · „C⁺“/„C“ am Zentrum ohne H
     (Ameisensäure, 1-Phenylethyl) · ⇌ fehlt (nur im Text, bewusst) · Kontaktbogen-Font ohne ⁺ (nur Skript, Arial → andere Font).
   Stereochemie durchweg richtig (Inversion, CIP, racemic — vom Gutachter nachgerechnet).

**Nächster Schritt:** Runde 3 durch einen frischen Opus-Arbeiter (Brief in der Hauptsession, 15:45): R1–R4 + billige GELB-Punkte,
`scripts/kontaktbogen.py` ins Repo (aus dem E-Scratch `kontakt.py`), Golden-SVGs bewusst neu und gesichtet, Gate rc=0 in Datei,
Kontaktbögen k3. Danach **derselbe Gutachter-Lauf noch einmal, blind** — erst wenn er keine ROT-Zeile mehr meldet, ist E abgenommen;
Jay bekommt Gutachten + Bögen zur Kenntnis, nicht zur Fachprüfung. Dann Handtest-Bericht `998386d` gegen den neuen Stand (Codex:
SN1-Schrittzahl ändert sich → ein kurzer Nachtest der SN1-Umschaltung), E abhaken, Release-Zeile 0.8.0 (Abschnitt darunter).

## Weiter bei — Jays Sichtung der E-Kontaktbögen, dann Release-Zeile 0.8.0 (Claude-Hauptsession, 05.11.2026 15:00, vor Kontext-Neustart)

**Nächster Schritt:** Jays Antwort auf die drei Kontaktbögen Runde 2 (SN2/SN1/Fischer, gesendet 05.11. ~14:55 per SendUserFile aus
`/private/tmp/claude-501/-Users-tom-Documents-projects-chemdraw-mcp/37e52ebd-cd21-4f12-abe6-e4c5741264e3/scratchpad/k2/`) abwarten.
**„passt“ zu den Bögen: unbeantwortet — nicht bauen.** Sagt Jay „passt“: Handtest-Bericht von Codex (`998386d`,
`docs/desktop-abnahme-etappe-e-2026-11-05.md`) gegen die E-Abnahmebedingung prüfen (Gate selbst laufen lassen, rc in Datei, nicht
nur Arbeiter-Angabe), E abhaken, dann Release-Zeile an Jay mit der dann aktuellen vollen SHA von main:
`gh release create v0.8.0 --target <SHA> --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)`,
danach `gh run list --workflow publish.yml --limit 1`, Freigabe `gh api -X POST repos/jurimaxam-dotcom/chemdraw-mcp/actions/runs/<run-id>/pending_deployments
-F 'environment_ids[]=25767991480' -f state=approved -f comment="0.8.0"`; Jobs `bundle` und `registry` laufen im Workflow mit
(Fallback `./scripts/publish-registry.sh`). Nennt Jay einen Fall als falsch: E-Session (Faden unten) oder neuer Opus-Arbeiter, Runde 3.

**Heute erledigt (geprüft):** Etappe A abgenommen (Lauf 1 `f402b94`, Lauf 2 `c776d83`, CHANGELOG-Zahl `37375a3`) · Branches:
mechanismus-substrate, mcp-2-migration(-v2) gelöscht, Tags `archiv/mcp-2-migration` und `archiv/demo-shorts` auf origin (Jay 05.11.) ·
Etappe E Runde 1+2 durch die E-Session (`522a8c4`…`59eee39`), Codex-Handtest grün mit zwei benannten Grenzen (SN1-Prompt ohne
Tool-Nennung = Desktop-Routing; Schrittumschaltung Ringfall nicht bestätigt).

**Danach:** Etappe F eigenes Marketing-Repo (Abschnitt unten, Jay 05.11.) in eigener Session, erst nach dem Release, weil Codex
`vermarktung/ax-claude.swift` für Handtests braucht · Dependabot-Branches als eigene Etappe · Befunde aus der Masse-Eval (Abschnitt
„Release-Klick 0.8.0“ unten, Punkte 1–5).

**Fragen an Jay (unbeantwortet — nicht bauen):** „passt“ zu den E-Kontaktbögen · Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

**Offene Tisch-Fäden:** `20261105-131815-etappe-e-mechanismen-vor` (E-Session `w4W:p4`, Hop 6/6 voll; Bericht der E-Session steht noch
aus) · `20261105-142437-etappe-e-desktop-handtest` von Codex geschlossen. Nebenbefund: Prozess 65536 ist ein liegengebliebener
Wächter einer alten Session (Kill verweigert, `kill 65536` durch Jay).

## Weiter bei — Codex nach E-Handtest und Kontext-Neustart (05.11.2026)

**Nächster Schritt:** neue Tisch-Nachrichten am Projektort lesen. Der eigene
E-Handtest ist vollständig erledigt (`998386d`); keine Wiederholung und keine
Produktfixes ohne neuen Auftrag. Claudes Abnahme des Berichts und Jays „passt“
zur Gestaltung stehen noch aus. Release 0.8.0 bleibt bis zur E-Abnahme gesperrt
und der Release-Klick bleibt Jays Hand.

**Dateien/Beweise:** `docs/desktop-abnahme-etappe-e-2026-11-05.md`, Abschnitte
„Fall 1“ bis „Fall 6“ sowie „Ergebnis und Rücksetzen“; Screenshots und AX-Texte
unter `/tmp/chemdraw-desktop-test/etappe-e/`. Getesteter Produktstand `59eee39`,
Desktop-Neustart auf `f2c7729` (nur Plan-Nachtrag). SN2-Stereolabel, Klammern/‡,
freie Pfeile, Namenstitel auch bei SMILES, sieben Fischer-Schritte einschließlich
Protontransfer/OH₂⁺ und Diels-Alder-Familienhinweis sichtbar geprüft. SN1-Panel
nach beauftragtem Zusatz grün; Originalprompt ohne Tool. Ring in der sichtbaren
Übersicht regelmäßig ohne C-Labels; Schrittumschaltung dieses Falls wegen
AX-/Screenshot-Widerspruch **nicht** abgenommen. Kein Produktcode geändert.

**Offene Tisch-Fäden:** ursprünglicher Auftrag
`20261105-131815-etappe-e-mechanismen-vor` #6 (Hop 6/6, voll); Fortsetzung
`20261105-142437-etappe-e-desktop-handtest` #2 Bericht an Claude `w4W:p4`,
#3 Status zum Neustart. Nach Antwort dort weiterlesen; aktuell keine ungelesene
Nachricht. Keine eigene zeitgebundene Wartefrist, kein Hintergrundjob und kein
halber Edit. Reservierungen nach dem Plan-Commit freigeben.

**Offene Fragen an Jay:** „Welle 3 eigenes Profil?“ und „Abfragemodus auch für
Reaktionen?“ — **unbeantwortet — nicht bauen**. Jays „passt“ zu den
E-Kontaktbögen: **unbeantwortet — nicht bauen**; keine Zustimmung unterstellen.

**Zugesagte Prüfmethoden:** sichtbarer Desktop mit frischen Chats, tatsächlichen
Toolparametern, Screenshots und AX-Belegen; Routing-Stichprobe vom Paneltest
trennen. Gate/Handshake-Zahlen aus dem Auftrag nicht als selbst geprüft ausgeben.
Desktop abschließend neu gestartet, leerer Chat bestätigt (`final-state.txt/png`),
Repo-Prozesse aktiv, Bundle deaktiviert; Konfiguration und Bundle-Einstellung
bytegleich zum Start (`identity-after.json`). Dokuprüfung vor Commit grün,
keine offene Freigabe im frischen Fenster.

## Weiter bei — Etappe E: Mechanismen sauber vor dem Release (Jay 05.11.2026, Claude-Folgesession per Auftrag)

**Jay (05.11.):** „Das macht viel mehr Sinn, das vor dem Release sauber zu machen. Lehrbuchabbildungen als Orientierung für
die Positionierung der Pfeile usw., eine klare Abnahmebedingung, und so lange mit verschiedenen Reaktionen iterieren, bis es
immer sauber dargestellt wird.“ → **Release 0.8.0 wartet, bis E abgenommen ist.** Release-Zeile unverändert (Abschnitt darunter),
nur die Ziel-SHA wird die neue Spitze von main.

**Bekannte Befunde (alle vier gehören in E):**
1. Panel: SN2-Produkt ohne (S)-Label, obwohl die Inversion in der Struktur steckt (`docs/desktop-abnahme-mechanismus-2026-11-05.md`).
2. Fischer: gebogener Pfeil liegt knapp über dem HO-Label.
3. „Mechanismus der Diels-Alder-Reaktion“ läuft in `generate_reaction` ohne Hinweis auf die drei Familien (Fence in beide Richtungen + Eval-Fall).
4. Titel bei SMILES-Eingabe verliert Name und Stereodeskriptor: „C₄H₉Br + CN⁻“ statt „(R)-2-bromobutane + cyanide“ (Jay 05.11.,
   Desktop-Beobachtung; Summenformel unterscheidet nicht einmal die Konstitution). Fix: Name per PubChem-Lookup + CIP aus RDKit
   (`FindMolChiralCenters`), ohne Netz kanonischer SMILES mit Stereo — nie nur die Summenformel.

**Abnahmebedingung (prüfbar, erst rot sehen, dann grün):**
- **Lehrbuch-Referenz:** Abbildungen zu SN1, SN2 und Fischer aus Jays Vorlesungsfolien/Lehrbuch per pymupdf als Originalbild
  ziehen (nie nachzeichnen; `~/.claude/docs/dokumente-und-grafiken.md`), Quelle als Bildunterschrift; daraus die Konventionen in
  `docs/mechanismus-substrate-design.md` festschreiben (Pfeil startet am freien Elektronenpaar bzw. an der Bindungsmitte, endet am
  Zielatom/der neuen Bindung; Abgangsgruppe geht vom Zentrum weg; Übergangszustand in eckigen Klammern mit ‡; Produkt trägt den
  CIP-Deskriptor, SN1 „racemic“). **Jay (05.11.): kein PDF vorhanden → Clayden-Konventionen aus Kenntnis + freie Quellen (LibreTexts/OpenStax
  zum Gegenlesen), Quelle je Regel; keine Originalabbildung.**
- **Geometrie-Test im Gate:** kein gebogener Pfeil schneidet eine Label-Bounding-Box im SVG; Pfeilspitze ≤ 0,35 Bindungslängen
  vom Zielatom; Pfeilanfang am Quellatom/an der Bindungsmitte. Test über alle Substrate der Matrix.
- **Substrat-Matrix:** ≥ 10 Substrate je Familie inkl. Randfälle (Stereozentrum, Aromat am Zentrum, lange Kette, Salz-Gegenion,
  sekundär/tertiär an der Grenze) rendern mit `substrates_drawn: true` ohne `fallback_reason`; Kontaktbogen (PNG, alle
  Schritte nebeneinander, Referenzbild daneben) für Jays 10-Sekunden-Test — per SendUserFile, iterieren bis Jay „passt“ sagt.
- **Stereo + Titel:** Produkt-Label (R)/(S) bzw. „racemic“ im Panel und in der Datei, Titel bei SMILES-Eingabe mit Name und
  Deskriptor; Test-enforced.
- **Routing:** Eval-Fall „Mechanismus der Diels-Alder-Reaktion“ → Antwort nennt die drei Familien; Taxonomie-Test für den Fence.
- **Schluss:** Golden-SVGs bewusst neu und gesichtet (`UPDATE_…`-Pfad im selben Commit), Gate rc=0, Desktop-Handtest durch Codex
  (`tisch auftrag codex`, Screenshots nach `/tmp/chemdraw-desktop-test/`), CHANGELOG 0.8.0 ergänzt. **Erst dann** Release-Zeile an Jay.

**Stand 05.11. 15:30 (Claude, vor Kontext-Neustart):** E fertig bis auf Jays Sichtung. Befunde 1–5 gebaut
(`522a8c4`…`59eee39`), Geometrie-Test + Matrix 33 Fälle im Gate, Gate rc=0 (7793), Handshake 16/12, Codex-Desktop-Handtest 6/6
grün (`998386d`). Kontaktbögen an Jay per SendUserFile (Scratchpad, neu erzeugbar: Matrix über `generate_mechanism` rendern).
Bericht: `~/.claude/tisch/20261105-131815-etappe-e-mechanismen-vor/bericht-hoplimit.md` (Faden voll, beide Fäden geschlossen).
**Nächster Schritt = Jay:** Kontaktbögen sichten → „passt“ oder Zeile nennen (unbeantwortet — nicht bauen ohne Antwort).
Bei „passt“: Release-Zeile mit `--target $(git rev-parse HEAD)` an Jay (Zeile im Abschnitt unten). Bei Zeilenhinweis: fixen, Matrix neu rendern, neu senden.
Bekannte Grenzen (nicht gebaut): lange Ketten im gemeinsamen Rahmen winzig; ÜZ volle Ladungen statt δ⁻; natürlicher SN1-Prompt ohne Tool.

**Abnahme 05.11. 15:55 (Advisor-Sichtung auf Jays Anweisung „lasse den Advisor die Abnahme machen“): E abgenommen.**
SN2 (Inversion (R)↔(S) korrekt, ÜZ mit ‡) und SN1 („racemic“ nur bei chiralem Produkt, Cyanid ohne Deprotonierung) bestehen.
Fischer: Pfeilrichtungen Schritt 4–6 in `mechanism_substrate.py` geprüft (freies Elektronenpaar → H, Bindung → O) — korrekt.
Einziger Befund „H   regenerated“ ohne ⁺ lag nur im Bogen-Skript (ImageMagick mit Arial ohne U+207A), nicht im Produkt
(Label im Code `H⁺`, Produkt-SVGs tragen keine Schrittüberschrift); Bogen mit Arial Unicode neu, korrekt.
Zusätzliche Grenzen (nicht gebaut): SN1 Schritt 5 zeigt das abgegebene H⁺ nicht (Fischer schon); Ameisensäure-Zeile
deutlich größer als die übrigen. **Nächster Schritt = Jay: Release-Klick 0.8.0** (Zeile im Abschnitt unten, Ziel-SHA = Spitze von main).

Arbeitsweise: Opus-Arbeiter je Bau-Etappe (`model: opus`, Effort medium), Brief nach `~/.claude/docs/modell-prompting/opus-5.md`;
TDD, Vorlage bleibt als Rückfall. Codex vorher per Tisch informieren (Dateien `chemdraw_tool/mechanism*.py`, `ui/src`, Tests).

## Weiter bei — Release-Klick 0.8.0 (Jays Hand), danach Befunde aus der Masse-Eval (Claude, 05.11.2026 01:10)

**Etappe A ist abgenommen** (Haken unten, Beweise in `docs/evidence/masse-eval-2026-11/`, README-Abschnitt
„Lauf 1 → Fix → Lauf 2“). A–D und Werkzeugbilanz sind damit alle erledigt; 0.8.0 ist vorbereitet (CHANGELOG, Version,
Gate rc=0 auf `8a5bb07`, Handshake 16/12 auf `150dcbb`; seither nur Skript-Deutungen, Doku und Evidenz).

**Nächster Schritt = Jay:** Release-Zeile aus Claudes Antwort 05.11. 01:10 ausführen (`gh release create v0.8.0 --target <SHA>`),
dann `gh run list --workflow publish.yml`, PyPI-Umgebung freigeben (pending_deployments), Bundle `.mcpb` am Release prüfen,
Registry `./scripts/publish-registry.sh` (isLatest). Release-Klick bleibt Jays Hand (Auftrag 04.11.: „0.8.0 vorbereiten“).

**Befunde für danach (nicht in 0.8.0, Reihenfolge nach Nutzen):**
1. Deutsche Trivialnamen ohne PubChem-Synonym (75 Eingaben, 74 Stoffe über INN grün): eigener Weg im Resolver —
   de.wikipedia-Weiterleitung auf den englischen Artikel oder Endungsregeln (-on/-one, -in/-ine, -säure/-ic acid), dann
   Lauf 3 über `stoffe-masse.json`.
2. OPSIN gewinnt vor PubChem und zerlegt Trivialnamen (chloroxylenol, methyldopa, methylthioninium chloride, tropicamide):
   OPSIN-Treffer gegen PubChem-Synonym gegenprüfen oder OPSIN nur für systematische Namen (Ziffern/Lokanten) nutzen.
3. PubChem-Synonymfehler ((−)-Ephedrin → CID 104213, Risperidon → CID 44402564): Formel-Plausibilität gegen Wikidata/ChEMBL.
4. Referenzliste: `fumaric acid` auf Q139857 pinnen, `tenofovir disoproxil` (Q155954 trägt Tenofovir-Key) korrigieren,
   `_chembl_namen` im Bericht ist langsam (120 s Timeout je Batch) — Bericht braucht > 5 min.
5. 12 IR-Gruppen ohne Regel (`ir-abdeckung.md`) · pH-Klemme [0,14] in `exact_ph` (3 Randfälle) · Desktop-Befunde aus
   `docs/desktop-abnahme-mechanismus-2026-11-05.md`.

**Branch-Fragen beantwortet (Jay 05.11.):** mechanismus-substrate, mcp-2-migration-v2 gelöscht; mcp-2-migration als Tag
`archiv/mcp-2-migration` archiviert und gelöscht; Dependabot-Branches als eigene Etappe nach 0.8.0.

- [x] **Etappe F erledigt 05.11.2026 (F-Session `edf9eeb9`, Faden `20261105-162003-etappe-f-marketing-repo`):** privates Repo
  https://github.com/jurimaxam-dotcom/chemdraw-vermarktung (`gh repo view` → `PRIVATE`), Stand `c91abb2`. Historie: `video/` per
  `git subtree split` vom Shorts-Branch (1 Commit, `036a4f4` → `3d80235`), darüber Arbeitsstand (`npm --prefix video test` 31/31);
  `plans/vermarktung.md` mit 24 Commits per `git filter-repo` (`cmp` identisch). Korrektur zum Vorab-Befund: diese Datei war
  **versioniert**, unversioniert waren nur `vermarktung/` und `docs/distribution/`. `vermarktung/` per `mv` umgezogen (gleiches
  Volume, `out/` 1,3 GB + `node_modules` reisen mit, `.gitignore`), `docs/distribution/` per `cp -a` + `diff -rq` (leer) → hier
  gelöscht, `plans/vermarktung.md` per `git rm`, `.git/info/exclude`-Einträge entfernt. Recorder-Änderung des Branchs war schon auf
  main (`--clicks`); `pyproject`-exclude + Wheel-Test vom Branch bewusst nicht übernommen. Codex wählte Variante A: Wrapper
  `scripts/ax-claude.sh` (CWD-unabhängig, `exec` mit allen Argumenten, kompiliert nur bei fehlendem/älterem Binary, meldet fehlendes
  Schwester-Repo; `preflight` aus `/tmp` → `screen=1 ax=1`). CLAUDE.md + `plans/grundlagen-darstellung.md` umgebogen. Branches
  `worktree-agent-a89d4c26da6a9d6c2` und `f-video-split` lokal gelöscht (nie auf origin), Tag `archiv/demo-shorts` bleibt auf origin.
  Gate `./test.sh` rc=0 (Log im F-Scratchpad `gate-f.log`). Ursprünglicher Auftrag:
  **Etappe F — eigenes Marketing-Repo (Jay 05.11., nach E, eigene Session):** `vermarktung/` (Aufnahme-Skripte, AX-Steuerung,
Posts, Launch-Checkliste) und die Shorts-Pipeline vom Branch `worktree-agent-a89d4c26da6a9d6c2` (Tag `archiv/demo-shorts`:
Recorder-Änderung in `ui/src/host/demo.record.mjs`, Remotion-Projekt `ui/video/`, `scripts/demo-short.sh`) in ein privates
Repo `~/Documents/projects/chemdraw-vermarktung` (`gh repo create --private`), Historie per `git subtree split` bzw.
`git filter-repo` mitnehmen. Vorher prüfen, wer `vermarktung/` noch braucht: Codex-Desktop-Handtest (`ax-claude.swift`,
CLAUDE.md), `tests/test_wheel_contents.py`, `demo-video.sh`, README-GIF-Aufnahme — Verweise umbiegen oder dünnen Wrapper lassen.
Danach Branch `worktree-agent-…` löschen (Tag bleibt). Videos selbst nie ins Repo. Erst nach E, weil Codex `ax-claude.swift`
für den E-Handtest braucht.

**Fragen an Jay (unbeantwortet — nicht bauen):** Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

Offene Tisch-Fäden: `20261105-001817-etappe-a-masse-eval` (Claude↔Codex, Reservierung; wird mit dem Bericht geschlossen).

## Weiter bei — Codex nach Kontext-Neustart (04.11.2026)

**Nächster Schritt:** Tisch-Aufträge am Projektort lesen und mit Claudes laufender
A/B-Arbeit abstimmen. D und Release-Abnahme (g) sind vollständig abgeschlossen;
beides nicht erneut ausführen. Falls die separate Desktop-Abnahme der neuen
README-Bilder beauftragt ist: deren konkreten Faden lesen und dort fortsetzen.
Keine Dateien der laufenden A/B-Arbeiter übernehmen.

**Neustart-Prüfung (04.11., Codex):** Keine eigene halbfertige Arbeit und keine
ungelesene Tisch-Nachricht. Einzige lokale Änderung beim Prüfen:
`scripts/masse_eval.py` (laufende Claude-/Arbeiter-Arbeit, nicht mitcommitten).
Offener Abstimmungsfaden: `20261104-230127-jay-will-vier-vorschlaege`, zuletzt
#4 Codex-Status zum Neustart. A wartet laut Helfer-Live auf seinen Hintergrundlauf;
nach dessen Bericht wertet Claude aus. Codex hat keine eigene Wartefrist und
keinen Hintergrundjob; nach Neustart Nachrichten prüfen, bei fehlendem Auftrag
keine A/B-Arbeit übernehmen.

**Dateien und Beweise:** `docs/desktop-abnahme-0-7-0-bundle.md` (249fca6,
vier frische Desktop-Chats grün, fünf Bundle-/56 Paketdateien gegen PyPI identisch,
Screenshots `/tmp/chemdraw-desktop-test/0-7-0-bundle/`); D in
`docs/repo-aufraeumen-2026-11-04.md` (0e5f8ed), eigener Rechner privat gepusht
nach `jurimaxam-dotcom/praktikumsrechner` (ea0ceb8). C laut Abnahme weiter unten
erledigt; A und B bleiben dort offen. Release-(f)/(g) sind bereits abgehakt.

**Desktop-Ausgangszustand wiederhergestellt:** Entwickler-Konnektor `chemdraw-tool`
exakt zur Sicherung, Bundle 0.7.0 installiert, aber deaktiviert, Desktop neu
gestartet; genau ein Entwickler-Konnektor sichtbar. Vorübergehend versehentlich
erweiterte Einzelberechtigungen vollständig zurückgesetzt und nochmals geprüft;
pH-Test mit Einmalfreigabe. Keine offene Installation und kein eigener
Hintergrundjob, der nach dem Neustart ausgewertet werden muss.

**Offene Entscheidungen:** „Welle 3 eigenes Profil?“ und „Abfragemodus auch für
Reaktionen?“ — **unbeantwortet — nicht bauen**. Vier gesicherte Branch-Entscheidungen
stehen mit Wortlaut im D-Befund; keine Branch-Löschung ohne Entscheidung.
Release-Befunde: Manifest „six tools“ laut Release-Abschnitt bereits behoben
(`dbd94e5`); offen bleiben Erststart-Timeout während Installation und
Anki zählt Notizen als „cards“.
Nicht selbst in dieser Abnahme fixen. Keine zeitgebundene Wartefrist offen.

**Prüfmethoden bei Folgeaufträgen:** echte Desktop-Chats und Screenshots für
sichtbares Verhalten; Host-/Gate-Prüfungen ersetzen das nicht. Änderungen nur in
der eigenen Reservierung, rote Regression vor Produktfix. Bei erneutem
Bundle-Test Receipt/Hash/PyPI-Dateivergleich plus isolierten laufenden Prozess
prüfen; Toolzahlen allein genügen nicht.

## Weiter bei — Etappe A abschließen, dann Release-Zeile 0.8.0 (Claude, 05.11.2026 00:20, vor Kontext-Neustart)

**Erledigt heute (geprüft):** Codex-Handtest Mechanismen abgenommen (`350b270`, Faden `20261104-234915` erledigt; Formel-Titel
im Desktop bestätigt) · Resolver-Fix NCI-500 „Page not found“ = not_found statt partial (`cc13e47`, TDD) · Nitro-SMARTS +
starke Base ohne Auslöschung (`c8b3e8b`; pH 48/51 grün, Nitro 10/10) · Version 0.8.0 in CHANGELOG/pyproject/server.json/uv.lock
(`150dcbb`) · Werkzeugbilanz neu gebaut und republisht (`cecb120`, Artifact Version 5) · **Gate rc=0 (7542 Tests) + Handshake
16/12 auf dem 0.8.0-Stand.**

**Läuft (Wartezeit mit Folgeaktion):** Identitätslauf 1 über 711 Eingaben, Prozess `scripts/identitaet.py --datei
tests/identity/stoffe-masse.json`, Stand 00:15 ≈ 480/711, schreibt am Ende `docs/evidence/masse-eval-2026-11/identitaet-lauf.json`.
Prüfen: `pgrep -f "scripts/identitaet.py --datei"` — leer = fertig. Dann:
1. Lauf 1 sichern: `cp …/identitaet-lauf.json …/identitaet-lauf-1-vor-nci-fix.json`, Bericht `uv run python scripts/masse_eval.py identitaet`,
   committen (Lauf 1 = Beweis für den NCI-Befund: ~14 % gelb „Quelle weg (partial)“ waren deutsche Namen, NCI antwortet 500 statt 404).
2. Lauf 2 mit gefixtem Resolver (Hintergrund, ~45 min): `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json
   --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht neu, README der Masse-Eval um „Lauf 1 → Fix → Lauf 2“ ergänzen.
3. A abhaken gegen die Abnahmepunkte: ≥ 250 Stoffe mit unabhängiger Quelle (711 Eingaben/414 Stoffe, Wikidata + ChEMBL ✓), drei
   Berichte mit Zahlen (ir-abdeckung.md ✓, ph.md ✓, identitaet.md nach Lauf 2), `uv run pytest tests/test_eval_cases.py
   tests/test_server_profiles.py -q` grün. Ein Opus-Arbeiter der alten Session (Task a8c187fe8efb448ce) hat ggf. parallel
   `identitaet.md` geschrieben/committet — Dateien sind die Wahrheit, `git log` ansehen, nichts doppelt committen.
4. Dann Release-Zeile an Jay (Release-Klick = Jays Hand, Auftrag 04.11. hieß „0.8.0 vorbereiten“):
   `gh release create v0.8.0 --target <volle SHA von main> --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)`,
   danach `gh run list --workflow publish.yml`, PyPI-Umgebung per API freigeben (pending_deployments), Bundle `.mcpb` am Release, Registry `isLatest`.

**Befunde für später (nicht in 0.8.0):** OPSIN-Fehlgriffe bei Trivialnamen (chloroxylenol → Cyclohexadienol, methyldopa →
N-Methyl-DOPA, methylthioninium chloride → Thiepinium; OPSIN gewinnt vor PubChem) · PubChem-Synonymfehler „(−)-Ephedrin“ →
CID 104213 · 12 IR-Gruppen ohne Regel (`ir-abdeckung.md`: Halogenaryl, Heteroaromat-NH, Imin, Sulfonamid, C–F, Carbamat,
β-Lactam, …) · pH-Klemme [0,14] in `exact_ph` (3 Randfälle, teilt sich die Funktion mit der Titrationskurve) · Desktop:
„Mechanismus der Diels-Alder-Reaktion“ läuft in generate_reaction ohne Drei-Familien-Hinweis, Fischer-Pfeil knapp über HO-Label,
SN2-Produkt ohne (S)-Label im Panel (`docs/desktop-abnahme-mechanismus-2026-11-05.md`).

**Fragen an Jay (unbeantwortet — nicht bauen):** vier Branch-Fragen in `docs/repo-aufraeumen-2026-11-04.md`
(mcp-2-migration behalten/archivieren · origin/mcp-2-migration-v2 löschen · worktree-agent Demo-Commits übernehmen ·
Dependabot-Update als eigene Etappe) · Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

Offene Tisch-Fäden: keine zu dieser Arbeit (`20261104-234915` erledigt 00:05).

## Weiter bei — Rest der Etappen A–D + Werkzeugbilanz (Claude, 04.11.2026 23:45, vor Kontext-Neustart)

**Erledigt heute (geprüft, Haken unten):** Release 0.7.0 draußen (PyPI, Bundle, Registry) · D Repo aufräumen · C README-Gate ·
g Bundle-Abnahme · B Mechanismus mit eigenen Substraten gemergt (`16fc11e`) + Titel-Fix (`a43104d`, `a18b849`), Gate grün.

**Läuft noch:**
- **A Masse-Evaluation (Opus-Arbeiter, gestartet 04.11. 23:12):** `ir-abdeckung.md`, `ph.md`, `README.md` in
  `docs/evidence/masse-eval-2026-11/` liegen schon; `identitaet.md` (PubChem-Lauf über ~300 Stoffe, Rate-Limit) steht aus.
  Nach Neustart: `git log --oneline -15` und `git status` ansehen; liegt `identitaet.md` vor und ist alles committet → Bericht
  gegen Abnahmepunkt A prüfen (Stoffliste ≥ 250 mit unabhängiger Quelle, drei Berichte mit Zahlen, `uv run pytest
  tests/test_eval_cases.py tests/test_server_profiles.py -q` grün) und abhaken. Liegt Ungecommittetes (`scripts/masse_eval.py`,
  `tests/identity/*.json`) → sichten, Lauf selbst zu Ende fahren (`uv run python scripts/identitaet.py --datei
  tests/identity/stoffe-masse.json`), committen. Der Arbeiter-Bericht geht mit dem Kontext-Neustart verloren; Dateien sind die Wahrheit.
- **Desktop-Handtest Mechanismen (Codex, Faden `20261104-234915-desktop-handtest-fuer-generate`):** Bericht kommt als Tisch-
  Nachricht; Datei `docs/desktop-abnahme-mechanismus-2026-11-05.md` entsteht. Prüfen, Haken bei B ergänzen, Faden erledigt.
  Bekannte Befunde: SN1 als Frage („SN1 von …“) ohne Tool = Desktop-Grenze; Titel-SMILES behoben.

**Danach (letzter Punkt):** Werkzeugbilanz neu bauen: in `scripts/werkzeugbilanz.py` den Eintrag `generate_mechanism`
anpassen (`erzeugt="rechnet"`, wie: Substrate per Reaktions-SMARTS, Grenze je Familie, Fallback Vorlage; Schwierigkeiten
aus dem Handtest), Lauf `HOME=<wegwerf> uv run python scripts/werkzeugbilanz_lauf.py <ordner>`, Seite bauen mit
`--welle3-log docs/evidence/routing-2026-11-03/welle3-vollprofil-2026-11-04-n1.log`, per Artifact `url`
https://claude.ai/artifact/PV3deo4duj9r8zad5gpskg republishen (erst `action: read`). Dann 0.8.0-Release vorbereiten
(CHANGELOG [Unreleased] → [0.8.0], Version, Gate, Handshake) — Release-Klick nach Jays Freigabe 04.11. („mache du den Release“)
darf Claude selbst; `gh release create v0.8.0 --target <volle SHA>`, PyPI-Umgebung per API freigeben (pending_deployments).

**Fragen an Jay (unbeantwortet — nicht bauen):** vier Branch-Fragen in `docs/repo-aufraeumen-2026-11-04.md`
(mcp-2-migration behalten/archivieren · origin/mcp-2-migration-v2 löschen · worktree-agent Demo-Commits übernehmen ·
Dependabot-Update als eigene Etappe).

Offene Tisch-Fäden: `20261104-234915-desktop-handtest-fuer-generate` (Codex, Auftrag läuft).

## Weiter bei — Werkzeugbilanz-Folgen A–D abarbeiten (Claude, 04.11.2026 23:10)

**Jay (04.11. 23:00):** „Sprich dich mit Codex und dem Advisor ab und arbeitet alle Punkte in der logisch sinnvollsten
Reihenfolge ab, das entscheidet der Advisor, hört erst auf, wenn alles erledigt ist.“ Jays drei Fragen (Mechanismus-Vorlagen,
README-Aktualität, Repo-Umfang) sind beantwortet (Antwort 04.11. 22:58); daraus die vier Vorschläge.

**Reihenfolge (Advisor, Codex einverstanden bis auf Nuance „D-Bestandsaufnahme parallel, Ausführung nach C“):**
D ∥ C → A → B. D ohne `assets/` (das ist C). B zuletzt und auf eigenem Branch, bis Jays Tag v0.7.0 steht — sonst
verschifft der Tag ein geändertes Tool, das der CHANGELOG nicht beschreibt.

**Zuständig:** D = Codex (Faden-Auftrag), C = Opus-Arbeiter (Claude prüft Diff + Gate), A = Opus-Arbeiter parallel zu C,
B = nach A, Opus-Arbeiter mit Design-Notiz vorweg; Desktop-Abnahme der README-Bilder = Codex nach C.
Abstimmungsfaden: `20261104-230127-jay-will-vier-vorschlaege`.

**Abnahme je Etappe (prüfbar, nicht beschrieben):**
- [x] **D Repo aufräumen (Codex, 04.11. 23:10, Claude geprüft: web/ weg, praktikumsrechner-Repo ea0ceb8 privat gepusht, Bundle 38 MB + Worktree-tar 359 MB in ~/Documents/archive, Worktree entfernt, keine Branch-Löschung, Gate grün, Ruff an Bilanzskripten gefixt 7007e14; vier Branch-Fragen an Jay in docs/repo-aufraeumen-2026-11-04.md):** nur gemergte Branches gelöscht, `git branch --merged`-Ausgabe als Beleg; `mcp-2-migration`
      (2 Commits nicht in main), `origin/mcp-2-migration-v2` (1), `worktree-agent-a89d4c26da6a9d6c2` (5 Commits: demo-short.sh,
      Kamera) werden NICHT gelöscht, sondern mit Patch-Vergleich und Bundle-Sicherung in einer Befunddatei `docs/repo-aufraeumen-2026-11-04.md`
      für Jay gelistet (Datenverlust-Bremse); `web/` samt `scripts/build-web.sh`, `deploy-pages.sh`, `rechner-e2e.sh` als Ganzes
      nach `~/Documents/projects/praktikumsrechner` oder `~/Documents/archive/` verschoben (Browsertrainer bleibt separat);
      Gate grün danach. `assets/` unangetastet.
- [x] **C README-Gate (Opus, 04.11. 23:30, Claude geprüft: Gate grün, Rot-Probe generate_tlc selbst wiederholt, 13 Bilder aus `scripts/readme_bilder.py` + Hash-Manifest, drei neue Bilder gesichtet, Limitations ergänzt; Commits 167c8b1…73b48fc; 7 ungenutzte Assets entfernt, Git behält sie):** `tests/test_readme.py` einmal rot gesehen (Toolzeile entfernt, wieder eingesetzt): jedes registrierte
      Tool des Standardprofils in der README-Tabelle, kein nicht registriertes, Toolzahlen (16/23) stimmen mit `create_server()`;
      `scripts/readme_bilder.py` erzeugt jedes Datei-Bild in `assets/` aus den Tools mit festen Beispielen (Titrationskurve mit
      Pufferpunkt auf der Kurve, neu: Look up/Calculate/Anki je ein Bild); Hash-Test im Gate wie Golden-SVGs (bewusst neu erzeugen
      per `UPDATE_README_BILDER=1`); Limitations-Absatz trägt die Desktop-Grenze aus dem CHANGELOG 0.7.0; Gate grün.
      GIFs bleiben Aufnahmen (demo-video.sh), nur Datum/Version geprüft.
- [x] **A Masse-Evaluation (Opus-Arbeiter + Claude, abgenommen 05.11. 01:10; Fixture ist `tests/identity/stoffe-masse.json` mit 711 Eingaben/414 Stoffen, `stoffe.json` bleibt unverändert; Erwartung Wikidata-InChIKey gegen ChEMBL (691/711 bestätigt); drei Berichte mit Zahlen in `docs/evidence/masse-eval-2026-11/`: `identitaet.md` Lauf 2 591 grün · 1 gelb · 119 rot (80 `not_found` = deutsche Labels ohne PubChem-Synonym, 21 stereo, 16 skelett davon 4 OPSIN-Fehlgriffe, 2 PubChem-Synonymfehler, 2 Wikidata-Referenzfehler), `ir-abdeckung.md`, `ph.md` 48/51; Lauf 1 vor NCI-Fix eingefroren `f402b94`; `pytest tests/test_eval_cases.py tests/test_server_profiles.py` 263 grün; Gate rc=0 7542 Tests):** `tests/identity/stoffe.json` von 24 auf ~300 Einträge; Erwartungswerte aus einer
      UNABHÄNGIGEN Quelle (Codex-Einwand): InChIKeys aus PubChem-Download je CID-Liste (Ph.-Eur.-Arzneistoffe / Top-200
      Wirkstoffe), nicht aus der eigenen Auflösungskette; IR-Regelabdeckung über dieselbe Menge (welche Gruppen keine Regel
      treffen) als Bericht; pH-Aufgaben (~50) gegen Lehrbuchlösungen. Ergebnis + Rot/Gelb-Zusammenfassung nach
      `docs/evidence/masse-eval-2026-11/`; bleibt außerhalb des Gates (Netz).
- [x] **B Mechanismus mit eigenen Molekülen (Opus, Branch `mechanismus-substrate`, 05.11. 00:20 gemergt `16fc11e`, Gate grün rc=0; Claude geprüft: 6 Commits, Design-Notiz, Grenzen je Familie in `mechanism_substrate.py`, README-Bild gesichtet; CHANGELOG [Unreleased] → 0.8.0; Desktop-Handtest Codex `350b270` abgenommen 05.11. 00:05):** Design-Notiz zuerst (Reaktionszentrum per
      SMARTS finden, Rest mitzeichnen, Pfeile an gefundene Atome), Unterstützungsgrenze je Familie benennen; TDD, Golden-SVGs
      gesichtet; CHANGELOG 0.8.0; Merge erst nach Tag v0.7.0.
- [x] Nach allem: Werkzeugbilanz neu bauen (`scripts/werkzeugbilanz.py`) und per url republishen (Claude 05.11. 00:10, `cecb120`, Artifact Version 5).

Bremsen bleiben: Release-Klick = Jay; Branch-Löschung nur gemergt; nichts nach außen.

## Weiter bei — Release 0.7.0 (Claude, 03.11.2026 07:50)

**Reihenfolge (Jay 02.11.):** erst 0.7.0 sauber raus → dann README sauber → Shorts zuletzt.

**Stand draußen:** GitHub, PyPI, Registry = 0.6.0 (26.10., 7 Tools). Repo bereit für 0.7.0 (`cb4afa9`:
Version, Changelog). Alte Erweiterung 0.5.1 in Desktop deaktiviert (Ursache der „7 alten Tools" 30./31.10.).

**Desktop-Messung 02.11.** (`docs/desktop-abnahme-2026-11-02.md`, je 1 Chat): 16 Tools in einem Konnektor,
12/12 Panels rendern, Routing 10/16 — ohne Tool: lookup, predict_spectrum, calculate_ph ×3, compare_molecules.

**Ursache Routing (Claude, belegt):** Desktop lädt Tools erst bei Bedarf. `run_claude.py` mit
`ENABLE_TOOL_SEARCH=true BUILTIN_TOOLS=ToolSearch` reproduziert es: die pH-Fälle 6/6 ohne Suche.
Fix `7596c26` (pH-Regel vorn in `_MVP_INSTRUCTIONS`): mit Tool-Suche 18/18, ohne 12/12.
Panel-Fixes `40723f9`: Vergleich im Dunkelmodus, Anki-Vorschau ohne Tags. Gate, Handshake 16/12, Host 167 ✔.

**Nachmessung Desktop 03.11. (Codex `bcd6f44`, Claude geprüft):** Originalprompts **0/18** — alle 6 Fälle 0 von 3,
Antworten aus dem Gedächtnis (pH 2,87 fachlich richtig). Mit Zusatz „— nutze ChemDraw" **6/6** (pH, Löslichkeit, Vergleich
je 2/2). Stichproben generate_molecule + Titrationskurve grün; Vergleich im Dunkelmodus lesbar; Anki ohne Tags.
→ Entscheidungsregel „pH weiter rot" greift: Hinweiszeile erreicht Desktops Toolwahl nicht. 0.7.0 geht raus,
Grenze + Workaround in CHANGELOG „Known limitations".
**Rückschrittkontrolle Claude Code (57 Fälle, je 2 Läufe):** mit Tool-Suche 50 + 49/57, ohne 54 + 53/57. Gegenmessung der
8 Rotfälle auf `7596c26^`: mit Suche 3/8 + 2/8, nach Fix 1/8 + 1/8 — schwaches Signal, im Rauschen; ohne Suche gleich.
Dauerhaft rot: `exam-revision` (batch_generate dazu), `reaction-in-conversation` mit Suche (nur Mechanismus).
Nebenbefund Codex: Label „Acetylsalicylsäure" im Vergleichspanel mit Lücke am Umlaut (nach 0.7.0).

**Nächster Schritt (03.11. 08:15, Jay will es jetzt): Release 0.7.0.** `publish.yml` startet bei `release: published`, ein
reiner Tag-Push reicht NICHT. Befehl (Projektordner): `gh release create v0.7.0 --title "0.7.0" --notes-file <(awk
'/^## \[0.7.0\]/{f=1;next} /^## \[0.6.0\]/{exit} f' CHANGELOG.md)` — Release = Jays Hand (Außenwirkung). Danach Actions-Lauf
prüfen (`gh run list --workflow publish.yml`), PyPI 0.7.0 + `.mcpb` am Release + Registry `isLatest`, dann (g) mit Codex.

**Werkzeugbilanz (Artifact, 04.11. neu gebaut):** https://claude.ai/artifact/PV3deo4duj9r8zad5gpskg — je Tool Dateien, Ablaufdiagramm,
Output (heutiger Lauf + Desktop-Screenshot), Toolwahl nach Name/Auftrag/Frage (CC 4 Läufe + Desktop), Mehrwert, Schwierigkeiten, Testbreite.
Generator `scripts/werkzeugbilanz.py <lauf> <ziel.html> --welle3-log …`, Lauf `scripts/werkzeugbilanz_lauf.py <ordner>`; Quellen fest im Repo
(`docs/evidence/routing-2026-11-03/`, Snapshots, Tests, Abnahme-Doku). Befund 04.11.: Auftrag 122/128, Frage 72/88 (mit Tool-Suche 31/44);
generate_mechanism = feste Vorlage (Substrate nur geprüft), predict_spectrum = 31 SMARTS-Regeln, alles andere gerechnet/live.
Nebenbefund: Ibuprofen kommt mit CAS 58560-75-1 (Racemat) statt 15687-27-1 (PubChem-Synonymreihenfolge).

**Nach 0.7.0 — API-Eval (Jay 03.11.: „erst 0.7.0, dann"):** Runner über Anthropic-API (Opus 5.5) gegen den ECHTEN Server
(MCP-stdio-Client, Tools mit `defer_loading` + `tool_search_tool_bm25_20251119` wie Desktops Nachladen), je Fall eine
Korrektheitsprüfung (pH 2,88 ± 0,02, InChIKey, Pufferrezept 38,7/61,3 mL; Text per Modell-Richter), alle 23 Tools.
Erst 10 Kernfälle (~3 $, Kosten je Fall messen), dann Freigabe für ~60 × 3 (~20–25 $ geschätzt). Voraussetzung Jay:
API-Schlüssel (`ANTHROPIC_API_KEY` oder `ant auth login`; heute weder Key noch `ant` noch SDK da). Grenze: sagt
Desktop-Routing NICHT verlässlich voraus (CC mit Tool-Suche 18/18 vs. Desktop 0/9) — dafür bleibt Codex' Klicktest.

**Fragen an Jay, geparkt (nicht in diesem Release):** Welle 3 eigenes Profil? · Abfragemodus auch für Reaktionen?

- [x] (a) alte Erweiterung aus, Desktop neu gestartet (Claude, 23:05)
- [x] (b) **Codex:** Desktop-Messlauf aller 16 Tools mit natürlichen Prompts (Faden `20261102-230541-desktop-abnahme-0-7`),
      Tabelle `docs/desktop-abnahme-2026-11-02.md`, Commit `1b8fded`; Messung vollständig, Abnahme rot (10/16 Routing).
- [x] (c) **Claude:** Host-Fälle für `batch_generate` und `generate_reaction` (fehlen in `host.e2e.mjs`)
- [x] (d) **Claude:** Befunde aus (b) fixen (TDD) — `40723f9`, `7596c26`
- [x] (d2) **Codex:** Desktop-Nachmessung „n von 3" je roter Fall — 0/18, mit „nutze ChemDraw" 6/6 (`bcd6f44`)
- [x] (e) **Claude:** CHANGELOG 0.7.0, Version 0.7.0 (`pyproject.toml`, `server.json`), Gate + Handshake grün
- [x] (f) Release v0.7.0 (Claude, 04.11. 23:08, Jays Freigabe „mache du den Release“): Tag auf `3016833` (kein Produktcode seit Gate 03.11.),
      Lauf 41922554381 grün: PyPI 0.7.0, `chemdraw-mcp-0.7.0.mcpb` am Release, Registry-Job grün; PyPI-Umgebung per API freigegeben
- [x] (g) Bundle 0.7.0 in Desktop abgenommen (Codex 04.11. 23:45, Jays Install-Freigabe; Claude geprüft: `docs/desktop-abnahme-0-7-0-bundle.md`
      @ 249fca6, 16 Screenshots, PyPI-Wheel bytegleich installiert, Entwickler-Konfig wiederhergestellt). Vier Stichproben grün.
      **Für 0.7.1:** Manifest „six tools“ (behoben dbd94e5) · Erstinstallation brauchte zweiten Neustart (10-s-Host-Timeout beim uv-Install) ·
      Anki-Panel zählt Notizen (14) statt Karten (16).
- danach: README-Bilder (Calculate, Anki, Look up; `wave2-titration-acetic.png` neu) · zuletzt Shorts S1/S8–S11
- Welle 3 (Profil-Entscheid, Jay) erst nach 0.7.0

Geparkt: Git-Ballast (`mcp-2-migration` + 2 Worktrees) · adjustText verworfen (scipy).

## Basis-Ausbau: Vollumfang zurück ins Standardprofil (Jay 30.10.2026)

> Auftrag Jay 30.10.: die 16 fürs Release zurückgenommenen Tools sauber wieder ins
> Standardprofil holen (`MVP_TOOLS`, `chemdraw_tool/server.py:258`), danach README hochwertig,
> danach Shorts. **Keine OC-Prüfungsfragen in dieser Runde.**
> Reihenfolge umgestellt 30.10. (Jay): nach Breitenwirkung in drei Wellen — Strukturansichten
> stehen, jetzt Reaktionen/Mechanismen; Rechnen ist Vertiefung und kommt später. Je Welle ein
> Release-Kandidat.
>
> Aufteilung: **Opus** = `server.py`, Tool-Snapshots, `cases.yaml`, Python-Tests ·
> **Codex** = Fälle in `host.e2e.mjs`, README-Bilder, Desktop-Handtest.

- [ ] **Jay:** Welle 3 (Vertiefung) ins Standardprofil oder in ein eigenes Profil? Davon hängt ab,
  ob `CHEMDRAW_PROFILE` am Ende wegfällt.

**Definition of Done je Tool** (jeder Tool-Haken unten heißt: alle Punkte erfüllt)

1. Ist-Zustand im Vollprofil messen: `CHEMDRAW_PROFILE=full`, ein echter Aufruf über den Server;
   bei Panel-Tools zusätzlich das Panel in `test:host` (heute deckt `src/host/host.e2e.mjs` nur
   `generate_molecule` ab → je Panel-Tool einen Host-Fall ergänzen).
2. Befunde fixen, TDD (Test erst rot, dann grün).
3. Freischalten: Name in `MVP_TOOLS` · Eintrag in `_MVP_SUMMARIES` (Auswahltext ohne Verweis auf
   noch abgeschaltete Tools) · Zeile in `_MVP_INSTRUCTIONS` · `MVP`-Menge in
   `tests/test_server_profiles.py` · Handshake-Erwartung (`./scripts/handshake.sh`, Zahl leitet
   sich aus dem Profil ab — nach dem Lauf prüfen).
   **Rückwärtszäune der Nachbarn:** die `_MVP_SUMMARIES` von `generate_molecule`,
   `batch_generate`, `generate_reaction` (und jedem anderen Nachbarn) bekommen wieder ihre
   „Not this tool for: … (use <neues Tool>)"-Zeile — `test_server_profiles.py` prüft nur
   `mentioned <= MVP`, nicht dass der Zaun zurückkommt; je Zaun ein Test.
   **Mitwandernde Texte:** Satz „Other features are temporarily disabled" in `_MVP_INSTRUCTIONS`
   (stimmt nach Welle 3 nicht mehr) · Testname `test_default_and_explicit_mvp_offer_exactly_seven_tools`
   · Zahlen „7 tools, 6 with a panel" in `CLAUDE.md` und README § Profiles.
4. Routing-Fall in `evals/tool-routing/cases.yaml` mit `expect` und `forbidden` (Regel dort: drei
   verschiedenartige Prompts je kritischem Tool); `tests/test_eval_cases.py` grün.
5. Tool-Snapshot bewusst segnen (`UPDATE_TOOLSNAPS=1 uv run pytest tests/test_tool_snapshots.py`)
   im selben Commit wie der Textwechsel; 2-KB-Grenze (`MAX_DESCRIPTION_BYTES`) bleibt grün.
6. README-Abschnitt mit echtem Bild aus einem echten Aufruf (kein Mock).
7. Codex-Handtest in Desktop per `tisch auftrag codex` (Prompt, Klicks, Erwartung je Schritt,
   Screenshots nach `/tmp/chemdraw-desktop-test/`); Gate `./test.sh` + `test:host` + Handshake grün.

**Rahmen, der für alle gilt**

- Toolzahl-Obergrenze: `tests/test_server_taxonomy.py:127` (`<= 23`). Die 16 Tools passen
  hinein; kein neues Tool in dieser Runde, sonst Grenze bewusst mit Begründung heben.
- Desktop nach jeder Server-Änderung neu starten (CLAUDE.md); Handshake ist der harte Beweis.
- Release-Kandidat je Etappe: Version heben, `.mcpb` bauen, Registry-Publish nicht vergessen
  (`./scripts/publish-registry.sh`); der Release-Klick bleibt Jays Hand.

**Messung 30.10.2026 (Vollprofil, `create_server("full")`)** — alle Modultests grün:

| Tool | Beschreibung | Panel | Modultests | Routing-Fälle (`expect`) |
|---|---|---|---|---|
| generate_3d | 614 B | ja | 5 grün (`test_structure3d`) + `test_server_anki` | **0** |
| generate_mechanism | 851 B | ja | 41 grün | 2 |
| generate_scope_table | 1964 B | ja | 57 grün | 1 |
| lookup | 1143 B | nein | 68 grün (databases + server_lookups/_lookup_ui) | 3 |
| predict_spectrum | 1349 B | nein | 32 grün (`spectro`) | 1 |
| generate_spectrum | 1606 B | ja | 36 grün | 1 |
| generate_tlc | 1833 B | ja | 37 grün | **0** |
| generate_titration_curve | 1167 B | ja | 19 grün (ph_plots + server_plots, mit species) | 1 |
| generate_species_distribution | 967 B | ja | (s. o.) | **0** |
| generate_calibration_curve | 1459 B | ja | 26 grün | 1 |
| generate_pk_curve | 1290 B | ja | 10 grün (`server_pk_plots`, mit dose) | 1 |
| generate_dose_response | 1125 B | ja | (s. o.) | 2 |
| calculate_solution | 2030 B | nein | 36 grün | 1 |
| calculate_ph | 1994 B | nein | 39 grün | 2 |
| calculate_content | **2041 B** | nein | 84 grün (calculator_* + server_content) | 1 |
| calculate_pharmacokinetics | 1803 B | nein | 35 grün | 3 |

Bekannte Baustellen aus der Messung:
- **2-KB-Kante:** `calculate_content` 2041 B, `calculate_solution` 2030 B, `calculate_ph` 1994 B,
  `generate_scope_table` 1964 B — unter 2048, aber jede neue Abgrenzungszeile kippt sie.
  Parameter-Doku kürzen, nie die Abgrenzung.
- **Routing-Lücken:** `generate_3d`, `generate_tlc`, `generate_species_distribution` haben keinen
  `expect`-Fall; alle übrigen nur 1–3, meist weniger als die geforderten drei verschiedenartigen.
- **Host-Test** kennt nur `generate_molecule`; die 12 Panel-Tools sind dort ungeprüft.
- `test_server_profiles.py` prüft `panel == MVP - {"save_png"}` — wächst automatisch mit, wenn
  die `MVP`-Menge gepflegt wird.
- Modultests grün heißt nicht „in Desktop richtig": Messung in Punkt 1 der DoD ist Pflicht.

Echte Aufrufe 30.10. (DoD 1, vor jedem Fix):
- `generate_mechanism`: zeichnet **immer** das feste Lehrbuchbeispiel des Templates
  (sn2: CH₃Br + OH⁻); nur der Titel übernimmt die Nutzer-Substrate. Beleg: `["CBr","[OH-]"]` und
  `["CCCCBr","[SH-]"]` liefern byte-gleiche SVGs, Titel „SN2: CCCCBr + [SH-]". Zwei
  Fehlermeldungen deutsch (`server.py` ~3479/3493). 12 KB Text ans Modell.
- `generate_3d`: Ibuprofen 0,5 s, 6,4 KB Text, `type: molecule3d` — sauber. Das Molekül-Panel hat
  **keine** 3D-Ansicht (Achse nur Skelett/All H/Fischer/Haworth, `MoleculeView.jsx:248`); das Tool
  bringt also den Chat-Weg und ist der einzige Weg zu 3D. Ein 3D-Knopf im Molekül-Panel (lazy wie
  All H) wäre eigene Arbeit — der 10-Sekunden-Test unten („3D klicken") setzt ihn voraus.
- `generate_scope_table`: 0,1 s, aber 36,7 KB Text ans Modell (Grid-SVG inline), wächst mit den
  Einträgen.

### Welle 1 — Reaktionen & Darstellung (Release-Kandidat danach)
- [ ] generate_mechanism — **Entscheid 30.10.:** ehrliche Lehrbuch-Galerie (SN1, SN2,
  Fischer-Ester). Titel und Beschreibung sagen „textbook example", `reaction_type` listet die drei
  Typen vollständig (kein „e.g."), die Substrate prüfen nur die Passung; Fehlermeldungen englisch.
  Serverseite fertig `142e581` (DoD 1–5); offen: Desktop-Handtest (Codex).
- [ ] generate_3d — Serverseite fertig `044e8d6` (Zäune ⇄ generate_molecule, 3 Routingfälle);
  offen: Desktop-Handtest (Codex).
- [ ] lookup — Serverseite fertig `ed2dee2`. Behobene Befunde: KEGG nahm den ersten unscharfen
  Treffer („glucose" → UDP-glucose C00029, jetzt C00031), Ausgabe halb deutsch → englisch, leere
  Zeile „| **** |" in physical, Link „CID ?". Offen: Desktop-Handtest (Codex).
  Nicht behoben, notiert: 6–10 s je Aufruf (PubChem/ChEBI/KEGG nacheinander); ChEBI-Zeitüberschreitung
  erscheint als „No ChEBI entry found" (Ausfall ≠ kein Eintrag); Familiennamen wie „xylene" →
  „not found" statt Isomerauswahl (lookup umgeht den Resolver).
- Stand Standardprofil nach Welle 1: 10 Tools, 8 Panels (Handshake grün).

### Welle 2 — Spektren & allgemeine Laborgrafik (Release-Kandidat danach)
- [ ] predict_spectrum — Serverseite fertig `3945648`; offen: Desktop-Handtest (Codex).
  Behoben: `structure="Aspirin"` scheiterte („could not be parsed"), das Modell musste SMILES
  tippen → läuft jetzt durch `resolve()`. Zäune generate_molecule/lookup → predict_spectrum.
  Notiert: Ausgabe doppelt („3 signal(s) for 8 hydrogens" in Kopf und Bullet).
- [ ] generate_spectrum — Serverseite fertig `c6c847c` + Desktop-Fix `6ba60ca`; offen:
  Desktop-Retests ausgeführt, Toolwahl weiterhin rot (`0c36b4b`). Behoben: überlappende IR-Banden (Aspirin C=O 1750/1690) addiert und
  bei 0 % abgeschnitten → Transmission multipliziert; Fehlertexte englisch; Exportknopf in
  SpectrumView (ExportPngButton). **Offen, Desktop-Befund (Codex):** „Aspirin IR-Spektrum
  schematisch" geht auch nach eigenem Auswahltext (`6ba60ca`) an Desktops eingebautes
  `visualize` — nicht weiter ohne Desktop-Messung an der Beschreibung drehen; Codex' sieben
  Fälle gesammelt auswerten. Notiert: 12–19 KB Text ans Modell (SVG inline im Payload-JSON).
- [ ] generate_tlc — Serverseite fertig `90cfd7b` (+ Exportknopf `d6098a9`); offen:
  Desktop-Handtest ausgeführt, Toolwahl rot (`0c36b4b`); Host/README `2c9a71a`. Behoben: sieben deutsche Fehlermeldungen; erster Zaun überhaupt
  (⇄ generate_reaction, → generate_spectrum), 3 Routingfälle (vorher 0). Notiert: eng
  benachbarte Flecken (0,50/0,52) überdecken ihre Rf-Beschriftung; 8–16 KB Modelltext.
- [ ] generate_titration_curve + generate_species_distribution — Serverseite fertig `6093b88`
  (+ Exportknopf PlotView `d6098a9`); Host/README `5eb9c43`, Desktop 0/4 (`a6d6e86`). Offen: Toollisten-Diskrepanz (oben); Pufferpunkte behoben `a08e3cb`. Behoben: absteigende
  pKa ([7.2, 2.1]) still gezeichnet (Pufferpunkte neben der Kurve, HA⁻ verschwand) → Fehler;
  Fehlertexte englisch. Eigene MVP-Auswahltexte ohne calculate_ph/calculate_content/
  generate_dose_response. Notiert: 17–24 KB Modelltext (Phosphorsäure); `notes` leer — das
  Modell sieht EP-Volumen/-pH nur im Bild.
- Stand Standardprofil nach Welle 2: 15 Tools, 12 Panels (Handshake grün). Randnotiz:
  generate_molecule-Auswahltext bei 2010 B — der nächste Zaun dort braucht Kürzung.
- [ ] calculate_ph — **Ausnahme** vom „Rechnen später": pH/Puffer ist Grundstudium.
  **Jay (31.10.2026):** ja, Welle 2. Serverseite fertig `71223ed` (Text-Tool, kein Panel; Zäune
  beidseitig zu Titrationskurve/Speziesverteilung, Standardprofil 16 Tools / 12 Panels).
  Offen: Desktop-Handtest + Host-Fälle/README (Codex).

### Welle 3 — Vertiefung (später)
- [ ] calculate_solution
- [ ] calculate_content
- [ ] calculate_pharmacokinetics
- [ ] generate_pk_curve
- [ ] generate_dose_response
- [ ] generate_calibration_curve
- [ ] generate_scope_table (36,7 KB Modelltext vorher verschlanken)
- [ ] generate_mechanism aus Nutzersubstraten: echte Mechanismen statt Lehrbuch-Galerie

### README hochwertig (nach Welle 2)
- [ ] Je Bereich (Zeichnen · Laborgrafik · Nachschlagen · Rechnen · Anki) ein echtes Bild aus
  einem echten Aufruf; heutiges „Full-profile feature reference" und „Profiles" auflösen.
- [ ] Installationsweg Desktop-Extension (`.mcpb`) zuerst, `install.sh`/PyPI danach.
- [ ] Werkzeugtabelle: Tool · Bereich · Beispiel-Prompt · Panel ja/nein.
- [ ] Danach Shorts: `plans/vermarktung.md` § „Shorts je Workflow" (Jay 26.10.) — dort weiter.

> Fokusentscheidung 14.10.2026: erst den allgemeinen Chemie-Kern stabilisieren.
> MVP als Standard: Einzelstrukturen, Batch, Vergleich, Reaktionsschema; Datenblatt
> und PNG-Export als Unterstützung (6 Tools). `CHEMDRAW_PROFILE=full` schaltet den
> erhaltenen Vollumfang wieder zu. Die Ausbauphasen unten bleiben dokumentiert,
> sind aber bis zur Abnahme des Kerns zurückgestellt. Keine weitere Fachvertiefung,
> Quiz-/Trainer- oder Bezahlfunktionen in dieser Etappe.
>
> Umgesetzt 14.10.: Profilumschaltung und passende Tooltexte, getrennte Tests für
> MVP und Vollbestand, profilabhängige Routing-Evals. Gate: 6.953 Python-Tests,
> 37 Frontendtests grün; Host-Test grün. Lokale Bundle-Installation aus dem
> aktuellen Wheel aktualisiert, Desktop neu gestartet; echter Extension-Start:
> 6 Tools / 5 Panels, installiertes Vollprofil: 23 Tools. Noch kein neuer öffentlicher
> Release. Sichtbarer Abnahmeschritt: neuer Desktop-Chat → „Nutze den ChemDraw-MCP:
> zeichne Koffein“ → Data → PNG-Export. Die Fehler aus
> `docs/projektpruefung-2026-10-14.md` sind damit noch nicht behoben.
>
> Unabhängig nachgeprüft 14.10. nach Claudes Kernpflege (`e17eb61`, `243b1e5`):
> Gate 6.958 Python / 37 Frontend grün, Host grün, Identität 22 grün / 2 gelb.
> Nullwerte korrigiert; PubChem-URL-Umstellung ist eine Bereinigung (alte Aliase
> antworten live weiterhin mit 200). Lokales Desktop-Wheel anschließend aus dem
> geprüften Repo aktualisiert, isoliert auf Codegleichheit und Nullwerte geprüft;
> Desktop neu gestartet. Einzelheiten und Grenzen im Prüfbericht.

> Zusammengelegt 08.10.2026 aus `plans/archiv/panel-ausbau.md` (03.10.) und dem MCP-Teil von
> den privaten Produktplan (`leben/plans/chemdraw-produkt.md`) (02.10.). Frühere, abgeschlossene Etappen: `plans/archiv/repo-level-up.md`
> (14.08.), `routing-und-umschalter.md` (15.08.), `studi-funktionen.md` (15.08.).
> Gate je Schritt: `./test.sh` grün · `npm --prefix chemdraw_tool/ui run test:host` · `./scripts/handshake.sh`.
> Vor Panel-/Manifestarbeit: `uv run python scripts/anthropic_sync.py --check` (CLAUDE.md).

## Etappen
- [ ] **Geparkt (Chef 31.10.2026: nicht löschen):** von der README (`65800df`) nicht mehr verwendete Assets —
  `assets/titration-phosphoric.png`, `species-phosphoric.png`, `ethyl-acetate-ir.png`, `tlc-esterification.png`,
  `mechanism-overview.png`, `demo-mechanism.gif`, `demo-3d.gif`. Vor einem Löschen `grep` in `docs/` und `~/Documents/projects/chemdraw-vermarktung/`.

### Etappe 14.10.2026: vorhandene MVP-Oberfläche autonom verbessern

- [x] Molekül- und Datenblattlayout lesbar, schmal gestapelt, breit mit eigener
  Informationsspalte; klare Exportbeschriftung, Hostschrift und Hosttheme.
- [x] Funktionelle Gruppen per Tastatur bedienbar; Molekülwechsel verwirft das
  fremde Datenblatt. Drei neue DOM-Regressionen zuerst rot, dann grün.
- [x] Unabhängige Abnahme: `./test.sh` mit 6.958 Python- und 40 Frontendtests grün;
  `test:host` prüft Struktur und Datenblatt hell/dunkel bei 360/980 px sowie
  explizite Host-Themes. Default-Pixelreferenz unverändert.
- [x] Lokales Wheel installiert und Bundle-Codegleichheit geprüft; Desktop
  neu gestartet; neuer Chat `132254e1-49e3-41b1-8bba-5f79198cae7e` zeigt Koffein,
  HBD 0 und Datenblatt mit CAS 58-08-2/CID 2519. Exportknopf bestätigt
  `~/ChemDraw-Output/png/Koffein-2.png`; Bild pixelgleich zur Ausgangsabnahme.
- [x] Automatische DOM-Schleife `test:ui:watch` ergänzt; Entwickleroptionen,
  Logs und Prüfschichten in `docs/ui-pruefung.md` dokumentiert. DevTools nicht
  ungefragt aktiviert. Layoutbelege: `docs/produkt/panel-mvp/`.
- [x] Anschließend auf Jays ausdrücklichen Auftrag DevTools aktiviert; neuer
  Entwickler-Menüpunkt und geöffnetes DevTools-Fenster mit Console/Network selbst
  sichtbar geprüft. Die Konfiguration liegt lokal außerhalb des Repositories.

- [ ] **Routing-Befund MVP (Claude, 14.10., `run_claude.py`, 11/13 grün):** zwei Fälle
  3 von 3 stabil rot — `lookup-data-sheet` ruft nach `lookup_molecule_data` zusätzlich
  das verbotene `generate_molecule`; `explain-why-acidic` („Warum ist Acetylsalicylsäure
  sauer?“) landet bei `generate_reaction` statt `generate_molecule`. Betrifft
  `_MVP_SUMMARIES`/Instructions; erst nach dem mcp-2-Branch angehen (Konfliktgefahr).
  **19.10.:** `explain-why-acidic` grün (Eigenschaftsfrage zu einem Stoff → generate_molecule,
  Zaun in generate_reaction); Gesamtlauf 12/13. `lookup-data-sheet` blieb nach drei
  Formulierungen (Summary beider Tools + Instructions) rot und ist zurückgenommen.
  Vermutung: Die Attrappe in `stub_server.py` liefert kein Datenblatt, also zeichnet das Modell
  nach. Prüfen mit einem Stub, der echten Datenblatt-Text zurückgibt.
- [x] **mcp-2.x-Migration** (14.10., `c0dd24d` auf main): `MCPServer`, `version=` im
  Konstruktor, `ValueError` → `ToolError` (Resolver-Meldungen kommen lesbar an, Test neu).
  Lokal nachgeprüft nach Rebase: Gate 6.964 grün, `test:host` grün, Routing 11/13 wie vorher,
  Handshake 6/5. Lief NICHT in der Cloud: `isolation: remote` fiel still auf einen lokalen
  Worktree zurück. Offen: Desktop-Wheel neu installieren + Smoke-Test; Entscheidung, ob
  auch andere Fehler (z. B. `OSError` beim Schreiben) als Klartext durchgereicht werden.
- [ ] Desktop-Entwicklermenü „MCP-Konfiguration neu laden“ ersetzt per AppleScript einen
  von zwei laufenden Serverprozessen (57152 → 63588, 57194 blieb). Vor einem Reload-Skript
  klären, welcher Prozess einen neuen Chat bedient.
- [x] SMILES-Dateinamen-Kollisionen behoben (20.10., `20c204f`): Großschreibung und
  Stereopunktuation bleiben durch einen stabilen Fingerabdruck unterscheidbar, für
  Einzel- und Batch-Export in PNG/SVG/CDXML. Zwölf Regressionen erst rot, dann grün;
  Gate 6.976 bestanden / 16 übersprungen. Explizit gleiche Labels bleiben überschreibbar.
- [ ] Offen aus der Kernanalyse: NCI CIR antwortet live
  mit 500 auf deutsche Namen (Methylphenidat, Salicylsäure) → Kandidat Wikidata-Stufe;
  ACS-1996-Stil nur nach Designrunde.

Noch offen bleibt die persönliche Gestaltungsrückmeldung von Jay; weitere
Panelmodi und Fachfunktionen sind damit nicht freigegeben.

### Etappe 03.10.2026: Panel-Ausbau — Ansichten, Animation, Abfrage- und Prüfungsmodus

Ziel: Das Moleküle-Panel wird vom Bild zum Lernwerkzeug. **Eine** Molekülanfrage liefert alle Ansichten, man schaltet sofort um, wird durch die Optionen geführt, und kann sich selbst abfragen.

Stand 08.10.: außer M0 und der Recherche W-1c ist nichts davon gebaut (geprüft: keine `readOnlyHint`, kein `svg_stereo`, kein `mode="quiz"`, kein Bundle-Budget-Test im Code).

#### Wow-Moment zuerst (Fokusänderung 03.10. abends — gilt vor den Phasen unten)
Jay: erst das Layout im Chat, Ansichten ohne Nachfragen umschaltbar, **allgemein** für alle, die es auf GitHub ausprobieren (Chemie, Pharmazie, Biologie). Liste aller Möglichkeiten: `docs/produkt/panel-moeglichkeiten.md`.

- [ ] **M3** alle 23 Werkzeuge mit `title` und `readOnlyHint` annotieren (Snapshot-Tests mit freigeben) — fehlt: `docs/anthropic/abgleich.md:27` „✗ 0 von 23"
- [ ] **M2** Größen der Panel-Ergebnisse messen (Grenze ~150.000 Zeichen, sonst lädt das Panel nicht), Großes nachladen
- [ ] **M7** Manifest: Icon (512 px), `privacy_policies`, Windows testen oder ausschließen; **M8** README: Organisationen können Extensions sperren — fehlt: `abgleich.md:35-36`
- [ ] W-1 Nativer Look: Host-Farben/-Schrift (`--color-*`, `--font-sans`) statt eigener Tokens, Skelett statt Spinner, Tippflächen ≥ 44 pt (Baustein 13)
- [ ] W-1b Quiz-Satz in den `instructions` + Eval-Fall (Baustein 14)
- [ ] W0 Host-Messung: Zeile im Panel „Claude Desktop · Vollbild · Nachricht · Download …" (1 h) — entscheidet über W4, Phasen 5, 6
- [ ] W1 Reiter **Struktur · Stereo · 3D · Daten** von Anfang an (= Phase 1 unten)
- [ ] W2 3D dreht sich von selbst, weicher Wechsel (Teil von Phase 4 vorgezogen)
- [ ] W3 **Browser-Demo ohne Installation**, Link ganz oben im README (Hebel für Sterne)
- [ ] W4 je nach W0: Atom anklicken → Claude erklärt · Vollbild + Download · Folge-Vorschläge
- [ ] W5 README neu aufbauen um den Wow-Moment (GIF der Reiter, Demo-Link) — erst nach W1–W3, sonst verspricht es Ungebautes
- [ ] W6 danach: Blind-Modus, Prüfmodus (Phasen 5–6), Biologie-Paket, Wirkstoffklassen-Galerie
- [x] **M0** `ext-apps` 2.0.3 migriert (ac13350, 1bacd64): keine Codeänderung im Panel, Bundle 524 → 399 kB, Gate/Host-Test/Handshake grün; MCP-Fassung 2026-07-28 gelesen, nichts zu tun (`docs/anthropic/abgleich.md` §1)
- [x] W-1c Recherche: Anthropic-Verzeichnis, geht ein lokaler Server? (bcf3286, `docs/anthropic/abgleich.md:38-50`: lokal nicht als Connector einreichbar, .mcpb nicht mehr angenommen, Weg wäre Plugin-Bundle)

#### Phase 0 — Grundlage und zwei Versuche (ca. 1 Stunde)
- [ ] Ausgangsbilder: `tests/gallery_ui.py` als Vorher-Stand ablegen (`docs/produkt/panel-vorher/`)
- [ ] Versuch 1: Kann das Panel dem Chat eine Nachricht schicken (`ui/message` der AppBridge)? Im Host-Test prüfen, dann **einmal in Desktop von Hand** — davon hängt D (Folge-Vorschläge) ab
- [ ] Versuch 2: Panelhöhe in Desktop messen (wie viel Platz bleibt unter dem Chat-Text?) — davon hängt das Layout in C ab
- [ ] Bundle-Budget als Test: `dist/index.html` ≤ 650 kB, rot sonst

#### Phase 1 — Ansichtsumschalter (A) → Release 0.5.0
- [ ] Payload: `MoleculePayload` bekommt `svg_stereo` und `mol3d` (Atome/Bindungen), nur wenn nicht zu groß (Obergrenze Atomzahl, sonst leer + Hinweis)
- [ ] Panel: Reiter **Struktur · Stereo · 3D · Daten**; 3D-Ansicht als wiederverwendbare Komponente (aus `Molecule3DView` herausgelöst, gleiche Drehung)
- [ ] Tests: Host-Test klickt durch alle vier Reiter; Komponententest je Ansicht; Payload-Parität (Python ⇄ App.jsx)
- [ ] **Jay:** 10-Sekunden-Test: „Zeichne Ibuprofen" → Stereo klicken (R/S sichtbar) → 3D klicken (dreht sich) → Data

#### Phase 2 — Seitenpanel und Layout (C) → 0.5.1
- [ ] Gestaltungsgrundsätze in `styles.css` als Tokens (Abstände, Schriftgrößen, Kartenstil), nicht pro View
- [ ] Steckbrief: einklappbare Abschnitte, klarere Hierarchie, Kopierknöpfe einheitlich
- [ ] Schmal/breit: Seitenleiste wird unter 560 px ein Block unter dem Bild
- [ ] Hell/dunkel prüfen; Galerie vorher/nachher nebeneinander ansehen

#### Phase 3 — Geführte Optionen (D) → 0.6.0
- [ ] Optionsleiste: Stil (kompakt / Präsentation / Graustufen), Stereo-Beschriftung, Gruppen abkürzen — Änderung ruft das Werkzeug erneut auf (`callServerTool`), Ergebnis ersetzt das Bild
- [ ] Folge-Vorschläge unter der Struktur („Mechanismus", „Vergleichen mit …", „Karteikarte") — **nur wenn Phase-0-Versuch 1 klappt**, sonst als kopierbarer Prompt
- [ ] Eval: Tool-Wahl-Fälle unverändert grün (28/28 Basis), Beschreibungen nicht länger

#### Phase 4 — Animationen (B) → 0.6.1
- [ ] 3D: Dauerdrehung mit Pause/Weiter, stoppt bei Ziehen, respektiert `prefers-reduced-motion`, pausiert, wenn das Panel nicht sichtbar ist
- [ ] Weiche Übergänge beim Ansichtswechsel (kurz, abschaltbar)
- [ ] Mechanismus: Schritte automatisch durchlaufen (Schleife, Tempo einstellbar)
- [ ] Messung: Bildrate bei 50 Atomen ≥ 30 fps, sonst automatisch weniger Details

#### Phase 5 — Abfragemodus (E) → 0.7.0
- [ ] `mode="quiz"` im Werkzeug; Panel zeigt die Struktur mit abgedeckten funktionellen Gruppen
- [ ] Klick deckt auf; „Wusste ich / Wusste ich nicht" pro Gruppe; Zähler
- [ ] Varianten: Name verdecken, Gruppen verdecken, nur Gerüst zeigen
- [ ] Tests: Abdeckung deckt genau die Atome der Gruppe; Aufdecken ist umkehrbar; Zustand nur im Panel (kein Server)

##### Entwurf „Prüfungsfragen OC-Grundlagen“ (26.10.2026, nur Entwurf — Jay gibt je Etappe frei)
**Pausiert (Jay 26.10. 23:55): zuerst die Shorts sauber, je Workflow ein Short (plans/vermarktung.md § Shorts je Workflow).**
Rahmen: Jay 26.10. OC-Grundlagen zuerst (funktionelle Gruppen, Isomerie, R/S, Reaktionstypen); MVP bleibt 7 Tools →
Parameter oder Panel-Knopf, kein achtes Tool. Ausgangspunkt ist Modus E (verdecken, aufdecken).

Was schon da ist (Bestand 26.10.):
- `MoleculePayload.functionalGroups` (`name`, `atomIndices`, `count`; SMARTS-Liste in `svg_renderer._FUNCTIONAL_GROUPS`
  plus „Aromat“, Namen deutsch; gemessen: Aspirin → Carbonsäure, Ester, Aromat) + `atoms` (`AtomData` idx/x/y) → genau das, was Abdecken braucht; `StructureCanvas` hebt
  per `groups`/`highlightAtoms` schon Atomlisten hervor, `FunctionalGroupList` listet sie.
- Isomerie: `AmbiguousPayload.candidates` (Isomer-Auswahl, 0a1d29a) und `stereo_variants` (max. 3 Stereoisomere als
  Auswahl) liefern fertige Antwortmengen für „welches Isomer ist das?“.
- R/S: `stereoWarnings` kennt nur **offene** Zentren; CIP-Labels der bestimmten Zentren stehen nur in der Zeichnung
  (`annotate_stereo`), **nicht** als Daten im Payload → für R/S-Fragen fehlt ein Feld (z. B. `AtomData.cip`).
- Reaktionstypen: `ReactionPayload` + `balance`; kein Typ-Etikett (Substitution/Addition/…) vorhanden.
- Abfrage-Ausgang: `export_anki_deck` + `curated_decks` (2 Decks, `VERIFIED_STRUCTURES` mit Formel-Gate) →
  „Falsch beantwortet → Karteikarten“ ohne neuen Server-Weg; `AddToAnkiButton` im Panel.

Bauvarianten:
- **A (Empfehlung) — Panel-Knopf „Quiz“ am Molekül-Panel, kein neuer Parameter.** Jede `generate_molecule`-Antwort
  kann abgefragt werden: Klick „Quiz“ deckt alle `functionalGroups` ab (graue Flächen über `atomIndices`), Klick auf eine
  Fläche → Auswahl aus 3–4 Gruppennamen (Distraktoren aus der SMARTS-Liste), dann Aufdecken. Zustand nur im Panel.
  Vorteil: null Änderung an Tool-Text/Snapshots/Evals, Daten liegen schon im Payload, sofort für jedes Molekül.
  Nachteil: Lernender muss erst „Zeichne X“ sagen; keine Fragenfolge.
- **B — Parameter `mode="quiz"` an `generate_molecule`** (wie Phase 5 geplant): Modell kann „frag mich Aspirin ab“
  direkt ins Quiz schicken, Panel startet abgedeckt. Kostet: Beschreibungsänderung (Snapshot neu segnen,
  Eval-Fall für „frag mich ab“ vs. „zeichne“), Routing-Risiko gegen `export_anki_deck`.
- **C — Fragenbestand als Datendatei + `curated_deck_id`-artiger Schlüssel** (`oc-grundlagen-1`: 15–20 geprüfte
  Lehrbuchmoleküle je Thema, Formel-Gate wie `VERIFIED_STRUCTURES`), abgespielt über `batch_generate` oder A/B.
  Eigentliche Fragenfolge (= Phase F). Groß; erst sinnvoll, wenn A sich im Gebrauch bewährt.
Reihenfolge: **A → (B, nur wenn Jay „frag mich ab“ im Chat will) → C**. Themen in A-Reihenfolge: funktionelle Gruppen
(Daten da) → Isomerie (Kandidaten da) → R/S (braucht `cip`-Feld) → Reaktionstypen (braucht Typ-Etikett, zuletzt).

**Voraussetzung A0 (Inhaltsfehler, vor jedem Quiz):** `extract_functional_groups` meldet bei Paracetamol
`['Amid', 'Sek. Amin', 'Phenol', 'Aromat']` — der Amid-Stickstoff zählt zusätzlich als sekundäres Amin. Im Panel ein
Schönheitsfehler, im Quiz falscher Lernstoff. Fix: Amin-SMARTS ohne Carbonyl-Nachbar (`[NX3H1;!$(NC=O)]…`), Test mit
Paracetamol/Lidocain zuerst rot; Golden-SVGs prüfen (Gruppen färben nur im Panel, Export vermutlich unberührt).

Erste prüfbare Etappe (A1, Vorschlag): Knopf „Quiz“ im Molekül-Panel, deckt alle funktionellen Gruppen ab, Klick deckt
eine auf (noch ohne Antwortauswahl), „Alle zeigen“ setzt zurück.
- Tests zuerst: Komponententest „Abdeckung = genau die `atomIndices` der Gruppe“, „Aufdecken umkehrbar“, Molekül ohne
  Gruppen → Knopf fehlt; `test:host` klickt Quiz bei Aspirin (3 Gruppen) durch. Bundle-Budget bleibt ≤ 650 kB.
- Kein Python-Code, kein Tool-Text, keine Golden-SVG berührt → Gate + Host-Test + Codex-Desktop-Test.
- 10-Sekunden-Test: „Zeichne Aspirin“ → Quiz → drei graue Flächen → eine anklicken → „Ester“ erscheint.
- [ ] **Jay:** Freigabe A1 (oder Variante B/C zuerst)?

#### Phase 6 — Prüfungsmodus (F) → 0.7.1
- [ ] Fragenfolge (N Strukturen), Fragetypen: Gruppen benennen, Name zur Struktur wählen, Stereozentren zählen/bestimmen (R/S)
- [ ] Kein Hinweis während der Prüfung, Auswertung nach Bereich (wie der Klausurmodus im Rechner)
- [ ] Fehler → Anki-Deck mit den falsch beantworteten Strukturen
- [ ] Optional: Zeitlimit

#### Offene Fragen an Jay
- [x] **Jay:** Welche Fachrichtung für die Prüfungsfragen zuerst: **Pharmazeutische Chemie** (Strukturen, funktionelle Gruppen) oder **Pharmakologie** (Wirkstoffklassen)? Empfehlung: Pharmazeutische Chemie — die Daten dafür gibt es schon.
  - **Jay 26.10.2026: OC-Grundlagen zuerst** (funktionelle Gruppen, Isomerie, R/S, Reaktionstypen) — breiteste Zielgruppe (Chemie, Bio, Medizin, Pharmazie, Schule), passt zu „Grundlagen zuerst“. Pharmazeutische Chemie danach als Aufbau, Pharmakologie zuletzt.
- [ ] **Jay:** Soll der Abfragemodus auch **Reaktionen/Mechanismen** abdecken (Edukte verdecken)? Empfehlung: erst Moleküle, Reaktionen als Phase 7.

#### Grundlagen der Etappe (unverändert vom 03.10.)

| # | Gedanke | Kern | Baut auf |
|---|---|---|---|
| A | Zwischen Ansichten umschalten (Stereo, 3D, …) | ein Payload, mehrere Ansichten, Umschalter im Kopf | — |
| B | Animationen, auch zum Schleifen | 3D-Dauerdrehung, weiche Übergänge, Mechanismus-Autoplay | A |
| C | Seitenpanel feiner und sauberer | Layout-Grundsätze statt Einzelfall-Styles | A |
| D | Durch die Tool-Optionen geführt werden | Optionsleiste (Stil, Stereo-Labels, Abkürzungen) + Folge-Vorschläge | A, C |
| E | Abfragemodus (Teile verdecken, aufdecken) | Funktionelle Gruppen/Atome abdecken, Klick deckt auf | A, C |
| F | Prüfungsmodus | feste Fragenfolge, kein Hinweis, Auswertung, Fehler → Anki | E |

Reihenfolge der Phasen: **A → C → D → B → E → F.**

Messungen (03.10.): 3D-Erzeugung kostet 10–30 ms je Molekül → alle Ansichten kommen gleich im Payload mit, nur das Datenblatt (PubChem, ~2 s) lädt beim Klick. Das Panel kennt schon `functionalGroups` mit `atomIndices` und `AtomData` mit x/y. 3D bleibt SVG-Drehlogik, kein WebGL. Bundle heute **399 kB** (nach M0, CHANGELOG.md:14; am 03.10. noch 524 kB); Budget für den ganzen Ausbau **≤ 650 kB**.

Entscheidungen (Jay kann widersprechen): 1. Ansichten mitliefern, nicht nachladen. 2. Stereo-Ansicht = dieselbe Struktur mit CIP-Beschriftung, `annotate_stereo` bleibt. 3. Abfrage- und Prüfungsmodus sind Panel-Modi über ein Argument `mode`, keine neuen Werkzeuge. 4. Fehler aus dem Prüfungsmodus gehen als Anki-Deck raus (`export_anki_deck`).

Für jede Phase: Tests zuerst und einmal rot gesehen · `./test.sh` grün · Host-Test und Galerie angesehen · CHANGELOG · README-Bild aktualisieren, wenn sich das Aussehen ändert · Release erst nach Jays Go.

### Etappe 02.10.2026: MCP verfeinern und Releases 0.4.3–0.4.8 (aus den privaten Produktplan (`leben/plans/chemdraw-produkt.md`))

- [ ] **Jay:** einmal von Hand in Desktop „Zeig mir Methylphenidat" → Data (nur noch Host-Eigenheiten, die der Nachbau `test:host` nicht kennt)
- [ ] `mcp-2-migration` (Worktree `.claude/worktrees/agent-a567114bbee585cc8`, Branch-Stand 836324b vom 02.10.): GEPARKT bis zum Desktop-Test. Die Vorbedingung „erst nach dem OPSIN-Merge" ist erfüllt (022507d); der Branch liegt jetzt 41 Commits hinter main → erneut mit main abgleichen (CHANGELOG-Konflikt), Gate + Handshake, dann mergen. Nicht nebenbei anfassen.
  - Zusätzlich liegt auf GitHub `mcp-2-migration-v2` (dd932f6 vom 14.10., Stand 30.10. 118 Commits hinter main): ein einzelner Commit „build: Server auf mcp 2.x (MCPServer) umgestellt, mcp>=2.3,<3“ direkt auf main d830726 — also eine Neuauflage der Umstellung auf frischem main statt Merge des alten Branches. Vor dem Abgleich entscheiden, welcher der beiden die Grundlage wird; der andere wird danach gelöscht.
- [ ] Hinweis in `_INSTRUCTIONS`/README: Desktop nimmt die Sandbox, wenn man den MCP nicht nennt — prüfen, ob ein Satz in `instructions` das ändert (nur in Desktop messbar). Fehlt: `chemdraw_tool/server.py:205-240` enthält keinen solchen Satz
- [ ] Geschwindigkeit (zurückgestellt): Server-Import 1,4 s (mcp 0,33 · rdkit 0,25 · matplotlib 0,25) — nur lazy laden, wenn die Handshake-Zeit unter Last wehtut; Datenblatt-Ladezeit 2,3 s (PubChem) — Vorabladen nur, falls Jay es spürt
- [~] Option: Server-Import ohne RDKit/matplotlib — gestrichen 08.10.2026, weil Dublette des Geschwindigkeits-Hakens darüber
- [x] 0.4.6 veröffentlichen: PyPI, `.mcpb`, bei Jay installiert (v0.4.6 GitHub-Release 03.10., 20ff181; PyPI steht inzwischen auf 0.4.8; `dist/chemdraw-mcp-0.4.8.mcpb`; Desktop-Test 03.10. mit 0.4.7 verbunden)
- [x] **Jay:** `gh release create v0.4.6` (`gh release list`: v0.4.6 am 2026-10-03)
- [x] Run.sh-Sperre verwaist bei abgebrochener Installation: trap auf TERM/INT/HUP, PID-Datei, tote PID sofort übernehmen (Release 0.4.6, 20ff181)
- [x] Bundle-Startfix: feste Installation statt `uv tool run` (adaed6c)
- [x] Release 0.4.3 (Titer, Daten-Knopf, Bundle-Start + Sperre) und 0.4.4 (Index-Refresh im Bundle), 02.10.
- [x] OPSIN gemergt (022507d), 0.4.5 veröffentlicht (3681f7b) und bei Jay installiert (Desktop verbunden 21:36, 20 Tools)
- [x] Data-Knopf Methylphenidat automatisiert: `npm --prefix chemdraw_tool/ui run test:host` (AppBridge-Host + echter Server, 02.10.). Computer use auf die Claude-Desktop-App selbst ist gesperrt
- [x] Messung: `evals/tool-routing/run_claude.py` (Tool-Wahl über claude -p, Attrappen-Server) — 24/28 → 26/28
- [x] `lookup_molecule_data`: 6–8 Folgeaufrufe → 4 bei „Datenblatt mit allem" (237698f)
- [x] `test:host` schreibt nicht mehr ins echte `~/ChemDraw-Output` (9a3b8d6)
- [x] Entschieden (02.10.): `reaction-in-conversation` — Reaktion + Mechanismus ist gute Antwort, `forbidden` nur noch generate_molecule; `draw-scope-real` mit Strukturen im Prompt. Eval 28/28 in drei Wiederholungen (0e39eb0)
- [x] Dateipfade im Panel mit `~` gekürzt (6 Views), Tooltip hat den vollen Pfad (6c9b308)
- [x] Design-Galerie: `uv run python tests/gallery_ui.py` → <Temp-Ordner chem-gallery-*>/sheet.png (13 Panel-Typen nebeneinander) (6c9b308)
- [x] Speziesverteilung: Legende neben der Achse (6763642, Test rot gesehen)
- [x] Geprüft, kein Fehler: Kalibrierkurve-Titel doppelt (der Titel im Bild gehört in die exportierten Dateien); Reaktion ohne Titel (Edukte/Produkte/Bedingungen sind beschriftet)
- [x] Mechanismus-Overview: gleiche Bindungslänge, Spalte statt Zeile, SN2-TS mit Platz für Teilbindungen (1bfedb2, Release 0.4.7)
- [x] Desktop-Test 03.10.: 0.4.7 verbunden, `generate_pk_curve` kam an, Zahlen stimmen (Css,av 4,74 mg/L, R 1,43). Desktop lädt MCP-Tools erst nach und nimmt sonst die Sandbox — Prompt mit „Nutze den ChemDraw-MCP" wirkt
- [x] Dateinamen von `generate_pk_curve`/`generate_dose_response` tragen ohne `drug` die Parameter (64a0cb8)
- [x] (0.4.8) Gleiches Überschreiben bei TLC, Scope, Kalibrierkurve, Reaktion ohne Titel und bei Titration — Dateiname aus den Eingaben ableiten, je mit Test (5c77bc5)
