import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ue_configurator.indexer import index_headers
from pathlib import Path

def test_index_headers(tmp_path: Path):
    header = tmp_path / "test.h"
    header.write_text('IConsoleVariable::Register("r.Test", "Test desc", 0);')
    result = index_headers(tmp_path)
    assert any(r["name"] == "r.Test" for r in result)
