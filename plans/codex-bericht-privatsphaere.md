# Codex-Bericht 20.10.2026: Privatsphäre-Check + Exportbug (mit Jay besprechen)

Quelle: Tisch-Faden `~/.claude/tisch/20261020-230643-jay-20-10-repo/004-codex-bericht.md` (23:08).

- [ ] **Historische persönliche Pfade:** reale macOS-Benutzerpfade in `chemdraw_tool/ui/.repro-harness/payload-desktop.json:1`,
      `payload.json:1`, `run.mjs:8` (seit b532286) und `ui/src/utils/displayPath.test.mjs:6` (seit 6c9b308).
      Codex' Vorschlag: Harness entfernen oder neutralisieren, Testnutzer synthetisch. Sonst keine Keys, Mails, Adressen
      (924 Textblobs, 192 Commits geprüft). Historie bleibt unverändert.
- [x] **Exportbug:** SMILES-Exporte durch stabilen Fingerabdruck getrennt (`20c204f`),
      zwölf Regressionen erst rot, dann grün; vollständiges Gate grün.
- Persönliche Finanz-Checklisten sind generisch formuliert.
- Branch hat eigene ungemergte Commits, Migration in c0dd24d vorhanden, nichts gelöscht.

Aktueller Stand und Entscheidungen: `docs/release-audit-2026-10-20.md`.
