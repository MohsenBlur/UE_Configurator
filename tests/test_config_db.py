import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ue_configurator.config_db import ConfigDB
from pathlib import Path


def write_ini(path: Path, content: str) -> None:
    path.write_text(content)


def test_duplicate_detection(tmp_path: Path):
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini1 = cfg / "DefaultGame.ini"
    ini2 = cfg / "ProjectGame.ini"
    write_ini(ini1, "[Section]\nKey=1\n")
    write_ini(ini2, "[Section]\nKey=2\n")

    db = ConfigDB()
    db.load(cfg)
    dups = db.find_duplicates()
    assert ("Section", "key") in dups
    assert len(dups[("Section", "key")]) == 2


def test_comment_and_save(tmp_path: Path):
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini1 = cfg / "DefaultGame.ini"
    ini2 = cfg / "ProjectGame.ini"
    write_ini(ini1, "[Section]\nKey=1\n")
    write_ini(ini2, "[Section]\nKey=2\n")

    db = ConfigDB()
    db.load(cfg)
    db.save(cfg)

    backup_dirs = list((cfg / "Backup").iterdir())
    assert backup_dirs, "backup created"
    # lower priority file should have commented entry
    text = ini1.read_text()
    assert ";Key=1" in text or "#Key=1" in text


def test_insert_and_resolve(tmp_path: Path):
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini1 = cfg / "DefaultGame.ini"
    ini2 = cfg / "ProjectGame.ini"
    write_ini(ini1, "[ConsoleVariables]\nr.Test=0\n")
    write_ini(ini2, "[ConsoleVariables]\n")

    db = ConfigDB()
    db.load(cfg)
    db.insert_setting("ConsoleVariables", "r.Test", "1", "ProjectGame.ini")
    db.resolve_duplicate("ConsoleVariables", "r.Test", "delete")
    db.save(cfg)

    text2 = ini2.read_text().lower()
    text1 = ini1.read_text().lower()
    assert "r.test" in text2
    assert "r.test" not in text1


def test_load_ini_with_internal_duplicates(tmp_path: Path) -> None:
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini = cfg / "DefaultGame.ini"
    # same key appears twice in the file which previously triggered
    # ``DuplicateOptionError`` during loading.
    write_ini(ini, "[Section]\nKey=1\nKey=2\n")

    db = ConfigDB()
    # should not raise
    db.load(cfg)
    assert db.files, "ini file loaded"
    dups = db.find_duplicates()
    assert ("Section", "key") in dups
    # same file is returned twice for the duplicate entries
    assert len(dups[("Section", "key")]) == 2




