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
