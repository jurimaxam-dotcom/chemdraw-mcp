**Keine Rechtsberatung.** Alles mit [E] ist meine Einschätzung; vor dem ersten Euro einmal mit Finanzamt bzw. Steuerberatung abgleichen. Quellen [n] unten, abgerufen 02.10.2026.

## 1. Steuer & Sozialversicherung

- **Gewerbe oder freiberuflich:** Online-Verkauf eines Zugangs zu einer App spricht für Gewerbe; „schriftstellerisch/unterrichtend" (§ 18 EStG) ist bei interaktiver Software unwahrscheinlich [E]. Gewerbe anmelden ist der sichere Weg; das Finanzamt ordnet ohnehin selbst ein.
- **Gewerbesteuer:** Freibetrag 24.500 € Gewerbeertrag für natürliche Personen [1, belegt] → praktisch null.
- **Kleinunternehmer § 19 UStG:** Grenzen bestätigt: 25.000 € Vorjahr / 100.000 € laufendes Jahr [2, belegt]. Gesamtumsatz = nur *steuerbare* Umsätze [2, belegt].
- **ELSTER-Fragebogen** binnen 1 Monat nach Aufnahme [3, belegt].
- **Einkommensteuer:** Grundfreibetrag 2026 = 12.348 € [4, belegt].
- **Familienversicherung:** Gewinn ≤ 565 €/Monat (2026) und nur nebenberuflich (Barmer: ≤ 20 h/Woche) [5, belegt] → ca. 6.780 €/Jahr Gewinn.
- **BAföG:** Freibetrag 389 €/Monat ab 01.01.2026 [6, belegt]. Die oft genannten 603 € gelten für Lohn. Bei Gewinn: Gewinn × 0,777 (Sozialpauschale 22,3 % [7]) / 12 ≤ 389 → **ca. 6.000 €/Jahr** anrechnungsfrei [E, eigene Rechnung]. Einkommen dem BAföG-Amt melden.
- **Kindergeld:** Bei Erstausbildung zählt das Einkommen nicht [8, belegt].

## 2. Verbraucherpflichten

- **Impressum** § 5 DDG: Name + *Anschrift, unter der man niedergelassen ist* + E-Mail [9, belegt]. Ob eine c/o-Adresse genügt, ist strittig → Jays Entscheidung.
- **Datenschutz:** Google Fonts vom Google-Server → LG München I 3 O 17493/20: unzulässig, Schadensersatz [10, belegt]. Gleiche Logik für das Pyodide-CDN jsDelivr [E] → Fonts und Pyodide selbst hosten. GitHub Pages loggt IPs [11, belegt] → in die Datenschutzerklärung.
- **Achtung, Paragraf verschoben:** Seit 19.06.2026 steht die Regel zu digitalen Inhalten in **§ 356 Abs. 6** BGB, nicht Abs. 5 [12, belegt]. Erlöschen erst, wenn alles erfüllt ist: Lieferung hat begonnen + ausdrückliche Zustimmung + bestätigte Kenntnis + Bestätigung per E-Mail (§ 312f) [12].
- **Größtes Risiko:** Ein „Semesterpass" kann als *digitale Dienstleistung* gelten. Dann greift Abs. 5: Das Widerrufsrecht erlischt erst bei vollständiger Erbringung, also am Semesterende. Wertersatz gibt es nur bei korrekter Belehrung [13, belegt; Haufe Rn 26b sieht Portalzugang eher als Inhalt [14]]. Pyodide liefert statische Dateien aufs Gerät, das spricht eher für „Inhalt" [E]. In beiden Fällen nötig: zwei nicht vorangekreuzte Checkboxen, getrennt von den AGB [13].
- **Widerrufsbutton § 356a BGB, Pflicht seit 19.06.2026:** „Vertrag widerrufen" → „Widerruf bestätigen" → Eingangsbestätigung auf dauerhaftem Datenträger. Bußgeld bis 50.000 € [15, belegt]. Braucht Mailversand, also ein Backend.
- **Button-Lösung:** „zahlungspflichtig bestellen" oder eine gleich eindeutige Formulierung [16, belegt].
- **AGB:** gesetzlich nicht Pflicht [E], die Pflichtinformationen schon.

## 3. Zahlung – Empfehlung: Stripe Managed Payments (MoR)

| | Gebühr | Quelle |
|---|---|---|
| Stripe normal | 1,5 % + 0,25 € | [17] |
| Stripe Managed Payments | +3,5 % (≈ 5 % + 0,25 €) | [17] |
| Paddle | 5 % + 0,50 $ | [18] |
| Lemon Squeezy | 5 % + 0,50 $ (geht in Managed Payments auf) | [19][20] |
| Polar (Neukonten) | 5 % + 0,50 $, +1,5 % Nicht-US-Karte | [21] |
| Gumroad | 10 % + 0,50 $ | [22] |

**Begründung:**
- Managed Payments nimmt Verkäufer aus DE an, deckt „Online-Kurse" ab und läuft über Payment Links [23, belegt].
- Gegenüber Kunden tritt „Link" als Verkäufer auf und verschickt Belege und Rechnungen selbst [24, belegt].
- Damit fallen USt/OSS und Rechnungen weg. Ob damit auch Widerrufsbutton und Belehrung bei Link liegen: **Lücke**, bei Stripe erfragen.
- Ohne MoR: EU-Verbraucherumsätze < 10.000 € bleiben in DE [25, belegt] → § 19 greift, kein OSS. Jay trägt dann aber alle Pflichten aus Abschnitt 2 selbst.

**§ 13b UStG:**
- Belegt: Auch Kleinunternehmer schulden Reverse-Charge-Steuer für Leistungen ausländischer Unternehmer und müssen sie voranmelden [26; § 19 Abs. 1 S. 2: „§ 18 Abs. 4a bleibt unberührt"] – ohne Vorsteuerabzug.
- Lücke: Ob Stripe-/MoR-Gebühren steuerfrei (Zahlungsverkehr) sind oder mit dem Kaufpreis verrechnet werden, ist offen. Erste Abrechnung auf den Vermerk „reverse charge" prüfen.
- [E] Jays Leistung an den MoR (Irland/UK) ist B2B, in DE nicht steuerbar und zählt nicht zum § 19-Umsatz.

## 4. Freischalten ohne eigenen Server

**Planabweichung:** GitHub Pages ist für Seiten, die „commercial transactions" abwickeln, ausdrücklich nicht erlaubt [27, belegt]. Umzug auf Cloudflare Pages [E, Nutzungsbedingungen dort nicht geprüft].

**Minimale Architektur:**
1. Payment Link → Weiterleitung mit `{CHECKOUT_SESSION_ID}` [E, für Payment Links nicht verifiziert].
2. Ein Cloudflare Worker (Free: 100.000 Anfragen/Tag, KV 1.000 Schreibvorgänge/Tag [28, belegt]) prüft die Session bei Stripe.
3. Der Worker signiert ein Token mit ECDSA-Schlüssel (WebCrypto), gültig bis Semesterende.
4. Die Seite prüft die Signatur offline mit dem öffentlichen Schlüssel.
5. Wiederherstellung: E-Mail eingeben → Worker sucht die bezahlte Session.
6. Derselbe Worker nimmt Widerrufe an und verschickt die Bestätigung.

**Ehrlich:** Statische Aufgabendateien bleiben abrufbar. Das Token ist eine Höflichkeitsschranke, für 29 € angemessen [E]. Echte Sperre nur, wenn der Worker die Aufgaben-JSONs selbst ausliefert. Lemon-Squeezy-License-API (60 Anfragen/min [29]) lohnt sich nicht mehr, weil LS in Managed Payments aufgeht.

**Lücken:**
- Paddle-Nutzungsrichtlinie (URL 404)
- ob der Student-Pack-Erlass die 3,5 % abdeckt
- Gebühr der Gewerbeanmeldung (je nach Gemeinde)

## Erste-Euro-Checkliste

1. Gewerbe anmelden – 30 min online – **Jay**
2. ELSTER-Fragebogen, Kleinunternehmer ankreuzen, § 13b-Frage stellen – 45 min – **Jay**
3. Krankenkasse + BAföG-Amt informieren – 15 min – **Jay**
4. Managed Payments aktivieren, Steuercode „Online-Kurs", Widerrufsbutton bei Stripe erfragen – 1 h – Jay (Login), Claude bereitet vor
5. Hosting auf Cloudflare Pages, Fonts und Pyodide selbst hosten – 2 h – Claude
6. Worker: Token + Widerrufsfunktion + Mail – 1 Tag – Claude
7. Impressum, Datenschutzerklärung, Widerrufsbelehrung, Checkboxen – 2 h Generator (z. B. IT-Recht/eRecht24) – Jay entscheidet die Adresse
8. Testkauf + Testwiderruf mit echter Karte – 20 min – **Jay**

**Quellen (abgerufen 02.10.2026)**
[1] gesetze-im-internet.de/gewstg/__11.html · [2] …/ustg_1980/__19.html · [3] …/ao_1977/__138.html · [4] …/estg/__32a.html · [5] barmer.de/unsere-leistungen/beitraege-tarife/krankenversicherung-familien/voraussetzungen-1480744 ; tk.de (Stand 19.12.2025) · [6] bafög.de „Welche Freibeträge…" + Rundschreiben 04.12.2025 · [7] …/baf_g/__21.html · [8] familienportal.de (Kindergeld eigenes Einkommen) · [9] …/ddg/__5.html · [10] gesetze-bayern.de LG München I 20.01.2022 3 O 17493/20 · [11] docs.github.com/…/what-is-github-pages · [12] …/bgb/__356.html ; buzer.de (Fassungsvergleich, G v. 03.02.2026) · [13] heuking.de (23.08.2023, Widerrufsbelehrungen digitale Inhalte) · [14] haufe.de Prütting/Wegen/Weinreich § 356 Rn 26b (01.09.2025) · [15] ihk.de/dortmund Widerrufsbutton ; bitkom Praxisleitfaden 05/2026 · [16] …/bgb/__312j.html · [17] stripe.com/de/pricing · [18] paddle.com/pricing · [19] lemonsqueezy.com/pricing · [20] lemonsqueezy.com/blog/2026-update (16.04.2026) · [21] polar.sh/resources/pricing · [22] gumroad.com/pricing · [23] docs.stripe.com/payments/managed-payments/eligibility · [24] …/managed-payments/how-it-works · [25] …/ustg_1980/__3a.html (Abs. 5 S. 3) · [26] …/ustg_1980/__13b.html (Abs. 5 S. 1) · [27] docs.github.com/…/github-pages-limits · [28] developers.cloudflare.com/workers/platform/pricing · [29] docs.lemonsqueezy.com/api/license-api
