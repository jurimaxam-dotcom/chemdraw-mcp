"""Die Messung muss auch bei GitHub-Teilfehlern Traffic erhalten."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/traffic-snapshot.sh"


@pytest.mark.parametrize("failure", ["", "stars", "profile"])
def test_snapshot_pagination_and_partial_failure(tmp_path, failure):
    gh = tmp_path / "gh"
    gh.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys
a = sys.argv[1:]
endpoint = a[1]
failure = os.environ.get("MOCK_FAILURE")
if endpoint.endswith("stargazers?per_page=100"):
    assert "--paginate" in a
    assert "Accept: application/vnd.github.star+json" in a
    if failure == "stars": sys.exit(1)
    print(json.dumps([{"starred_at":"2026-10-25T12:00:00Z", "user":{"login":"alice"}}]))
    print(json.dumps([{"starred_at":"2026-10-26T06:00:00Z", "user":{"login":"bob"}}]))
elif endpoint.startswith("users/"):
    if failure == "profile" and endpoint == "users/bob": sys.exit(1)
    print(json.dumps(dict(created_at="2020-01-01T00:00:00Z", followers=2,
        public_repos=3, location=None, company=None, bio="test")))
elif endpoint.endswith("views"): print('{"count":1,"views":[]}')
elif endpoint.endswith("clones"): print('{"count":2,"clones":[]}')
else: print('[]')
''')
    gh.chmod(0o755)
    root = tmp_path / "data"
    result = subprocess.run(["bash", str(SCRIPT)], env={
        **os.environ, "CHEMDRAW_TRAFFIC_ROOT": str(root),
        "CHEMDRAW_TRAFFIC_GH": str(gh), "MOCK_FAILURE": failure,
    }, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    snapshot = json.loads(next((root / "traffic").glob("*.json")).read_text())
    assert snapshot["views"]["count"] == 1
    assert snapshot["captured_at"].endswith("Z")
    if failure == "stars":
        assert snapshot["stargazers"] is None
        assert snapshot["stargazers_error"]
    else:
        assert [s["login"] for s in snapshot["stargazers"]] == ["alice", "bob"]
        assert snapshot["stargazers"][0]["public_repos"] == 3
        if failure == "profile":
            assert snapshot["stargazers"][1]["profile_error"]
            assert snapshot["stargazers"][1]["created_at"] is None
