"""
tasks.py – Pure business-logic functions for task operations.
All functions receive the task list and return (updated_list, message).
None is returned as the list on failure so callers can detect errors.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed"}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _next_id(tasks: list[dict]) -> int:
    """Return the next available integer task ID."""
    return max((t["id"] for t in tasks), default=0) + 1


def _find_task(tasks: list[dict], task_id: int) -> dict | None:
    """Return the task dict matching task_id, or None."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def _find_task_by_title(tasks: list[dict], title: str) -> list[dict]:
    """Return all tasks whose title matches (case-insensitive)."""
    return [t for t in tasks if t["title"].lower() == title.lower()]


def _resolve_task(tasks: list[dict], identifier: int | str) -> tuple[dict | None, str | None]:
    """
    Resolve a task by ID (int) or title (str).
    Returns (task, None) on success, or (None, error_message) on failure.
    """
    if isinstance(identifier, int):
        task = _find_task(tasks, identifier)
        if task is None:
            return None, f"Task with ID {identifier} not found."
        return task, None
    else:
        matches = _find_task_by_title(tasks, identifier)
        if not matches:
            return None, f"No task with title '{identifier}' found."
        if len(matches) > 1:
            ids = ", ".join(str(t["id"]) for t in matches)
            return None, (
                f"Multiple tasks match title '{identifier}' (IDs: {ids}). "
                f"Use --id to be specific."
            )
        return matches[0], None


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── CRUD Operations ──────────────────────────────────────────────────────────
def create_task(
    tasks: list[dict],
    title: str,
    description: str = "",
    priority: str = "medium",
) -> tuple[list[dict], str]:
    """
    Create a new task and append it to the list.

    Returns (updated_tasks, success_message) or raises ValueError on bad input.
    """
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty.")
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority '{priority}'. Choose: low, medium, high.")

    task: dict[str, Any] = {
        "id": _next_id(tasks),
        "title": title,
        "description": description.strip(),
        "priority": priority,
        "status": "pending",
        "created_at": _now(),
    }
    tasks.append(task)
    return tasks, f"Task '{title}' created with ID {task['id']}."


def list_tasks(tasks: list[dict]) -> None:
    """Print all tasks to stdout in a tabular format."""
    if not tasks:
        print("📭 No tasks found.")
        return

    header = f"{'ID':<5} {'Title':<30} {'Priority':<10} {'Status':<12} {'Created'}"
    print(f"\n{'─'*85}")
    print(header)
    print(f"{'─'*85}")
    for t in tasks:
        status_icon = "✔️ " if t["status"] == "completed" else "⏳"
        priority_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
            t["priority"], "⚪"
        )
        print(
            f"{t['id']:<5} {t['title']:<30} {priority_icon} {t['priority']:<8} "
            f"{status_icon} {t['status']:<10} {t['created_at']}"
        )
    print(f"{'─'*85}")
    print(f"Total: {len(tasks)} task(s)\n")


def get_task_by_id(tasks: list[dict], task_id: int) -> dict | None:
    """Return a single task by ID, or None if not found."""
    return _find_task(tasks, task_id)


def update_task(
    tasks: list[dict],
    identifier: int | str,
    updates: dict,
) -> tuple[list[dict] | None, str]:
    """
    Update allowed fields (title, description, priority) of a task.

    ``identifier`` can be an integer task ID or a string title.
    Returns (updated_tasks, message). Returns (None, error_msg) on failure.
    """
    task, err = _resolve_task(tasks, identifier)
    if err:
        return None, err
    task_id = task["id"]

    allowed_fields = {"title", "description", "priority"}
    for field, value in updates.items():
        if field not in allowed_fields:
            return None, f"Field '{field}' cannot be updated."
        if field == "title":
            value = value.strip()
            if not value:
                return None, "Title cannot be empty."
        if field == "priority" and value not in VALID_PRIORITIES:
            return None, f"Invalid priority '{value}'. Choose: low, medium, high."
        task[field] = value

    return tasks, f"Task ID {task_id} updated successfully."


def complete_task(
    tasks: list[dict], task_id: int
) -> tuple[list[dict] | None, str]:
    """
    Mark a task as completed.

    Returns (updated_tasks, message). Returns (None, error_msg) on failure.
    """
    task = _find_task(tasks, task_id)
    if task is None:
        return None, f"Task with ID {task_id} not found."
    if task["status"] == "completed":
        return None, f"Task ID {task_id} is already completed."

    task["status"] = "completed"
    return tasks, f"Task ID {task_id} marked as completed."


def delete_task(
    tasks: list[dict], task_id: int
) -> tuple[list[dict] | None, str]:
    """
    Delete a task by ID.

    Returns (updated_tasks, message). Returns (None, error_msg) on failure.
    """
    task = _find_task(tasks, task_id)
    if task is None:
        return None, f"Task with ID {task_id} not found."

    tasks.remove(task)
    return tasks, f"Task ID {task_id} deleted successfully."