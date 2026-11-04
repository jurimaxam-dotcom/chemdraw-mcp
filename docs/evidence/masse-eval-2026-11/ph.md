# pH-Aufgaben — Masse-Evaluation

Stand 2026-11-05 · `uv run python scripts/masse_eval.py ph` · offline, < 5 s

**51 Aufgaben: 48 grün · 3 rot.** Referenz aus `tests/identity/ph-aufgaben.json` (sympy, Polynomwurzel der Ladungsbilanz — Herleitung je Aufgabe in der Datei). Geprüft werden der Rückgabewert von `ph_calc` (Toleranz in der Datei, pH ±0,005) UND die Überschrift, die `calculate_ph` dem Nutzer zeigt (auf 2 Stellen gerundet). Spalte *Näherung* = Lehrbuchnäherung bzw. Henderson-Hasselbalch bzw. −log c, nur zur Einordnung, nicht geprüft.

## Abweichungen

| Aufgabe | Thema | Parameter | Referenz | ph_calc | Δ | Tool-Kopf | Näherung | Status | Quelle/Zweck |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| stark-konz | weak_acid | concentration=5.0, pka=0.5 | -0.04502 | 6.072e-18 | +0.045 | 0.00 | -0.10 | rot | Randfall: exakter pH < 0 |
| schwach-konz | weak_acid | concentration=10.0, pka=-1.0 | -0.791 | 6.072e-18 | +0.79 | 0.00 | -1.00 | rot | Randfall: pKs < 0, pH deutlich < 0 |
| starkebase-konz | weak_base | concentration=5.0, pkb=0.5 | 14.05 | 14 | -0.045 | 14.00 | 14.10 | rot | Randfall: exakter pH > 14 |

### Deutung

- **stark-konz**: `ph_core.exact_ph` sucht per Bisektion nur in [0, 14] und klemmt am Rand: Ergebnis pH 0,00 statt −0,05. Die Näherung (−0,10) liegt hier näher an der Wahrheit als der 'exakte' Wert.
- **schwach-konz**: wie stark-konz: Klemme bei pH 0 — 0,00 statt −0,79.
- **starkebase-konz**: Spiegelbild: Klemme bei pH 14 — 14,00 statt 14,05.

## Alle Aufgaben

| Aufgabe | Thema | Parameter | Referenz | ph_calc | Δ | Tool-Kopf | Näherung | Status | Quelle/Zweck |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| hcl-0.1 | strong_acid | concentration=0.1 | 1 | 1 | -4.3e-13 | 1.00 | 1.00 | grün | Lehrbuch-Standardbeispiel: 0,1 M HCl → pH 1 |
| hcl-0.01 | strong_acid | concentration=0.01 | 2 | 2 | -4.3e-11 | 2.00 | 2.00 | grün | Lehrbuch-Standardbeispiel |
| hcl-1e-5 | strong_acid | concentration=1e-05 | 5 | 5 | -4.2e-07 | 5.00 | 5.00 | grün | verdünnt, Wasser noch vernachlässigbar |
| hcl-1e-7 | strong_acid | concentration=1e-07 | 6.791 | 6.791 | +3.6e-07 | 6.79 | 7.00 | grün | Grenzfall: Säure und Wasser gleich stark (Lehrbuchwert 6,79) |
| hcl-1e-8 | strong_acid | concentration=1e-08 | 6.978 | 6.978 | +3.1e-07 | 6.98 | 8.00 | grün | Klassische Fangfrage: 1e-8 M HCl ist nicht basisch (pH 6,98) |
| hcl-2 | strong_acid | concentration=2.0 | -0.301 | -0.301 | +4.3e-09 | -0.30 | -0.30 | grün | konzentriert: negativer pH (ideal gerechnet) |
| naoh-0.1 | strong_base | concentration=0.1 | 13 | 13 | +4.4e-13 | 13.00 | 13.00 | grün | Lehrbuch-Standardbeispiel |
| naoh-1e-3 | strong_base | concentration=0.001 | 11 | 11 | +4.3e-09 | 11.00 | 11.00 | grün | Lehrbuch-Standardbeispiel |
| naoh-1e-8 | strong_base | concentration=1e-08 | 7.022 | 7.022 | -3.1e-07 | 7.02 | 6.00 | grün | Spiegelbild der Fangfrage |
| naoh-2 | strong_base | concentration=2.0 | 14.3 | 14.3 | -4.3e-09 | 14.30 | 14.30 | grün | konzentriert: pH über 14 (ideal gerechnet) |
| essig-0.1 | weak_acid | concentration=0.1, pka=4.76 | 2.883 | 2.883 | -4.6e-07 | 2.88 | 2.88 | grün | Essigsäure 0,1 M: Lehrbuchwert pH 2,88 |
| essig-0.01 | weak_acid | concentration=0.01, pka=4.76 | 3.389 | 3.389 | -4.6e-07 | 3.39 | 3.38 | grün | Essigsäure 0,01 M: Lehrbuchwert ≈ 3,4 |
| essig-1e-4 | weak_acid | concentration=0.0001, pka=4.76 | 4.47 | 4.47 | -2e-07 | 4.47 | 4.38 | grün | Näherung bricht: Säure merklich dissoziiert |
| essig-1e-6 | weak_acid | concentration=1e-06, pka=4.76 | 6.019 | 6.019 | -2e-07 | 6.02 | 5.38 | grün | fast vollständig dissoziiert + Wasser |
| essig-1 | weak_acid | concentration=1.0, pka=4.76 | 2.381 | 2.381 | +2.2e-07 | 2.38 | 2.38 | grün | Essigsäure 1 M |
| ameisen-0.1 | weak_acid | concentration=0.1, pka=3.75 | 2.384 | 2.384 | +3.4e-07 | 2.38 | 2.38 | grün | Ameisensäure |
| hf-0.1 | weak_acid | concentration=0.1, pka=3.17 | 2.103 | 2.103 | -2.5e-07 | 2.10 | 2.08 | grün | Flusssäure |
| hcn-0.1 | weak_acid | concentration=0.1, pka=9.21 | 5.105 | 5.105 | -1.7e-07 | 5.10 | 5.11 | grün | Blausäure, sehr schwach: pH ≈ 5,1 |
| nh4-0.1 | weak_acid | concentration=0.1, pka=9.25 | 5.125 | 5.125 | -3.3e-07 | 5.12 | 5.12 | grün | Ammoniumchlorid 0,1 M: pH ≈ 5,1 |
| phenol-0.01 | weak_acid | concentration=0.01, pka=10.0 | 5.998 | 5.998 | -2.9e-07 | 6.00 | 6.00 | grün | sehr schwache Säure, verdünnt — Wasser zählt |
| mittelstark-0.01 | weak_acid | concentration=0.01, pka=1.0 | 2.038 | 2.038 | -3e-07 | 2.04 | 1.50 | grün | pKs 1: fast vollständig dissoziiert |
| mittelstark-0.1 | weak_acid | concentration=0.1, pka=2.0 | 1.568 | 1.568 | +4.2e-08 | 1.57 | 1.50 | grün | pKs 2: Näherung weit daneben |
| stark-konz | weak_acid | concentration=5.0, pka=0.5 | -0.04502 | 6.072e-18 | +0.045 | 0.00 | -0.10 | rot | Randfall: exakter pH < 0 |
| schwach-konz | weak_acid | concentration=10.0, pka=-1.0 | -0.791 | 6.072e-18 | +0.79 | 0.00 | -1.00 | rot | Randfall: pKs < 0, pH deutlich < 0 |
| h3po4-0.1 | weak_acid | concentration=0.1, pka_values=[2.12, 7.21, 12.67] | 1.62 | 1.62 | -2.4e-07 | 1.62 | 1.56 | grün | Phosphorsäure 0,1 M: pH ≈ 1,6 |
| h3po4-0.001 | weak_acid | concentration=0.001, pka_values=[2.12, 7.21, 12.67] | 3.048 | 3.048 | -3.8e-08 | 3.05 | 2.56 | grün | verdünnte Phosphorsäure |
| citronen-0.1 | weak_acid | concentration=0.1, pka_values=[3.13, 4.76, 6.4] | 2.083 | 2.083 | +1.7e-07 | 2.08 | 2.06 | grün | Citronensäure |
| kohlen-0.01 | weak_acid | concentration=0.01, pka_values=[6.35, 10.33] | 4.176 | 4.176 | +4.9e-07 | 4.18 | 4.17 | grün | Kohlensäure |
| oxal-0.05 | weak_acid | concentration=0.05, pka_values=[1.25, 4.27] | 1.495 | 1.495 | +1.3e-07 | 1.50 | 1.28 | grün | Oxalsäure |
| h2s-0.1 | weak_acid | concentration=0.1, pka_values=[7.0, 12.9] | 4 | 4 | -7.1e-08 | 4.00 | 4.00 | grün | Schwefelwasserstoff |
| nh3-0.1 | weak_base | concentration=0.1, pkb=4.75 | 11.12 | 11.12 | +3.2e-07 | 11.12 | 11.12 | grün | Ammoniak 0,1 M: Lehrbuchwert 11,13 |
| nh3-0.01 | weak_base | concentration=0.01, pkb=4.75 | 10.62 | 10.62 | -3.3e-07 | 10.62 | 10.62 | grün | Ammoniak 0,01 M |
| nh3-1e-5 | weak_base | concentration=1e-05, pkb=4.75 | 8.854 | 8.854 | +2.2e-07 | 8.85 | 9.12 | grün | Näherung bricht |
| acetat-0.1 | weak_base | concentration=0.1, pkb=9.24 | 8.88 | 8.88 | +2.6e-07 | 8.88 | 8.88 | grün | Natriumacetat 0,1 M: pH ≈ 8,9 |
| pyridin-0.1 | weak_base | concentration=0.1, pka=5.25 | 9.125 | 9.125 | +2.6e-07 | 9.12 | 9.12 | grün | Pyridin über pKs der korresp. Säure |
| methylamin-0.1 | weak_base | concentration=0.1, pkb=3.36 | 11.81 | 11.81 | -1.7e-07 | 11.81 | 11.82 | grün | Methylamin |
| starkebase-konz | weak_base | concentration=5.0, pkb=0.5 | 14.05 | 14 | -0.045 | 14.00 | 14.10 | rot | Randfall: exakter pH > 14 |
| acetatpuffer-1:1 | buffer | acid_concentration=0.1, base_concentration=0.1, pka=4.76 | 4.76 | 4.76 | -1.1e-07 | 4.76 | 4.76 | grün | Äquimolarer Puffer: pH = pKs |
| acetatpuffer-1:10 | buffer | acid_concentration=0.1, base_concentration=0.01, pka=4.76 | 3.768 | 3.768 | -1.1e-07 | 3.77 | 3.76 | grün | HH: pKs − 1 |
| acetatpuffer-10:1 | buffer | acid_concentration=0.01, base_concentration=0.1, pka=4.76 | 5.76 | 5.76 | -2.7e-07 | 5.76 | 5.76 | grün | HH: pKs + 1 |
| phosphatpuffer | buffer | acid_concentration=0.05, base_concentration=0.05, pka=7.21 | 7.21 | 7.21 | +2.5e-07 | 7.21 | 7.21 | grün | Phosphatpuffer |
| ammonpuffer | buffer | acid_concentration=0.1, base_concentration=0.2, pka=9.25 | 9.551 | 9.551 | +4.5e-07 | 9.55 | 9.55 | grün | NH4Cl/NH3 1:2 |
| puffer-verduennt | buffer | acid_concentration=1e-05, base_concentration=1e-05, pka=4.76 | 5.274 | 5.274 | -1.1e-08 | 5.27 | 4.76 | grün | sehr verdünnt: HH gilt nicht mehr |
| puffer-saurer-pks | buffer | acid_concentration=0.01, base_concentration=0.01, pka=2.0 | 2.383 | 2.383 | -3.1e-07 | 2.38 | 2.00 | grün | pKs 2: HA dissoziiert merklich, HH daneben |
| puffer-basisch-verduennt | buffer | acid_concentration=0.0001, base_concentration=0.0001, pka=10.0 | 9.617 | 9.617 | -4.2e-07 | 9.62 | 10.00 | grün | basischer Puffer verdünnt |
| ion-ass-magen | ionisation | pka=3.5, target_ph=1.5, drug_type=acid | 99.01 | 99.01 | -9.9e-09 |  |  | grün | ASS im Magen |
| ion-ass-blut | ionisation | pka=3.5, target_ph=7.4, drug_type=acid | 0.01259 | 0.01259 | -3.3e-07 |  |  | grün | ASS im Blut |
| ion-base-blut | ionisation | pka=9.0, target_ph=7.4, drug_type=base | 2.45 | 2.45 | -2.4e-07 |  |  | grün | basischer Arzneistoff im Blut |
| ion-gleich | ionisation | pka=6.0, target_ph=6.0, drug_type=base | 50 | 50 | +0 |  |  | grün | pH = pKs: die Hälfte ungeladen |
| rezept-acetat-pH5 | buffer_recipe | target_ph=5.0, pka=4.76, total_concentration=0.1, volume_ml=1000.0 | 0.03653 | 0.03653 | -3.3e-07 |  |  | grün | Acetatpuffer pH 5, 1 L, 0,1 M |
| rezept-phosphat-pH7.4 | buffer_recipe | target_ph=7.4, pka=7.21, total_concentration=0.05, volume_ml=500.0 | 0.009808 | 0.009808 | +4.7e-07 |  |  | grün | Phosphatpuffer pH 7,4 |
