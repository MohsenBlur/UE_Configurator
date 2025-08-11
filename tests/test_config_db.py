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

def test_comment_requires_user_action(tmp_path: Path):
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini1 = cfg / "DefaultGame.ini"
    ini2 = cfg / "ProjectGame.ini"
    write_ini(ini1, "[Section]\nKey=1\n")
    write_ini(ini2, "[Section]\nKey=2\n")

    db = ConfigDB()
    db.load(cfg)
    # Saving without resolving duplicates should keep both entries intact
    db.save(cfg)
    text = ini1.read_text()
    assert "Key=1" in text and ";Key=1" not in text and "#Key=1" not in text

    # User explicitly resolves the duplicate by commenting the lower priority
    db.resolve_duplicate("Section", "Key", "comment")
    db.save(cfg)

    backup_dirs = list((cfg / "Backup").iterdir())
    assert backup_dirs, "backup created"
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


def test_ignore_files(tmp_path: Path) -> None:
    cfg = tmp_path / "Config"
    cfg.mkdir()
    ini1 = cfg / "DefaultGame.ini"
    ini2 = cfg / "ProjectGame.ini"
    write_ini(ini1, "[Section]\nKey=1\n")
    write_ini(ini2, "[Section]\nKey=2\n")

    db = ConfigDB()
    db.load(cfg)
    # disable the default ini
    db.set_file_enabled("DefaultGame.ini", False)

    # only project ini should be available
    assert db.available_targets() == ["ProjectGame.ini"]
    # no duplicates when one file is ignored
    assert db.find_duplicates() == {}

    # insert without specifying target should go to project ini
    db.insert_setting("Section", "NewKey", "3")
    db.save(cfg)
    assert "newkey" in ini2.read_text().lower()
    assert "newkey" not in ini1.read_text().lower()




