"""
test_task_manager.py – Unit tests for the CLI Task Management System.
Run with: pytest test_task_manager.py -v
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from tasks import (
    create_task,
    list_tasks,
    get_task_by_id,
    update_task,
    complete_task,
    delete_task,
)
import storage


# ─── Test: Task Creation ───────────────────────────────────────────────────────
class TestCreateTask(unittest.TestCase):
    def setUp(self):
        self.tasks = []

    def test_create_basic_task(self):
        tasks, msg = create_task(self.tasks, "Buy groceries")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Buy groceries")
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertEqual(tasks[0]["priority"], "medium")
        self.assertIn("created_at", tasks[0])
        self.assertIn("Task", msg)

    def test_create_task_with_all_fields(self):
        tasks, _ = create_task(self.tasks, "Deploy app", "Push to prod", "high")
        self.assertEqual(tasks[0]["description"], "Push to prod")
        self.assertEqual(tasks[0]["priority"], "high")

    def test_create_multiple_tasks_unique_ids(self):
        tasks, _ = create_task(self.tasks, "Task A")
        tasks, _ = create_task(tasks, "Task B")
        ids = [t["id"] for t in tasks]
        self.assertEqual(len(set(ids)), 2)

    def test_create_task_empty_title_raises(self):
        with self.assertRaises(ValueError):
            create_task(self.tasks, "   ")

    def test_create_task_invalid_priority_raises(self):
        with self.assertRaises(ValueError):
            create_task(self.tasks, "Task", priority="urgent")

    def test_auto_increment_id_after_deletion(self):
        """ID should always be max+1, never reuse deleted IDs."""
        tasks, _ = create_task(self.tasks, "Task 1")
        tasks, _ = create_task(tasks, "Task 2")
        tasks, _ = delete_task(tasks, 1)
        tasks, _ = create_task(tasks, "Task 3")
        ids = [t["id"] for t in tasks]
        self.assertIn(3, ids)


# ─── Test: Task Update ────────────────────────────────────────────────────────
class TestUpdateTask(unittest.TestCase):
    def setUp(self):
        self.tasks = []
        self.tasks, _ = create_task(self.tasks, "Original Title", "Original desc", "low")

    def test_update_title(self):
        tasks, msg = update_task(self.tasks, 1, {"title": "New Title"})
        self.assertIsNotNone(tasks)
        self.assertEqual(tasks[0]["title"], "New Title")
        self.assertIn("updated", msg)

    def test_update_priority(self):
        tasks, _ = update_task(self.tasks, 1, {"priority": "high"})
        self.assertEqual(tasks[0]["priority"], "high")

    def test_update_description(self):
        tasks, _ = update_task(self.tasks, 1, {"description": "New desc"})
        self.assertEqual(tasks[0]["description"], "New desc")

    def test_update_nonexistent_task(self):
        tasks, msg = update_task(self.tasks, 999, {"title": "Ghost"})
        self.assertIsNone(tasks)
        self.assertIn("not found", msg)

    def test_update_empty_title_rejected(self):
        tasks, msg = update_task(self.tasks, 1, {"title": ""})
        self.assertIsNone(tasks)
        self.assertIn("empty", msg.lower())

    def test_update_invalid_priority(self):
        tasks, msg = update_task(self.tasks, 1, {"priority": "critical"})
        self.assertIsNone(tasks)
        self.assertIn("Invalid priority", msg)

    def test_update_disallowed_field(self):
        tasks, msg = update_task(self.tasks, 1, {"status": "completed"})
        self.assertIsNone(tasks)
        self.assertIn("cannot be updated", msg)


# ─── Test: Task Deletion ──────────────────────────────────────────────────────
class TestDeleteTask(unittest.TestCase):
    def setUp(self):
        self.tasks = []
        self.tasks, _ = create_task(self.tasks, "Delete me")

    def test_delete_existing_task(self):
        tasks, msg = delete_task(self.tasks, 1)
        self.assertIsNotNone(tasks)
        self.assertEqual(len(tasks), 0)
        self.assertIn("deleted", msg)

    def test_delete_nonexistent_task(self):
        tasks, msg = delete_task(self.tasks, 42)
        self.assertIsNone(tasks)
        self.assertIn("not found", msg)

    def test_delete_correct_task_from_multiple(self):
        self.tasks, _ = create_task(self.tasks, "Keep me")
        tasks, _ = delete_task(self.tasks, 1)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Keep me")


# ─── Test: Data Persistence ───────────────────────────────────────────────────
class TestDataPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.original_file = storage.TASKS_FILE
        # Redirect storage to a temp file
        storage.TASKS_FILE = os.path.join(self.tmp_dir.name, "test_tasks.json")

    def tearDown(self):
        storage.TASKS_FILE = self.original_file
        self.tmp_dir.cleanup()

    def test_save_and_load_round_trip(self):
        tasks = []
        tasks, _ = create_task(tasks, "Persist me", priority="high")
        storage.save_tasks(tasks)
        loaded = storage.load_tasks()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "Persist me")
        self.assertEqual(loaded[0]["priority"], "high")

    def test_load_returns_empty_list_when_no_file(self):
        result = storage.load_tasks()
        self.assertEqual(result, [])

    def test_load_returns_empty_list_on_malformed_json(self):
        with open(storage.TASKS_FILE, "w") as f:
            f.write("NOT VALID JSON {{{")
        result = storage.load_tasks()
        self.assertEqual(result, [])

    def test_multiple_saves_preserve_all_tasks(self):
        tasks = []
        for i in range(5):
            tasks, _ = create_task(tasks, f"Task {i+1}")
        storage.save_tasks(tasks)
        loaded = storage.load_tasks()
        self.assertEqual(len(loaded), 5)

    def test_overwrite_on_save(self):
        tasks = []
        tasks, _ = create_task(tasks, "First")
        storage.save_tasks(tasks)
        tasks2 = []
        tasks2, _ = create_task(tasks2, "Second")
        storage.save_tasks(tasks2)
        loaded = storage.load_tasks()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "Second")


# ─── Test: Invalid Input Handling ─────────────────────────────────────────────
class TestInvalidInputHandling(unittest.TestCase):
    def setUp(self):
        self.tasks = []

    def test_view_nonexistent_id_returns_none(self):
        result = get_task_by_id(self.tasks, 999)
        self.assertIsNone(result)

    def test_complete_nonexistent_task(self):
        tasks, msg = complete_task(self.tasks, 999)
        self.assertIsNone(tasks)
        self.assertIn("not found", msg)

    def test_complete_already_completed_task(self):
        self.tasks, _ = create_task(self.tasks, "Done task")
        self.tasks, _ = complete_task(self.tasks, 1)
        tasks, msg = complete_task(self.tasks, 1)
        self.assertIsNone(tasks)
        self.assertIn("already completed", msg)

    def test_create_task_strips_whitespace_from_title(self):
        tasks, _ = create_task(self.tasks, "  Trimmed  ")
        self.assertEqual(tasks[0]["title"], "Trimmed")

    def test_list_tasks_empty_produces_no_error(self):
        # Should not raise; just print a message
        try:
            list_tasks([])
        except Exception as exc:
            self.fail(f"list_tasks raised an exception: {exc}")


# ─── Test: Complete Task ──────────────────────────────────────────────────────
class TestCompleteTask(unittest.TestCase):
    def setUp(self):
        self.tasks = []
        self.tasks, _ = create_task(self.tasks, "Finish report")

    def test_complete_task_changes_status(self):
        tasks, msg = complete_task(self.tasks, 1)
        self.assertIsNotNone(tasks)
        self.assertEqual(tasks[0]["status"], "completed")
        self.assertIn("completed", msg)

    def test_complete_does_not_affect_other_fields(self):
        tasks, _ = complete_task(self.tasks, 1)
        self.assertEqual(tasks[0]["title"], "Finish report")
        self.assertEqual(tasks[0]["priority"], "medium")


# ─── Test: CLI Integration ────────────────────────────────────────────────────
class TestCLIIntegration(unittest.TestCase):
    """Integration tests that invoke main() with mocked sys.argv."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.original_file = storage.TASKS_FILE
        storage.TASKS_FILE = os.path.join(self.tmp_dir.name, "test_tasks.json")

    def tearDown(self):
        storage.TASKS_FILE = self.original_file
        self.tmp_dir.cleanup()

    @patch("sys.argv", ["task_manager", "add", "--title", "CLI Task", "--priority", "high"])
    def test_add_via_cli(self):
        from task_manager import main
        main()
        loaded = storage.load_tasks()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "CLI Task")
        self.assertEqual(loaded[0]["priority"], "high")
        self.assertEqual(loaded[0]["status"], "pending")

    @patch("sys.argv", ["task_manager", "list"])
    def test_list_via_cli_empty(self):
        from task_manager import main
        # Should not raise on empty task list
        try:
            main()
        except SystemExit:
            self.fail("main() raised SystemExit on 'list' with no tasks.")


if __name__ == "__main__":
    unittest.main(verbosity=2)