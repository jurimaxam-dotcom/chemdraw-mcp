"""Unit-Tests für Hilfsfunktionen aus chempane/ui/src/host/readme-gifs.mjs (ohne Desktop/Browser)."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UI_DIR = REPO / "chempane" / "ui"
SKRIPT = UI_DIR / "src" / "host" / "readme-gifs.mjs"


def _node(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "--input-type=module", "-e", code],
        cwd=UI_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def test_erster_tool_aufruf_begrenzt_anki_deliver_auf_apkg():
    """export_anki_deck darf im Aufnahme-Host nie deliver='open' an den Server reichen (würde Anki starten)."""
    r = _node(
        f"""
        import assert from "node:assert/strict";
        import {{ sichereToolArgs }} from {str(SKRIPT)!r};

        const eingabe = {{ name_or_smiles: "aspirin", deliver: "open" }};
        const aus = sichereToolArgs("export_anki_deck", eingabe);
        assert.deepEqual(aus, {{ name_or_smiles: "aspirin", deliver: "apkg" }});
        assert.equal(eingabe.deliver, "open");

        assert.deepEqual(
          sichereToolArgs("export_anki_deck", {{ name_or_smiles: "aspirin" }}),
          {{ name_or_smiles: "aspirin", deliver: "apkg" }},
        );
        assert.deepEqual(
          sichereToolArgs("generate_molecule", {{ name_or_smiles: "aspirin", deliver: "open" }}),
          {{ name_or_smiles: "aspirin", deliver: "open" }},
        );
        """
    )
    assert r.returncode == 0, r.stdout + r.stderr
    quelltext = SKRIPT.read_text(encoding="utf-8")
    assert "client.callTool({ name: tool, arguments: args })" not in quelltext


def test_feed_temp_ordner_wird_immer_aufgeraeumt():
    """Feed-Einzelbilder im Temp-Ordner werden sowohl nach Erfolg als auch nach Fehler entfernt."""
    r = _node(
        f"""
        import assert from "node:assert/strict";
        import {{ existsSync, writeFileSync }} from "node:fs";
        import {{ join }} from "node:path";
        import {{ mitTempOrdner }} from {str(SKRIPT)!r};

        let pfadOk = null;
        const erg = await mitTempOrdner("feed-test-ok-", async (dir) => {{
          pfadOk = dir;
          writeFileSync(join(dir, "f00000.jpg"), "x");
          assert.equal(existsSync(dir), true);
          return 42;
        }});
        assert.equal(erg, 42);
        assert.equal(existsSync(pfadOk), false);

        let pfadErr = null;
        await assert.rejects(
          mitTempOrdner("feed-test-err-", async (dir) => {{
            pfadErr = dir;
            writeFileSync(join(dir, "f00000.jpg"), "x");
            assert.equal(existsSync(dir), true);
            throw new Error("abbruch");
          }}),
          /abbruch/,
        );
        assert.equal(existsSync(pfadErr), false);
        """
    )
    assert r.returncode == 0, r.stdout + r.stderr
    quelltext = SKRIPT.read_text(encoding="utf-8")
    assert "mkdtempSync(join(tmpdir(), `feed-" not in quelltext


def test_szene_temp_ordner_nutzt_mit_temp_ordner():
    """Auch szene() (GIF-/Video-Modus) räumt seinen Temp-Ordner readme-<name>-<theme>- per mitTempOrdner auf."""
    quelltext = SKRIPT.read_text(encoding="utf-8")
    assert "mkdtempSync(join(tmpdir(), `readme-" not in quelltext
    assert "mitTempOrdner(`readme-${name}-${theme}-`" in quelltext
