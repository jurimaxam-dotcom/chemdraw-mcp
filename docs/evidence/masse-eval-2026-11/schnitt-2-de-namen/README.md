# Schnitt 2: deutsche Namen und gemessene Form-Zusätze

06.11.2026; Auftrag `20261106-231238-chemdraw-mcp-schnitt-2`, Erweiterung um
`resolver.py` / `test_resolver.py` vom Chef im selben Faden #3 bestätigt.
Keine Änderung an `stoffe-masse.json`, `masse_eval.py` oder `identitaet-lauf.json`
durch diesen Schnitt. Keine neue Abhängigkeit, Reparatur bestehender Regeln.

## Ergebnis der fünf Zielfälle

Frische Prozesse, `resolve(name)` und `Chem.MolToInchiKey(result[1])`, vollständige
Antworten samt erwartetem Key und `found_as` in `live.json`:

| Eingabe | InChIKey | gefunden als |
|---|---|---|
| Cefixim Anhydrat | `OKBVVJOGVLARMR-QSWIMTSFSA-N` | Cefixim |
| N-Methylglucaminantimonat | `XOGYVDXPYVPAAQ-SESJOKTNSA-M` | meglumine antimoniate |
| Metamizol (freie Säure) | `LVWZTYCIRDMTEY-UHFFFAOYSA-N` | Metamizol |
| Ethylendiamintetraessigsäure | `KCXVZYZYPLLWCC-UHFFFAOYSA-N` | ethylenediaminetetraacetic acid |
| Citral A+B | `WTEVQBCEXWBHNA-UHFFFAOYSA-N` | Citral |

Alle fünf stimmen mit ihrer jeweiligen Fixture überein. Die feste
Meglumin-Zuordnung vermeidet die gemessene OPSIN-Falle bei
`N-methylglucamine antimonate` (anderer Stoff).

Isosorbiddinitrat wird jetzt korrekt zu `Isosorbide dinitrate`, Benzylpenicillin-Benzathin
zu `Benzylpenicillin benzathine`. Die volle Kaskade trifft beim Original aber schon
Stereo-abweichende Records: `MOYKHGMNXAOIAT-OMMKOOBNSA-N` bzw.
`BVGLIYRKPOITBQ-UHFFFAOYSA-N`. Beide bleiben deshalb für Schnitt 3 offen.

## Warum die volle Kaskade nach einem Form-Zusatz nötig ist

Gemessen: `resolve("Citral")` → `WTEVQBCEXWBHNA-UHFFFAOYSA-N`,
`_pubchem_lookup("Citral", [])` dagegen → `WTEVQBCEXWBHNA-JXMROGBWSA-N`
(Geranial, mit E-Geometrie). Reines Abschneiden in `english_variant` und erneutes
Fragen nur bei PubChem wäre für Citral falsch.

Die geschlossene Whitelist enthält ausschließlich ` Anhydrat`, ` (freie Säure)`
und ` A+B` am Ende. Erst wenn OPSIN, PubChem und NCI das Original nicht auflösen,
läuft der Grundname durch die volle Kaskade. Stereodeskriptor und Drehwert bleiben
bei der Kürzung exakt erhalten; `found_as` macht den Umweg sichtbar. Unbekannte
Klammern, Trihydrat und andere Gemischzusätze werden nicht gekürzt. Auch die
vorhandenen Gegenproben dürfen Form-Zusätze nicht vorzeitig entfernen.

**Abnahmegrenze:** Opus' parallel gestartete Kippmessung für Schnitt 3 aus dem
eigenen Worktree enthält diese neue Form-Fallback-Stufe noch nicht.

## Holdout vorher/nachher

Beide Läufe führen `holdout_de_namen.py` unverändert aus. Ein lokaler Wrapper
zeichnet die aufgerufenen Varianten und die tatsächlichen PubChem-Keys auf,
ohne Rückgabewerte zu verändern. Kandidaten: die 177 deutschen Eingaben, die
im historischen Lauf 2 grün waren. Die historischen Erwartungskeys bleiben für
diesen Vergleich unverändert; spätere Fixture-Korrekturen werden nicht nachgewertet.

| Wert | vorher | nachher |
|---|---:|---:|
| Ohne Variante | 44 | 44 |
| Exakter erwarteter Key | 121 | 121 |
| Stereo/Form abweichend (Nicotin) | 1 | 1 |
| Anderer Stoff | 0 | 0 |
| Nicht gefunden | 11 | 11 |

`holdout-vor.json` und `holdout-nach.json` sind bytegleich:
SHA-256 `165b353f1b13cb785cb6f9936d9221c0115cbf22995ef63a1b77de0561928fd5`.
Alle 177 Einzelfälle einschließlich Variante und vollständigem Key bleiben gleich;
**0 richtig→anders**, Details in `holdout-vergleich.json`.
Summary reproduzieren: `uv run python docs/evidence/masse-eval-2026-11/holdout_de_namen.py`.

`varianten-aenderungen.json` vergleicht zusätzlich alle Fixture-Namen gegen den
Stand `327216f`: 14 Varianten ändern sich, davon die sieben Zielfälle und sieben
englische Penicillin-Namen, deren überflüssiges Endungs-e entfällt. Letztere
wurden zusätzlich vollständig live aufgelöst: alle sieben treffen ihren vollen
Fixture-Key, `found_as` bleibt leer (`penicillin-live.json`).

## Rot-Grün und Gate

- `uv run pytest tests/test_de_names.py -q`: vor Fix 7 failed / 65 passed.
- Form-Fallback: vor Fix 4 failed / 159 passed; zusätzlicher Original-Konfliktfall
  vor seinem Fix 1 failed / 163 deselected.
- Drei isolierte In-Memory-Mutationen: zu breite Klammerkürzung, verlorenes
  Stereopräfix, vorzeitige Kürzung im Variantenvergleich → jeweils 1 failed.
- Danach `uv run pytest tests/test_de_names.py tests/test_resolver.py -q`:
  **236 passed**. Ruff grün.
- Finaler Stand: `./test.sh > /tmp/chemdraw-schnitt2-final-gate.log 2>&1` →
  **rc=0, 8328 passed / 16 skipped**, UI-Bundle, Frontend und Chromium-Snapshot grün.
