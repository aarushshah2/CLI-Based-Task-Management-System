# CLI-Based Task Management System

A command-line application for managing personal tasks, built in Python. Tasks are persisted to a local JSON file so data survives program restarts.

## Features

- **Add / View / Update / Delete** tasks from the terminal
- **Mark tasks as completed**
- Auto-generated unique IDs, timestamps, and priority levels (`low`, `medium`, `high`)
- Data persistence via JSON (atomic write-then-rename for safety)
- Structured logging to `app.log`
- 30 unit / integration tests

---

## Project Structure

```
.
├── task_manager.py          # CLI entry point (argparse)
├── tasks.py                 # Business-logic functions (CRUD)
├── storage.py               # JSON file persistence layer
├── test_task_manager.py     # Unit & integration tests
├── tasks.json               # Auto-created data file
├── app.log                  # Auto-created log file
└── README.md
```

## Setup Instructions

### Prerequisites

- **Python 3.9+** (uses modern type hints)

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/task-management-system.git
cd task-management-system
```

No external dependencies are required — the project uses only the Python standard library.

---

## How to Run

All commands follow the pattern:

```bash
python3 task_manager.py <command> [options]
```

### Add a Task

```bash
python3 task_manager.py add --title "Buy groceries" --desc "Milk, eggs, bread" --priority high
```

### List All Tasks

```bash
python3 task_manager.py list
```

### View a Task by ID

```bash
python3 task_manager.py view --id 1
```

### Update a Task

```bash
python3 task_manager.py update --id 1 --title "Updated title" --priority low
```

### Mark a Task as Completed

```bash
python3 task_manager.py complete --id 1
```

### Delete a Task

```bash
python3 task_manager.py delete --id 1
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Modular architecture** (`tasks.py`, `storage.py`, `task_manager.py`) | Separates business logic, persistence, and CLI concerns — makes each layer independently testable |
| **JSON file storage** | Simple, human-readable, zero dependencies; sufficient for a single-user CLI tool |
| **Atomic writes** (write to `.tmp`, then `os.replace`) | Prevents data corruption if the program crashes mid-write |
| **`(list, msg)` / `(None, msg)` return convention** | Functions return a tuple so callers can distinguish success from failure without exceptions for expected error paths (e.g., "task not found") |
| **`ValueError` for invalid input** | True programming errors (empty title, bad priority) raise exceptions; "not found" is a normal flow handled via return values |
| **Pathlib-anchored data file** | `tasks.json` is always stored next to `storage.py`, regardless of the user's working directory |
| **Logging to file + stdout** | `app.log` provides an audit trail; stdout keeps the user informed |

---

## Test Execution

Run the full test suite with the built-in `unittest` runner:

```bash
python3 -m unittest test_task_manager -v
```

Or with **pytest** (if installed):

```bash
python3 -m pytest test_task_manager.py -v
```

### Test Coverage Summary

| Test Class | # Tests | Covers |
|------------|---------|--------|
| `TestCreateTask` | 6 | Task creation, unique IDs, validation |
| `TestUpdateTask` | 7 | Field updates, invalid fields, edge cases |
| `TestDeleteTask` | 3 | Single/multi delete, not-found |
| `TestDataPersistence` | 5 | Save/load round-trip, malformed JSON, overwrites |
| `TestInvalidInputHandling` | 5 | Nonexistent IDs, already-completed, whitespace |
| `TestCompleteTask` | 2 | Status change, field preservation |
| `TestCLIIntegration` | 2 | End-to-end CLI `add` and `list` via mocked argv |
| **Total** | **30** | |
