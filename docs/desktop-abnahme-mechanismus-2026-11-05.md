# Desktop-Abnahme: Mechanismus mit eigenen Substraten

Messlauf 04.11.2026, 23:49 bis 05.11.2026, kurz nach 00:00 MEZ,
Claude Desktop, Opus 5.5 Mittel.
Auftrag: Tisch `20261104-234915-desktop-handtest-fuer-generate` #1.
Fünf ursprüngliche Prompts jeweils in einem frischen Chat. Zusätzliche explizite
Toolanforderungen sind getrennt ausgewiesen; sie ersetzen keinen Routing-Erfolg.

## Laufzeit und Belege

Desktop vor Beginn vollständig per `osascript -e 'quit app "Claude"'` beendet
und per `open -a Claude` gestartet. HEAD dabei `2613e69`, einschließlich Merge
`16fc11e`. Konfiguration `mcpServers.chemdraw-tool`:

```json
{"command":"/opt/homebrew/bin/uv","args":["--directory","/Users/tom/Documents/projects/chemdraw-mcp","run","chemdraw-tool-server"]}
```

`pgrep -fl 'chemdraw-tool-server|chemdraw-mcp-bundle'` zeigte den Repo-Server
mit `.venv/bin/python3` und keinen Bundle-Prozess. Die Erweiterungseinstellung
`local.mcpb.jurimaxam-dotcom.chemdraw-mcp.json` hatte `isEnabled: false`.
Beleg: `/tmp/chemdraw-desktop-test/mechanismus-substrate/identity.txt`.
Es wurden ausschließlich sichtbare **Einmal erlauben**-Knöpfe gewählt;
keine Beschreibungen, Konfigurationen oder dauerhaften Berechtigungen verändert.

Alle Screenshots und AX-Texte liegen unter
`/tmp/chemdraw-desktop-test/mechanismus-substrate/`. Das sind lokale Belege,
keine versionierten Bilder. Screenshots zeigen den echten Desktop, keinen Testhost.

## Fälle

### 1. SN2 mit Stereozentrum

Prompt: „Zeig mir den SN2-Mechanismus von (R)-2-Brombutan mit Cyanid Schritt für Schritt“.

Chat: https://claude.ai/chat/35ce94de-ef3a-410a-9941-4ec323161541

Tool: `generate_mechanism`, `reaction_type: sn2`,
`substrates: ["C[C@@H](Br)CC", "[C-]#N"]`, `current_step: 0`.
Einmalfreigabe. Das Panel öffnet direkt, Overview und Step by step funktionieren;
drei Stationen: Reactants, Backside attack (transition state), Products.
Das C4-Gerüst bleibt erhalten, im Produkt sind Nitrilgruppe und Stereokeil sichtbar.
Der Begleittext nennt `(S)-2-Methylbutannitril` und Inversion. Das Panel selbst
trägt kein `(S)`-Label; ein Keil allein ist keine unabhängige CIP-Prüfung.

Titel im ersten Lauf: `Nucleophilic Substitution (SN2) — C[C@@H](Br)CC + [C-]#N`.
Damit ist die konkrete Erwartung „Titel nennt 2-Brombutan + Cyanid“ nicht erfüllt.
Der Titel gibt die SMILES-Eingaben des Modells wörtlich wieder.

Layout: zwei gut erkennbare rote Elektronenpfeile im Übergangszustand;
Pfeilspitzen liegen unmittelbar an C bzw. Br, keine auffällig kurzen Pfeile.
Die Übersicht ist höher als ihr sichtbarer Ausschnitt und scrollt intern;
das Produkt ist in der Schrittansicht vollständig zu sehen.

Belege: `01-sn2.png`, `01-sn2-transition.png`, `01-sn2-product.png`,
`01-sn2-product.txt`.

### 2. SN1 mit tert-Butylchlorid

Prompt: „SN1 von tert-Butylchlorid mit Wasser“.

Chat: https://claude.ai/chat/69e86c04-4d0d-4671-962e-7cbea823a64b

Ursprüngliches Ergebnis: **kein ChemDraw-Tool und kein ChemDraw-Panel**,
stattdessen Text, Formeln und Mermaid. Deshalb Routing in dieser Stichprobe rot.
Belege: `02-sn1-natural.png`, `02-sn1-natural.txt`.

Zusatz im selben Chat: „Nutze ChemDraw generate_mechanism mit meinen Substraten und zeige das Panel.“
Danach `generate_mechanism`, `reaction_type: sn1`,
`substrates: ["tert-Butylchlorid", "Wasser"]`, `current_step: 0`.
Einmalfreigabe. Titel: `Nucleophilic Substitution (SN1) — tert-Butylchlorid + Wasser`.
Fünf Schritte. Schritt 3/5 zeigt das tertiäre `C⁺` neben `Cl⁻` gut lesbar;
keine überlagerten Atomlabels in dieser Zwischenstufe.
Desktop erzeugte zusätzlich ein separates Visualize-Widget; es ist kein
ChemDraw-Beleg und wurde für die Abnahme nicht verwendet.

Belege: `02-sn1-leaving.png`, `02-sn1-carbocation.png`, `02-sn1-panel.txt`.

### 3. Fischer-Veresterung

Prompt: „Fischer-Veresterung von Propionsäure mit Ethanol als Mechanismus“.

Chat: https://claude.ai/chat/dd115d64-042f-408e-9954-3f445eda35d7

Direkt `generate_mechanism`, `reaction_type: fischer_ester`,
`substrates: ["propionic acid", "ethanol"]`, `current_step: 0`.
Einmalfreigabe. Titel: `Fischer esterification — propionic acid + ethanol`.
Sechs Stationen, Next bis Products (6/6) funktioniert. Produktzeichnung zeigt
Ethylpropanoat und Wasser, also Propionsäure-/Ethylreste statt einer Acetatvorlage.
Begleittext nennt ausdrücklich Ethylpropanoat.

Sichtbarer Layoutbefund: Bei Protonation endet der rote Pfeil auf dem H⁺-Label;
beim Alkoholangriff läuft sein Ansatz über das `HO`-Label und die Spitze bis
in das `C⁺`-Label. Der Verlauf ist erkennbar, die Abstände an Atomlabels sind
knapp. Keine verschwundene Struktur, keine auffällig kurzen Pfeile.

Belege: `03-fischer-protonation.png`, `03-fischer-attack.png`,
`03-fischer-product.png`, `03-fischer.txt`.

### 4. Tertiäres Halogenid für SN2

Prompt: „SN2 von tert-Butylbromid mit Hydroxid“.

Chat: https://claude.ai/chat/98d68cda-565f-47a7-a024-51290447d23e

Ursprüngliches Ergebnis: kein Tool, kein ChemDraw-Panel; Text erklärt tertiäre
Hinderung und bespricht E2 sowie SN1. Das prüft die Tool-Grenze noch nicht.

Zusatz im selben Chat: „Prüfe genau diese Eingabe mit ChemDraw generate_mechanism: reaction_type sn2, substrates [\"tert-butyl bromide\", \"[OH-]\"]. Zeige die Fehlermeldung und wähle keinen Ersatzmechanismus.“

Danach `generate_mechanism` mit genau diesen Parametern, Einmalfreigabe.
Server lehnt ab, Desktop zeigt den Toolaufruf als fehlgeschlagen und gibt
die Meldung wieder: `The substrates do not fit the sn2 mechanism: tertiary
halide — SN2 needs a methyl, primary or secondary alkyl halide; use sn1.`
Kein Ersatzbild und kein automatischer Wechsel auf SN1. Erwartete fachliche
Validierungsgrenze im expliziten Tooltest bestanden.

Belege: `04-tertiary-natural.png`, `04-tertiary-natural.txt`,
`04-tertiary-error.png`, `04-tertiary-error.txt`.

### 5. Diels-Alder außerhalb der drei Familien

Prompt: „Mechanismus der Diels-Alder-Reaktion“.

Chat: https://claude.ai/chat/51dd5156-5584-4871-851a-33d8c66f233f

Ursprüngliches Ergebnis: `generate_reaction`, kein `generate_mechanism`.
Panel-Titel `Diels-Alder-Reaktion`, Schema 1,3-Butadien + Ethen → Cyclohexen,
`[4+2]-Cycloaddition`, Kennzeichnung `balanced`. Kein Absturz und keine fremde
SN1-/SN2-/Fischer-Vorlage als Diels-Alder ausgegeben. Elektronenverschiebungen
werden im Text und in Mermaid erklärt. **Der ausdrücklich erwartete Hinweis
auf die drei unterstützten Mechanismusfamilien fehlt im ursprünglichen Chat.**
Somit ist die beauftragte Grenzkommunikation in dieser Stichprobe nicht erfüllt,
auch wenn die Wahl des Schema-Tools zur dokumentierten Ausweichroute passt.

Belege: `05-diels-alder.png`, `05-diels-alder.txt`.

Zusatzfrage: „Kann ChemDraw generate_mechanism den Diels-Alder-Mechanismus mit Elektronenpfeilen selbst zeichnen? Nenne seine unterstützten Mechanismusfamilien und die Grenze.“
Darauf nennt Desktop ohne weiteren Toolaufruf ausdrücklich nur SN2, SN1 und
Fischer-Veresterung und erklärt, dass `generate_reaction` nur das Nettoschema
ohne Elektronenpfeile zeichnet. Grenzhinweis bei gezielter Nachfrage also korrekt.
Belege: `05-diels-alder-limit.png`, `05-diels-alder-limit.txt`.

## SN2-Nachmessung nach Titel-Fix

Nach Tisch-Status #3 Desktop erneut vollständig beendet und gestartet; HEAD
`917ad59`, einschließlich `a43104d` und `a18b849`. Neuer Repo-Serverprozess,
Bundle weiter deaktiviert: `identity-retest.txt`.

Identischer ursprünglicher SN2-Prompt in neuem Chat:
https://claude.ai/chat/ad39ea61-b72a-4a5e-911a-cb98b1762276

Diesmal sendet das Modell Namen: `substrates: ["(R)-2-bromobutane", "cyanide"]`,
`reaction_type: sn2`, `current_step: 0`. Einmalfreigabe. Panel-Titel:
`Nucleophilic Substitution (SN2) — (R)-2-bromobutane + cyanide`.
Stoffnamen sind lesbar, drei Schritte und Produkt öffnen sich weiterhin.
Das bestätigt den Namenspfad, übt den neuen SMILES→Formel-Pfad allein noch nicht aus.
Belege: `06-sn2-retest-names.png`, `06-sn2-retest-product.png`,
`06-sn2-retest-names.txt`.

Gezielter Zusatz im selben Chat: „Wiederhole generate_mechanism mit exakt diesen SMILES als substrates: [\"C[C@@H](Br)CC\", \"[C-]#N\"], reaction_type \"sn2\". Ich prüfe den Paneltitel bei SMILES-Eingaben.“
Desktop sendet genau diese SMILES und `current_step: 0`, Einmalfreigabe.
**Sichtbarer neuer Titel: `Nucleophilic Substitution (SN2) — C₄H₉Br + CN⁻`.**
Damit ist der Formel-Titel nach echtem Neustart im Desktop bestätigt.
Belege: `07-sn2-formula-title.png`, `07-sn2-formula-title.txt`.

## Ergebnis und offene Befunde

Der Handtest ist vollständig durchgeführt; eine pauschal grüne Abnahme aller
ursprünglichen Erwartungen wäre falsch:

| Kriterium | Ergebnis |
|---|---|
| Eigene SN2-Substrate, Übergangszustand, Produktkeil | Sichtbar; `(S)` im Begleittext, kein CIP-Label im Panel |
| Eigene SN1-Substrate mit sichtbarem Carbokation | Panel grün nach explizitem Zusatz; ursprünglicher Prompt ohne Tool |
| Fischer-Produkt Ethylpropanoat | Direktes Tool, Panel und Produkt grün |
| Tertiäres SN2 wird abgelehnt und verweist auf SN1 | Expliziter Serveraufruf grün; ursprünglicher Prompt nur Text |
| Diels-Alder: Hinweis auf drei Familien | Fehlt ursprünglich; erst gezielte Nachfrage erklärt Grenze |
| Titel ohne rohe SMILES | Nach Neustart grün, Namen bleiben Namen, SMILES werden Formeln |

Offen bleiben das fehlende Panel beim natürlichen SN1-Prompt, der fehlende
Grenzhinweis beim natürlichen Diels-Alder-Prompt und die knappen Pfeilabstände
an Atomlabels (besonders Fischer-Angriff). Die breite Desktop-Routing-Grenze
ist bereits bekannt; dieser Lauf ist jeweils nur eine Stichprobe, kein
Häufigkeitsnachweis. Kein Produktfix und keine Beschreibung geändert.

Die Zeichnungen wurden gezielt für die beauftragten Stationen gesichtet;
keine vollständige fachliche Validierung aller Zwischenstufen oder unabhängige
CIP-Auswertung aus dem Bild. Gate-/Host-Tests wurden für diesen reinen
Desktop-/Dokumentationsauftrag nicht erneut ausgeführt. Dokuprüfung:
`git diff --cached --check`. Laufender Zustand am Ende: frischer Repo-Server,
Bundle deaktiviert, letzte Desktop-Antwort abgeschlossen, keine Freigabe offen.
