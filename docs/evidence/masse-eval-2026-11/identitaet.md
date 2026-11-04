# Identität — Masse-Evaluation (ZWISCHENSTAND, Lauf läuft noch)

Stand 2026-11-04 23:58 CET: **358 von 711 Eingaben geprüft — 291 grün · 50 gelb · 17 rot.**
Der fertige Bericht ersetzt diese Datei (`uv run python scripts/masse_eval.py identitaet`).

## Rote Fälle bisher (Rohzeilen)

```
  ✗  54 L-scopolamine                  3.6 s  falscher Stoff (stereo): STECJAGHUSJQJN-USLFZFAMSA-N statt STECJAGHUSJQJN-FWXGHANASA-N
  ✗  58 Prussian blue                  3.8 s  falscher Stoff (skelett): DCYOBGZUOMKFPA-UHFFFAOYSA-N statt DNMNDNSFJMUUFM-UHFFFAOYSA-N
  ✗  59 Berliner Blau                  3.9 s  falscher Stoff (skelett): DCYOBGZUOMKFPA-UHFFFAOYSA-N statt DNMNDNSFJMUUFM-UHFFFAOYSA-N
  ✗ 103 Bendamustin                    3.7 s  falscher Stoff (skelett): ZHSKUOZOLHMKEA-UHFFFAOYSA-N statt YTKUWDBFDASYHO-UHFFFAOYSA-N
  ✗ 105 Benzylpenicillin-Benzathin     3.5 s  falscher Stoff (stereo): BVGLIYRKPOITBQ-UHFFFAOYSA-N statt BVGLIYRKPOITBQ-ANPZCEIESA-N
  ✗ 143 chloroxylenol                  0.0 s  falscher Stoff (skelett): OJFZXRZZXBFEAP-UHFFFAOYSA-N statt OSDLLIBGSJNGJE-UHFFFAOYSA-N
  ✗ 151 clindamycin                    3.5 s  falscher Stoff (stereo): KDLRVYVGXIQJDK-AWPVFWJPSA-N statt KDLRVYVGXIQJDK-NOWPCOIGSA-N
  ✗ 154 clomifene                      3.6 s  falscher Stoff (stereo): GKIRPKYJQBWNGO-QPLCGJKRSA-N statt GKIRPKYJQBWNGO-UHFFFAOYSA-N
  ✗ 208 doxycycline                    3.6 s  falscher Stoff (skelett): SGKRLCUYIXIAHR-AKNGSSGZSA-N statt JBIWCJUYHHGXTC-AKNGSSGZSA-N
  ✗ 209 Doxycyclin                     3.5 s  falscher Stoff (skelett): SGKRLCUYIXIAHR-AKNGSSGZSA-N statt JBIWCJUYHHGXTC-AKNGSSGZSA-N
  ✗ 217 (−)-Ephedrin                   3.6 s  falscher Stoff (skelett): MWFDNXJPZUOTJB-UHFFFAOYSA-N statt KWGRBVOPPLSCSI-WPRPVWTQSA-N
  ✗ 271 Hydroxycobalamin               3.5 s  falscher Stoff (skelett): DQOCFCZRZOAIBN-WZHZPDAFSA-L statt YOZNUFWCRFCGIH-WZHZPDAFSA-K
  ✗ 287 Isosorbiddinitrat              3.5 s  falscher Stoff (stereo): MOYKHGMNXAOIAT-OMMKOOBNSA-N statt MOYKHGMNXAOIAT-JGWLITMVSA-N
  ✗ 321 Mefloquin                      3.6 s  falscher Stoff (stereo): XEEQGYMUWCZPDN-DOMZBBRYSA-N statt XEEQGYMUWCZPDN-UHFFFAOYSA-N
  ✗ 334 methyldopa                     0.0 s  falscher Stoff (skelett): QZIWDCLHLOADPK-ZETCQYMHSA-N statt CJCSPKMFHVPWAR-JTQLQIEISA-N
  ✗ 337 methylthioninium chloride      0.0 s  falscher Stoff (skelett): UYIDWJXVRJXHKX-UHFFFAOYSA-N statt CXKWCBBOMKCUKX-UHFFFAOYSA-M
  ✗ 354 Naloxon                        3.6 s  falscher Stoff (stereo): UZHSEJADLWPNLE-BIAVLDQUSA-N statt UZHSEJADLWPNLE-GRGSLBFTSA-N
```

## Gelbe Fälle bisher

```
  ~  46 (RS)-Cyclophosphamid          24.2 s  Quelle weg (partial)
  ~  49 4-Aminosalicylsäure           38.9 s  Quelle weg (partial)
  ~  53 Levofolinsäure                38.5 s  Quelle weg (partial)
  ~  55 L-Scopolamin                  24.3 s  Quelle weg (partial)
  ~  69 Alcuroniumchlorid             24.4 s  Quelle weg (partial)
  ~  75 Amilorid                      24.8 s  Quelle weg (partial)
  ~  77 Amiodaron                     24.9 s  Quelle weg (partial)
  ~  89 Artesunat                     24.4 s  Quelle weg (partial)
  ~  93 Atracurium-Besilat            24.4 s  Quelle weg (partial)
  ~  99 Beclometasondipropionat       24.3 s  Quelle weg (partial)
  ~ 101 Bedaquilin                    24.2 s  Quelle weg (partial)
  ~ 114 Betamethason                  44.0 s  Quelle weg (partial)
  ~ 116 Bicalutamid                   26.9 s  Quelle weg (partial)
  ~ 121 Calciumgluconat               24.7 s  Quelle weg (partial)
  ~ 128 Cefixim Anhydrat              24.5 s  Quelle weg (partial)
  ~ 132 Ceftazidim                    24.2 s  Quelle weg (partial)
  ~ 153 Clofazimin                    25.2 s  Quelle weg (partial)
  ~ 157 Clomipramin                   24.4 s  Quelle weg (partial)
  ~ 168 Cyclizin                      24.4 s  Quelle weg (partial)
  ~ 174 Dacarbazin                    25.2 s  Quelle weg (partial)
  ~ 189 Dexamethason                  24.6 s  Quelle weg (partial)
  ~ 191 Amidotrizoesäure              38.6 s  Quelle weg (partial)
  ~ 194 Didanosin                     24.5 s  Quelle weg (partial)
  ~ 196 Diethylcarbamazin             24.2 s  Quelle weg (partial)
  ~ 199 Diloxanidfuroat               25.6 s  Quelle weg (partial)
  ~ 205 Docusat                       24.2 s  Quelle weg (partial)
  ~ 212 Emtricitabin                  25.4 s  Quelle weg (partial)
  ~ 224 Ethionamid                    24.4 s  Quelle weg (partial)
  ~ 226 Ethosuximid                   24.2 s  Quelle weg (partial)
  ~ 228 Etoposid                      24.2 s  Quelle weg (partial)
  ~ 234 5-Fluorcytosin                24.3 s  Quelle weg (partial)
  ~ 236 Fludarabin-Phosphat           24.9 s  Quelle weg (partial)
  ~ 238 Fludrocortison                24.2 s  Quelle weg (partial)
  ~ 252 Gemcitabin                    24.4 s  Quelle weg (partial)
  ~ 255 Glibenclamid                  24.4 s  Quelle weg (partial)
  ~ 257 gliclazid                     24.4 s  Quelle weg (partial)
  ~ 275 Hydroxychloroquin             24.1 s  Quelle weg (partial)
  ~ 285 Isofluran                     24.5 s  Quelle weg (partial)
  ~ 290 (RS)-ketamine                 24.3 s  Quelle weg (partial)
  ~ 291 (RS)-Ketamin                  24.3 s  Quelle weg (partial)
  ~ 293 β-lactulose                   24.2 s  Quelle weg (partial)
  ~ 295 Lamivudin                     24.4 s  Quelle weg (partial)
  ~ 297 Lamotrigin                    24.3 s  Quelle weg (partial)
  ~ 310 Loperamid                     24.3 s  Quelle weg (partial)
  ~ 313 Loratadin                     24.1 s  Quelle weg (partial)
  ~ 319 Medroxyprogesteronacetat      24.4 s  Quelle weg (partial)
  ~ 323 N-Methylglucaminantimonat     25.4 s  Quelle weg (partial)
  ~ 330 (RS)-methadone                23.9 s  Quelle weg (partial)
  ~ 331 (RS)-Methadon                 24.2 s  Quelle weg (partial)
  ~ 341 Metoclopramid                 24.3 s  Quelle weg (partial)
```
