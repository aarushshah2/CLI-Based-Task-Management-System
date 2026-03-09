import argparse
import sys
import logging
from storage import load_tasks, save_tasks
from tasks import (
    create_task,
    list_tasks,
    get_task_by_id,
    update_task,
    complete_task,
    delete_task,
)

#Logging Setup 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


#CLI Parsers 
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_manager",
        description="CLI Task Management System",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # add
    add_p = sub.add_parser("add", help="Add a new task")
    add_p.add_argument("--title", required=True, help="Task title")
    add_p.add_argument("--desc", default="", help="Task description")
    add_p.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
        help="Task priority (default: medium)",
    )

    # list
    sub.add_parser("list", help="View all tasks")

    # view
    view_p = sub.add_parser("view", help="View a task by ID")
    view_p.add_argument("--id", required=True, type=int, help="Task ID")

    # update
    update_p = sub.add_parser("update", help="Update a task")
    id_group = update_p.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--id", type=int, help="Task ID")
    id_group.add_argument("--find-title", metavar="TITLE", dest="find_title",
                          help="Locate task by its current title")
    update_p.add_argument("--title", help="New title")
    update_p.add_argument("--desc", help="New description")
    update_p.add_argument(
        "--priority", choices=["low", "medium", "high"], help="New priority"
    )

    # complete
    complete_p = sub.add_parser("complete", help="Mark a task as completed")
    complete_p.add_argument("--id", required=True, type=int, help="Task ID")

    # delete
    delete_p = sub.add_parser("delete", help="Delete a task")
    delete_p.add_argument("--id", required=True, type=int, help="Task ID")

    return parser


#Entry Point
def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    tasks = load_tasks()

    if args.command == "add":
        try:
            tasks, msg = create_task(tasks, args.title, args.desc, args.priority)
        except ValueError as exc:
            print(f"❌ {exc}")
            sys.exit(1)
        save_tasks(tasks)
        logger.info("Task created: %s", args.title)
        print(f"✅ {msg}")

    elif args.command == "list":
        list_tasks(tasks)

    elif args.command == "view":
        task = get_task_by_id(tasks, args.id)
        if task:
            _print_task(task)
        else:
            print(f"❌ Task with ID {args.id} not found.")
            sys.exit(1)

    elif args.command == "update":
        updates = {}
        if args.title is not None:
            updates["title"] = args.title
        if args.desc is not None:
            updates["description"] = args.desc
        if args.priority is not None:
            updates["priority"] = args.priority

        if not updates:
            print("⚠️  No fields to update. Provide --title, --desc, or --priority.")
            sys.exit(1)

        identifier = args.id if args.id is not None else args.find_title
        tasks, msg = update_task(tasks, identifier, updates)
        if tasks is not None:
            save_tasks(tasks)
            id_info = f"ID={args.id}" if args.id is not None else f"title='{args.find_title}'"
            logger.info("Task updated: %s fields=%s", id_info, list(updates.keys()))
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
            sys.exit(1)

    elif args.command == "complete":
        tasks, msg = complete_task(tasks, args.id)
        if tasks is not None:
            save_tasks(tasks)
            logger.info("Task completed: ID=%d", args.id)
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
            sys.exit(1)

    elif args.command == "delete":
        tasks, msg = delete_task(tasks, args.id)
        if tasks is not None:
            save_tasks(tasks)
            logger.info("Task deleted: ID=%d", args.id)
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
            sys.exit(1)


def _print_task(task: dict):
    """Pretty-print a single task."""
    priority_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
        task["priority"], "⚪"
    )
    status_icon = "✔️ " if task["status"] == "completed" else "⏳"
    print(
        f"\n{'─'*45}\n"
        f"  ID       : {task['id']}\n"
        f"  Title    : {task['title']}\n"
        f"  Desc     : {task['description'] or '—'}\n"
        f"  Priority : {priority_icon} {task['priority']}\n"
        f"  Status   : {status_icon} {task['status']}\n"
        f"  Created  : {task['created_at']}\n"
        f"{'─'*45}\n"
    )


if __name__ == "__main__":
    main()