import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import types
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
        status_code = 200
        text = SAMPLE_HTML

        def raise_for_status(self):
            return None
    captured = {}
    def fake_get(url, headers, timeout):
        captured.update(headers)
        return DummyResp()
    monkeypatch.setattr("ue_configurator.indexer.requests.get", fake_get)
    data = scrape_console_variables("5.6")
    assert [d["name"] for d in data] == ["r.Test", "r.Test2"]
    # Ensure that our request includes the additional browser-like headers
    assert captured.get("Referer") == "https://dev.epicgames.com/documentation/"


def test_scrape_console_variables_cloudflare(monkeypatch):
    class ForbiddenResp:
        status_code = 403
        text = ""

        def raise_for_status(self):
            return None

    class DummyResp:
        status_code = 200
        text = SAMPLE_HTML

        def raise_for_status(self):
            return None

    def fake_requests_get(url, headers, timeout):
        return ForbiddenResp()

    called = {}

    class DummyScraper:
        def get(self, url, headers, timeout):
            called["used"] = True
            return DummyResp()

    # Patch requests.get to simulate a 403 response
    monkeypatch.setattr("ue_configurator.indexer.requests.get", fake_requests_get)
    # Patch cloudscraper.create_scraper to return our dummy scraper
    monkeypatch.setattr(
        "ue_configurator.indexer.cloudscraper",
        types.SimpleNamespace(create_scraper=lambda: DummyScraper()),
    )
    data = scrape_console_variables("5.6")
    assert called.get("used") is True
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
    built = build_cache(cache)
    data = json.loads(built.read_text())
    assert data[0]["name"] == "r.Online"
