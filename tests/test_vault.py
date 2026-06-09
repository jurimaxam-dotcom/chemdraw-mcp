import pytest

from chemdraw_tool.vault import VAULT_PATH, list_entries, read_entry, search


@pytest.fixture(autouse=True)
def _skip_if_no_vault():
    if VAULT_PATH is None or not VAULT_PATH.exists():
        pytest.skip(
            "Vault not present on this machine (set CHEMDRAW_VAULT_PATH to enable)"
        )


class TestListEntries:
    def test_returns_categories(self):
        entries = list_entries()
        assert "Arzneistoffe" in entries
        assert "Methoden" in entries
        assert "Analysen" in entries

    def test_arzneistoffe_not_empty(self):
        entries = list_entries()
        assert len(entries["Arzneistoffe"]) > 10


class TestSearch:
    def test_exact_match_scores_highest(self):
        results = search("Paracetamol")
        assert results
        assert results[0]["name"] == "Paracetamol"
        assert results[0]["score"] == 100

    def test_substring_match(self):
        results = search("Acidimetrie")
        assert results
        names = [r["name"] for r in results]
        assert "Acidimetrie" in names

    def test_content_match(self):
        results = search("Sulfonylharnstoff")
        assert results
        for r in results:
            assert r["snippet"]

    def test_no_results(self):
        results = search("xyznonexistent12345")
        assert results == []

    def test_empty_query(self):
        assert search("") == []

    def test_case_insensitive(self):
        results = search("paracetamol")
        assert results
        assert results[0]["name"] == "Paracetamol"

    def test_returns_category(self):
        results = search("Paracetamol")
        assert results[0]["category"] == "Arzneistoffe"

    def test_max_10_results(self):
        results = search("Analyse")
        assert len(results) <= 10


class TestReadEntry:
    def test_exact_name(self):
        name, content = read_entry("Paracetamol")
        assert name == "Paracetamol"
        assert "Anilin-Derivat" in content

    def test_case_insensitive(self):
        name, content = read_entry("paracetamol")
        assert name == "Paracetamol"
        assert content is not None

    def test_partial_name(self):
        name, content = read_entry("Acetylsalicyl")
        assert name is not None
        assert "Acetylsalicylsäure" in name

    def test_not_found(self):
        name, content = read_entry("xyznonexistent12345")
        assert name is None
        assert content is None

    def test_method_entry(self):
        name, content = read_entry("Redoxtitration")
        assert name == "Redoxtitration"
        assert "Maßlösung" in content or "Redox" in content

    def test_analysis_entry(self):
        name, content = read_entry("Analyse 05 — Validierung")
        assert name is not None
        assert content is not None
