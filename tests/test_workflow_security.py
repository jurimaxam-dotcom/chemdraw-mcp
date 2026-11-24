"""Sicherheitsregeln für GitHub-Workflows (Zwei-Job-Muster und Tag-Sperre bei publish.yml)."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _lade(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _nutzt_modell(job: dict) -> bool:
    text = yaml.safe_dump(job)
    return "claude-code-action" in text or "CLAUDE_CODE_OAUTH_TOKEN" in text


def test_doku_waechter_trennt_modell_und_schreibrecht():
    """Zwei-Job-Muster (wie zustandsbericht.yml): der Modell-Job darf nur lesen
    und keine Issues kommentieren; der Schreib-Job hat kein Modell."""
    wf = _lade("doku-waechter.yml")
    assert wf.get("permissions") == {}, "Top-Level-permissions muss {} sein, damit kein Job Schreibrechte erbt"

    jobs = wf["jobs"]
    modell_jobs = [name for name, job in jobs.items() if _nutzt_modell(job)]
    schreib_jobs = [name for name, job in jobs.items() if (job.get("permissions") or {}).get("issues") == "write"]

    assert modell_jobs, "Kein Modell-Job in doku-waechter.yml gefunden"
    assert schreib_jobs, "Kein Schreib-Job mit issues: write in doku-waechter.yml gefunden"
    assert set(modell_jobs).isdisjoint(schreib_jobs), f"Modell- und Schreib-Job nicht getrennt: {modell_jobs} vs {schreib_jobs}"

    for name in modell_jobs:
        job = jobs[name]
        perms = job.get("permissions") or {}
        assert all(v in ("read", "none") for v in perms.values()), f"Modell-Job {name} hat Schreibrechte: {perms}"
        assert "gh issue comment" not in yaml.safe_dump(job), f"Modell-Job {name} darf keine Issues kommentieren"

    for name in schreib_jobs:
        job = jobs[name]
        assert not _nutzt_modell(job), f"Schreib-Job {name} darf kein Modell aufrufen"
        needs = job.get("needs")
        needs_set = {needs} if isinstance(needs, str) else set(needs or [])
        assert needs_set & set(modell_jobs), f"Schreib-Job {name} hängt nicht vom Modell-Job ab"


def test_publish_workflow_laesst_handstart_nur_fuer_v_tags_zu():
    """workflow_dispatch darf keinen Release von einem Branch starten — nur Tags refs/tags/v*."""
    wf = _lade("publish.yml")
    for job_name in ("check", "publish"):
        bedingung = str(wf["jobs"][job_name].get("if") or "")
        assert "startsWith(github.ref, 'refs/tags/v')" in bedingung, (
            f"publish.yml Job {job_name!r} braucht if: startsWith(github.ref, 'refs/tags/v')"
        )


def test_doku_waechter_sichert_body_vor_modell_und_trennt_artefakte():
    """body.md muss vor dem claude-code-action-Schritt als eigenes Artefakt hochgeladen werden,
    damit das Modell den ungefilterten Issue-Body nicht per Write überschreiben kann."""
    wf = _lade("doku-waechter.yml")
    steps = wf["jobs"]["pruefen"]["steps"]
    claude_idx = next(i for i, s in enumerate(steps) if "claude-code-action" in str(s.get("uses", "")))
    uploads = [
        (i, s.get("with") or {})
        for i, s in enumerate(steps)
        if "actions/upload-artifact" in str(s.get("uses", ""))
    ]
    body_uploads = [(i, w) for i, w in uploads if "body.md" in str(w.get("path", ""))]
    einordnung_uploads = [(i, w) for i, w in uploads if "einordnung.md" in str(w.get("path", ""))]

    assert body_uploads, "Kein Upload-Schritt für body.md gefunden"
    assert all(i < claude_idx for i, _ in body_uploads), "Upload von body.md muss vor claude-code-action liegen"
    assert einordnung_uploads, "Kein eigener Upload-Schritt für einordnung.md gefunden"
    assert all(i > claude_idx for i, _ in einordnung_uploads), "Upload von einordnung.md muss nach claude-code-action liegen"
    for _, w in einordnung_uploads:
        assert "body.md" not in str(w.get("path", "")), "Einordnungs-Artefakt darf body.md nicht enthalten"
        assert w.get("name") != body_uploads[0][1].get("name"), "Body und Einordnung müssen getrennte Artefakte sein"


def test_workflows_setzen_explizite_permissions_fuer_jeden_job():
    """CodeQL #17/#3: jeder Job in ci.yml, publish.yml und doku-waechter.yml hat effektive permissions."""
    for datei in ("ci.yml", "publish.yml", "doku-waechter.yml"):
        wf = _lade(datei)
        assert "permissions" in wf, f"{datei}: Top-Level-permissions fehlt"
        for job_name, job in wf["jobs"].items():
            eff = job["permissions"] if "permissions" in job else wf["permissions"]
            assert isinstance(eff, dict) and eff, f"{datei} Job {job_name!r}: keine effektiven permissions"
