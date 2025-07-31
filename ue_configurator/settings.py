"""Load and save user settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SETTINGS_FILE = Path.home() / ".ue5_config_assistant" / "settings.json"


def load_settings() -> Dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_settings(data: Dict[str, Any]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = load_settings()
    existing.update(data)
    SETTINGS_FILE.write_text(json.dumps(existing, indent=2))
