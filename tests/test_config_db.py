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




