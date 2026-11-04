# Claude Desktop: veröffentlichtes Bundle 0.7.0

Abnahme am 04.11.2026, Opus 5.5 Mittel, Desktop 4.16336.0. Stichproben, jeweils
neuer Chat. Prüft das veröffentlichte Paket, keine Repository-Installation.

## Identität und Isolation

- Download: `gh release download v0.7.0 -p '*.mcpb' -D /tmp/chemdraw-0.7.0/`.
- Bundle-SHA-256: `884403233b72b78e8ad7eef71f0cca844a337ca7feadad1b908a229cb25c201e`.
- Installations-Receipt: `~/Library/Application Support/Claude/extensions-installations.json`,
  Schlüssel `local.mcpb.jurimaxam-dotcom.chemdraw-mcp`; Version 0.7.0,
  derselbe Bundle-Hash, installedAt `2026-11-04T22:13:10.641Z`.
- Installationspfad: `~/Library/Application Support/Claude/Claude Extensions/local.mcpb.jurimaxam-dotcom.chemdraw-mcp/`.
  Alle fünf Dateien bytegleich zum heruntergeladenen Bundle.
- Laufzeit: `~/.local/share/chemdraw-mcp-bundle/env-0.7.0/`, METADATA-Version 0.7.0.
  Prozessliste zeigt Python und chemdraw-mcp aus genau dieser Umgebung.
- PyPI-Wheel: `chemdraw_mcp-0.7.0-py3-none-any.whl`, SHA-256
  `342542c27c598dde3535833eda57089988dd2b2872115c1a458c366d18ff5767`.
  Hash gegen `https://pypi.org/pypi/chemdraw-mcp/0.7.0/json` geprüft und im
  Bundle-Lock gefunden; alle **56 installierten Paketdateien** bytegleich
  zu diesem Wheel. Also kein Schluss allein aus dem Versionsstring.
- Entwickler-Eintrag `mcpServers.chemdraw-tool` während der Tests aus der
  Desktop-Konfiguration entfernt und separat unter /tmp gesichert;
  andere Server unverändert. Desktop vollständig beendet und neu gestartet.
- UI bestätigt genau einen ChemDraw-Konnektor, darunter **12 interaktive + 4 weitere Tools**.
  Zwei Serverprozesse gehören zur Bundle-Umgebung (Chat/Cowork), kein Repo-Server.

Lokale Belege: `/tmp/chemdraw-0.7.0/{receipt-chemdraw-0.7.0.json,pypi-0.7.0.json,installed-hash-comparison.txt}`.
Screenshots und AX-Belege: `/tmp/chemdraw-desktop-test/0-7-0-bundle/`.

## Fälle

| Fall | Erwartet | Ergebnis | Screenshot |
|---|---|---|---|
| Kontrollchat | Ein ChemDraw-Konnektor, 16 Tools | Grün: genau ein Bundle-Konnektor; 12 + 4 Tools in Erweiterungsdetails | 02-single-connector.png, 03-tools-12-plus-4.png, 03-tools.txt |
| „Zeichne Ibuprofen“ | generate_molecule, Strukturpanel | Grün; Struktur, Formel C13H18O2, 206,28 g/mol | 04-ibuprofen.png |
| Stereo-Knopf | Zwei auswählbare Enantiomere | Grün: (R)- und (S)-Ibuprofen | 05-stereo-variants.png |
| Data-Klick | Datenblatt über AppBridge | Grün: PubChem CID 3672, InChIKey HEFNNWSXXWATRW-UHFFFAOYSA-N | 06-ibuprofen-data.png |
| Export PNG | Datei über Panelknopf | Grün: `/Users/tom/ChemDraw-Output/png/Ibuprofen-3.png`, gültiges PNG, 918 × 441 Pixel | 07-ibuprofen-export.png |
| „Zeig mir die Titrationskurve von Phosphorsäure mit NaOH“ | generate_titration_curve, Panel mit EP | Grün: Kurve, EP1/EP2/EP3 bei 20/40/60 mL; Pufferpunkte liegen auf der Kurve | 08-titration.png |
| „Mach mir Anki-Karten zu Aspirin und Ibuprofen“ | export_anki_deck, Vorschau ohne wörtliche HTML-Tags, apkg-Pfad | Grün: Vorschau zeigt Fragen als Text; gültiges APKG mit 14 Notizen / 16 Karten und 5 Medien | 09-anki.png, 09-anki.txt |

| „Welchen pH hat 0,1 M Essigsäure? — nutze ChemDraw“ | calculate_ph, Ergebnis aus Tool | Grün: topic weak_acid, c=0.1, pKa=4.76; Toolantwort pH 2.88; nur Einmalfreigabe | 10-ph-result.png, 11-ph-tool-details.png / .txt |

Titrationschat: https://claude.ai/chat/33b38bc4-bb51-4000-840e-d22895284721

Anki-Chat: https://claude.ai/chat/afd40163-eca0-4a40-8e3d-6b677afb2b4c

pH-Chat: https://claude.ai/chat/6785ea83-a0a8-45c9-bd17-d9ae227b4849

APKG: `/Users/tom/ChemDraw-Output/anki/pharmakoaspirin-und-ibuprofen.apkg`;
ZIP-Integrität und SQLite-Zählung geprüft; kein Import in Anki vorgenommen.

Ibuprofen-Chat: https://claude.ai/chat/fc6df569-f936-41d5-9fb0-bee7df426645

## Befunde

1. Veralteter Text in **manifest.json → long_description** des veröffentlichten
   Bundles: „The default MVP registers six tools; other features are retained in
   an optional full profile.“ Tatsächlich registriert: 16 Tools. Der Text steht
   im Installationsdialog; er beschreibt den veröffentlichten Stand falsch.
2. Beim Erststart nach Installation meldete die UI keine Verbindung; der
   Desktop-Log enthält `ensureAllConfiguredConnected timed out after 10000ms`.
   Währenddessen installierte `uv pip install --require-hashes` die neue
   Umgebung. Nach Abschluss und erneutem vollständigem Neustart war das Bundle
   verfügbar. Kein Produktfix in dieser Abnahme.
3. Anki-Panel: Die Beschriftung „14 cards“ zählt hier Notizen. Das APKG enthält
   14 Notizen und 16 Karten (zwei Struktur-Notiztypen erzeugen jeweils zwei
   Karten). Vorschau und Export funktionieren, die Zählungsbeschriftung ist
   ungenau. Kein Fix während dieser Abnahme.
4. Ibuprofen-CAS ist 58560-75-1 (PubChem CID 3672), bereits bekannter Befund.

## Installationsfreigabe

Die automatische Freigabeprüfung lehnte den Aktualisieren-Klick zunächst ab
(unsignierte/nicht von Anthropic verifizierte Erweiterung, Computerzugriff).
Nach der Ablehnung zeigte das Receipt dennoch bereits 0.7.0 mit passendem Hash
und die Erweiterung war aktiviert; deshalb nicht als sicher „unverändert“
gewertet. Zunächst wieder deaktiviert, dann nach Jays ausdrücklicher Freigabe
über Tisch-Faden #3 für die Abnahme aktiviert. Keine technische Umgehung.

## Rücksetzen und Grenze der Abnahme

Der originale Entwickler-Eintrag wurde nach den Tests **exakt** aus der
Sicherung wiederhergestellt (JSON-Vergleich wahr), das Bundle deaktiviert
(`isEnabled: false`), Desktop vollständig beendet und neu gestartet.
Die aktualisierte Erweiterung 0.7.0 bleibt installiert, läuft im Alltag
aber nicht zusätzlich zum Entwickler-Konnektor.

Bedienfehler bei der Navigation: Eine Berechtigungsgruppe wurde versehentlich
auf „Immer erlauben“ erweitert. Vor dem pH-Test wurden anhand des anfänglichen
AX-Befunds alle Einzelwerte wiederhergestellt und nach dem Test nochmals auf
der neu geöffneten Einstellungsseite bestätigt. Unverändert dauerhaft erlaubt:
export_anki_deck, compare_molecules, batch_generate, save_png; die übrigen zwölf
Tools benötigen wieder Genehmigung. Für den pH-Test wurde ausdrücklich
**Einmal erlauben** gewählt. Beleg: `permissions-restored.txt`.
Die ersten drei Stichproben liefen während der vorübergehenden Erweiterung;
sie prüfen Panel-/Exportfunktionen, nicht das Auftreten von Freigabedialogen.

**Ergebnis:** Vier beauftragte funktionale Stichproben bestanden, Paketidentität
nachgewiesen. Keine Aussage über alle 16 Tools oder die gesamte Toolwahl.
Manifesttext, Erststart-Timeout und Anki-Zählung bleiben dokumentierte Befunde;
über Folgefixes entscheidet Jay. Toolbeschreibungen und Produktcode wurden
in dieser Abnahme nicht verändert.

Abschließende Rückprüfung: UI-Konnektorenliste zeigt genau `chemdraw-tool`,
kein aktives „ChemDraw MCP (unofficial)“. Screenshot `12-developer-restored.png`.
Prozessliste zeigt die zwei üblichen Desktop-Instanzen aus
`/Users/tom/Documents/projects/chemdraw-mcp/.venv/bin/chemdraw-tool-server`,
keinen Prozess aus der Bundle-Umgebung.
