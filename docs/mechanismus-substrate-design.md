# Mechanismus mit eigenen Molekülen — Design-Notiz (Etappe B, 04.11.2026)

**Frage (Jay, plans/mcp-server.md, Punkt B):** Kann `generate_mechanism` das Molekül des
Studierenden zeichnen statt der festen Vorlage? **Antwort:** Ja, für die drei vorhandenen
Familien (SN2, SN1, Fischer-Veresterung) innerhalb je einer benannten Unterstützungsgrenze
(Codex-Vorgabe: keine pauschale Beliebigkeit). Alles außerhalb bekommt eine Fehlermeldung mit
Grund, nicht ein falsches Bild. Release: erst mit 0.8.0 (Branch `mechanismus-substrate`).

Neues Modul: `chemdraw_tool/mechanism_substrate.py`. `mechanism_coords.py` und
`mechanism_renderer.py` bleiben unverändert in der Schnittstelle — sie bekommen wie bisher
eine Liste gemappter SMILES je Schritt und `CurvedArrow`s mit Map-IDs.

## (a) Reaktionszentrum finden

1. Jede Eingabe wird wie heute aufgelöst (`resolve`, parse-first). Danach wird sie in
   Fragmente zerlegt; Gegenionen (Na⁺, K⁺, Li⁺, Cs⁺, NH₄⁺ …, alle einatomigen Kationen und
   Ammonium) fallen weg — „sodium cyanide" liefert `[C-]#N`.
2. Je Familie gibt es ein Rollen-SMARTS mit Atom-Maps für die Atome, an denen etwas passiert:

   | Familie | Rolle | SMARTS (Maps = Reaktionszentrum) |
   |---|---|---|
   | SN2/SN1 | Substrat | `[CX4:1]-[Cl,Br,I:2]` |
   | SN2 | Nucleophil | Liste in (d), angreifendes Atom `:3` |
   | SN1 | Nucleophil | Liste in (d), angreifendes Atom `:3` |
   | Fischer | Säure | `[CX3:1](=[OX1:2])[OX2H1:3]` |
   | Fischer | Alkohol | `[OX2H1:4][CX4]` |

   Die Map-Nummer des Musters wird auf das getroffene Atom des Nutzer-Moleküls übertragen
   (1–9 = Reaktionszentrum, identisch mit den bisherigen Vorlagen, damit die
   `CurvedArrow`-Definitionen gleich bleiben). **Alle übrigen Atome** bekommen Map-IDs ab 100.
   Dadurch hält `stabilize_sequence` das ganze Gerüst über alle Schritte fest, nicht nur die
   Reaktionsatome; `_render_mols_svg` löscht die Maps vor dem Zeichnen.
3. Eindeutigkeit: genau ein Treffer je Rolle. Zwei Halogene, zwei COOH-Gruppen, ein Molekül in
   beiden Rollen (Hydroxysäure) oder eine fehlende Rolle → Ablehnung mit Grund.
4. Klassifikation am Zentrum (Zahl der C-Nachbarn von `:1`, aromatischer/allylischer
   Nachbar) entscheidet die Grenze in (d), nicht ein loses SMARTS wie bisher (`[O,N,S:3]` ließ
   Wasser als SN2-Nucleophil durch).

## (b) Zwischenstufen und Produkte ableiten

Pro Schritt eine Transformation des gemappten Zustands; danach `Chem.MolToSmiles` des
gemappten Moleküls → Liste für `stabilize_sequence`.

- **Gültige Moleküle per `rdChemReactions`** (Reaktions-SMARTS, `RunReactants`):
  - SN2-Produkt: `[C@:1][X:2].[Nu-:3]>>[C@@:1][Nu+0:3].[X-:2]` — `@`→`@@` lässt RDKit die
    Konfiguration invertieren (`molInversionFlag`); am achiralen Zentrum wirkungslos.
  - SN1-Produkt: `[C+:1].[Nu:3]>>[C+0:1]-[Nu+0:3]` (bei Wasser/Alkohol: Produkt nach
    Deprotonierung, wie die bisherige Vorlage).
  - Fischer: Protonierung `[C:1]=[O:2]>>[C+:1]-[O:2]` (Carbokation-Grenzformel wie bisher),
    Angriff `[C+:1].[O:4]>>[C+0:1]-[O:4]` (tetraedrische Zwischenstufe, neutral gezeichnet wie
    bisher), Abspaltung `[C:1]([O:2])([O:3])[O:4]>>[C:1](=[O:2])[O:4].[O:3]` (Ester + Wasser).
  - Nach `RunReactants` tragen die Template-Atome keine Map mehr, sondern `old_mapno`;
    die Map wird sofort zurückgeschrieben. Aus mehreren Produktsätzen wird derjenige gewählt,
    dessen `react_atom_idx` das gefundene Zentrum ist.
- **Bruchstücke per `RWMol`**, wo kein gültiges Molekül entsteht: SN2-Übergangszustand
  (Nucleophil, Kohlenstoffgerüst, Abgangsgruppe als drei Fragmente mit Teilbindungen) und
  SN1-Carbokation + Halogenid: `RemoveBond` + `SetFormalCharge`, Chiralität am Zentrum gelöscht
  (planar). Grund: Reaktions-SMARTS liefern sanitisierbare Produkte; ein Übergangszustand ist
  keins.
- **Stereo:** SN2 invertiert am Stereozentrum (geprüft per CIP: (R)-2-Brombutan + CN⁻ →
  (S)-2-Methylbutannitril). SN1 zeichnet das Produkt ohne Stereodeskriptor am Zentrum
  (planare Kation, Angriff von beiden Seiten); ist das Zentrum stereogen, sagt das Schrittlabel
  „racemic".

## (c) Pfeile an gemappte Atome

Die Pfeile bleiben `CurvedArrow`s mit Map-IDs 1–9 und sind je Familie fest (dieselben wie in
den Vorlagen): SN2 `3 lone_pair → 1`, `bond 1–2 → 2`; SN1 `bond 1–2 → 2`, dann
`3 lone_pair → 1`; Fischer `2 lone_pair → 7 (H⁺)`, `4 lone_pair → 1`, `bond 1–3 → 3`.
Weil (a) die Map-IDs auf die gefundenen Atome legt, zeigen die Pfeile automatisch auf
das richtige Atom des Nutzer-Moleküls. Eduktreihenfolge in Schritt 1 (propagiert über alle
Schritte): SN2 Nucleophil links, Halogenid rechts; SN1 Halogenid, Nucleophil; Fischer Säure,
Alkohol, H⁺.

SN2-Rückseitenangriff: Nach `stabilize_sequence` wird im Übergangszustand das
Nucleophil-Fragment so verschoben, dass sein angreifendes Atom gegenüber der Abgangsgruppe
liegt (`C + (C − X)·Faktor`), die Abgangsgruppe auf der Verlängerung von C–X.

## (d) Unterstützungsgrenze je Familie

- **SN2:** primäres oder sekundäres Alkylhalogenid (auch Methyl; Cl, Br, I an sp³-C) +
  anionisches Nucleophil aus der Liste OH⁻, CN⁻, I⁻, Br⁻, RO⁻ (Alkoxid), N₃⁻, RS⁻ (Thiolat,
  auch HS⁻). Tertiär → Grund „tertiary halide — use sn1"; neutrales Nucleophil → Grund „SN2
  needs an anionic nucleophile from the list"; Fluorid als Abgangsgruppe → „fluoride is not a
  leaving group here".
- **SN1:** tertiäres, benzylisches oder allylisches Halogenid (Cl, Br, I) + neutrales
  (Wasser, primärer/sekundärer/tertiärer Alkohol) oder anionisches Nucleophil (dieselbe Liste wie
  SN2). Primär/sekundär ohne Stabilisierung → „use sn2". Allyl-Umlagerung wird nicht gezeichnet
  (nur das direkte Produkt).
- **Fischer:** Carbonsäure mit genau einer COOH-Gruppe + primärer oder sekundärer Alkohol
  (auch Methanol), zwei getrennte Moleküle. Tertiärer Alkohol, Phenol, Hydroxysäure in einem
  Molekül → Ablehnung mit Grund.
- Alles andere: `ValueError` mit dem Grund im Klartext („The substrates do not fit the sn2
  mechanism: …"), nie ein stilles Ersatzbild.

**SN1-Lehrbuchbeispiel ändert sich:** Die Vorlage hieß „2-bromopropane + water" — ein
sekundäres Halogenid, das die neue Grenze für SN1 ablehnt. Sie wird auf
„2-bromo-2-methylpropane + water" umgestellt (tertiäres Kation), damit Vorlage und Grenze
dasselbe sagen.

## (e) Fallback

Passt das Substrat in die Grenze, scheitert aber die Ableitung (Reaktions-SMARTS liefert kein
Produkt) oder das Layout (`stabilize_sequence`/Renderer wirft), wird die Vorlage gezeichnet.
Die Antwort sagt es: `substrates_drawn=False`, `fallback_reason="…"`, Titel wieder
„textbook example: …". Leere `substrates` zeichnen die Vorlage ebenso, mit Grund
„no substrates given". Erfolgsfall: `substrates_drawn=True`, `fallback_reason=""`, Titel
nennt die Eingaben wörtlich („Nucleophilic Substitution (SN2) — 2-bromobutane + cyanide").

## (f) Beschreibung und `instructions`

- Beschreibung: „draws the user's own substrates" + je Familie ein Satz zur Grenze; der Satz
  „they are not drawn" entfällt. Fence bleibt: nur `sn1`, `sn2`, `fischer_ester`; alles andere
  → `generate_reaction`. Unter 2 KB, keine Superlative. Snapshot im selben Commit segnen.
- `_MVP_INSTRUCTIONS`: „(textbook examples; other mechanisms are not drawn)" wird falsch und
  wird zu „(draws the user's substrates within each family's limits; other mechanisms are not
  drawn)".
- Payload: `substrates_drawn: bool = False`, `fallback_reason: str = ""` — Defaults, das
  Panel (`MechanismView`) läuft unverändert.
