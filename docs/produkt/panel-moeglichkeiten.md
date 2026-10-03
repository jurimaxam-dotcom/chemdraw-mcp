# Was ein Panel im Chat kann — und was davon für den Wow-Moment taugt (03.10.2026)

Quelle: Spezifikation des MCP-Apps-Standards, `@modelcontextprotocol/ext-apps` 1.7.4
(`dist/src/spec.types.d.ts`), die Grundlage für Panels in Claude Desktop. **Ob Desktop jede Fähigkeit
wirklich anbietet, steht nicht in der Spezifikation** — das meldet der Host beim Start des Panels.
Deshalb ist die erste Aufgabe unten ein Versuch, kein Bauen.

Ziel: Wer das Projekt auf GitHub findet und ausprobiert, sieht in den ersten 60 Sekunden etwas,
das er nicht erwartet hat — egal ob Chemie, Pharmazie oder Biologie. Nicht eine Nische.

## 1. Was der Standard einer Oberfläche im Chat erlaubt

| Fähigkeit | Was das Panel damit tun kann | Wird heute genutzt? |
|---|---|---|
| **Anzeigemodi** `inline` · `fullscreen` · `pip` | Vollbild für 3D/Prüfung, schwebendes Mini-Fenster | nein |
| **Werkzeug aufrufen** (`callServerTool`) | Panel holt Daten/ändert Optionen ohne neue Chat-Frage | ja (Daten-Reiter, PNG-Export) |
| **Nachricht an den Chat** (`ui/message`) | Knopf im Panel schickt eine Frage ab („Zeig den Mechanismus") | nein |
| **Modellkontext aktualisieren** (`ui/update-model-context`) | Claude „sieht", was du anklickst — Atom, Ansicht, Antwort im Quiz | nein |
| **Datei speichern** (`ui/download-file`) | PNG/SVG/SDF direkt aus dem Panel herunterladen | nein (nur über Server-Pfad) |
| **Link öffnen** (`ui/open-link`) | PubChem, Literatur, Lehrbuch | nein |
| **Eingabe streamen** (`tool-input-partial`) | Panel erscheint schon, während Claude noch schreibt | nein |
| **Design des Hosts** (`theme`, `styles`, Maße, Berührung/Hover, Sprache) | Hell/Dunkel, passende Größe, Touch vs. Maus, deutsche Oberfläche | teilweise |
| **Sampling** (`sampling/createMessage`) | Panel lässt das Modell selbst Fragen oder Erklärungen erzeugen | nein (Host-Unterstützung offen) |
| **Berechtigungen** Kamera/Mikrofon/Ort | z. B. Zeichnung abfotografieren | nein, nicht sinnvoll |

Daneben gibt es in Claude selbst **Artefakte** (eigenständige Seiten mit Speicher) und die
Fragekarten, die du als Quiz gesehen hast. Das ist ein anderer Mechanismus als unser Panel: Artefakte
und Fragekarten liefert Claude selbst, ein Panel kommt aus unserem Server. Beides lässt sich
kombinieren, aber nur das Panel hängt am Molekül.

## 2. Mögliche Bausteine, nach Wow pro Aufwand

Wow = sieht ein Neuling es in 60 s und denkt „das kann ich alles sehen?". Aufwand für mich in Stunden.

| # | Baustein | Wow | Aufwand | Fächer | Risiko |
|---|---|---|---|---|---|
| 1 | **Alle Ansichten als Reiter von Anfang an**: Struktur · Stereo (R/S) · 3D · Daten — ohne dass man danach fragt | hoch | 4–6 | alle | gering (3D braucht nur 10–30 ms) |
| 2 | **Im Browser ausprobieren, ohne Claude und ohne Installation** (Demo-Seite mit Beispielmolekülen) — Link ganz oben im README | sehr hoch | 4–6 | alle | gering; Hosting kostenlos auf GitHub Pages |
| 3 | **3D dreht sich von selbst** (Pause bei Berührung), weicher Wechsel zwischen Reitern | hoch | 2–3 | alle | gering |
| 4 | **Atom oder Gruppe anklicken → Claude erklärt es** (Modellkontext) | sehr hoch | 3–4 | alle | **Host-abhängig** — erst messen |
| 5 | **Vollbild-Knopf** (3D, Mechanismus) + **Herunterladen-Knopf** (PNG/SVG/SDF) | mittel | 2–3 | alle | Host-abhängig |
| 6 | **Folge-Vorschläge unter dem Bild** („Mechanismus", „Mit Naproxen vergleichen", „Karteikarten") per Nachricht an den Chat | hoch | 2–3 | alle | Host-abhängig |
| 7 | **Blind-Modus**: Gruppen oder Namen abdecken, Klick deckt auf, „wusste ich / nicht" | hoch | 6–8 | alle | gering |
| 8 | **Prüfmodus** über mehrere Moleküle mit Auswertung, Fehler als Anki-Deck | mittel–hoch | 6–8 | alle | gering (baut auf 7) |
| 9 | **Biologie-Paket klein**: Aminosäuren/Peptide aus der Sequenz („Gly-Ala-Ser"), Zucker, Nukleotide — in denselben Reitern | hoch für Biologie | 6–10 | Biologie, Pharmazie | mittel (SMILES-Erzeugung prüfen) |
| 10 | **Wirkstoffklassen-Galerie**: 8 Strukturen einer Klasse als Kacheln, Antippen vergrößert | hoch | 4–6 | Pharmazie, Chemie | gering |
| 11 | **Enzymkinetik** (Michaelis-Menten, Hemmtypen) neben Dosis-Wirkung | mittel | 3–4 | Biologie, Pharmazie | gering |
| 12 | **Host-Zeile im Panel** („Claude Desktop · Vollbild ja · Nachricht ja …") — für Bug-Meldungen und als Messinstrument | indirekt | 1 | alle | keines |

## 3. Was ich empfehle: zuerst messen, dann das Paket bauen

**Schritt 0 (1 Stunde, keine Funktion):** Baustein 12 als Versuch. Das Panel schreibt aus, was Desktop
wirklich anbietet. Davon hängen 4, 5, 6 ab, und ich will nicht blind bauen, was der Host dann verweigert.

**Paket „Wow-Moment" (die Reihenfolge, in der ein Neuling es sieht):**
1. Reiter Struktur · Stereo · 3D · Daten — sofort da (Baustein 1)
2. 3D dreht sich von selbst, Wechsel weich (3)
3. Browser-Demo mit Link im README (2) — der Hebel für Sterne, weil man ohne Claude etwas sieht
4. Je nach Messung: Atom anklicken → Claude erklärt (4), Vollbild und Herunterladen (5), Folge-Vorschläge (6)

**Danach:** Blind-Modus und Prüfmodus (7, 8), Biologie-Paket (9), Wirkstoffklassen-Galerie (10).

Was bewusst **nicht** vorne steht: Pharmakologie-Spezialfälle. Die sind gebaut und bleiben, aber sie
sind für den Erstkontakt eine Nische.
