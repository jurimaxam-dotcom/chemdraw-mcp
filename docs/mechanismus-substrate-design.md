# Mechanismus mit eigenen Molekülen — Design-Notiz (Etappe B, 04.11.2026)

**Frage (Jay, plans/mcp-server.md, Punkt B):** Kann `generate_mechanism` das Molekül des
Studierenden zeichnen statt der festen Vorlage? **Antwort:** Ja, für die drei vorhandenen
Familien (SN2, SN1, Fischer-Veresterung) innerhalb je einer benannten Unterstützungsgrenze
(Codex-Vorgabe: keine pauschale Beliebigkeit). Alles außerhalb bekommt eine Fehlermeldung mit
Grund, nicht ein falsches Bild. Release: erst mit 0.8.0 (Branch `mechanismus-substrate`).

Neues Modul: `chemdraw_tool/mechanism_substrate.py`. `mechanism_coords.py` (neu: `layout_anchored`) und
`mechanism_renderer.py` bleiben in der Schnittstelle gleich — sie bekommen wie bisher
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
   Dadurch bleibt jedes Atom über alle Schritte identifizierbar (Layout: `layout_anchored`, siehe (c)), nicht nur die
   Reaktionsatome; `_render_mols_svg` löscht die Maps vor dem Zeichnen.
3. Eindeutigkeit: genau ein Treffer je Rolle. Zwei Halogene, zwei COOH-Gruppen, ein Molekül in
   beiden Rollen (Hydroxysäure) oder eine fehlende Rolle → Ablehnung mit Grund.
4. Klassifikation am Zentrum (Zahl der C-Nachbarn von `:1`, aromatischer/allylischer
   Nachbar) entscheidet die Grenze in (d), nicht ein loses SMARTS wie bisher (`[O,N,S:3]` ließ
   Wasser als SN2-Nucleophil durch).

## (b) Zwischenstufen und Produkte ableiten

Pro Schritt eine Transformation des gemappten Zustands; danach `Chem.MolToSmiles` des
gemappten Moleküls → Liste für das Layout (`layout_anchored`).

- **Gültige Moleküle per `rdChemReactions`** (Reaktions-SMARTS, `RunReactants`):
  - SN2-Produkt: `[C@:1][X:2].[Nu-:3]>>[C@@:1][Nu+0:3].[X-:2]` — `@`→`@@` lässt RDKit die
    Konfiguration invertieren (`molInversionFlag`); am achiralen Zentrum wirkungslos.
  - SN1-Produkt: `[C+:1].[*:3]>>[C+0:1]-[*+0:3]` für Anionen. Wasser/Alkohol (Runde 3,
    05.11.2026): `[C+:1].[O:3]>>[C+0:1]-[O+:3]` → Oxonium-Ion, ein H als eigenes Atom
    (`H_LEAVING` = 9), Deprotonierung per `_drop_h` → ROH/ROR′ + X⁻ + H⁺ (siehe (g)10).
  - Fischer (Etappe E, 05.11.2026, nach Clayden Kap. 10 — sieben Stationen): Protonierung
    `[C:1]=[O:2]>>[C+:1]-[O:2]` — die protonierte Säure wird **bewusst als Carbokation-Grenzformel
    C⁺(OH)₂** gezeichnet (die Grenzformel, an der der Alkohol angreift; die C=O⁺H-Form ist
    gleichwertig); Angriff `[C+:1].[O:4]>>[C+0:1]-[O+:4]` → Oxonium am Alkohol-O, sein H als
    eigenes Atom (Map 8); **Protonentransfer** O4–H → O3 (`RWMol`: Bindung umhängen, O4 neutral,
    O3 +1) → C–OH₂⁺; **Wasserabspaltung**: C–O3 bricht, O2 bildet C=O⁺H (H als Atom, Map 7) →
    protonierter Ester + H₂O; **Deprotonierung** → Ester + H₂O + H⁺. Jedes Zwischenprodukt wird
    voll sanitisiert (Valenz, Ladung), Test `test_fischer_folgt_clayden_mit_protonentransfer`.
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
`3 lone_pair → 1`; Fischer `2 lone_pair → 7 (H⁺)`, `4 lone_pair → 1`, Protonentransfer `3 lone_pair → 8 (H)` +
`bond 8–4 → 4`, Wasserabspaltung `bond 1–3 → 3` + `2 lone_pair → Bindung 1–2` (Ziel ist die
Mitte der entstehenden C=O-Bindung: `target=(1, "bond_to", 2)`), Deprotonierung `bond 7–2 → 2`.
Weil (a) die Map-IDs auf die gefundenen Atome legt, zeigen die Pfeile automatisch auf
das richtige Atom des Nutzer-Moleküls. Eduktreihenfolge in Schritt 1 (propagiert über alle
Schritte): SN2 Nucleophil links, Halogenid rechts; SN1 Halogenid, Nucleophil; Fischer Säure,
Alkohol, H⁺.

**Layout (nach Sichtung geändert):** `stabilize_sequence` übernahm die Positionen des
Vorschritts — bei 2-Brombutan + CN⁻ behielt das Nucleophil im Produkt seinen Platz aus Schritt 1
(meterlange C–C-Bindung) und kam im Übergangszustand nicht von der Rückseite. Der Substratweg
nutzt deshalb `mechanism_coords.layout_anchored`: jeder Schritt gibt je Molekül feste Positionen
für das Reaktionszentrum und dessen direkte Nachbarn vor (`MechanismStep.anchors`, in
Bindungslängen, Zentrum im Ursprung), RDKit legt den Rest drumherum; stößt ein Nebenmolekül an,
wird es nach außen geschoben; Moleküle ohne Anker stehen rechts daneben. SN2: Abgangsgruppe auf
+x, Nucleophil auf −x, Substituenten bei 120°/240° (Edukt), 90°/270° (Übergangszustand),
60°/300° (Produkt — der umgeklappte Regenschirm). **Zentrum im Ring** (Etappe E): die zwei
Ring-Nachbarn bekommen ein Winkelpaar mit 120° Abstand — Übergangszustand 30°/150° (Ring über der
Achse Nu···C···X), SN1 150°/270° mit dem dritten Substituenten auf 90°; sonst faltete RDKit den
Sechsring (90°/270°) oder zog ein Ringatom gerade und beschriftete es mit „C“. Geprüft:
`test_ringe_bleiben_regelmaessig_in_jedem_schritt`, `test_kein_geruest_kohlenstoff_traegt_ein_c`.

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
  Tertiäres Halogenid + Cyanid wird gezeichnet, steht aber nicht in der Substrat-Matrix: kein
  Lehrbuch-SN1 (E2 überwiegt, am Kation entsteht nach Kornblum eher das Isonitril; Sichtung
  05.11.2026) — die Matrix zeigt stattdessen den Azid-Abfang des tert-Butyl-Kations.
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
Produkt) oder das Layout (`layout_anchored`/Renderer wirft), wird die Vorlage gezeichnet.
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

## (g) Zeichenkonventionen (Etappe E, 05.11.2026)

**Referenz:** Clayden, Greeves, Warren, *Organic Chemistry*, 2. Aufl. (OUP 2012) — Jays Wahl 05.11.;
kein PDF vorhanden, daher aus Kenntnis des Buchs (Kap. 5 „Organic reactions", Kap. 10
„Nucleophilic substitution at the carbonyl group", Kap. 15 „Nucleophilic substitution at saturated
carbon"; Kapitelzuordnung ohne Seitenangabe, nicht am Buch geprüft) und gegengelesen an freien Quellen:
[LT-Curly] = LibreTexts „The Use of Curly Arrows" (chem.libretexts.org, Supplemental Modules →
Fundamentals), [LT-Malik] = LibreTexts Malik, *Organic Chemistry Part 1*, 4.7 „Conventions followed
for using curly arrows", [OS-6.5] = OpenStax *Organic Chemistry* 6.5 „Using Curved Arrows in Polar
Reaction Mechanisms". Keine Abbildung übernommen.

| # | Regel | Quelle | Im Code |
|---|---|---|---|
| 1 | Pfeil = Bewegung eines Elektronenpaars, Schwanz an der Elektronenquelle (freies Paar oder Bindung), Spitze an der Senke; nie Atombewegung | Clayden Kap. 5; [LT-Curly]; [OS-6.5] | `CurvedArrow` |
| 2 | Freies Paar: Schwanz am Atom mit dem Paar (außerhalb seiner Beschriftung); Bindung: Schwanz an der Bindungsmitte | [LT-Malik] Regel 1–2 | Renderer, Geometrie-Test |
| 3 | Neue Bindung: Spitze zum Zielatom bzw. zur Mitte der entstehenden Bindung; neues freies Paar (Abgangsgruppe): Spitze zum Atom, das es trägt | [LT-Malik] Regel 3–4; [LT-Curly] | Renderer, Geometrie-Test |
| 4 | Oktettregel: bekommt ein volles Atom ein Paar, muss im selben Schritt eins gehen (SN2: C–X bricht, während Nu–C entsteht → zwei Pfeile in einem Schritt) | [OS-6.5] Regel 4; Clayden Kap. 15 | SN2-Schritt 2 |
| 5 | Pfeile sind gekrümmt, auch wenn das Paar „geradeaus" wandert; Pfeil und Beschriftungen überschneiden sich nicht | [LT-Curly]; Lesbarkeit | Geometrie-Test |
| 6 | Übergangszustand in eckigen Klammern mit ‡, Teilbindungen gestrichelt, Ladung als δ⁻ verteilt: Nucleophil und Abgangsgruppe je δ⁻, keine vollen Ladungen (sonst Summe −2 statt −1) | Clayden Kap. 15 | Renderer (Klammern); ÜZ-Moleküle neutral, `MechanismStep.partial_charges` {NU, X: „δ−“} als Text oben rechts am Symbol (Runde 3, R2); `test_sn2_uebergangszustand_traegt_delta_minus_statt_voller_ladungen` |
| 7 | SN2 kehrt die Konfiguration um (Walden); das Produkt trägt seinen CIP-Deskriptor | Clayden Kap. 15 | Schrittlabel + Stereo-Annotation |
| 8 | SN1 über planares Kation → Angriff von beiden Seiten, stereogenes Zentrum „racemic" | Clayden Kap. 15 | Schrittlabel |
| 9 | Fischer-Veresterung: Protonierung des Carbonyl-O, Angriff des Alkohols, Protonentransfer, Wasser verlässt als OH₂⁺, Deprotonierung; jeder Schritt reversibel | Clayden Kap. 10 | Sieben Stationen: Edukte, Protonierung, Angriff (→ Oxonium), Protonentransfer (→ OH₂⁺), Wasserabspaltung mit Rückbildung von C=O⁺H, Deprotonierung (H⁺ zurück), Produkte. Protonierte Säure als Grenzformel C⁺(OH)₂ gezeichnet (siehe (b)); Reversibilität nur im Text, nicht als ⇌ |
| 10 | SN1 mit neutralem Nucleophil (Wasser, Alkohol): der Angriff gibt das Oxonium-Ion R–OH₂⁺ bzw. R–O⁺(H)R′; erst die Deprotonierung (Pfeil von der O–H-Bindung zum O) gibt das Produkt, H⁺ steht in den Produkten | Clayden Kap. 15; [OS-11.4] OpenStax 11.4 „The SN1 Reaction“ (Hydrolyse von tert-Butylbromid über das protonierte Alkohol-Kation) | Sechs Stationen: Edukte, Abgang, Kation, Angriff, „Oxonium ion“, „Products“; Anionen fünf. Buchführung ohne Ausnahme, `test_gesamtladung_bleibt_erhalten` (Runde 3, R4) |

**Befund aus (g)9 (behoben 05.11.2026):** Die Fischer-Ableitung ließ Wasser von einem neutralen
OH abgehen. Seither Protonentransfer vor der Abspaltung; Vorlage und Substratweg sind dieselbe
Ableitung (die Vorlagen in `templates/` rufen `build_steps` mit den Beispiel-Substraten auf und
laufen durch `layout_anchored` — damit ist auch die gedehnte C–O-Bindung der alten SN2-Vorlage weg).

## Pfeil-Geometrie (Etappe E, 05.11.2026)

Anker eines Pfeilendes ist der **Rand der Atombeschriftung**, nicht der Atommittelpunkt; nur ein
unbeschriftetes Gerüst-C (keine Box) wird am Atom selbst angefahren. Die Boxen stammen aus den
Glyphenpfaden des RDKit-SVG (`class='atom-N'`), (R)/(S)-Notizen (`CIP_Code`) sind Hindernisse.
- Freies Paar: Schwanz 3,5 px außerhalb der Box der Quelle, auf der Seite, zu der der Bogen aufbricht.
- Bindung: Schwanz an der Bindungsmitte. Bindung → eigene Abgangsgruppe: Spitze neben deren Box,
  auf der Wölbungsseite.
- Spitze: 3,5 px vor der Box des Ziels, entlang der Anflugrichtung (Kontrollpunkt → Atom).
- Körper: schneidet er eine Box, erst die andere Seite, dann stärkere Wölbung (bis 3,2×).
- Toleranz im Test: 0,35 Bindungslängen; gleiche Bindungslänge in allen Schritten (± 5 %).
Konflikt Box vs. Mitte: Box gewinnt — liegt die Mitte in der Box, zählt nur der Rand.
Gleicher Maßstab beim Anzeigen braucht gleiche viewBoxen: `mechanism_renderer.unify_frames` über
alle Schritte, aufgerufen in `generate_mechanism` für Substrat- und Vorlagenweg
(Test `test_alle_schritte_teilen_eine_viewbox`). Grenze: bei langen Ketten (Stearinsäure) bestimmt
die Kette den Rahmen, das Reaktionszentrum wird bei 420 px Breite klein — Abkürzung (R = C₁₇H₃₅)
wäre der nächste Schritt, nicht gebaut. Prüfung: tests/test_mechanism_geometry.py.

**Ladung links, wenn die Bindung rechts abgeht (R1, Sichtung 05.11.2026):** RDKit setzt die Ladung
eines Atoms ohne H immer oben rechts, auch über eine nach rechts gehende Bindung — im Azid lag das
„⁻“ des endständigen N unter der Doppelbindung (gelesen als N=N⁺=N⁻). `_draw` gibt solchen Atomen
(Ladung, kein H, alle Nachbarn rechts) die Beschriftung `<sup>-</sup>N` per `_displayLabel`.
Prüfung: `test_keine_bindung_laeuft_durch_ein_beschriftungszeichen` — jedes Glyph einzeln gegen jede
gerade Bindungslinie, über Matrix und Vorlagen.
