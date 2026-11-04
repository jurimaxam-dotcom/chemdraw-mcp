#!/usr/bin/env python3
"""Baut die Werkzeugbilanz-Seite (ein HTML-Artifact) aus festen Quellen im Repo.

Quellen:
  docs/evidence/routing-2026-11-03/*.log   Toolwahl in Claude Code, 57 Fälle × 4 Läufe
  evals/tool-routing/cases.yaml            Prompts, erwartetes Tool
  tests/__snapshots__/tools/*.json         Beschreibung + Parameter, die das Modell liest
  tests/                                   Testzahlen und Eingabevielfalt (gezählt, nicht geschätzt)
  docs/desktop-abnahme-2026-11-02.md       Desktop-Messung (hier als Tabelle eingetragen, Quelle verlinkt)
  <lauf>/                                  Ausgaben eines echten Laufs aller Tools (scripts/werkzeugbilanz_lauf.py)
  /tmp/chemdraw-desktop-test/              Desktop-Screenshots von Codex, falls vorhanden

Aufruf:  uv run python scripts/werkzeugbilanz.py <lauf-ordner> <ziel.html> [--welle3-log datei]
"""
from __future__ import annotations

import ast
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "docs" / "evidence" / "routing-2026-11-03"
SHOTS = Path("/tmp/chemdraw-desktop-test")

TOOLS_MVP = [
    "generate_molecule", "batch_generate", "compare_molecules", "generate_reaction",
    "generate_mechanism", "generate_3d", "generate_spectrum", "generate_tlc",
    "generate_titration_curve", "generate_species_distribution", "lookup",
    "lookup_molecule_data", "predict_spectrum", "calculate_ph", "export_anki_deck", "save_png",
]
TOOLS_W3 = [
    "generate_scope_table", "generate_calibration_curve", "generate_pk_curve",
    "generate_dose_response", "calculate_solution", "calculate_content",
    "calculate_pharmacokinetics",
]

AREAS = [
    ("draw", "Zeichnen", "Strukturen und Reaktionen"),
    ("lab", "Laborgrafik", "Messdaten als Diagramm"),
    ("look", "Nachschlagen", "Fakten zu einem Stoff"),
    ("calc", "Rechnen", "Zahl und Rechenweg"),
    ("anki", "Anki & intern", "Karteikarten, Exportknopf"),
]

# --------------------------------------------------------------------------------------
# Redaktioneller Teil je Tool: Dateien, Funktionsweise, Pipeline, Mehrwert, Schwierigkeiten.
# Zahlen (Routing, Tests, Laufzeit) kommen NICHT von hier, sondern aus den Quellen oben.
# erzeugt: "rechnet" | "tabelle" | "vorlage" | "netz" | "knopf"
# --------------------------------------------------------------------------------------
T = {
 "generate_molecule": dict(a="draw", v="0.6", w="Ein Stoff als 2D-Struktur",
  files=["server.py: generate_molecule", "resolver.py", "generator.py", "svg_renderer.py", "image_export.py", "render_style.py", "cdxml_writer.py", "databases.py (CAS/CID)", "payloads.py: MoleculePayload", "ui: MoleculeView.jsx, StructureCanvas"],
  deps=["RDKit", "py2opsin (optional, Java)", "PubChem/NCI (nur bei Namen)", "Pillow"],
  erzeugt="rechnet",
  wie="Name oder SMILES → Resolver (SMILES gewinnt, wenn er parst; sonst OPSIN offline → PubChem → NCI) → RDKit 2D-Koordinaten → SVG fürs Panel und PNG/SVG als Datei. Eigenschaften (Formel, Masse, logP, TPSA) rechnet RDKit, CAS/CID holt PubChem. Mehrdeutige Familiennamen (Glucose, Xylol) liefern einen Isomer-Picker statt einer stillen Wahl.",
  pipe=[("IN","Name / SMILES","vom Modell"),("RES","Resolver","OPSIN→PubChem→NCI"),("RD","RDKit 2D","Koordinaten, Props"),("SVG","Renderer","svg_renderer + image_export"),("OUT","Panel + Datei","MoleculePayload · PNG/SVG")],
  focal=2, beispiel=("output_dir/ibuprofen.png","Datei-Rendering von heute: „ibuprofen“"), shots=["02-generate_molecule.png"],
  mehrwert="Hoch. Claude ohne Tool kann keine verlässliche Strukturformel zeigen; mit Tool ist die Struktur korrekt, prüfbar (InChIKey-Check gegen 24 Stoffe) und interaktiv (Gruppen-Hover, Stereo-Varianten, All-H, Fischer/Haworth, Datenblatt).",
  schwer=["Erklärfragen („Was macht Ibuprofen im Körper?“) rufen das Tool nicht; das Bild bleibt aus.", "Name-Auflösung braucht Netz oder Java; 9,5 s im heutigen Lauf (PubChem-Rundreise).", "PubChem-Rohdaten sind nicht immer der Lehrbuchwert: Ibuprofen kam als CID 3672 „Ibuprofen, (+-)-“ mit CAS 58560-75-1 (Racemat-Nummer), nicht 15687-27-1.", "Kein 3D-Knopf im Panel; 3D nur über generate_3d."]),
 "batch_generate": dict(a="draw", v="0.6", w="Mehrere Strukturen, je eine Datei",
  files=["server.py: batch_generate", "resolver.py", "generator.py", "svg_renderer.py", "image_export.py", "payloads.py: BatchPayload", "ui: BatchView"],
  deps=["RDKit", "PubChem/NCI"], erzeugt="rechnet",
  wie="Liste von Namen → je Name dieselbe Kette wie generate_molecule; ein Fehler blockiert die anderen nicht (Feld `failed`). Das Panel zeigt je Molekül eine Karte mit eigenem Export-Knopf.",
  pipe=[("IN","Liste","2–n Namen"),("RES","Resolver","je Name"),("RD","RDKit 2D","je Molekül"),("OUT","Panel + Dateien","BatchPayload · n × PNG/SVG")],
  focal=2, beispiel=("output_dir/toluene.png","eine der drei Dateien von heute (benzene, toluene, phenol)"), shots=["16-batch_generate.png"],
  mehrwert="Mittel. Bequemlichkeit: drei Stoffe in einem Aufruf statt drei Aufrufen. Nichts, was generate_molecule nicht auch könnte.",
  schwer=["Drängt sich bei Nachbarn vor: „alle Stereoisomere der Weinsäure“ und „Klausur über NSAR“ landen hier statt bei generate_molecule bzw. Anki (4/4 bzw. 4/4 Läufe rot).", "23 s für drei Namen im heutigen Lauf: jede Auflösung geht einzeln ins Netz."]),
 "compare_molecules": dict(a="draw", v="0.6", w="2–4 Moleküle, Unterschiede markiert",
  files=["server.py: compare_molecules", "resolver.py", "image_export.py: render_comparison_*", "payloads.py: PlotPayload", "ui: PlotView"],
  deps=["RDKit (rdFMCS)", "PubChem/NCI"], erzeugt="rechnet",
  wie="Alle Strukturen auflösen → RDKit sucht die maximale gemeinsame Teilstruktur (MCS) → gemeinsames Gerüst neutral, Rest farbig → ein gemeinsames Bild mit Beschriftung.",
  pipe=[("IN","2–4 Stoffe","Namen/SMILES"),("RES","Resolver","je Stoff"),("MCS","RDKit MCS","gemeinsames Gerüst"),("SVG","Renderer","Hervorhebung"),("OUT","Panel + Datei","PlotPayload")],
  focal=2, beispiel=("plot_dir/compare-aspirin-vs-paracetamol.png","Datei-Rendering von heute: Aspirin vs. Paracetamol"), shots=["nach-compare-panel-dark.png"],
  mehrwert="Hoch, wenn es läuft: der markierte Unterschied ist etwas, das Text nicht leistet. Desktop beantwortet „Vergleiche X und Y“ aber als pharmakologischen Textvergleich.",
  schwer=["Desktop: 0 von 3 ohne Zusatz, 2 von 2 mit „— nutze ChemDraw“.", "„Was ist der Unterschied zwischen Ibuprofen und Naproxen?“ in Claude Code mit Tool-Suche 0/2 (Frage, kein Auftrag).", "Label „Acetylsalicylsäure“ mit sichtbarer Lücke am Umlaut (Nebenbefund Codex 03.11.).", "Nur 3 Testaufrufe, alle mit demselben Paar."]),
 "generate_reaction": dict(a="draw", v="0.6", w="Reaktionsgleichung Edukte → Produkte",
  files=["server.py: generate_reaction", "resolver.py", "layout.py (Pfeile, +, Bedingungen)", "reaction_balance.py", "condition_text.py", "svg_renderer.py", "image_export.py", "cdxml_writer.py", "payloads.py: ReactionPayload", "ui: ReactionView.jsx"],
  deps=["RDKit", "lxml (CDXML)", "PubChem/NCI"], erzeugt="rechnet",
  wie="Edukte und Produkte auflösen → RDKit zeichnet jede Spezies → layout.py setzt Pfeil (→, ⇌, Retro), Plus-Zeichen, Bedingungen über/unter dem Pfeil → Bilanzprüfung zählt Atome und schlägt Koeffizienten vor, ändert das Bild aber nicht.",
  pipe=[("IN","Edukte, Produkte","+ Bedingungen"),("RES","Resolver","je Spezies"),("LAY","layout.py","Pfeil, +, Text"),("BAL","Bilanz","Atome zählen"),("OUT","Panel + Datei","ReactionPayload")],
  focal=2, beispiel=("reaction_dir/reaktion-fe7f77/reaktion-fe7f77.png","Datei-Rendering von heute: Veresterung mit Gleichgewichtspfeil"), shots=["17-generate_reaction.png"],
  mehrwert="Hoch. Eine saubere Gleichung mit Bedingungen und Bilanz ist Grundstudium-Alltag; Claude ohne Tool liefert nur Text.",
  schwer=["„Wie läuft die Veresterung ab?“ (Frage) ruft mit Tool-Suche den Mechanismus statt der Gleichung (2/2 rot).", "Das Modell muss die Produkte selbst kennen; das Tool prüft nur die Bilanz, nicht die Chemie."]),
 "generate_mechanism": dict(a="draw", v="0.7", w="Lehrbuch-Mechanismus mit Elektronenpfeilen",
  files=["server.py: generate_mechanism", "templates/substitution.py (SN1, SN2)", "templates/ester.py (Fischer)", "mechanism.py: validate_substrates", "mechanism_coords.py", "mechanism_renderer.py", "payloads.py: MechanismPayload", "ui: MechanismView"],
  deps=["RDKit"], erzeugt="vorlage",
  wie="Drei feste Vorlagen mit vorgegebenen Molekülen je Schritt. Die Substrate des Nutzers werden nur per SMARTS auf Passung geprüft (Alkylhalogenid? Nucleophil?); gezeichnet wird immer das Lehrbuchbeispiel (Brommethan + Hydroxid, tert-Butylbromid, Essigsäure + Methanol). Die Pfeile liegen als Overlay auf stabilisierten Koordinaten.",
  pipe=[("IN","Typ + Substrate","sn1 / sn2 / fischer_ester"),("CHK","SMARTS-Prüfung","passt das Substrat?"),("TPL","Vorlage","feste Moleküle je Schritt"),("SVG","Renderer","Pfeil-Overlay"),("OUT","Panel","Schritte, kein File")],
  focal=2, beispiel=("generate_mechanism.json:steps:1","Schritt 2 (Übergangszustand) aus dem heutigen Lauf"), shots=["03-generate_mechanism.png"],
  mehrwert="Hoch für die drei Fälle: gebogene Pfeile kann Claude nicht zeichnen. Ehrlich bei allem anderen (sagt, was nicht drin ist).",
  schwer=["Nur drei Beispiele; die eigenen Substrate tauchen nicht im Bild auf, nur in der Prüfung.", "Tests: 9 Aufrufe, 2 verschiedene Substratpaare."]),
 "generate_3d": dict(a="draw", v="0.7", w="Drehbares 3D-Modell",
  files=["server.py: generate_3d", "resolver.py", "structure3d.py (ETKDGv3 + MMFF)", "payloads.py: Molecule3DPayload", "ui: Molecule3DView (Canvas)"],
  deps=["RDKit"], erzeugt="rechnet",
  wie="Auflösen → explizite H → RDKit-Konformer (ETKDGv3) → Kraftfeld-Optimierung → Atome und Bindungen als Koordinaten ans Panel, das sie selbst zeichnet und dreht. Zusätzlich eine SDF-Datei.",
  pipe=[("IN","Name / SMILES",""),("RES","Resolver",""),("3D","RDKit ETKDG","+ MMFF"),("OUT","Panel + SDF","Koordinaten, kein Bild")],
  focal=2, beispiel=("text:generate_3d","heutiger Lauf: Koffein, 24 Atome, 25 Bindungen, 0,02 s"), shots=["04-generate_3d.png"],
  mehrwert="Mittel bis hoch: Geometrie (gewinkelt, tetraedrisch, Sessel) zum Anfassen. Ein Konformer, keine Konformationsanalyse.",
  schwer=["„Warum ist Wasser gewinkelt?“ ruft mit Tool-Suche kein Tool (2/2 rot).", "Ein einziger Testaufruf (Methan); kein Bild als Datei, nur SDF."]),
 "generate_spectrum": dict(a="lab", v="0.7", w="Schematisches Spektrum aus einer Peakliste",
  files=["server.py: generate_spectrum", "spectrum.py (IR, NMR, MS, UV/Vis)", "image_export.py", "payloads.py: SpectrumPayload", "ui: SpectrumView + Export"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="Peakliste (Position, Intensität, Label) → matplotlib zeichnet je Typ das passende Achsen-Schema (IR als Transmission mit umgekehrter Achse, MS als Strichspektrum) → PNG/SVG. Es wird nichts gemessen oder vorhergesagt: die Peaks liefert das Modell.",
  pipe=[("IN","Peakliste","vom Modell"),("PLT","matplotlib","Typ-Schema"),("OUT","Panel + Datei","SpectrumPayload")],
  focal=1, beispiel=("spectrum_dir/aspirin.png","Datei-Rendering von heute: drei Banden"), shots=["07-generate_spectrum.png"],
  mehrwert="Mittel. Fürs Protokoll nützlich, aber die Werte kommen aus dem Modellgedächtnis und müssen geprüft werden.",
  schwer=["Ein falscher Peak vom Modell wird sauber gezeichnet; das Tool kann ihn nicht erkennen.", "12–19 KB SVG-Text je Antwort, die das Modell mitliest."]),
 "generate_tlc": dict(a="lab", v="0.7", w="DC-Platte aus Rf-Werten",
  files=["server.py: generate_tlc", "tlc.py", "image_export.py", "payloads.py: TlcPayload", "ui: TlcView + Export"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="Bahnen mit Flecken (Rf, Label, Intensität) → matplotlib zeichnet Platte, Startlinie, Front, Flecken proportional → PNG/SVG. Rf aus Laufstrecken rechnet das Modell vorher.",
  pipe=[("IN","Bahnen + Rf","Laufmittel, Detektion"),("PLT","matplotlib","Platte"),("OUT","Panel + Datei","TlcPayload")],
  focal=1, beispiel=("tlc_dir/veresterung.png","Datei-Rendering von heute: Edukt, Reaktion, Co-Spot"), shots=["08-generate_tlc.png"],
  mehrwert="Mittel. Protokollskizze, die man sonst von Hand malt; sicher getroffen.",
  schwer=["Eng benachbarte Flecken (0,50/0,52) überdecken ihre Beschriftung."]),
 "generate_titration_curve": dict(a="lab", v="0.7", w="Titrationskurve, Äquivalenz- und Pufferpunkte",
  files=["server.py: generate_titration_curve", "ph_plots.py (Kurve)", "ph_core.py (exakte Ladungsbilanz)", "image_export.py", "payloads.py: PlotPayload", "ui: PlotView"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="pKa-Werte, Konzentrationen, Volumen → ph_core löst je Titrantvolumen die exakte Ladungsbilanz (keine Henderson-Hasselbalch-Näherung) → Kurve mit Äquivalenzpunkten, Pufferpunkten auf der Kurve und Indikatorband. Dieselbe Mathematik wie calculate_ph, deshalb stimmen Zahl und Bild überein.",
  pipe=[("IN","pKa, c, V",""),("PH","ph_core","Ladungsbilanz je Punkt"),("PLT","ph_plots","Kurve, EP, Indikator"),("OUT","Panel + Datei","PlotPayload")],
  focal=1, beispiel=("plot_dir/titration-essigsäure.png","Datei-Rendering von heute: Essigsäure, Pufferpunkt bei 12,5 mL"), shots=["nach-titration.png"],
  mehrwert="Hoch. Exakte Kurve statt Skizze; Pufferpunkt auf der Kurve (Fix 31.10., noch nicht im README-Bild).",
  schwer=["Äquivalenzpunkte stehen nur im Bild, nicht als Text in der Antwort.", "Desktop verlangt für dieses Tool jedes Mal eine Freigabe („Einmal erlauben“)."]),
 "generate_species_distribution": dict(a="lab", v="0.7", w="Speziesverteilung über pH",
  files=["server.py: generate_species_distribution", "ph_plots.py", "ph_core.py", "payloads.py: PlotPayload", "ui: PlotView"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="pKa-Werte → Anteil jeder Protonierungsstufe von pH 0 bis 14 → Kurvenschar mit Schnittpunkten bei den pKa-Werten.",
  pipe=[("IN","pKa-Werte","+ Labels"),("PH","ph_core","Anteile je pH"),("PLT","ph_plots","Kurvenschar"),("OUT","Panel + Datei","PlotPayload")],
  focal=1, beispiel=("plot_dir/species-phosphorsäure.png","Datei-Rendering von heute: Phosphorsäure"), shots=["13-generate_species_distribution.png"],
  mehrwert="Hoch für die Frage „welche Form liegt bei pH x vor“: als Bild sofort klar. Sicher getroffen (12/12, Desktop ✔).",
  schwer=["Wie die Titrationskurve: Freigabe je Aufruf in Desktop."]),
 "lookup": dict(a="look", v="0.7", w="Einzelwert als Text (CAS, Schmelzpunkt, GHS, KEGG …)",
  files=["server.py: lookup + _lookup_* je Topic", "databases.py (PubChem, ChEBI, UniProt, KEGG)", "ui: keins (Text)"],
  deps=["requests", "PubChem PUG REST", "ChEBI", "UniProt", "KEGG"], erzeugt="netz",
  wie="Name → PubChem-Datensatz (Properties, Synonyme, GHS, experimentelle Daten) bzw. ChEBI/UniProt/KEGG je Topic → Markdown-Tabelle mit Quelle und Link. Nichts wird berechnet oder gespeichert; ohne Netz gibt es eine Fehlermeldung mit Grund.",
  pipe=[("IN","Name + Topic","properties / safety / …"),("API","PubChem u. a.","REST, 6–10 s"),("FMT","Markdown","Tabelle + Quelle"),("OUT","Text","kein Panel")],
  focal=1, beispiel=("text:lookup","heutiger Lauf: Paracetamol, topic properties, 7,7 s"), shots=["05-lookup.png"],
  mehrwert="Gering bis mittel. Der Vorteil ist die Quelle mit Link, nicht die Zahl: für Lehrbuchstoffe weiß Claude den Wert meist selbst. PubChem ist manchmal gröber als das Lehrbuch (Paracetamol-Löslichkeit „1–5 mg/mL“ statt 14 g/L).",
  schwer=["Desktop ruft es bei natürlichen Fragen nicht (0 von 4 Chats), mit „— nutze ChemDraw“ 2/2.", "6–10 s je Aufruf, reines Netz.", "Alle Modultests laufen gegen Attrappen (requests.get gepatcht); echtes Netz nur im Host-Test und in identitaet.py."]),
 "lookup_molecule_data": dict(a="look", v="0.6", w="Datenblatt-Panel: Struktur neben den Fakten",
  files=["server.py: lookup_molecule_data", "resolver.py", "databases.py", "svg_renderer.py", "payloads.py: DatabasePayload", "ui: DatabaseView.jsx (Data-Knopf im Molekül-Panel)"],
  deps=["RDKit", "PubChem"], erzeugt="netz",
  wie="Name → Struktur (RDKit, lokal) + PubChem-Datensatz per InChIKey (CID, IUPAC, Masse, XLogP, TPSA, CAS, GHS-Gruppen) → Panel mit Struktur und Tabelle. Das Molekül-Panel ruft es beim Klick auf „Data“ selbst, einmal, dann aus dem Cache.",
  pipe=[("IN","Name",""),("RES","Resolver → RDKit","Struktur lokal"),("API","PubChem","per InChIKey"),("OUT","Panel","DatabasePayload")],
  focal=2, beispiel=("text:lookup_molecule_data","heutiger Lauf: Ibuprofen, 10,7 s, Quellen + Struktur"), shots=["18-lookup_molecule_data.png"],
  mehrwert="Hoch als Knopf: ein Klick vom Bild zu CAS, Masse, InChIKey mit Quelle. Als Modellaufruf selten nötig.",
  schwer=["Ohne Tool-Suche ruft das Modell für „Datenblatt mit allem“ zusätzlich lookup ×3, generate_molecule, calculate_ph (2/2 Läufe rot wegen verbotener Nachbarn).", "Netzlaufzeit ~10 s; Spinner im Panel."]),
 "predict_spectrum": dict(a="look", v="0.7", w="Erwartete IR-Banden, Bandenzuordnung, ¹H-Signalzahl",
  files=["server.py: predict_spectrum", "spectro.py (_IR_TABLE: 31 SMARTS-Regeln, ¹H-Äquivalenzklassen)", "resolver.py", "ui: keins (Text)"],
  deps=["RDKit"], erzeugt="tabelle",
  wie="Struktur auflösen → jede der 31 kuratierten SMARTS-Regeln gegen das Molekül matchen (Ester-C=O, Säure-O–H, Aromat …) → Tabelle Wellenzahl/Gruppe/Intensität/Form plus „Was zuerst anschauen“. ¹H: topologische Symmetrieklassen zählen Signale und Integrale. Deterministisch, keine ppm-Werte, keine Datenbank.",
  pipe=[("IN","Struktur / Wellenzahl","topic"),("RES","Resolver",""),("TAB","31 SMARTS-Regeln","kuratierte Tabelle"),("OUT","Text","Markdown")],
  focal=2, beispiel=("text:predict_spectrum","heutiger Lauf: Aspirin, 7 Banden, 0,0 s"), shots=["06-predict_spectrum.png"],
  mehrwert="Mittel. Aus der Struktur abgeleitet statt aus dem Gedächtnis; bei Lehrbuchstoffen kennt Claude die Banden aber selbst.",
  schwer=["Desktop ruft es nicht (0 von 4 Chats); mit Zusatz nicht gemessen.", "Regeltabelle ist eine Vorhersage per Regel, keine Messung; seltene Gruppen fehlen.", "14 Testaufrufe, aber nur 4 verschiedene Strukturen."]),
 "calculate_ph": dict(a="calc", v="0.7", w="pH, Puffer, Pufferrezept, Ionisationsgrad",
  files=["server.py: calculate_ph", "ph_calc.py (Formatierung, Näherung)", "ph_core.py (exakte Ladungsbilanz, geteilt mit der Kurve)", "ui: keins (Text)"],
  deps=["keine (reine Mathematik)"], erzeugt="rechnet",
  wie="Topic + Werte → ph_core löst die Ladungsbilanz numerisch (inkl. Autoprotolyse) → daneben die Lehrbuchnäherung mit Formel und eingesetzten Zahlen; weicht beides ab, sagt es die Antwort. Pufferrezept rechnet Mol → Volumen/Masse.",
  pipe=[("IN","Topic + Werte","pKa vom Nutzer"),("PH","ph_core","Ladungsbilanz exakt"),("APX","Näherung","Formel daneben"),("OUT","Text","Rechenweg")],
  focal=1, beispiel=("text:calculate_ph","heutiger Lauf: 0,1 M, pKa 4,76 → pH 2,88"), shots=["09-calculate_ph-acid.png"],
  mehrwert="Gering bei Lehrbuchfällen (Desktop rechnete 2,87 selbst richtig), hoch dort, wo die Näherung kippt (verdünnte Säuren, mehrprotonig) und beim Pufferrezept in Gramm.",
  schwer=["Desktop ruft es bei natürlichen pH-Fragen nicht: 0 von 12 Chats; mit „— nutze ChemDraw“ 2/2, aber nur der Essigsäure-Prompt wurde so nachgemessen, Puffer und Ionisation nicht.", "In Claude Code nach der Hinweiszeile in `instructions` 20/20; die Zeile erreicht Desktops Toolwahl nicht (Tools werden erst nachgeladen).", "Beschreibung 1980 Zeichen, knapp unter der 2-KB-Grenze."]),
 "export_anki_deck": dict(a="anki", v="0.6", w="Anki-Deck (.apkg) mit Strukturbildern",
  files=["server.py: export_anki_deck", "anki_export.py (genanki, Bilder rendern, AnkiConnect)", "curated_decks.py (2 Startdecks, 8 geprüfte SMILES)", "payloads.py: AnkiDeckPayload", "ui: AnkiDeckView, AnkiButton (Add to Anki)"],
  deps=["genanki", "RDKit", "Anki (optional, zum Öffnen)"], erzeugt="rechnet",
  wie="Karten (Text + max. ein Bild: Struktur, Reaktion, Spektrum) → Bilder werden gerendert → genanki packt .apkg mit stabilen IDs (gleicher Deckname = Update statt Duplikat) → Datei oder Übergabe an Anki. Die Kartentexte schreibt das Modell; zwei kuratierte Decks liegen fest im Paket.",
  pipe=[("IN","Karten vom Modell","oder curated_deck_id"),("IMG","Renderer","Struktur/Reaktion/Spektrum"),("PKG","genanki",".apkg, stabile IDs"),("OUT","Datei / Anki","AnkiDeckPayload")],
  focal=2, beispiel=("text:export_anki_deck","heutiger Lauf: 1 Karte, 1 Bild, beispiel.apkg, 0,1 s"), shots=["nach-anki-preview.png"],
  mehrwert="Hoch. Strukturbilder auf Karten macht sonst niemand; der Lernweg Bild → Karte ist ein Klick.",
  schwer=["„Ich schreibe Freitag über NSAR“ ruft zusätzlich batch_generate (4/4 Läufe), mit Tool-Suche nur batch_generate.", "Kartentexte kommen aus dem Modell, nicht aus dem Tool; Inhalt ungeprüft."]),
 "save_png": dict(a="anki", v="0.6", w="Interner Exportknopf des Panels",
  files=["server.py: save_png", "png_writer.py", "ui: ExportPngButton.jsx"],
  deps=["Pillow"], erzeugt="knopf",
  wie="Das Panel rastert das sichtbare SVG im Browser zu PNG (Base64) und ruft das Tool per AppBridge; der Server schreibt die Datei nach ~/ChemDraw-Output/png. Kein Modellaufruf: die Beschreibung markiert es als intern.",
  pipe=[("UI","Export-Klick","Panel rastert SVG"),("BR","AppBridge","callServerTool"),("OUT","Datei","png_writer")],
  focal=1, beispiel=None, shots=["02-export.png"],
  mehrwert="Nötig, kein Mehrwert an sich: Speichern ist der Klick des Nutzers.",
  schwer=["Gewollt nie vom Modell gerufen; 57 Fälle enthalten einen Negativfall (never-save-png: 4/4 grün)."]),
 # Welle 3
 "generate_scope_table": dict(a="draw", v="w3", w="Substratbreite-Raster (Paper-Abbildung)",
  files=["server.py: generate_scope_table", "scope.py", "layout.py", "image_export.py", "payloads.py: ScopePayload", "ui: ScopeView"],
  deps=["RDKit", "matplotlib"], erzeugt="rechnet",
  wie="Allgemeine Gleichung oben, darunter ein Raster aus Produktstrukturen mit Ausbeute/ee als Beschriftung.",
  pipe=[("IN","Einträge + Reaktion",""),("RES","Resolver","je Produkt"),("GRID","scope.py","Raster + Captions"),("OUT","Panel + Datei","ScopePayload")],
  focal=2, beispiel=("scope_dir/*.png","Datei-Rendering von heute: Suzuki-Scope aus den Testdaten"), shots=[],
  mehrwert="Gering fürs Grundstudium: eine Abbildung für Forschungsartikel.",
  schwer=["Hat am 02.10. „Zeichne Aspirin“ abgefangen (Ursprung der Taxonomie).", "22 KB Text je Antwort."]),
 "generate_calibration_curve": dict(a="lab", v="w3", w="Kalibriergerade, Rückrechnung, LOD/LOQ (DIN 32645)",
  files=["server.py: generate_calibration_curve", "calibration.py (kleinste Quadrate, DIN 32645)", "calibration_plot.py", "payloads.py: PlotPayload"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="Standards → lineare Regression mit Residuen, R², Nachweis-/Bestimmungsgrenze nach DIN 32645; Unbekannte werden auf der Geraden zurückgerechnet.",
  pipe=[("IN","Standards + Signale",""),("FIT","calibration.py","Regression, LOD/LOQ"),("PLT","calibration_plot",""),("OUT","Panel + Datei","PlotPayload")],
  focal=1, beispiel=("plot_dir/paracetamol.png","Datei-Rendering von heute: Kalibriergerade Paracetamol mit Rückrechnung"), shots=[],
  mehrwert="Hoch im Analytik-Praktikum: Rückrechnung und Nachweisgrenze nach Norm.",
  schwer=["Nur ein Routing-Fall, nie im Standardprofil gemessen, kein Desktop-Test."]),
 "generate_pk_curve": dict(a="lab", v="w3", w="Plasmaspiegel über Zeit (Einkompartiment)",
  files=["server.py: generate_pk_curve", "pk.py", "pk_plot.py", "payloads.py: PlotPayload"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="Dosis, Vd, ke/t½/CL, ka, Bioverfügbarkeit, Intervall → Bateman-Funktion, Akkumulation bis Steady State, therapeutisches Fenster als Band.",
  pipe=[("IN","Dosis, Vd, ke, ka",""),("PK","pk.py","Bateman, Css"),("PLT","pk_plot",""),("OUT","Panel + Datei","PlotPayload")],
  focal=1, beispiel=("plot_dir/*ibuprofen*.png","Datei-Rendering von heute"), shots=[],
  mehrwert="Pharmazie-spezifisch; Desktop-Test 03.10.: Css,av 4,74 mg/L, R 1,43 korrekt.",
  schwer=["Für allgemeine Chemie kaum gefragt; gehört mit dose_response und calculate_pharmacokinetics in ein Pharma-Profil."]),
 "generate_dose_response": dict(a="lab", v="w3", w="Dosis-Wirkungs-Kurve, kompetitiver Antagonist",
  files=["server.py: generate_dose_response", "pk.py / pharmacology", "pk_plot.py", "payloads.py: PlotPayload"],
  deps=["matplotlib"], erzeugt="rechnet",
  wie="Hill-Gleichung mit EC50, Emax, Hill-Koeffizient; Antagonist verschiebt nach Schild (Dosisverhältnis r = 1 + [B]/KB).",
  pipe=[("IN","EC50, Emax, Hill","+ Antagonist"),("HILL","Hill / Schild","r = 1+[B]/KB"),("PLT","pk_plot",""),("OUT","Panel + Datei","PlotPayload")],
  focal=1, beispiel=("plot_dir/*agonist*.png","Datei-Rendering von heute"), shots=[],
  mehrwert="Pharmakologie-Vorlesung; außerhalb davon ohne Nutzen.",
  schwer=["Wie pk_curve: Pharma-Profil statt Standard."]),
 "calculate_solution": dict(a="calc", v="w3", w="Einwaage, Verdünnung, Mischkreuz, Molmasse",
  files=["server.py: calculate_solution", "solution.py"],
  deps=["molmass (parst Hydrate)"], erzeugt="rechnet",
  wie="Topic + Werte → n = c·V, m = n·M mit Molmasse aus der Formel (auch Hydrate wie CuSO₄·5H₂O), Verdünnungsformel, Mischkreuz; Rechenweg Zeile für Zeile.",
  pipe=[("IN","Topic + Werte",""),("MM","molmass","Formel → M"),("CALC","solution.py","Rechenweg"),("OUT","Text","")],
  focal=1, beispiel=("text:calculate_solution","heutiger Lauf: 250 mL 0,1 M NaOH"), shots=[],
  mehrwert="Hoch im Praktikum: Hydrate und Rundung sind die typischen Fehlerquellen.",
  schwer=["Beschreibung 2000 Zeichen, an der Grenze; jede neue Abgrenzung kippt sie.", "Nie im Standardprofil gemessen."]),
 "calculate_content": dict(a="calc", v="w3", w="Gehaltsbestimmung Ph. Eur., Fettkennzahlen, Statistik",
  files=["server.py: calculate_content", "calculator/titration.py", "calculator/photometry.py", "calculator/stats.py (Grubbs)", "calculator/fat_values.py"],
  deps=["keine (reine Mathematik)"], erzeugt="rechnet",
  wie="Einwaagen + Messwerte je Methode (Titration mit Titer/Blindwert, Photometrie mit A1%1cm, Säure-/Verseifungs-/Iodzahl, Karl Fischer) → Gehalt je Messung, Mittelwert, Streuung, Ausreißertest.",
  pipe=[("IN","Methode + Messreihe",""),("CALC","calculator/*","je Messung"),("STAT","stats.py","Mittel, Grubbs"),("OUT","Text","Tabelle + Rechenweg")],
  focal=1, beispiel=("text:calculate_content","heutiger Lauf: Titration, drei Einwaagen"), shots=[],
  mehrwert="Hoch im Pharmazie-Praktikum, Nische außerhalb.",
  schwer=["Beschreibung 2027 Zeichen, über der 2-KB-Marke (Claude Code schneidet ab).", "Nie im Standardprofil gemessen."]),
 "calculate_pharmacokinetics": dict(a="calc", v="w3", w="PK-Zahlen im Einkompartimentmodell",
  files=["server.py: calculate_pharmacokinetics", "pk.py"],
  deps=["keine"], erzeugt="rechnet",
  wie="Topic (t½, i.v.-Bolus, oral, Steady State, Loading Dose) + Parameter → Formel, eingesetzte Werte, Ergebnis.",
  pipe=[("IN","Topic + Parameter",""),("PK","pk.py","Formeln"),("OUT","Text","Rechenweg")],
  focal=1, beispiel=("text:calculate_pharmacokinetics","heutiger Lauf: t½ aus CL und Vd"), shots=[],
  mehrwert="Pharmazie-spezifisch.",
  schwer=["Gehört in ein Pharma-Profil; im Standardprofil nicht registriert."]),
}

# Modultests je Tool (Dateien unter tests/), zusätzlich zu den Dateien, die das Tool direkt aufrufen.
MODUL_TESTS = {
 "generate_molecule": ["test_resolver", "test_image_export", "test_svg_renderer", "test_projection", "test_stereo_variants", "test_stereo_warnings", "test_all_hydrogens", "test_ambiguous_names", "test_server_identity", "test_render_style", "test_server_render_style", "test_server_formats", "test_validator"],
 "batch_generate": ["test_server_formats"],
 "compare_molecules": [],
 "generate_reaction": ["test_layout", "test_reaction_balance", "test_reaction_coefficients", "test_cdxml_writer", "test_server_reaction"],
 "generate_mechanism": ["test_mechanism", "test_mechanism_coords", "test_mechanism_renderer", "test_server_mechanism", "test_aufgaben_mechanismus"],
 "generate_3d": [],
 "generate_spectrum": ["test_spectrum", "test_server_spectrum"],
 "generate_tlc": ["test_tlc", "test_server_tlc"],
 "generate_titration_curve": ["test_ph_plots", "test_aufgaben_titration"],
 "generate_species_distribution": ["test_ph_plots"],
 "lookup": ["test_databases", "test_server_lookups", "test_ghs"],
 "lookup_molecule_data": ["test_databases", "test_server_lookup_ui", "test_ghs"],
 "predict_spectrum": ["test_spectro", "test_server_spectro"],
 "calculate_ph": ["test_ph_calc", "test_server_ph", "test_aufgaben_ph"],
 "export_anki_deck": ["test_anki_export", "test_server_anki"],
 "save_png": ["test_png_writer"],
 "generate_scope_table": ["test_scope", "test_server_scope"],
 "generate_calibration_curve": ["test_calibration", "test_server_calibration"],
 "generate_pk_curve": ["test_pk", "test_server_pk_plots"],
 "generate_dose_response": ["test_pk", "test_server_pk_plots"],
 "calculate_solution": ["test_solution_math", "test_server_solution", "test_aufgaben_loeslichkeit"],
 "calculate_content": ["test_calculator_titration", "test_calculator_photometry", "test_calculator_stats", "test_calculator_outlier", "test_calculator_fat_values", "test_server_content"],
 "calculate_pharmacokinetics": ["test_pk", "test_server_pk", "test_aufgaben_pharmakokinetik"],
}
UI_TESTS = {
 "generate_molecule": ["moleculeView", "stereoVariants", "stereoNote", "viewToggle", "ambiguousView", "provenance"],
 "generate_reaction": ["reactionView"], "lookup_molecule_data": ["databaseView"],
 "export_anki_deck": ["ankiButton", "ankiDeckView"], "generate_spectrum": ["spectrumView"],
 "save_png": ["panelExport", "svgToPng"],
}

# Desktop-Messung (docs/desktop-abnahme-2026-11-02.md): je Tool (Ergebnis, Klasse, Kurztext)
DESKTOP = {
 "generate_molecule": ("ok", "✔ 02.11. + 03.11.", "„Zeichne Ibuprofen“ → Panel, Stereo (R)/(S), Data, Export"),
 "batch_generate": ("ok", "✔ 02.11.", "„Benzol, Toluol, Phenol“ → drei Panels"),
 "compare_molecules": ("no", "0 von 4 · mit Zusatz 2/2", "„Vergleiche Aspirin und Paracetamol“ → Text (02.11. + 3× 03.11.); mit „— nutze ChemDraw“ Panel"),
 "generate_reaction": ("ok", "✔ 02.11.", "Veresterung mit H₂SO₄, Δ, balanced"),
 "generate_mechanism": ("ok", "✔ 02.11.", "SN2 mit Übergangszustand und Pfeilen"),
 "generate_3d": ("ok", "✔ 02.11.", "Koffein als Kugel-Stab-Modell"),
 "generate_spectrum": ("ok", "✔ 02.11.", "zwei IR-Peaks als Transmissionsminima"),
 "generate_tlc": ("ok", "✔ 02.11.", "zwei Bahnen, Rf 0,30/0,60"),
 "generate_titration_curve": ("ok", "✔ 02.11. + 03.11.", "Phosphorsäure, drei EP; Freigabe je Aufruf"),
 "generate_species_distribution": ("ok", "✔ 02.11.", "vier Spezieskurven; Freigabe je Aufruf"),
 "lookup": ("no", "0 von 4 · mit Zusatz 2/2", "„Löslichkeit von Paracetamol?“ → Text aus dem Gedächtnis"),
 "lookup_molecule_data": ("ok", "✔ Data-Klick + Aufruf", "CID 3672, IUPAC, Masse, XLogP, TPSA, InChIKey"),
 "predict_spectrum": ("no", "0 von 4", "„Welche IR-Banden erwarte ich bei Aspirin?“ → Text"),
 "calculate_ph": ("no", "0 von 12 · mit Zusatz 2/2 (nur pH-Fall)", "pH, Puffer, Ionisation je 0/1 + 0/3; Antwort pH ≈ 2,88 fachlich richtig; Zusatz nur für den Essigsäure-Prompt gemessen"),
 "export_anki_deck": ("ok", "✔ 02.11. + 03.11.", "17 Karten, 3 Bilder, Add-to-Anki öffnet Importdialog"),
 "save_png": ("ok", "✔ 02.11.", "Export-Klick → Ibuprofen-2.png, 38 KB"),
 "generate_pk_curve": ("mid", "03.10. ✔ Zahlen", "letzter Desktop-Test vor Welle 1"),
}

VER = {"0.6": ("v06", "0.6 draußen"), "0.7": ("v07", "0.7 neu"), "w3": ("vw3", "Welle 3, nur Vollprofil")}
ERZ = {
 "rechnet": ("Erzeugt", "wird je Eingabe neu gerechnet (RDKit/matplotlib/Mathematik)"),
 "tabelle": ("Regeltabelle", "kuratierte Regeln werden auf die Eingabe angewendet, Ergebnis deterministisch"),
 "vorlage": ("Feste Vorlage", "Bild ist vorgespeichert; die Eingabe wird nur geprüft"),
 "netz": ("Datenbank", "Werte kommen live aus dem Netz, nichts wird gerechnet"),
 "knopf": ("Knopf", "kein Modellaufruf, der Nutzer klickt"),
}


# ---------------------------------------------------------------- Quellen einlesen
def lies_routing() -> dict[str, dict[str, tuple[bool, str]]]:
    runs = {"ohne 1": "lauf1-ohne-toolsuche.log", "ohne 2": "lauf2-ohne-toolsuche.log",
            "TS 1": "lauf1-mit-toolsuche.log", "TS 2": "lauf2-mit-toolsuche.log"}
    res: dict[str, dict[str, tuple[bool, str]]] = {}
    for k, f in runs.items():
        for line in (EVID / f).read_text().splitlines():
            m = re.match(r"^(✔|✘) (\S+)\s+gerufen: (.*)$", line.strip())
            if m:
                res.setdefault(m.group(2), {})[k] = (m.group(1) == "✔", m.group(3))
    return res


def lies_welle3(pfad: Path | None) -> dict[str, tuple[bool, str]]:
    if not pfad or not pfad.exists():
        return {}
    out = {}
    for line in pfad.read_text().splitlines():
        m = re.match(r"^(✔|✘) (\S+)\s+gerufen: (.*)$", line.strip())
        if m:
            out[m.group(2)] = (m.group(1) == "✔", m.group(3))
    return out


FALLART_FEST = {
    "bare-name-with-article": "Name",      # „Zeig mir mal Paracetamol“ gehört zur Familie blanker Name
    "draw-with-caption": "Auftrag",         # „Strukturformel von … mit Beschriftung“ nennt das Bild
    "desktop-vergleich": "Auftrag",         # „Vergleiche …“ ist ein Imperativ
    "calc-content": "Auftrag",              # „Gehaltsbestimmung per Titration: Einwaagen …“ nennt die Aufgabe
    "calibration-curve": "Auftrag",         # „Kalibriergerade aus 5 Standards“ nennt das Bild
}


def fallart(prompt: str, fall_id: str = "") -> str:
    if fall_id in FALLART_FEST:
        return FALLART_FEST[fall_id]
    p = prompt.strip().lower()
    if len(p.split()) <= 1:
        return "Name"
    auftrag = r"^(zeichne|zeichn|zeig|zeige|plot|show|draw|gib mir|mach|erstell|fischer projection|dc meiner|my tlc|aspirin ir-spektrum|kannst du mir)"
    if re.search(auftrag, p) or re.search(r"\b(zeichne|zeichnen|plot|draw|zeig mir|show me|als eigene datei|als drehbares)\b", p):
        return "Auftrag"
    return "Frage"


def lies_faelle() -> list[dict]:
    cases = yaml.safe_load((ROOT / "evals/tool-routing/cases.yaml").read_text())["cases"]
    for c in cases:
        c["art"] = fallart(c["prompt"], c["id"])
    return cases


def lies_beschreibungen() -> dict[str, dict]:
    out = {}
    for f in sorted((ROOT / "tests/__snapshots__/tools").glob("*.json")):
        d = json.loads(f.read_text())
        schema = d.get("inputSchema") or d.get("input_schema") or {}
        out[d["name"]] = {"description": d["description"], "params": list(schema.get("properties", {}).keys())}
    return out


def zaehle_tests(tool: str) -> dict:
    tests = ROOT / "tests"
    direkt_dateien, direkt_n, aufrufe, erstargs = [], 0, 0, set()
    for f in sorted(tests.glob("test_*.py")):
        src = f.read_text()
        n = len(re.findall(r"^\s*(?:async )?def test_", src, re.M))
        if re.search(rf"\b{tool}\(", src):
            direkt_dateien.append(f.stem)
            direkt_n += n
            for m in re.finditer(rf"\b{tool}\(([^)\n]{{0,80}})", src):
                aufrufe += 1
                arg = re.split(r"[,)]", m.group(1))[0].strip()
                if arg:
                    erstargs.add(arg)
    modul_n = 0
    modul_dateien = []
    for stem in MODUL_TESTS.get(tool, []):
        f = tests / f"{stem}.py"
        if f.exists() and stem not in direkt_dateien:
            modul_dateien.append(stem)
            modul_n += len(re.findall(r"^\s*(?:async )?def test_", f.read_text(), re.M))
    ui_n, ui_dateien = 0, []
    for stem in UI_TESTS.get(tool, []):
        for f in (ROOT / "chemdraw_tool/ui/src").rglob(f"{stem}.test.mjs"):
            ui_dateien.append(stem)
            ui_n += len(re.findall(r"^\s*(?:test|it)\(", f.read_text(), re.M))
    return dict(direkt_dateien=direkt_dateien, direkt_n=direkt_n, aufrufe=aufrufe, erstargs=len(erstargs),
                modul_dateien=modul_dateien, modul_n=modul_n, ui_n=ui_n, ui_dateien=ui_dateien)


def bild_uri(pfad: Path, breite: int = 880, jpeg: bool = False) -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    if not pfad.exists():
        return None
    im = Image.open(pfad)
    if im.width > breite:
        im = im.resize((breite, round(im.height * breite / im.width)))
    buf = io.BytesIO()
    if jpeg:
        im.convert("RGB").save(buf, "JPEG", quality=78, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def beispiel_html(tool: str, lauf: Path) -> str:
    spec = T[tool].get("beispiel")
    if not spec:
        return "<p class='muted'>Kein Modell-Output: das Tool antwortet nur auf den Klick im Panel.</p>"
    quelle, caption = spec
    if quelle.startswith("text:"):
        f = lauf / f"{quelle[5:]}.json"
        if not f.exists():
            return "<p class='muted'>Lauf fehlt.</p>"
        raw = f.read_text()
        try:
            d = json.loads(raw)
            if isinstance(d, dict):
                d = {k: v for k, v in d.items() if k not in ("svg", "molecule_svg", "atoms", "bonds", "functionalGroups")}
                raw = json.dumps(d, ensure_ascii=False, indent=1)
        except json.JSONDecodeError:
            pass
        return f"<figure><pre class='out'>{html.escape(raw[:2200])}{'…' if len(raw) > 2200 else ''}</pre><figcaption>{html.escape(caption)}</figcaption></figure>"
    if ":steps:" in quelle:
        name, _, idx = quelle.partition(":steps:")
        d = json.loads((lauf / name).read_text())
        svg = d["steps"][int(idx)]["svg"]
        return f"<figure><div class='svgbox'>{svg}</div><figcaption>{html.escape(caption)}</figcaption></figure>"
    pfade = sorted(lauf.glob(quelle)) if "*" in quelle else [lauf / quelle]
    for p in pfade:
        uri = bild_uri(p)
        if uri:
            return f"<figure><img src='{uri}' alt='{html.escape(caption)}'><figcaption>{html.escape(caption)}</figcaption></figure>"
    return "<p class='muted'>Beispielbild nicht gefunden.</p>"


def shots_html(tool: str) -> str:
    out = []
    for name in T[tool].get("shots", []):
        uri = bild_uri(SHOTS / name, 880, jpeg=True)
        if uri:
            out.append(f"<figure><img src='{uri}' alt='Claude Desktop, {html.escape(name)}'><figcaption>Claude Desktop 02./03.11. (Codex): <code>{html.escape(name)}</code></figcaption></figure>")
    return "".join(out)


# ---------------------------------------------------------------- Pipeline-Diagramm (SVG)
def pipeline_svg(tool: str) -> str:
    nodes = T[tool]["pipe"]
    focal = T[tool].get("focal", -1)
    W, H, GAP, NW, NH = 0, 120, 36, 156, 60
    n = len(nodes)
    W = 16 + n * NW + (n - 1) * GAP + 16
    parts = [f'<svg class="pipe" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="pipe-{tool}-t pipe-{tool}-d">',
             f'<title id="pipe-{tool}-t">Ablauf {tool}</title>',
             f'<desc id="pipe-{tool}-d">Die Stationen, die eine Anfrage an {tool} vom Modell bis zur Ausgabe durchläuft.</desc>',
             '<defs><marker id="arr-' + tool + '" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="var(--d-muted)"/></marker></defs>']
    y = 30
    for i in range(n - 1):
        x1 = 16 + (i + 1) * NW + i * GAP
        x2 = x1 + GAP
        parts.append(f'<line x1="{x1}" y1="{y + NH/2}" x2="{x2 - 1}" y2="{y + NH/2}" stroke="var(--d-muted)" stroke-width="1.2" marker-end="url(#arr-{tool})"/>')
    for i, (tag, name, sub) in enumerate(nodes):
        x = 16 + i * (NW + GAP)
        is_focal = i == focal
        fill = "var(--d-accent-tint)" if is_focal else "var(--d-paper)"
        stroke = "var(--d-accent)" if is_focal else "var(--d-muted)"
        parts.append(f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="6" fill="var(--d-paper)"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(f'<rect x="{x+8}" y="{y+6}" width="{max(24, 7*len(tag)+10)}" height="12" rx="2" fill="transparent" stroke="{stroke}" stroke-opacity="0.4" stroke-width="0.8"/>')
        parts.append(f'<text x="{x+8+max(24, 7*len(tag)+10)/2}" y="{y+15}" fill="{stroke}" fill-opacity="0.9" font-size="7" font-family="var(--f-mono)" text-anchor="middle" letter-spacing="0.08em">{html.escape(tag)}</text>')
        parts.append(f'<text x="{x+NW/2}" y="{y+36}" fill="var(--d-ink)" font-size="12" font-weight="600" font-family="var(--f-sans)" text-anchor="middle">{html.escape(name)}</text>')
        if sub:
            parts.append(f'<text x="{x+NW/2}" y="{y+50}" fill="var(--d-soft)" font-size="9" font-family="var(--f-mono)" text-anchor="middle">{html.escape(sub[:30])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def toolwahl_svg() -> str:
    """Überblick: wie Beschreibung und instructions zum Modell kommen und wo Desktop abweicht."""
    s = []
    W, H = 920, 300
    s.append(f'<svg class="pipe" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="tw-t tw-d">')
    s.append('<title id="tw-t">Wie das Modell ein Tool wählt</title><desc id="tw-d">Server schickt instructions und Tool-Beschreibungen, das Modell entscheidet aus dem Kontext; Desktop lädt Beschreibungen erst bei Bedarf.</desc>')
    s.append('<defs><marker id="tw-arr" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="var(--d-muted)"/></marker><marker id="tw-acc" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="var(--d-accent)"/></marker></defs>')
    def box(x, y, w, h, tag, name, sub, focal=False):
        st = "var(--d-accent)" if focal else "var(--d-muted)"
        fl = "var(--d-accent-tint)" if focal else "var(--d-paper)"
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="var(--d-paper)"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fl}" stroke="{st}" stroke-width="1"/>')
        tw = max(24, 7*len(tag)+10)
        s.append(f'<rect x="{x+8}" y="{y+6}" width="{tw}" height="12" rx="2" fill="transparent" stroke="{st}" stroke-opacity="0.4" stroke-width="0.8"/><text x="{x+8+tw/2}" y="{y+15}" fill="{st}" font-size="7" font-family="var(--f-mono)" text-anchor="middle" letter-spacing="0.08em">{tag}</text>')
        s.append(f'<text x="{x+w/2}" y="{y+36}" fill="var(--d-ink)" font-size="12" font-weight="600" font-family="var(--f-sans)" text-anchor="middle">{name}</text>')
        for i, line in enumerate(sub):
            s.append(f'<text x="{x+w/2}" y="{y+50+i*11}" fill="var(--d-soft)" font-size="9" font-family="var(--f-mono)" text-anchor="middle">{html.escape(line)}</text>')
    def arrow(x1, y1, x2, y2, label="", acc=False, dash=False):
        mk = "tw-acc" if acc else "tw-arr"
        col = "var(--d-accent)" if acc else "var(--d-muted)"
        extra = ' stroke-dasharray="5,4"' if dash else ""
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1.2" marker-end="url(#{mk})"{extra}/>')
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            lw = 6.2*len(label)+10
            if x1 == x2:   # senkrecht: Label rechts neben der Linie, nicht darauf
                s.append(f'<rect x="{x1+8}" y="{my-6}" width="{lw}" height="12" fill="var(--d-paper)"/><text x="{x1+8+lw/2}" y="{my+3}" fill="var(--d-soft)" font-size="8" font-family="var(--f-mono)" text-anchor="middle" letter-spacing="0.06em">{label}</text>')
            else:
                s.append(f'<rect x="{mx-lw/2}" y="{my-18}" width="{lw}" height="12" fill="var(--d-paper)"/><text x="{mx}" y="{my-9}" fill="var(--d-soft)" font-size="8" font-family="var(--f-mono)" text-anchor="middle" letter-spacing="0.06em">{label}</text>')
    # Pfeile zuerst, Boxen danach (Linien liegen hinter den Knoten)
    arrow(196, 60, 300, 60, "TOOLS/LIST")
    arrow(476, 60, 580, 60, "KONTEXT")
    arrow(668, 90, 668, 170, "TOOLS/CALL")
    arrow(580, 200, 476, 200, "PAYLOAD")
    arrow(108, 232, 108, 90, "ERST BEI SUCHE", acc=True, dash=True)
    box(20, 30, 176, 60, "SRV", "chemdraw-tool", ["instructions (1 Text)", "16 Beschreibungen ≤ 2 KB"])
    box(300, 30, 176, 60, "CLI", "Client", ["Claude Desktop / Code", "initialize → tools/list"])
    box(580, 30, 176, 60, "LLM", "Modell", ["liest Kontext + Prompt", "wählt oder antwortet selbst"])
    box(580, 170, 176, 60, "SRV", "Tool läuft", ["RDKit, matplotlib, PubChem", "→ Payload + Dateien"])
    box(300, 170, 176, 60, "UI", "Panel", ["MCP App im Chat", "Export, Data, Anki"])
    box(20, 232, 280, 60, "DT", "Desktop lädt erst bei Bedarf", ["Beschreibungen nicht im Kontext,", "bis das Modell sucht (Tool-Suche)"], focal=True)
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- Seite
def routing_html(tool: str, cases: list[dict], res: dict, w3: dict) -> tuple[str, dict]:
    meine = [c for c in cases if c["expect"] == tool and (c["id"] in res or c["id"] in w3)]
    if not meine:
        return "<p class='muted'>Kein Routing-Fall in den Logs.</p>", {}
    runs = ["ohne 1", "ohne 2", "TS 1", "TS 2"]
    stat = {"Name": [0, 0], "Auftrag": [0, 0], "Frage": [0, 0]}
    rows = []
    for c in meine:
        r = res.get(c["id"])
        if r:
            marks = "".join(f"<i class='{'g' if r[k][0] else 'r'}' title='{k}: {html.escape(r[k][1])}'></i>" for k in runs if k in r)
            ok = sum(r[k][0] for k in runs if k in r); n = sum(1 for k in runs if k in r)
            rot = "; ".join(f"{k}: {html.escape(r[k][1])}" for k in runs if k in r and not r[k][0])
        else:
            rr = w3[c["id"]]
            marks = f"<i class='{'g' if rr[0] else 'r'}' title='Vollprofil n=1: {html.escape(rr[1])}'></i>"
            ok, n = int(rr[0]), 1
            rot = "" if rr[0] else html.escape(rr[1])
        stat[c["art"]][0] += ok; stat[c["art"]][1] += n
        rows.append(f"<tr><td><span class='tag t-{c['art']}'>{c['art']}</span></td><td class='prompt'>{html.escape(c['prompt'].strip())}</td><td class='marks'>{marks} <span class='m'>{ok}/{n}</span></td><td class='muted small'>{rot}</td></tr>")
    tbl = ("<table class='cases'><thead><tr><th>Art</th><th>Prompt</th><th>Treffer</th><th>Wenn rot: gerufen</th></tr></thead><tbody>"
           + "".join(rows) + "</tbody></table>")
    return tbl, stat


def tool_card(tool: str, beschr: dict, cases: list[dict], res: dict, w3: dict, lauf: Path, laufres: dict) -> str:
    t = T[tool]
    d = beschr.get(tool, {"description": "", "params": []})
    tests = zaehle_tests(tool)
    rt, stat = routing_html(tool, cases, res, w3)
    dt = DESKTOP.get(tool, ("na", "nicht getestet", "kein Desktop-Lauf seit 03.10."))
    lr = laufres.get(tool)
    lauf_txt = (f"{lr['s']:.2f} s, {lr.get('type','text')}, {lr.get('len',0)//1024} KB Antwort" if lr and lr.get("ok") else ("Fehler: " + lr["err"] if lr else "—"))
    erz_name, erz_txt = ERZ[t["erzeugt"]]
    def ratio(k):
        o, n = stat.get(k, [0, 0])
        return f"{o}/{n}" if n else "–"
    gesamt_ok = sum(v[0] for v in stat.values()); gesamt_n = sum(v[1] for v in stat.values())
    cc_cls = "na" if not gesamt_n else ("ok" if gesamt_ok == gesamt_n else ("mid" if gesamt_ok >= gesamt_n * 0.6 else "no"))
    first = d["description"].split("\n\n")[0].strip()
    fence = re.search(r"Not this tool for:.*?(?=\n\n|\Z)", d["description"], re.S)
    return f"""
<article class="tool" id="{tool}" data-v="{t['v']}">
  <header class="tool-head" tabindex="0" role="button" aria-expanded="false" aria-controls="{tool}-body">
    <div class="tool-title"><span class="name">{tool}</span><span class="what">{html.escape(t['w'])}</span></div>
    <div class="tool-kpis">
      <span class="ver {VER[t['v']][0]}">{VER[t['v']][1]}</span>
      <span class="kpi"><b class="{cc_cls}">{gesamt_ok}/{gesamt_n}</b><span>CC Toolwahl</span></span>
      <span class="kpi"><b class="{dt[0]}">{html.escape(dt[1])}</b><span>Desktop</span></span>
      <span class="kpi"><b>{erz_name}</b><span>Output</span></span>
      <span class="kpi"><b>{tests['direkt_n'] + tests['modul_n'] + tests['ui_n']}</b><span>Tests</span></span>
    </div>
  </header>
  <div class="tool-body" id="{tool}-body" hidden>
    <section class="block">
      <h4>Was es tut</h4>
      <p>{html.escape(t['wie'])}</p>
      <div class="svgwrap">{pipeline_svg(tool)}</div>
      <div class="grid3">
        <div><h5>Dateien</h5><ul class="mono">{''.join(f'<li>{html.escape(x)}</li>' for x in t['files'])}</ul></div>
        <div><h5>Abhängigkeiten</h5><ul class="mono">{''.join(f'<li>{html.escape(x)}</li>' for x in t['deps'])}</ul>
             <h5>Parameter</h5><p class="mono small">{html.escape(', '.join(d['params']))}</p></div>
        <div><h5>Vorgespeichert oder erzeugt?</h5><p><b>{erz_name}:</b> {erz_txt}.</p>
             <h5>Heutiger Lauf (04.11., in-process)</h5><p class="mono small">{html.escape(lauf_txt)}</p></div>
      </div>
    </section>
    <section class="block">
      <h4>Was das Modell liest</h4>
      <p class="quote">{html.escape(first)}</p>
      {('<p class="quote fence">' + html.escape(fence.group(0)) + '</p>') if fence else ''}
      <p class="muted small">{len(d['description'])} Zeichen · ganze Beschreibung in <code>tests/__snapshots__/tools/{tool}.json</code>. Es gibt keine weitere Regel-Datei: diese Beschreibung und der eine <code>instructions</code>-Text des Servers sind alles, was das Modell über das Tool weiß.</p>
    </section>
    <section class="block">
      <h4>Output</h4>
      <div class="figs">{beispiel_html(tool, lauf)}{shots_html(tool)}</div>
    </section>
    <section class="block">
      <h4>Trifft das Modell das Tool?</h4>
      <div class="stat-row">
        <span class="stat"><b>{ratio('Name')}</b><span class="tag t-Name">Name</span> blanker Stoffname</span>
        <span class="stat"><b>{ratio('Auftrag')}</b><span class="tag t-Auftrag">Auftrag</span> nennt die Handlung (zeichne, plot, zeig)</span>
        <span class="stat"><b>{ratio('Frage')}</b><span class="tag t-Frage">Frage</span> Student fragt, nennt kein Tool</span>
        <span class="stat"><b class="{dt[0]}">{html.escape(dt[1])}</b><span class="tag t-DT">Desktop</span> {html.escape(dt[2])}</span>
      </div>
      <p class="muted small">Claude Code: 4 Läufe je Fall (2 mit allen Tools im Kontext, 2 mit Tool-Suche wie in Desktop), Attrappen-Server, misst nur die Wahl. Desktop: echter Server, frischer Chat je Versuch, Codex-Klicktest.</p>
      {rt}
    </section>
    <section class="block grid2">
      <div><h4>Mehrwert gegenüber Claude ohne Tool</h4><p>{html.escape(t['mehrwert'])}</p><p class="muted small">Einschätzung, außer wo Desktop-Zahlen genannt sind.</p></div>
      <div><h4>Schwierigkeiten</h4><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in t['schwer'])}</ul></div>
    </section>
    <section class="block">
      <h4>Wie gut getestet</h4>
      <div class="grid3">
        <div><h5>Direkte Aufrufe</h5><p><b>{tests['aufrufe']}</b> Aufrufe in {len(tests['direkt_dateien'])} Datei(en), <b>{tests['erstargs']}</b> verschiedene Eingaben</p><p class="mono small">{html.escape(', '.join(tests['direkt_dateien']) or '—')}</p></div>
        <div><h5>Modultests dahinter</h5><p><b>{tests['modul_n']}</b> Tests</p><p class="mono small">{html.escape(', '.join(tests['modul_dateien']) or '—')}</p></div>
        <div><h5>Panel-Tests (JS)</h5><p><b>{tests['ui_n']}</b> Tests</p><p class="mono small">{html.escape(', '.join(tests['ui_dateien']) or '—')}</p></div>
      </div>
      <p class="muted small">Alle Modultests laufen ohne Netz (requests.get gepatcht, conftest sperrt Zugriffe). Echtes Netz nur in <code>scripts/handshake.sh</code>, <code>npm run test:host</code> (echter Server im Sandbox-Iframe) und <code>scripts/identitaet.py</code> (24 Stoffe → InChIKey). Golden-Dateien (<code>tests/__fixtures__/*.golden.svg</code>) sind eingefrorene <em>Erwartungen</em>, keine gespeicherten Ausgaben.</p>
    </section>
    <div class="decide"><label for="d-{tool}">Deine Entscheidung:</label>
      <select id="d-{tool}" data-tool="{tool}"><option value="">— offen —</option>
      {''.join(f'<option>{o}</option>' for o in ['Behalten','Nachbessern','Ins Standardprofil','Eigenes Pharma-Profil','Raus'])}</select></div>
  </div>
</article>"""


def baue(lauf: Path, ziel: Path, welle3_log: Path | None) -> None:
    res = lies_routing()
    w3 = lies_welle3(welle3_log)
    cases = lies_faelle()
    beschr = lies_beschreibungen()
    laufres = json.loads((lauf / "_ergebnis.json").read_text()) if (lauf / "_ergebnis.json").exists() else {}
    gesamt = {"Name": [0, 0], "Auftrag": [0, 0], "Frage": [0, 0]}
    for c in cases:
        r = res.get(c["id"])
        if r:
            gesamt[c["art"]][0] += sum(v[0] for v in r.values()); gesamt[c["art"]][1] += len(r)
    ts = {"Name": [0, 0], "Auftrag": [0, 0], "Frage": [0, 0]}
    for c in cases:
        r = res.get(c["id"])
        if r:
            ts[c["art"]][0] += sum(r[k][0] for k in ("TS 1", "TS 2") if k in r); ts[c["art"]][1] += sum(1 for k in ("TS 1", "TS 2") if k in r)

    areas_html = []
    for aid, aname, adesc in AREAS:
        tools = [t for t in TOOLS_MVP + TOOLS_W3 if T[t]["a"] == aid]
        cards = "".join(tool_card(t, beschr, cases, res, w3, lauf, laufres) for t in tools)
        areas_html.append(f"<section class='area'><div class='area-head'><h2>{aname}</h2><p>{adesc} · {len(tools)} Tools</p></div>{cards}</section>")

    page = f"""<title>ChemDraw Werkzeugbilanz</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap">
<style>
/* Layout: Kopf mit Zahlen → ein Diagramm zur Toolwahl → je Bereich aufklappbare Tool-Karten (Steckbrief, Ablauf, Output, Routing, Mehrwert, Tests) → Entscheidungen als Prompt. */
:root{{
  --bg:#f5f5f5; --panel:#ffffff; --fg:#2d3142; --muted:#4f5d75; --soft:#5a6580; --line:rgba(45,49,66,0.14); --line2:#bfc0c0;
  --accent:#bf4520; --accent-tint:rgba(191,69,32,0.08); --link:#2e5aa8;
  --good:#1d7a4c; --good-soft:#dff1e7; --warn:#a46200; --warn-soft:#f8ecd6; --bad:#b3261e; --bad-soft:#f8e1df;
  --d-paper:#f5f5f5; --d-ink:#2d3142; --d-muted:#4f5d75; --d-soft:#5a6580; --d-accent:#bf4520; --d-accent-tint:rgba(191,69,32,0.08);
  --f-serif:'Instrument Serif',Georgia,serif; --f-sans:'Geist',system-ui,sans-serif; --f-mono:'Geist Mono',ui-monospace,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bg:#2d3142; --panel:#393e53; --fg:#f5f5f5; --muted:#bfc0c0; --soft:#949eb2; --line:rgba(245,245,245,0.14); --line2:rgba(191,192,192,0.3);
  --accent:#f08a59; --accent-tint:rgba(240,138,89,0.10); --link:#739fdf;
  --good:#5cc790; --good-soft:#163a28; --warn:#e6a64a; --warn-soft:#3a2b12; --bad:#f08a82; --bad-soft:#44201d;
  --d-paper:#393e53; --d-ink:#f5f5f5; --d-muted:#bfc0c0; --d-soft:#949eb2; --d-accent:#f08a59; --d-accent-tint:rgba(240,138,89,0.10);
  color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#2d3142; --panel:#393e53; --fg:#f5f5f5; --muted:#bfc0c0; --soft:#949eb2; --line:rgba(245,245,245,0.14); --line2:rgba(191,192,192,0.3);
  --accent:#f08a59; --accent-tint:rgba(240,138,89,0.10); --link:#739fdf;
  --good:#5cc790; --good-soft:#163a28; --warn:#e6a64a; --warn-soft:#3a2b12; --bad:#f08a82; --bad-soft:#44201d;
  --d-paper:#393e53; --d-ink:#f5f5f5; --d-muted:#bfc0c0; --d-soft:#949eb2; --d-accent:#f08a59; --d-accent-tint:rgba(240,138,89,0.10);
  color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--fg);font:15px/1.55 var(--f-sans);margin:0}}
.wrap{{max-width:1180px;margin:0 auto;padding-block:32px 72px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:28px}}
.eyebrow{{font:500 11px/1 var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
h1{{font:400 clamp(30px,4.5vw,44px)/1.1 var(--f-serif);margin:8px 0 10px;text-wrap:balance}}
h2{{font:400 26px/1.2 var(--f-serif);margin:0;text-wrap:balance}}
h3{{font:400 22px/1.2 var(--f-serif);margin:0 0 8px}}
h4{{font:600 13px/1.3 var(--f-sans);letter-spacing:.02em;margin:0 0 8px;color:var(--fg)}}
h5{{font:500 10px/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:10px 0 4px}}
p{{margin:0 0 8px}} ul{{margin:0;padding-left:18px}} li{{margin-bottom:3px}}
.lead{{color:var(--muted);max-width:70ch}}
.muted{{color:var(--muted)}} .small{{font-size:13px}} .mono{{font-family:var(--f-mono);font-size:12.5px}} ul.mono li{{margin-bottom:2px}}
code{{font-family:var(--f-mono);font-size:.9em;background:var(--accent-tint);padding:0 4px;border-radius:3px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.stat-tile{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px 16px;display:flex;flex-direction:column;gap:4px}}
.stat-tile b{{font:400 30px/1 var(--f-serif);font-variant-numeric:tabular-nums}} .stat-tile span{{color:var(--muted);font-size:13px}}
.finding{{display:grid;grid-template-columns:1.1fr 1fr 0.9fr;gap:12px}}
@media (max-width:760px){{.finding{{grid-template-columns:1fr}}}}
.finding div{{padding:12px 14px;border-radius:6px;font-size:14px;min-width:0}}
.finding .g{{background:var(--good-soft)}} .finding .w{{background:var(--warn-soft)}} .finding .b{{background:var(--bad-soft)}}
.finding strong{{display:block;margin-bottom:2px}}
.explain{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:18px 20px;display:flex;flex-direction:column;gap:10px}}
.explain .cols{{display:grid;grid-template-columns:1.2fr 1fr;gap:18px}} @media (max-width:760px){{.explain .cols{{grid-template-columns:1fr}}}}
.explain .cols>div{{min-width:0}}
.svgwrap{{overflow-x:auto;margin:6px 0 10px}} .svgwrap svg{{display:block;min-width:0}}
svg.pipe{{display:block;height:auto}} /* behält seine Breite, der Wrapper scrollt (Lesbarkeit vor Verkleinerung) */
.callout{{font:italic 16px/1.4 var(--f-serif);color:var(--fg);border-left:2px solid var(--accent);padding-left:12px;margin:6px 0}}
.controls{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.chip{{font:500 13px var(--f-sans);border:1px solid var(--line2);background:var(--panel);color:var(--fg);padding:5px 12px;border-radius:999px;cursor:pointer}}
.chip[aria-pressed="true"]{{background:var(--fg);border-color:var(--fg);color:var(--bg)}}
.chip:focus-visible,.tool-head:focus-visible,select:focus-visible,button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
section.area{{display:flex;flex-direction:column;gap:10px}}
.area-head{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line2);padding-bottom:6px}}
.area-head p{{margin:0;color:var(--muted);font-size:14px}}
.tool{{background:var(--panel);border:1px solid var(--line);border-radius:6px}}
.tool-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;flex-wrap:wrap}}
.tool-head:hover{{background:var(--accent-tint)}}
.tool-title{{display:flex;flex-direction:column;min-width:0}}
.name{{font:500 14px var(--f-mono)}} .what{{color:var(--muted);font-size:13px}}
.tool-kpis{{display:flex;gap:14px;flex-wrap:wrap;align-items:center}}
.kpi{{display:flex;flex-direction:column;align-items:flex-start;min-width:64px}}
.kpi b{{font:600 14px var(--f-sans);font-variant-numeric:tabular-nums}} .kpi span{{font:500 9px var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
.ver{{font:500 11px var(--f-mono);padding:2px 8px;border-radius:3px;white-space:nowrap}}
.v06{{background:var(--good-soft);color:var(--good)}} .v07{{background:var(--accent-tint);color:var(--accent)}} .vw3{{background:var(--warn-soft);color:var(--warn)}}
.ok{{color:var(--good)}} .mid{{color:var(--warn)}} .no{{color:var(--bad)}} .na{{color:var(--muted)}}
.tool-body{{border-top:1px solid var(--line);padding:4px 16px 16px;display:flex;flex-direction:column;gap:6px}}
.block{{padding:12px 0;border-bottom:1px dashed var(--line)}} .block:last-of-type{{border-bottom:0}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px 24px}} .grid3>div{{min-width:0}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px 24px}} @media (max-width:760px){{.grid2{{grid-template-columns:1fr}}}} .grid2>div{{min-width:0}}
.quote{{font-size:14px;background:var(--bg);border-radius:4px;padding:10px 12px;white-space:pre-wrap;margin:0 0 6px}}
.quote.fence{{border-left:2px solid var(--accent)}}
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
figure{{margin:0;min-width:0}} figure img{{max-width:100%;height:auto;border:1px solid var(--line);border-radius:4px;background:#fff}}
figcaption{{font-size:12px;color:var(--muted);margin-top:4px}}
.svgbox{{background:#fff;border:1px solid var(--line);border-radius:4px;padding:6px;overflow-x:auto}} .svgbox svg{{max-width:100%;height:auto}}
pre.out{{font:12px/1.45 var(--f-mono);background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:10px;overflow-x:auto;white-space:pre-wrap;margin:0;max-height:360px;overflow-y:auto}}
.stat-row{{display:flex;flex-wrap:wrap;gap:8px 22px;margin-bottom:8px}}
.stat-row .stat{{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--muted)}}
.stat-row .stat b{{font:600 16px var(--f-sans);color:var(--fg);font-variant-numeric:tabular-nums}}
.tag{{font:500 10px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;padding:2px 6px;border-radius:3px;border:1px solid var(--line2);white-space:nowrap}}
.t-Name{{border-color:var(--muted)}} .t-Auftrag{{background:var(--good-soft);border-color:transparent;color:var(--good)}} .t-Frage{{background:var(--warn-soft);border-color:transparent;color:var(--warn)}} .t-DT{{background:var(--accent-tint);border-color:transparent;color:var(--accent)}}
.tblwrap{{overflow-x:auto}}
table.cases{{border-collapse:collapse;width:100%;font-size:13px}}
table.cases th{{font:500 10px var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}}
table.cases td{{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
td.prompt{{max-width:52ch}} td.marks{{white-space:nowrap}}
.marks i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:3px;vertical-align:middle}}
.marks i.g{{background:var(--good)}} .marks i.r{{background:var(--bad)}} .marks .m{{font:500 12px var(--f-mono);margin-left:4px}}
.decide{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding-top:12px;border-top:1px solid var(--line)}}
select{{font:14px var(--f-sans);background:var(--panel);color:var(--fg);border:1px solid var(--line2);border-radius:4px;padding:4px 8px}}
.out-box{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px;display:flex;flex-direction:column;gap:10px}}
.out-box textarea{{width:100%;min-height:120px;font:13px/1.5 var(--f-mono);background:var(--bg);color:var(--fg);border:1px solid var(--line2);border-radius:4px;padding:10px;resize:vertical}}
.btn{{font:600 14px var(--f-sans);background:var(--fg);color:var(--bg);border:0;border-radius:4px;padding:8px 16px;cursor:pointer;align-self:flex-start}}
.src{{font-size:12px;color:var(--muted)}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:13px;color:var(--muted)}}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">chemdraw-mcp · Stand 04.11.2026 · Repo bereit für 0.7.0, draußen 0.6.0</div>
    <h1>Werkzeugbilanz: 23 Tools, jedes einzeln geprüft</h1>
    <p class="lead">Je Tool: welche Dateien es ausmachen, wie die Anfrage durchläuft, was es ausgibt, ob das Modell es bei einem Auftrag und bei einer Studentenfrage trifft, was es gegenüber Claude ohne Server bringt, wo es hakt und wie breit es getestet ist. Zahlen sind gezählt oder gemessen; Einschätzungen sind als solche markiert.</p>
  </header>

  <div class="stats">
    <div class="stat-tile"><b>{gesamt['Auftrag'][0]}/{gesamt['Auftrag'][1]}</b><span>Toolwahl bei einem <b style="font:inherit">Auftrag</b> („Zeichne …“), Claude Code, 4 Läufe</span></div>
    <div class="stat-tile"><b>{gesamt['Frage'][0]}/{gesamt['Frage'][1]}</b><span>Toolwahl bei einer <b style="font:inherit">Studentenfrage</b> ohne Toolwort</span></div>
    <div class="stat-tile"><b>{ts['Frage'][0]}/{ts['Frage'][1]}</b><span>dieselben Fragen mit Tool-Suche (Desktop-Modus)</span></div>
    <div class="stat-tile"><b>0/18</b><span>Desktop, Wissensfragen ohne Zusatz · mit „— nutze ChemDraw“ 6/6</span></div>
  </div>

  <div class="finding">
    <div class="g"><strong>Aufträge treffen.</strong> „Zeichne“, „Plot“, „DC meiner Veresterung“: in Claude Code fast immer, in Desktop bei allen 12 Panel-Tools. Was dann erscheint, wird je Eingabe neu gerechnet (RDKit, matplotlib, Ladungsbilanz), nicht aus einem Speicher geholt.</div>
    <div class="w"><strong>Fragen fallen durch.</strong> „Warum ist Wasser gewinkelt?“, „Was ist der Unterschied …?“, „Welchen pH hat …?“: das Modell antwortet aus dem Gedächtnis. In Desktop traf das alle 6 gemessenen Wissensfragen (0/18 Chats), weil die Tool-Beschreibungen dort erst nachgeladen werden.</div>
    <div class="b"><strong>Zwei Tools sind Vorlage oder Tabelle.</strong> generate_mechanism zeichnet drei feste Lehrbuchbeispiele (Substrate werden nur geprüft), predict_spectrum wendet 31 kuratierte Regeln an. Alles andere rechnet oder holt live aus PubChem.</div>
  </div>

  <section class="explain">
    <h2>Wie die Toolwahl funktioniert</h2>
    <div class="cols">
      <div>
        <p>Es gibt keine Regel-Datei „wenn der Nutzer X schreibt, nimm Tool Y“. Der Server schickt beim Start zwei Dinge: einen <code>instructions</code>-Text (die Bereichskarte mit Standardregeln wie „ein blanker Stoffname heißt generate_molecule“) und je Tool eine Beschreibung mit Parametern. Beides landet im Kontext des Modells, und das Modell entscheidet beim Lesen des Prompts selbst, ob es ein Tool ruft oder aus dem Gedächtnis antwortet.</p>
        <p>Deshalb ist Routing ein Textproblem: eine Beschreibung, die ihren Nachbarn nicht ausschließt („Not this tool for …“), gewinnt dessen Fälle; ein Superlativ zieht Aufrufe ab, ohne besser zu sein. Beides ist in <code>tests/test_server_taxonomy.py</code> erzwungen, die 67 Prompts in <code>evals/tool-routing/cases.yaml</code> sind die Messlatte.</p>
        <p class="callout">Desktop lädt die Beschreibungen erst, wenn das Modell nach einem Tool sucht. Eine Wissensfrage löst diese Suche nicht aus, also bleibt das Tool unsichtbar, so gut seine Beschreibung auch ist.</p>
      </div>
      <div class="svgwrap">{toolwahl_svg()}</div>
    </div>
    <div class="legend">
      <span><span class="tag t-Name">Name</span> blanker Stoffname („Coffein“)</span>
      <span><span class="tag t-Auftrag">Auftrag</span> Prompt nennt die Handlung („Zeichne“, „Plot“, „Zeig mir … als 3D“)</span>
      <span><span class="tag t-Frage">Frage</span> Student fragt oder erzählt, ohne Toolwort („Warum …?“, „Ich schreibe Freitag …“)</span>
      <span><span class="tag t-DT">Desktop</span> echter Server in Claude Desktop, Klicktest Codex 02./03.11.</span>
    </div>
  </section>

  <div class="controls" role="group" aria-label="Filter Version">
    <span class="eyebrow">Version</span>
    <button class="chip" data-f="all" aria-pressed="true">Alle 23</button>
    <button class="chip" data-f="0.6" aria-pressed="false">0.6 draußen (7)</button>
    <button class="chip" data-f="0.7" aria-pressed="false">0.7 neu (9)</button>
    <button class="chip" data-f="w3" aria-pressed="false">Welle 3 (7)</button>
    <button class="chip" id="openall" aria-pressed="false">Alle aufklappen</button>
  </div>

  {''.join(areas_html)}

  <div class="out-box">
    <h2>Deine Entscheidungen</h2>
    <p class="src">Je Tool unten in der Karte wählen. Der Text geht als Prompt zurück an Claude.</p>
    <textarea id="prompt" readonly aria-label="Prompt mit Entscheidungen"></textarea>
    <button class="btn" id="copy">Als Prompt kopieren</button>
  </div>

  <p class="src">Quellen: Toolwahl aus <code>docs/evidence/routing-2026-11-03/</code> (57 Fälle × 4 Läufe, Claude Code, Attrappen-Server) und für Welle 3 ein Lauf im Vollprofil am 04.11.; Desktop aus <code>docs/desktop-abnahme-2026-11-02.md</code> (02.11. und Nachmessung 03.11., Codex); Beschreibungen aus <code>tests/__snapshots__/tools/</code>; Testzahlen gezählt in <code>tests/</code> und <code>chemdraw_tool/ui/src/</code>; Beispielausgaben aus einem Lauf aller 23 Tools am 04.11. (<code>scripts/werkzeugbilanz_lauf.py</code>). Seite gebaut von <code>scripts/werkzeugbilanz.py</code>.</p>
</div>

<script>
const decisions={{}};
function toggle(h){{const b=document.getElementById(h.getAttribute('aria-controls'));const open=h.getAttribute('aria-expanded')==='true';h.setAttribute('aria-expanded',!open);b.hidden=open;}}
document.querySelectorAll('.tool-head').forEach(h=>{{h.addEventListener('click',()=>toggle(h));h.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();toggle(h)}}}})}});
document.querySelectorAll('.chip[data-f]').forEach(c=>c.addEventListener('click',()=>{{
  const f=c.dataset.f;document.querySelectorAll('.chip[data-f]').forEach(x=>x.setAttribute('aria-pressed',x===c));
  document.querySelectorAll('.tool').forEach(t=>{{t.hidden=!(f==='all'||t.dataset.v===f)}});
  document.querySelectorAll('section.area').forEach(a=>{{a.hidden=![...a.querySelectorAll('.tool')].some(t=>!t.hidden)}});
}}));
document.getElementById('openall').addEventListener('click',e=>{{
  const on=e.target.getAttribute('aria-pressed')!=='true';e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Alle zuklappen':'Alle aufklappen';
  document.querySelectorAll('.tool-head').forEach(h=>{{h.setAttribute('aria-expanded',on);document.getElementById(h.getAttribute('aria-controls')).hidden=!on}});
}});
function updatePrompt(){{
  const e=Object.entries(decisions);
  document.getElementById('prompt').value=e.length
   ? 'chemdraw-mcp, Werkzeugbilanz 04.11.2026 — meine Entscheidungen je Tool:\\n'+e.map(([t,d])=>`- ${{t}}: ${{d}}`).join('\\n')+'\\n\\nBitte in plans/mcp-server.md eintragen und die nächsten Schritte daraus ableiten.'
   : 'Noch keine Entscheidung gewählt. Karte aufklappen und unten wählen.';
}}
document.querySelectorAll('select[data-tool]').forEach(s=>s.addEventListener('change',e=>{{if(e.target.value)decisions[s.dataset.tool]=e.target.value;else delete decisions[s.dataset.tool];updatePrompt()}}));
document.getElementById('copy').addEventListener('click',async e=>{{
  const ta=document.getElementById('prompt');
  try{{await navigator.clipboard.writeText(ta.value);e.target.textContent='Kopiert'}}catch{{ta.select();e.target.textContent='Markiert – mit ⌘C kopieren'}}
  setTimeout(()=>e.target.textContent='Als Prompt kopieren',2000);
}});
const h=location.hash.replace('#','');if(h&&document.getElementById(h)){{const hd=document.querySelector('#'+CSS.escape(h)+' .tool-head');if(hd)toggle(hd)}}
updatePrompt();
</script>
"""
    ziel.write_text(page)
    print(f"geschrieben: {ziel} ({ziel.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    args = sys.argv[1:]
    w3 = None
    if "--welle3-log" in args:
        i = args.index("--welle3-log"); w3 = Path(args[i + 1]); del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    baue(Path(args[0]), Path(args[1]), w3)
