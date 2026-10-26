"""Rollierende Referrer dürfen nicht als Stern-Herkunft ausgegeben werden."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/sterne-auswertung.py"


def module():
    spec = importlib.util.spec_from_file_location("sterne", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_report_keeps_negative_deltas_missing_sources_and_private_bios():
    mod = module()
    snapshots = [
        {"datum": "2026-10-25", "captured_at": "2026-10-25T08:00:00Z",
         "referrers": [{"referrer": "Google", "count": 9, "uniques": 7},
                       {"referrer": "Bing", "count": 2, "uniques": 2}]},
        {"datum": "2026-10-26", "captured_at": "2026-10-26T08:00:00Z",
         "referrers": [{"referrer": "Google", "count": 7, "uniques": 6}],
         "stargazers": [
             {"login": "1234", "starred_at": "2026-10-25T12:00:00Z",
              "created_at": "2026-10-20T00:00:00Z", "public_repos": 0,
              "followers": 0, "bio": "PRIVATE BIO"},
             {"login": "alice", "starred_at": "2026-10-01T12:00:00Z",
              "created_at": "2020-01-01T00:00:00Z", "public_repos": 10},
         ]},
    ]
    report = mod.render_report(snapshots)
    assert "Google: -2" in report
    assert "Bing: -2" in report
    assert "14-Tage" in report and "keinen Referrer pro Stern" in report
    assert "keine zeitliche Abdeckung" in report
    assert "rein numerisch" in report and "0 Repos" in report
    assert "PRIVATE BIO" not in report
    assert "unecht bewiesen" not in report


def test_failed_latest_list_does_not_represent_older_stars_as_current():
    report = module().render_report([
        {"datum": "2026-10-25", "referrers": [], "stargazers": [
            {"login": "old", "starred_at": "2026-10-01T00:00:00Z"}]},
        {"datum": "2026-10-26", "referrers": [], "stargazers": None,
         "stargazers_error": "API failed"},
    ])
    assert "Stargazer-Abruf fehlgeschlagen" in report
    assert "| old |" not in report
