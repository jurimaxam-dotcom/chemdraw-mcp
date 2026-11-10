# Desktop-Routing Runde 9 — 10.11.2026

**generate_protein_or_antibody 4/4**. Alle vier Aufrufe lieferten ein sichtbares ChemDraw-Panel.

| Nr. | Uhrzeit CET | Prompt wörtlich | Konnektor | Tool | Panel | Screenshot |
|---|---|---|---|---|---|---|
| 1 | 16:50:46 | Draw an antibody | chemdraw | generate_protein_or_antibody | ja, IgG-Domänenschema (1HZH) | `01-result.png` |
| 2 | 16:52:10 | Draw an antibody | chemdraw | generate_protein_or_antibody | ja, IgG-Domänenschema (1HZH) | `02-result.png` |
| 3 | 16:53:27 | Draw an antibody | chemdraw | generate_protein_or_antibody | ja, IgG-Domänenschema (1HZH) | `03-result.png` |
| 4 | 16:54:46 | Draw trastuzumab | chemdraw-pharma | generate_protein_or_antibody | ja, Fab-Cartoon (1N8Z) | `04-result.png` |

- Pro Versuch neuer Chat, Eingabefeld vor dem Absenden wörtlich geprüft (`01-input.ax` bis `04-input.ax`). Zeit per `date` unmittelbar vor dem Sendeklick. Keine verworfenen Versuche.
- Entwurf aus Runde 8 war beim ersten Lesezugriff bereits leer (`claude.ai/new`, leeres Eingabefeld); nichts davon abgesendet. Danach über New jeweils frischen Chat geöffnet.
- Alle vier Aufrufe fragten nach Genehmigung; jeweils ausschließlich **Allow once**. Danach Panel sichtbar, kein Fehler und kein ausstehender Genehmigungsdialog. Keine gespeicherten Rechte verändert.
- Einmalige Prozessaufnahme 16:50:29 CET in `processes.txt`: Python-Server **62908 / 62910**, Start **16:49:57**, **63025**, Start **16:49:59**, **63030**, Start **16:50:00** (10.11.2026). Keine Zuordnung eines einzelnen Toolaufrufs zu genau einer PID gemessen.
- Keine Einstellungsprüfung, keine Positivkontrolle, kein Code, kein Gate, kein Neustart. Arbeitsbaum am Ende sauber. Keine Deutung.
