# Verifizierter Stand — Auftrag (Jay 07.11.2026)

Jay: „Wir brauchen jetzt einmal einen verifizierten Stand, also eine wirkliche Wahrheit, und
dass die ganzen Kommunikationslücken und Fehler, die entstanden sind, jetzt einmal bereinigt
werden." Owner dieser Bereinigung ist die Claude-Owner-Session; sie nimmt jeden Bericht
nur mit Beweis ab (Screenshot gesehen, Test selbst gelaufen, Commit selbst gelesen).

Was schiefging (Stand vor der Bereinigung):

- Drei Agenten (Chef/Opus/Codex) schrieben `plans/mcp-server.md` in 89 von 203 Commits um
  (1319 Zeilen, 26 gestapelte „Weiter bei"-Blöcke); die jüngste Zeile gewann, auch wenn sie
  falsch war — z. B. „Stereo-Klick erst nach W1", obwohl der Stereo-Picker seit 0.6.0
  existiert (`fd709cc`).
- CI war stundenlang rot (Lint in `scripts/notebooklm/bundle.py`, „Eigentümer unklar"),
  behoben `b708dd3`.
- `test:host` lief seit den 0.8.0-Änderungen (Namens-Titel, Schrittzahlen, Glucose-Auflösung
  `41da7c4`) nicht mehr durch; Erwartungen nachgezogen `cce71b0`/`feef949`. Hinweis zur
  Historie: die Nachricht von `cce71b0` nennt den aldehydo-D-glucose-Fall, der erst in
  `feef949` landete (bereits gepusht, nicht umgeschrieben).
- Codex konnte sich ohne `HERDR_PANE_ID` nicht neu starten und wartete auf den „Chef".
- Desktop-Handtests der Welle-1/2-Tools stehen als „offen" im Plan; keiner wurde seit den
  Server-Fixes mit Screenshot belegt.

## Arbeitsstrang A — Plan-Audit (Opus, frischer Agent, Skill `plan-pflegen`)

Gegenstand: `plans/mcp-server.md`, alles unterhalb des Abschnitts „Stand für Jay" bis
einschließlich „Etappen". Für **jeden** Haken `[ ]`/`[x]` dort:

- Urteil **erledigt / offen / nicht prüfbar** mit Beweis: Commit-Hash (`git show`), Testname
  (einmal selbst mit `uv run pytest <datei>::<test> -q` gelaufen) oder `datei:zeile`.
- Bekannt falsche oder veraltete Zeilen ausdrücklich korrigieren:
  „Stereo-Klick erst nach W1" (falsch, `fd709cc`); „CI rot laut Chef, Eigentümer unklar"
  (behoben `b708dd3`); der 16-mal wiederholte Absatz „Welle-3-Entscheid (Jay 06.11.,
  beantwortet)" (einmal behalten); die drei alten Rückfragen an Jay („10-Sekunden-Test" →
  wird durch Strang B beantwortet; „Freigabe A1" → Herkunft finden oder als veraltet
  markieren; „Methylphenidat → Data" → Plan hält es am 07.11. für erledigt, Beleg nennen).
- **Kein Haken „Desktop-Handtest" wird gesetzt** — die kommen ausschließlich aus Strang B.

Ergebnis (nichts committen, keinen Code anfassen):

1. `docs/evidence/verifizierter-stand-2026-11-07/plan-audit.md`: Tabelle Behauptung →
   Beweis → Urteil, dazu eine Liste „falsch im Plan → korrigiert".
2. `plans/mcp-server.md` neu gegliedert: „Stand für Jay" oben (unverändert lassen, nur
   Haken 4 ergänzen, wenn Strang B/C ihn liefert), dann Wellen 1–3, README, Etappen mit
   korrigierten Haken. Alle „Weiter bei"-Blöcke und der Orchestrierungs-Abschnitt wandern
   unverändert nach `plans/archiv/mcp-server-verlauf-2026-11.md` (mit Datum und Hinweis,
   dass Zeilen dort Behauptungen der jeweiligen Agenten sind).

## Arbeitsstrang B — Desktop-Handtest mit Screenshots (Codex)

Voraussetzung: Schwester-Repo `~/Documents/projects/chemdraw-vermarktung` mit
`scripts/ax-claude.sh`; Screenshots nach `/tmp/chemdraw-desktop-test/2026-11-07/verifiziert/`.

0. **Zuerst** Claude Desktop neu starten (`osascript -e 'quit app "Claude"' && sleep 2 &&
   open -a Claude`), dann `./scripts/handshake.sh` → muss **16 Tools / 12 Panels** melden.
   Ohne diese Zeile keinen Klick (Falle: veralteter Serverprozess). Ist ein Werkzeug in
   Desktop durch Rechte blockiert: Screenshot + melden, nicht umgehen (Rechte setzt Jay).
1. Neuer Chat, Konnektor chemdraw-tool. Prompt „Zeichne Ibuprofen" → Panel mit Struktur
   (Screenshot `01-ibuprofen.png`) → Knopf **Show variants** → 2 Isomere (`02-varianten.png`)
   → **(R)-Ibuprofen** wählen → Keilzeichnung (`03-r-ibuprofen.png`) → **Data** → CAS
   **51146-57-7** (`04-data.png`) → **Export PNG** → Datei in `~/ChemDraw-Output` (Pfad +
   `ls -la` im Bericht) → **Add to Anki** → Dialog/Datei (`05-anki.png`).
2. „Zeige den SN2-Mechanismus von 2-Brombutan mit Cyanid Schritt für Schritt" → Panel
   `generate_mechanism`, Titel „(R)-2-bromobutane + cyanide", Step by step 1/3 → 2/3
   (`06-sn2.png`).
3. „Zeig mir Koffein in 3D" → Werkzeug `generate_3d` (Chat-Weg, kein Panel-Knopf)
   (`07-3d.png`).
4. „Welche IR-Banden erwarte ich für Aspirin?" → `predict_spectrum`, Tabelle mit
   C=O ~1750 (`08-ir-vorhersage.png`).
5. „Zeichne ein schematisches IR-Spektrum von Aspirin" → **festhalten, welches Werkzeug
   Desktop wählt** (`generate_spectrum` oder Desktops eingebautes `visualize`) (`09-spektrum.png`).
6. „DC-Platte: Edukt Rf 0,3, Produkt Rf 0,6, Co-Spot beide" → `generate_tlc` Panel (`10-dc.png`).
7. „Titrationskurve 25 mL 0,1 M Essigsäure (pKs 4,76) mit 0,1 M NaOH" →
   `generate_titration_curve` Panel mit Äquivalenzpunkt (`11-titration.png`).
8. „Was ist der pH von 0,1 M Essigsäure, pKs 4,76?" → `calculate_ph`, Text **pH = 2.88**
   (`12-ph.png`).
9. „Schlag Ibuprofen nach" → `lookup`, PubChem-Tabelle CID 3672 (`13-lookup.png`).

Bericht als `tisch bericht` mit dem Block aus `tisch bericht-vorlage` — je Schritt:
aufgerufenes Werkzeug (Zeile „chemdraw-tool · <name>" in Desktop), Ergebnis, Screenshot-Pfad.
Abweichungen nicht glätten: Falsch gewähltes Werkzeug, leeres Panel, Fehlertext → so melden.

## Arbeitsstrang C — Owner (Claude)

1. `tisch faeden` → erledigte chemdraw-Fäden schließen; `tisch leases` → veraltete
   Codex-Reservierungen (`scripts/demo-video.sh`, `assets/demo-molecule.gif`) freigeben.
2. `test:host` gegen HEAD (`feef949`) → rc=0 als Beleg für Punkt 4.
3. Berichte abnehmen: **jeden Screenshot selbst ansehen** und mit der Erwartung vergleichen;
   mindestens 5 Beweiszeilen aus Strang A per `git show`/`pytest` stichprobenartig
   nachprüfen. Erst dann Haken setzen, committen, Fahrplan-Artifact unter derselben URL
   neu publizieren.
