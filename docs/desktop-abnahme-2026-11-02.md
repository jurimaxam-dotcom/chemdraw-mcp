# Desktop-Abnahme 0.7.0 · 02.11.2026

Prüfstand: `b6c2c7401939eab3bee52102a2138e2e79744a42`; während der Abnahme HEAD `ef6166e` und `74c7794` (Plan- und Host-Teständerungen, Laufzeitcode gegenüber b6c2c74 unverändert). Nur Messung, keine Änderungen an Tool-Beschreibungen oder dauerhaften Berechtigungen.

**Ergebnis: Release-Abnahme nicht bestanden.** Alle 16 Tools sind im bereinigten Kontrollchat sichtbar. Von 16 vorgegebenen Routingfällen wählen 10 das erwartete Tool; 6 antworten ohne Tool. Alle 12 Panel-Tools rendern sichtbaren Inhalt ohne „Warte auf Daten…“, zwei davon zusätzlich ausdrücklich angefordert (compare_molecules und lookup_molecule_data). Das Vergleichspanel hat einen Kontrastfehler. PNG-Export und Anki-Übergabe funktionieren. Abschluss der Dokumentation am 03.11.2026.

## Vorprüfung

- Claude Desktop per `osascript -e 'quit app "Claude"' && sleep 2 && open -a Claude` neu gestartet. Desktop-Version laut Einstellungen: 4.4212.0.
- Konnektor `chemdraw-tool`: 12 interaktive und 4 weitere Tools sichtbar.
- Während der Vorprüfung wechselten calculate_ph, predict_spectrum und lookup von „Blockiert“ zu „Immer erlauben“, ohne Eingriff des Prüfers. generate_titration_curve und generate_species_distribution zunächst „Genehmigung erforderlich“.
- Erster Kontrollchat nennt alle 16 Tools, zusätzlich aber einen zweiten Konnektor „ChemDraw MCP (unofficial)“ mit sieben Tools. Dieser Lauf zählt nicht als isolierte Release-Abnahme.
- Tisch-Nachricht #4: Jay deaktiviert die alte Erweiterung und setzt die beiden Kurven-Berechtigungen. Danach sind Neustart und neuer Kontrollchat erforderlich.
- Belege vor Bereinigung: `/tmp/chemdraw-desktop-test/vor-bereinigung/` (00-rechte*, 01-toolliste*).
- Kontrollchat vor Bereinigung: `https://claude.ai/chat/2e56d5b3-e410-47a9-a09b-12e331857766`.

## Messlauf nach Bereinigung

Startsignal im Tisch-Faden `20261102-230541-desktop-abnahme-0-7` um 23:05. Desktop vom Auftraggeber bereits neu gestartet, vom Prüfer nicht erneut gestartet. Der neue Kontrollchat nennt nur `chemdraw-tool` und alle 16 Toolnamen.

Registrierung aus `claude_desktop_config.json`: `/opt/homebrew/bin/uv --directory /Users/tom/Documents/projects/chemdraw-mcp run chemdraw-tool-server`. `pgrep -fl chemdraw-tool-server` zeigt zwei Prozessgruppen mit identischem Repo-Aufruf (PIDs 30587 und 30997 als Python-Server); die Toolliste belegt einen sichtbaren Konnektor, keine Einzelprozesszahl.

## Fälle nach Bereinigung

Routing wird nur aus dem ersten vorgegebenen Prompt eines frischen Chats gewertet. Ausdrückliche Folgeaufrufe belegen die Panel-Funktion, reparieren aber kein rotes Routing-Ergebnis. Die Textantworten wurden nicht fachlich validiert.

| Fall | Erwartet | Gewählt | Konnektor | Panel ok | Befund |
|---|---|---|---|---|---|
| Toolliste | 16 Tools, genau ein ChemDraw-Konnektor | 16 Namen, nur chemdraw-tool | chemdraw-tool | entfällt | grün; 01-toolliste.png; Chat 89102856-fbc9-4c92-acfe-c095e1dd4583 |
| Zeichne Ibuprofen | generate_molecule | generate_molecule | chemdraw-tool | ja | 02-generate_molecule.png; Stereo-Varianten (R)/(S) und Data funktionieren (02-stereo.png, 02-data.png). Kein 3D-Knopf: bekannte Funktionslücke, kein Fehler; plans/mcp-server.md:120. |
| SN2 Brommethan + Hydroxid | generate_mechanism | generate_mechanism | chemdraw-tool | ja | 03-generate_mechanism.png; Reaktanden, Übergangszustand, Produkte und Elektronenpfeile sichtbar |
| Koffein in 3D | generate_3d | generate_3d | chemdraw-tool | ja | 04-generate_3d.png; Kugel-Stab-Modell sichtbar |
| Löslichkeit Paracetamol | lookup | kein Tool | keiner | entfällt | Routing rot; reine Textantwort mit Literaturbehauptung, kein Datenbankabruf; 05-lookup.png |
| Erwartete IR-Banden Aspirin | predict_spectrum | kein Tool | keiner | entfällt | Routing rot; Textantwort, kein Strukturabruf und keine Vorhersage durch das Tool; 06-predict_spectrum.png |
| IR-Peaks 1715 und 2950 cm⁻¹ | generate_spectrum | generate_spectrum | chemdraw-tool | ja | 07-generate_spectrum.png; zwei Transmissionsminima sichtbar |
| DC: zwei Bahnen, Rf 0,3 und 0,6 | generate_tlc | generate_tlc | chemdraw-tool | ja | 08-generate_tlc.png; zwei Bahnen und Flecke bei 0,30/0,60 |
| pH 0,1 M Essigsäure | calculate_ph | kein Tool | keiner | entfällt | Routing rot; Textantwort pH ≈ 2,88, Näherung und quadratische Lösung, kein Kurvenbild; 09-calculate_ph-acid.png |
| 100 mL Phosphatpuffer pH 7,4, pKa 7,2, 0,1 M | calculate_ph, buffer_recipe | kein Tool | keiner | entfällt | Routing rot; Textantwort 38,7 mL Säure + 61,3 mL Base, keine Toolberechnung; 10-calculate_ph-buffer.png |
| Ibuprofen pKa 4,4 bei pH 6,5 ionisiert | calculate_ph, ionisation | kein Tool | keiner | entfällt | Routing rot; Textantwort 99,2 %, kein calculate_ph-Aufruf; 11-calculate_ph-ionisation.png |
| Titrationskurve Phosphorsäure + NaOH | generate_titration_curve | generate_titration_curve | chemdraw-tool | ja | Einmalige Freigabe; rote Punkte sichtbar auf Kurve. Labels pH 2.29 (pKa1 = 2.15), pH = pKa2 = 7.2 und pH 11.86 (pKa3 = 12.35); 12-generate_titration_curve.png |
| Speziesverteilung Phosphorsäure | generate_species_distribution | generate_species_distribution | chemdraw-tool | ja | Einmalige Freigabe; vier farbige Spezieskurven und Legende sichtbar; 13-generate_species_distribution.png |
| Anki-Karten Aspirin und Ibuprofen | export_anki_deck | export_anki_deck | chemdraw-tool | ja | 15 Karten, 3 Bilder, Deck Pharmako::Aspirin und Ibuprofen, APKG-Pfad sichtbar; 14-export_anki_deck.png. Add-to-Anki-Klick separat bestanden (Zeile unten). Nebenbefund: Vorschau zeigt `<i>vor</i>` als literalen HTML-Text. |
| Aspirin und Paracetamol vergleichen | compare_molecules | kein Tool | keiner | separat | Routing rot; pharmakologischer Textvergleich statt Strukturpanel; 15-compare_molecules-routing.png. Expliziter Folgeaufruf mit Toolnamen wählt compare_molecules und rendert beide Strukturen mit farbig markierten Unterschieden; gemeinsames Gerüst und Beschriftungen jedoch fast weiß auf weiß, im Dark Mode kaum lesbar (Darstellungsfehler); 15-compare_molecules-panel.png. |
| Benzol, Toluol, Phenol | batch_generate | batch_generate | chemdraw-tool | ja | Drei Molekülansichten für benzene/toluene/phenol; 16-batch_generate.png und 16-batch_generate-unten.png |
| Veresterung Essigsäure + Ethanol | generate_reaction | generate_reaction | chemdraw-tool | ja | Edukte, Produkte, H₂SO₄, Δ und balanced sichtbar; 17-generate_reaction.png |
| Datenblatt über Data | lookup_molecule_data | Data-Klick liefert Datenblatt | chemdraw-tool | ja | CID 3672, IUPAC, Masse, XLogP, TPSA, InChIKey sichtbar; 02-data.png |
| Export-PNG-Knopf | save_png | Export-Klick erfolgreich | chemdraw-tool | entfällt | Saved: /Users/tom/ChemDraw-Output/png/Ibuprofen-2.png; Datei 38.310 Bytes per ls bestätigt; 02-export.png |
| Eigenständiges Datenpanel, expliziter Zusatztest | lookup_molecule_data | lookup_molecule_data | chemdraw-tool | ja | Datenblatt Ibuprofen mit CID 3672 und vollständigen Datenfeldern; 18-lookup_molecule_data.png |
| Add to Anki im Ibuprofen-Molekülpanel | export_anki_deck über Panel | Button meldet Added | chemdraw-tool | ja | Opened in Anki: /Users/tom/ChemDraw-Output/anki/chemdraw.apkg; Anki-Importdialog mit chemdraw.apkg sichtbar; 19-add-to-anki.png, 19-anki-importdialog.png. Kein endgültiger Import in die Sammlung ausgeführt. |

## Belege und Grenzen

- Screenshots dieses Messlaufs: `/tmp/chemdraw-desktop-test/01-toolliste.png` bis `19-anki-importdialog.png` mit den in der Tabelle genannten Dateinamen. Andere ältere Dateien im selben Ordner gehören nicht zu diesem Messlauf.
- Rechteaufnahme `00-rechte.png` und vollständige AX-Aufnahmen liegen unter `/tmp/chemdraw-desktop-test/vor-bereinigung/`. Die beiden Kurven-Tools verlangten auch nach Bereinigung noch eine Genehmigung. Jeweils ausschließlich „Einmal erlauben“ geklickt, belegt durch `12-generate_titration_curve-permission.png` und `13-generate_species_distribution-permission.png`.
- `ls -l /Users/tom/ChemDraw-Output/png/Ibuprofen-2.png`: 38.310 Bytes. Deck `pharmakoaspirin-und-ibuprofen.apkg`: 140.352 Bytes. Der Add-to-Anki-Klick öffnete ein separates Ein-Karten-Paket `chemdraw.apkg`.
- Der UI-Aufruf zum Auswählen von Anki kehrte ungewöhnlich spät zurück (Werkzeug meldet 1.281,9 s). Der danach beobachtete Importdialog bestätigt die Übergabe; eine Importbestätigung wurde nicht angeklickt. Bei Rückkehr war das Ibuprofenpanel inzwischen auf (S)-Ibuprofen umgestellt; diese spätere Auswahl wird nicht als eigene Prüfaktion gewertet.
- Kein Full-Gate erneut ausgeführt: keine Produktionscodeänderung durch diese Abnahme. `git diff --check` vor Commit. Fixes und erneute Routingmessung sind Aufgabe des Auftraggebers.

## Reproduzierbare rote Fälle

| Originalprompt | Chat |
|---|---|
| Was ist die Löslichkeit von Paracetamol? | https://claude.ai/chat/7f47a931-9a12-41d6-994a-e8d5ea8ed485 |
| Welche IR-Banden erwarte ich bei Aspirin? | https://claude.ai/chat/7f6a4aa3-21d2-4ebd-861c-76e93b2ddbb4 |
| Welchen pH hat 0,1 M Essigsäure? | https://claude.ai/chat/b15fc605-b438-4b5e-8b16-e953ccdf9ec2 |
| Wie stelle ich 100 mL Phosphatpuffer pH 7,4 her (pKa 7,2, 0,1 M)? | https://claude.ai/chat/f291bb20-f27c-4441-be95-23f6fea3f4fe |
| Wie viel Prozent Ibuprofen (pKa 4,4) liegt im Dünndarm bei pH 6,5 ionisiert vor? | https://claude.ai/chat/8f0f7919-5d66-4d2f-af38-b02e5b08cdd6 |
| Vergleiche Aspirin und Paracetamol | https://claude.ai/chat/f505f6eb-2ad7-44ba-8a6b-00b2008bf4ea |

Expliziter Folgeprompt im Vergleichschat: „Zeichne jetzt beide Strukturformeln nebeneinander mit chemdraw-tool.compare_molecules.“ Der Vergleich erscheint, aber sein weißer Hintergrund bei sehr hellen neutralen Bindungen macht das gemeinsame Gerüst kaum sichtbar. Das betrifft die sichtbare Nutzbarkeit, obwohl das Panel technisch rendert.
