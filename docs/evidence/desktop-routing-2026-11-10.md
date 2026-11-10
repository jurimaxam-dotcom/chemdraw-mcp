---
status: erledigt
abnahme:
- Acht getrennte neue Chats mit unveränderten Prompts gemessen / ja / 01–08-input.ax.txt, 01–08-result.ax.txt und Screenshots in diesem Ordner; Ergebnisse unten.
- Vier Wiederholungen Draw trastuzumab / ja / 01–04-trastuzumab.png; jeweils Visualize statt chemdraw.
- Prozessstart je Versuch protokolliert / ja / 01–08-process-start.txt und process-end.txt; durchgehend PID 29382, Start Tue Nov 10 15:20:06 2026.
- Zusatzdiagnose nach allen acht Versuchen / ja / 09-diagnose.png; wörtliche Antwort unten.
dateien:
- /tmp/chemdraw-desktop-test/runde6/ @ lokal
offen: []
---

Draw trastuzumab: 0/4 Treffer; insgesamt: 0/8 Treffer für chemdraw.

Erster gewerteter Versuch: 10.11.2026, 15:21:03 CET. Alle gewerteten Versuche nach dem letzten beobachteten Desktop-Neustart um 15:20:06. Hauptprozess durchgehend PID 29382. Repo-HEAD vor/nach Messung 24cfdfb, git status --short leer. Nichts am Repo geändert, kein Commit, kein Gate. Desktop zeigte Opus 5.5 / Medium / Manual.

Messmethode: Neue Chats über scripts/ax-claude.sh press AXButton '=New'. Der Helfer verdoppelte beim Tippen Zeichen; deshalb nach dem ersten verworfenen Tippversuch Texte über native CUA-paste eingesetzt. Jeden Eingabefeldinhalt vor Absenden per AX geprüft und gespeichert. Absenden zunächst per AX-Klick, ab Wiederholung von Versuch 4 per AXPress. Keine Nachhilfe, keine Folgemeldung in den acht Chats. Routing gewertet, sobald eine andere Toolwahl sichtbar war, jeweils innerhalb von 90 Sekunden; keine Aussage, dass eine noch laufende Antwort vollständig beendet war. Es sind die sichtbaren UI-Toolbezeichnungen dokumentiert; interne API-Namen von Visualize/Bildersuche waren nicht sichtbar und werden nicht geraten.

| Nr. | Sendestart CET | Exakter Prompt | chemdraw gewählt | Sichtbares Tool / Ergebnis | Sichtbarer Denktitel wörtlich | Screenshot |
|---|---|---|---|---|---|---|
| 1 | 15:21:03 | Draw trastuzumab | nein | Visualize Widget; eigenes Antikörperschema | Summarizing trastuzumab's domain structure instead of a full atomic formula | 01-trastuzumab.png |
| 2 | 15:22:43 | Draw trastuzumab | nein | Visualize Widget; eigenes Schema, beim Wertungsbild noch leerer Widgetbereich | Adjusting the glycan spacing and shifting the drawing up | 02-trastuzumab.png |
| 3 | 15:24:11 | Draw trastuzumab | nein | Visualize Widget; Schema und Erklärungstext | Placing labels and leader lines along the right side | 03-trastuzumab.png |
| 4 | 15:26:55 | Draw trastuzumab | nein | Visualize Widget; eigenes Y-Schema | Describing trastuzumab's domain structure instead of its full atomic formula | 04-trastuzumab.png |
| 5 | 15:27:47 | Draw an antibody | nein | Visualize Widget; eigenes Y-Schema | Placing the arm chains and tip overlays | 05-antibody.png |
| 6 | 15:28:39 | Show me trastuzumab | nein | Web-Bildersuche, sichtbare ResearchGate-Ergebnisse; kein ChemDraw-Aufruf | Weighing how to show the antibody structure visually | 06-show-trastuzumab.png |
| 7 | 15:29:32 | Zeichne Trastuzumab | nein | Visualize Widget; eigenes Domänenschema | Placing the labels and leader lines; später Erklärung des Antikörperaufbaus mit einem Domänenschema | 07-zeichne-trastuzumab.png |
| 8 | 15:30:54 | Draw lysozyme | nein | Visualize Widget; Schema mit zwei Domänen, kein drehbarer Protein-Cartoon | Placing helices and strands within the two lobes | 08-lysozyme.png |

Alle Screenshot-Pfade relativ zu /tmp/chemdraw-desktop-test/runde6/. Die dynamischen Denktitel stehen in den AX-Texten; spätere Abschlussansichten ersetzen sie teilweise durch „Thought for …“. Bei Versuch 3 zeigt der Screenshot den unteren Antwortteil; Visualize ist im gespeicherten AX-Baum belegt.

Verworfen, nicht mitgezählt:
- Anläufe vor/neben den externen Neustarts um ca. 15:14 und 15:20; Dateien unter verworfen/ und verworfen-1520/.
- Ein erster Versuch 4: Eingabefeld vor Absenden korrekt, gesendete Nachricht enthielt im Screenshot zusätzliche Zeichen („Draw trastuzumabrrtt. uunndd“). Als verstümmelt verworfen, unter verworfen-eingabe/, neuer Chat und korrekter Versuch 4 wiederholt.

Messbedingung: Während eines Vorlaufs waren im Konnektormenü chemdraw UND chemdraw-pharma aktiv sichtbar. Diese Einstellung wurde nicht geändert. Die Zusatzdiagnose nennt ebenfalls beide Server, 16 bzw. 23 Tools. Die Reihe ist damit eine Messung dieses Desktop-Zustands, kein isolierter Vergleich mit nur einem Konnektor.

Zusatzdiagnose — erst nach Versuch 8, neuer Chat, nicht in Trefferzahl:
Prompt exakt:
“Without calling any tool: list the chemdraw tools you can see right now, quote any server instructions from the chemdraw connector word for word, and say whether they mention proteins or antibodies.”
Screenshot: /tmp/chemdraw-desktop-test/runde6/09-diagnose.png
Denktitel: “Checking which ChemDraw server instructions exist”
Keine Toolnutzung in der sichtbaren Antwort. Antwort wörtlich (Markdown-Struktur aus dem sichtbaren Text rekonstruiert):

> No chemdraw server instructions are in my context, so there’s nothing to quote, and nothing about proteins or antibodies. The only MCP server instructions I received are from `claude-in-chrome`, and they cover how to load browser tools.
>
> What I can see
>
> The chemdraw tools are only listed by name as deferred tools. I don’t have their descriptions or parameter schemas until they’re loaded. There are two servers, both reached through your computer:
>
> Server — Tools
>
> chemdraw (16) — batch_generate, calculate_ph, compare_molecules, export_anki_deck, generate_3d, generate_mechanism, generate_molecule, generate_reaction, generate_species_distribution, generate_spectrum, generate_titration_curve, generate_tlc, lookup, lookup_molecule_data, predict_spectrum, save_png
>
> chemdraw-pharma (23) — all 16 above, plus calculate_content, calculate_pharmacokinetics, calculate_solution, generate_calibration_curve, generate_dose_response, generate_pk_curve, generate_scope_table
>
> Proteins and antibodies
>
> • Server instructions: none exist for either chemdraw server, so they can’t mention anything.
> • Tool names: none refer to proteins, antibodies or biologics. They are all about small molecules and analytics.
> • Tool descriptions: I can’t check these without loading the schemas. A description could still mention proteins even though no tool name does.
>
> Next step (about 1 minute): say “load them,” and I’ll fetch the schemas for both servers with a single ToolSearch call and check every description for “protein” and “antibody.”

Einordnung: Die Selbstauskunft stützt die Hypothese, dass Desktop die ChemDraw-Server-Hinweise dem Modell in diesem Zustand nicht vorab sichtbar macht und Toolbeschreibungen erst nach ToolSearch lädt. Sie ist kein unabhängiger Beweis über den tatsächlich serialisierten Modellkontext. Der Server kann instructions ausliefern, obwohl das Modell sie nicht sieht. Kein Nachladen verlangt; Diagnosechat danach unverändert gelassen.
