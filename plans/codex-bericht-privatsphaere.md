# Codex-Bericht 20.10.2026: Privatsphäre-Check + Exportbug (mit Jay besprechen)

Quelle: Tisch-Faden `~/.claude/tisch/20261020-230643-jay-20-10-repo/004-codex-bericht.md` (23:08).

- [ ] **Persönliche Pfade im Repo:** `/Users/tom`-Pfade in `chemdraw_tool/ui/.repro-harness/payload-desktop.json:1`,
      `payload.json:1`, `run.mjs:8` (seit b532286) und `ui/src/utils/displayPath.test.mjs:6` (seit 6c9b308).
      Codex' Vorschlag: Harness entfernen oder neutralisieren, Testnutzer synthetisch. Sonst keine Keys, Mails, Adressen
      (924 Textblobs, 192 Commits geprüft). Historie bleibt unverändert.
- [ ] **Exportbug:** beide Buten-Stereoisomere überschreiben dieselbe `cccc.svg`. Codex hat es reproduziert,
      Regressionstest und Fix kommen von Codex.
- Codex macht auf seiner Seite persönliche Finanz-Checklisten generisch.
- Branch hat eigene ungemergte Commits, Migration in c0dd24d vorhanden, nichts gelöscht.

Nächster Schritt: mit Jay klären, ob die Harness-Dateien gelöscht oder neutralisiert werden.
