# Desktop-Abnahme Etappe E: Mechanismen

Messlauf am 05.11.2026 ab 14:24 MEZ, Claude Desktop, Opus 5.5 Mittel.
Auftrag: `20261105-131815-etappe-e-mechanismen-vor` #6 (Hop 6/6).
Rückweg wegen vollem Faden: `20261105-142437-etappe-e-desktop-handtest`.
Nur diese Dokumentation wird geändert und committet, keine Produktänderungen.

## Identität und Ablauf

Vor Beginn Desktop vollständig per `osascript -e 'quit app "Claude"'` beendet,
danach `open -a Claude`. HEAD beim Neustart:
`f2c772933b81a725de602b3161247b5de1a569d3`, ein Plan-Nachtrag über dem beauftragten
`59eee39`. Repo-Konfiguration:

```json
{"command":"/opt/homebrew/bin/uv","args":["--directory","/Users/tom/Documents/projects/chemdraw-mcp","run","chemdraw-tool-server"]}
```

`pgrep -fl 'chemdraw-tool-server|chemdraw-mcp-bundle'` zeigt den Repo-Prozess
`.venv/bin/python3 .venv/bin/chemdraw-tool-server` (PID 37012) und keinen
Bundle-Prozess. Bundle-Einstellung `isEnabled: false`. Belege:
`/tmp/chemdraw-desktop-test/etappe-e/identity-before.json` und
`process-after-restart.txt`. Konfiguration und Bundle-Einstellung vorab gehasht.

Jeder neue Reaktionsfall beginnt in einem frischen Chat; nur die ausdrücklich
beauftragte SMILES-Wiederholung bleibt im SN2-Chat. Sichtbare Einmalfreigaben
werden einzeln gewählt. Alle Bilder sind echte Desktop-Screenshots;
kein Hosttest und keine gerenderte Ersatzdarstellung.

Belegordner für alle unten genannten Dateien:
`/tmp/chemdraw-desktop-test/etappe-e/`.

## Fall 1: chirales SN2

Prompt: „Zeig mir den SN2-Mechanismus von (R)-2-Brombutan mit Cyanid Schritt für Schritt“.

Chat: https://claude.ai/chat/502d8fb5-826f-4b57-bdb8-a37db0d24444

Tool `generate_mechanism`, Parameter:
`{"current_step":0,"reaction_type":"sn2","substrates":["(R)-2-bromobutane","cyanide"]}`.
Einmal erlaubt.

**Grün.** Titel `Nucleophilic Substitution (SN2) — (R)-2-bromobutane + cyanide`.
In der Schrittansicht drei Schritte. Übergangszustand in echten eckigen
Klammern mit ‡ oben rechts, zusätzlich Schrittlabel
`[Backside attack (transition state)]‡`. Beide roten Elektronenpfeile verlaufen
mit sichtbarem Abstand zu C-, C⁻- und Br⁻-Labels. Letzter Schritt
`Products, (S)`, mit `(S)` direkt neben dem Stereozentrum und ausgefülltem Keil.
Keine Summenformel im Titel.

Belege: `01-sn2-transition.png`, `01-sn2-product.png`, `01-sn2.txt`.

## Fall 2: dieselben Substrate als SMILES

Zusatz im selben Chat: „Wiederhole generate_mechanism mit exakt diesen SMILES als substrates: [\"C[C@@H](Br)CC\", \"[C-]#N\"], reaction_type \"sn2\"“.

Tool `generate_mechanism`, Parameter:
`{"current_step":0,"reaction_type":"sn2","substrates":["C[C@@H](Br)CC","[C-]#N"]}`.
Einmal erlaubt; die Freigabe zeigt exakt diese SMILES.

**Grün.** Neuer Panel-Titel erneut
`Nucleophilic Substitution (SN2) — (R)-2-bromobutane + cyanide`, weder rohe SMILES
noch `C₄H₉Br + CN⁻`. Übergangszustand und `Products, (S)` bleiben vorhanden.

Belege: `02-smiles-title.png`, `02-smiles-title.txt`, `02-smiles-permission.txt`.

## Fall 3: Fischer-Veresterung

Prompt: „Fischer-Veresterung von Propionsäure mit Ethanol als Mechanismus“.

Chat: https://claude.ai/chat/a2808d3f-3d6e-42bb-8d7e-97b57074145a

Tool `generate_mechanism`, Parameter:
`{"current_step":0,"reaction_type":"fischer_ester","substrates":["CCC(=O)O","CCO"]}`.
Einmal erlaubt. Titel: `Fischer esterification — propionic acid + ethanol`.

**Grün.** Alle sieben Schritte einzeln per Next geöffnet und gesichert:

1. Reactants
2. Protonation of the carbonyl group
3. Nucleophilic attack of the alcohol
4. Proton transfer to an OH group
5. Loss of water
6. Deprotonation (H⁺ regenerated)
7. Products

In Schritt 3 beginnt der rote Angriffspfeil oberhalb und mit Abstand zum `HO`-Label
und endet vor dem `C⁺`-Label. Er durchschneidet beide Labels nicht mehr.
Schritt 4 zeigt den Protontransfer als eigenen Schritt mit explizitem H und
Elektronenpfeilen. Schritt 5 zeigt die protonierte Abgangsgruppe `OH₂⁺` und
den Abgangspfeil. Produkte: Ethylpropanoat, Wasser und regeneriertes H⁺.
Die sieben Ansichten springen nicht in unterschiedliche Vergrößerungen;
C–C-Bindungslängen und Schriftgrößen bleiben visuell gleich. Translation und
Konformation wechseln passend zum Schritt. Das ist eine visuelle Prüfung,
keine Behauptung pixelgenau gleicher Bindungslängen.

Belege: `03-fischer-step1.png` bis `03-fischer-step7.png`,
`03-fischer.txt`, `03-fischer-permission.txt`. Ergänzend
`03-fischer-scale-comparison.png`: identischer Ausschnitt aus den sieben
Original-Screenshots, jeweils mit identischem Faktor verkleinert, zum Vergleich.

## Fall 4: SN1 mit Wasser

Prompt: „SN1 von tert-Butylchlorid mit Wasser“.

Chat: https://claude.ai/chat/db519c93-2a36-4ced-ad92-a793dcdd889d

Ursprüngliche Antwort ohne Tool und ohne ChemDraw-Panel. Beauftragter Zusatz
im selben Chat: „Nutze ChemDraw generate_mechanism“.

Danach Tool `generate_mechanism`, Parameter:
`{"current_step":0,"reaction_type":"sn1","substrates":["CC(C)(C)Cl","O"]}`.
Einmal erlaubt.

**Panel grün nach Zusatz; natürliches Routing ohne Tool.** Titel
`Nucleophilic Substitution (SN1) — tert-butyl chloride + water`, also der
erwartete englische Name in Kleinschreibung. Schritt 3/5 zeigt das tertiäre
Carbokation mit `C⁺` neben `Cl⁻`. Kein abgeschnittener Titel und keine
Überlappung in dieser Zwischenstufe.

Belege: `04-sn1-natural.png`, `04-sn1-natural.txt`, `04-sn1-permission.txt`,
`04-sn1-carbocation.png`, `04-sn1-panel.txt`.

## Fall 5: Diels-Alder

Prompt: „Mechanismus der Diels-Alder-Reaktion“.

Chat: https://claude.ai/chat/6810ca30-794f-4016-924c-8035f07667d1

Tool `generate_reaction`, Parameter aus der Einmalfreigabe:

```json
{"conditions":"Δ","conditions_below":"[4+2]-Cycloaddition","name":"Diels-Alder: Butadien + Methylacrylat","products":["COC(=O)C1CC=CCC1"],"reactants":["C=CC=C","C=CC(=O)OC"]}
```

Schema-Panel öffnet mit Titel `Diels-Alder: Butadien + Methylacrylat`,
Kennzeichnung `balanced`. Kein falscher SN1-/SN2-/Fischer-Mechanismus als
Diels-Alder ausgegeben. Diese Messung ist eine Routing-Stichprobe.

**Grün in dieser Stichprobe.** Die ursprüngliche Antwort nennt die Grenze
ausdrücklich und ohne Zusatzfrage: „Die Elektronenpfeile kann das Werkzeug nur
für SN1, SN2 und Fischer-Veresterung zeichnen, deshalb stehen sie unten als
Diagramm.“ Der Hinweis unterscheidet das Nettoschema vom Pfeilmechanismus.

Belege: `05-diels-alder.png`, `05-diels-alder.txt`,
`05-diels-alder-permission.txt`.

## Fall 6: Cyclohexyl-Ring bei SN2

Prompt: „SN2 von Cyclohexylbromid mit Iodid“.

Chat: https://claude.ai/chat/6ce4ed9f-927c-4586-9e62-7bfccd4844dd

Direkt Tool `generate_mechanism`, Parameter aus der Freigabe:
`{"current_step":0,"reaction_type":"sn2","substrates":["bromocyclohexane","I-"]}`.
Titel: `Nucleophilic Substitution (SN2) — bromocyclohexane + I-`.

**Zeichnung grün.** Die sichtbare Übersicht zeigt den Übergangszustand
in Klammern mit ‡. Der Ring ist ein regelmäßiges Sechseck, ohne `C`-Label
an den sechs Ringatomen. I⁻ und Br⁻ stehen außerhalb des Rings, die roten
Pfeile darunter. Kein gedehnter oder eingedrückter Ring.

Grenze des Belegs: Bei der Bedienung dieses letzten Panels liefen AX-Baum
und Screenshot zeitweise auseinander. AX meldete Step 2/3, der sichtbare
Screenshot weiterhin Overview. Bewertet wurde deshalb ausschließlich der
tatsächlich sichtbare Übergangszustand in der Übersicht. Kein Schluss aus
AX allein auf eine sichtbar funktionierende Schrittumschaltung dieses Falls.
Die übrigen Fälle hatten übereinstimmende Screenshots und AX-Zustände.
Beim Einmalfreigabe-Klick meldete die Automatisierung einen ungültigen Index;
bei der folgenden frischen Beobachtung war der Aufruf bereits ausgeführt
und das Panel geladen. Es wurde kein Immer-erlauben-Knopf gewählt.

Belege: `06-ring-overview.png` (maßgeblich), `06-ring.txt`.
`06-ring-transition.png` zeigt ebenfalls die Übersicht, obwohl AX zu diesem
Zeitpunkt die Schrittansicht meldete; der Dateiname beweist keinen Modus.

## Ergebnis und Rücksetzen

| Fall | Ergebnis der beauftragten Sichtprüfung |
|---|---|
| 1 SN2 mit Namen | Grün: Titel, Klammern/‡, freie Pfeile, Products (S) und Stereolabel |
| 2 SN2 mit SMILES | Grün: englische Stoffnamen statt Formel oder SMILES im Titel |
| 3 Fischer | Grün: sieben Schritte, Protontransfer, OH₂⁺, freie Angriffspfeile, visuell gleicher Maßstab |
| 4 SN1 | Panel grün nach beauftragtem Zusatz; ursprünglicher Prompt ohne Tool |
| 5 Diels-Alder | Grün in einer Stichprobe: generate_reaction und ungefragter Familienhinweis |
| 6 Cyclohexyl | Zeichnung in sichtbarer Übersicht grün; Schrittumschaltung wegen AX-/Bild-Widerspruch nicht abgenommen |

Keine neuen Produktänderungen. Die breite Desktop-Toolwahl bleibt Modellverhalten;
insbesondere ist der SN1-Zusatz kein Erfolg des ursprünglichen Prompts.
Die Sichtprüfung ist keine vollständige fachliche Validierung aller Mechanismen
und kein Häufigkeitsnachweis für Routing.

Beim letzten Chat blieb der Begleittext als laufend markiert. Der Versuch,
ihn über den sichtbaren Stop-Knopf zu beenden, scheiterte in der Automatisierung
mit `elementHasNoFrame`. Deshalb Desktop zum Abschluss erneut vollständig
beendet und gestartet, statt einen sauberen UI-Zustand aus AX allein abzuleiten.
Keine weiteren Prompts gesendet. Testchats bleiben als Belege erhalten.

`identity-after.json` belegt identische SHA-256-Werte der Entwickler-Konfiguration
und Bundle-Einstellung gegenüber dem Start (`config_unchanged: true`,
`bundle_unchanged: true`, `bundle_enabled: false`). Es wurde keine
dauerhafte Berechtigung gewählt. Der ungefragte Zeitzonen-Hinweis in einigen
Screenshots wurde nicht bestätigt und keine geplante Aufgabe geändert.

Abschließend bestätigt: Desktop auf `claude.ai/new` mit leerem Eingabefeld,
keine laufende Antwort im frischen Fenster (`final-state.txt` und
`final-state.png`). `process-final.txt` zeigt die zwei üblichen Repo-Instanzen
(Chat/Cowork), keine Bundle-Umgebung.

Für diesen reinen Handtest wurde das Gate nicht erneut ausgeführt; die vom
Auftrag genannten Gate-Zahlen sind Fremdbericht, keine eigene Abnahme.
Eigene Dokuprüfung: `git diff --cached --check` vor dem Commit.
