import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from pathlib import Path
from ue_configurator.indexer import parse_console_variable_page, scrape_console_variables, build_cache

SAMPLE_HTML = """
<table class=\"table\">
<thead><tr><th>Variable</th><th>Default Value</th><th>Description</th></tr></thead>
<tbody>
<tr><td><code>r.Test</code></td><td><code>0</code></td><td>Test variable</td></tr>
</tbody>
</table>
<table class=\"table\">
<thead><tr><th>Variable</th><th>Default Value</th><th>Description</th></tr></thead>
<tbody>
<tr><td><code>r.Test2</code></td><td><code>1</code></td><td>Second test variable</td></tr>
</tbody>
</table>
"""

def test_parse_console_variable_page():
    data = parse_console_variable_page(SAMPLE_HTML)
    assert len(data) == 2
    assert data[0]["name"] == "r.Test"
    assert data[1]["name"] == "r.Test2"
    assert data[1]["description"] == "Second test variable"

def test_scrape_console_variables(monkeypatch):
    class DummyResp:
        text = SAMPLE_HTML
        def raise_for_status(self):
            return None
    def fake_get(url, headers, timeout):
        return DummyResp()
    monkeypatch.setattr("ue_configurator.indexer.requests.get", fake_get)
    data = scrape_console_variables("5.6")
    assert [d["name"] for d in data] == ["r.Test", "r.Test2"]


def test_build_cache_online(monkeypatch, tmp_path: Path):
    def fake_scrape(version: str):
        return [
            {
                "name": "r.Online",
                "description": "Online var",
                "default": "0",
                "category": "",
                "range": "",
                "file": "",
            }
        ]

    monkeypatch.setattr(
        "ue_configurator.indexer.scrape_console_variables", fake_scrape
    )
    cache = tmp_path / "cache.json"
    build_cache(cache)
    data = json.loads(cache.read_text())
    assert data[0]["name"] == "r.Online"
