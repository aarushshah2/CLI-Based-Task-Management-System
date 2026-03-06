"""
storage.py – JSON file-based persistence layer.
All reads and writes go through load_tasks() / save_tasks().
"""

import json
import logging
import os
from pathlib import Path

# Anchor data file next to this script so it works regardless of cwd
TASKS_FILE = str(Path(__file__).parent / "tasks.json")
logger = logging.getLogger(__name__)


def load_tasks() -> list[dict]:
    """
    Load tasks from the JSON file.
    Returns an empty list if the file does not exist or is malformed.
    """
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, list):
                logger.warning(
                    "tasks.json contained non-list data; resetting to empty list."
                )
                return []
            return data
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse tasks.json: %s", exc)
        return []


def save_tasks(tasks: list[dict]) -> None:
    """
    Persist the task list to the JSON file atomically (write-then-rename).
    """
    tmp_file = TASKS_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as fh:
            json.dump(tasks, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_file, TASKS_FILE)
    except OSError as exc:
        logger.error("Failed to save tasks: %s", exc)
        raise