"""
Docker runtime initializer.

Ensures `/app/Volume` has the required `settings.json` and `DouK-Downloader.db`
before handing off execution to `main.py`.

This avoids interactive prompts (language selection, disclaimer) that would
otherwise cause the container to exit on first boot when a fresh volume is
mounted.
"""

import json
import os
import sqlite3
from pathlib import Path


def ensure_volume() -> Path:
    """Ensure the persistent volume directory `/app/Volume` exists.

    Returns:
    - Path: The volume path.
    """
    vol = Path("/app/Volume")
    vol.mkdir(parents=True, exist_ok=True)
    return vol


def init_settings(volume: Path) -> None:
    """Create or update `settings.json` to force Web API mode.

    Parameters:
    - volume (Path): The mounted volume path.

    Returns:
    - None: Writes settings to disk.
    """
    settings_path = volume / "settings.json"
    data: dict
    try:
        if settings_path.exists():
            with settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        else:
            data = {}
    except Exception:
        data = {}

    # Ensure Web API mode on boot
    data["run_command"] = "7"

    with settings_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def init_database(volume: Path) -> None:
    """Create tables and seed defaults inside the mounted volume.

    Parameters:
    - volume (Path): The mounted volume path.

    Returns:
    - None: Writes database to disk.
    """
    db_path = volume / "DouK-Downloader.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS config_data (
          NAME TEXT PRIMARY KEY,
          VALUE INTEGER NOT NULL CHECK(VALUE IN (0, 1))
        );
        CREATE TABLE IF NOT EXISTS download_data (
          ID TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS mapping_data (
          ID TEXT PRIMARY KEY,
          NAME TEXT NOT NULL,
          MARK TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS option_data (
          NAME TEXT PRIMARY KEY,
          VALUE TEXT NOT NULL
        );
        """
    )

    # Insert defaults if missing, and force disclaimer accepted + language preset
    cur.execute("INSERT OR IGNORE INTO config_data (NAME, VALUE) VALUES ('Record', 1)")
    cur.execute("INSERT OR IGNORE INTO config_data (NAME, VALUE) VALUES ('Logger', 0)")
    cur.execute("INSERT OR REPLACE INTO config_data (NAME, VALUE) VALUES ('Disclaimer', 1)")
    cur.execute("INSERT OR IGNORE INTO option_data (NAME, VALUE) VALUES ('Language', 'zh_CN')")
    cur.execute("INSERT OR REPLACE INTO option_data (NAME, VALUE) VALUES ('Language', 'zh_CN')")

    conn.commit()
    conn.close()


def main() -> None:
    """Initialize runtime state, then exec the application entrypoint.

    Returns:
    - None: Replaces current process with `python main.py`.
    """
    vol = ensure_volume()
    init_settings(vol)
    init_database(vol)

    # Hand off to API-only entrypoint
    os.execvp("python", ["python", "api_main.py"])


if __name__ == "__main__":
    main()