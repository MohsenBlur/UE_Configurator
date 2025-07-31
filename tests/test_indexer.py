import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ue_configurator.indexer import index_headers, load_cache, detect_engine_from_uproject
from pathlib import Path

def test_index_headers(tmp_path: Path):
    header = tmp_path / "test.h"
    header.write_text(
        "// Category: Rendering\n// Range: 0-1\nIConsoleVariable::Register(\"r.Test\", 0, \"Test desc\");"
    )
    result = index_headers(tmp_path)
    assert any(r["name"] == "r.Test" for r in result)
    item = next(r for r in result if r["name"] == "r.Test")
    assert item["default"] == "0"
    assert item["category"] == "Rendering"
    assert item["range"] == "0-1"


def test_load_cache(tmp_path: Path):
    cache = tmp_path / "cache.json"
    cache.write_text('[{"name": "r.Test", "description": "Test", "default": "1", "category": "Cat", "range": "0-1"}]')
    data = load_cache(cache)
    assert data[0]["name"] == "r.Test"
    assert data[0]["default"] == "1"


def test_detect_engine(tmp_path: Path):
    engine = tmp_path / "Engine"
    engine.mkdir()
    proj = tmp_path / "Proj"
    proj.mkdir()
    (proj / "Proj.uproject").write_text('{"EngineAssociation": "%s"}' % engine)
    found = detect_engine_from_uproject(proj)
    assert found == engine
