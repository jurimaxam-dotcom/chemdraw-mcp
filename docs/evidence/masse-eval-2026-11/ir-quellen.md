# IR-Ergänzungen: Bandlagen und Grenzen

Stand 06.11.2026. Die Quellen wurden an diesem Tag abgerufen; bei den laufend gepflegten Webseiten ist kein verlässliches Editionsjahr angegeben. Die Regeln liefern charakteristische Bereiche, keine stoff- oder lösungsmittelspezifisch berechneten Spektren. Die folgenden Zahlen sind aus den Tabellen entnommene Daten; alle Zuordnungen zu SMARTS sind unsere eingeschränkte Implementierung.

## Abgerufene Lehrbuchtabellen

- **[Reusch, Virtual Textbook of Organic Chemistry, Abschnitt 4](https://beta.organicchemistrydata.org/reusch/virtualtext/spectroscopy/infrared-spectroscopy)**, Prof. William H. Reusch, Michigan State University, gehostet von ACS Division of Organic Chemistry: Schwefel- und Phosphorfunktionen.
- **[Infrared Spectroscopy Absorption Table](https://chem.libretexts.org/Ancillary_Materials/Reference/Reference_Tables/Spectroscopic_Reference_Tables/Infrared_Spectroscopy_Absorption_Table)**, LibreTexts; auch als [Lehrtabelle der University of York](https://chemtl.york.ac.uk/data-analysis-reporting/analytical-techniques/ir/ir-spectroscopy-absorption-table) mit Herkunftsnachweis angeboten: Halogene, Sulfonamid und Azid.
- **[Typical IR Absorption Frequencies](https://clas.niu.edu/clas/chembio/research/analytical-lab/ftir/ir-frequencies-table.shtml)**, Northern Illinois University, Department of Chemistry and Biochemistry: Imine/Oxime und N–H-Frequenzbereich.

| Ergänzung | Bereich / cm⁻¹ | Quelle | Grenze der implementierten Regel |
|---|---:|---|---|
| C–F | 1000–1400 | LibreTexts/York | Kohlenstoffgebunden, einschließlich Aryl; kein freies Fluorid |
| C–Cl | 550–850 | LibreTexts/York | Kohlenstoffgebunden, einschließlich Aryl; kein Chloridion |
| C–Br | 515–690 | LibreTexts/York | Kohlenstoffgebunden |
| C–I | 500–600 | LibreTexts/York | Kohlenstoffgebunden |
| Sulfonamid, asymmetrisch / symmetrisch | 1335–1370 / 1155–1170 | LibreTexts/York | R–SO₂–N, kein Sulfamat oder Sulfaminsäurederivat |
| Sulfon, asymmetrisch / symmetrisch | 1300–1350 / 1120–1160 | Reusch | R–SO₂–R; schließt Sulfonamide und Sulfonsäuren aus |
| Sulfoxid | 1030–1060 | Reusch | R–S(O)–R |
| Thiocarbonyl | 1050–1200 | Reusch | C=S; Hinweis auf mögliche Modenkopplung bleibt in der Rückgabe |
| Organisches Azid | 2120–2160 | LibreTexts/York | einschließlich der ladungsgetrennten RDKit-Schreibweise |
| Imin/Oxim | 1640–1690 | NIU | einfache C=N; Amidine/Guanidine ausgeschlossen |
| Phosphat P=O | 1100–1200 | Reusch | P(O)(OR)₃, einschließlich entsprechender OH-Gruppen; keine anionischen O-Nachbarn |
| Phosphonat P=O | 1230–1260 | Reusch | R–P(O)(OR)₂ |
| Phosphoramid P=O | 1200–1275 | Reusch | N–P(O)(OR)₂; keine Verallgemeinerung auf mehrfach N-substituierte P-Zentren |
| Phosphor-Ester P–O | 900–1050 | Reusch | P(O)–O–C; zählt im Evaluator ausdrücklich **nicht** als Ersatz für die fehlende P=O-Regel |

Die bestehende sekundäre Aminregel erfasst jetzt auch C=C–NH–C. Ihre Bandlage bleibt unverändert (3300–3500 cm⁻¹, innerhalb des breiteren NIU-N–H-Bereichs); Amid-/Thioamid-/Amidin- und Sulfonamid-N werden ausdrücklich ausgeschlossen.

## Bewusst offen nach dieser Etappe

- **Heteroaromaten und aromatisches NH:** Eine pauschale Benzol-Regel für jeden N/O/S-Ring wäre eine neue, nicht ausreichend spezifizierte Frequenzannahme. Die Benzol-Regel bleibt unverändert; eigene Heterocyclusklassen mit belegten Bereichen fehlen.
- **Carbamat, β-Lactam und Imid:** Eigene Carbonylregeln brauchen belegte Unterklassen und eine Vorranglogik gegenüber den bestehenden allgemeinen Amid-/Esterregeln. Die derzeit falsche bzw. unspezifische Mehrfachzuordnung ist weiterhin als Lücke sichtbar.
- **Amidine/Guanidine:** Die neue Imin-Tabelle wird nicht auf diese mesomeren Unterklassen übertragen. Daher bleibt die gemischte Evaluatorgruppe teilweise offen.
- **Phosphor:** Ionisierte Formen und andere Substitutionsmuster bleiben offen. Eine gemeldete P–O-Esterbande lässt diese P=O-Lücke nicht verschwinden.
- **Sulfonsäure/Sulfat/Sulfonat sowie Sulfamat:** Unterschiedliche Protonierungs- und Bindungsformen werden nicht zu einer gemeinsamen S=O-Frequenz zusammengezogen. Aztreonam bleibt deshalb im weit gefassten Evaluator-Sulfonamidtest offen.
- **Carboxylat, Nitratester und Formaldehyd:** In dieser Etappe keine eigene, an passenden Quellenbandlagen geprüfte Regel ergänzt. Diese expliziten Lücken werden weiterhin berichtet.

## Reproduzierbare Abnahme

`uv run python scripts/masse_eval.py ir` untersucht dieselben 414 Moleküle und 43 unabhängigen Gruppen wie zuvor. Vorher: **20 Gruppen mit 302 Gruppen-Molekül-Lücken**; nachher: **12 Gruppen mit 168 Gruppen-Molekül-Lücken**. Eine Gruppen-Molekül-Lücke zählt ein Molekül pro diagnostischer Gruppe, nicht jede einzelne Bindung.

TDD: `uv run pytest -q tests/test_spectro.py` vor dem Fix **22 failed, 33 passed**; danach mit dem Evaluator-Selbsttest **56 passed**. Der Berichtstest prüft reale Struktur→Banden→Bericht-Durchläufe und lässt Guanidin, Carbamat sowie ein geladenes Phosphatester-Beispiel ausdrücklich offen. Die Tool-Snapshots und Render-Goldens wurden nicht geändert.
