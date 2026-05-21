from __future__ import annotations

import os
import re
import sqlite3
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from ui_templates import MAIN_HTML, category_window_html, safe_accent

try:
    import winsound
except ImportError:  # pragma: no cover - Windows has winsound.
    winsound = None


APP_NAME = "Simple Todo"
APP_DIR_NAME = "SimpleTodo"
DB_FILENAME = "todo.sqlite3"
DB_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
USER_DATETIME_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class Category:
    id: int
    name: str
    pending: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pending": self.pending,
            "total": self.total,
        }


@dataclass(frozen=True)
class Task:
    id: int
    category_id: int
    title: str
    completed: bool
    reminder_at: Optional[datetime]
    reminder_shown_at: Optional[datetime]
    category_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        due = self.reminder_at is not None and self.reminder_at <= datetime.now() and not self.completed
        return {
            "id": self.id,
            "category_id": self.category_id,
            "title": self.title,
            "completed": self.completed,
            "reminder_at": format_user_datetime(self.reminder_at) if self.reminder_at else "",
            "reminder_label": reminder_label(self.reminder_at),
            "due": due,
            "category_name": self.category_name or "",
        }


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        path = Path(base) / APP_DIR_NAME
    else:
        path = Path.home() / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_datetime(value: datetime) -> str:
    return value.strftime(DB_DATETIME_FORMAT)


def parse_db_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, DB_DATETIME_FORMAT)


def format_user_datetime(value: datetime) -> str:
    return value.strftime(USER_DATETIME_FORMAT)


def parse_reminder(value: str) -> Optional[datetime]:
    raw = value.strip()
    if not raw:
        return None

    lower = raw.lower()
    quick_match = re.fullmatch(r"\+?\s*(\d+)\s*(m|min|mins|minute|minutes)", lower)
    if quick_match:
        return datetime.now() + timedelta(minutes=int(quick_match.group(1)))

    quick_match = re.fullmatch(r"\+?\s*(\d+)\s*(h|hr|hrs|hour|hours)", lower)
    if quick_match:
        return datetime.now() + timedelta(hours=int(quick_match.group(1)))

    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if fmt == "%Y-%m-%d":
                parsed = parsed.replace(hour=9, minute=0)
            return parsed
        except ValueError:
            pass

    try:
        parsed_time = datetime.strptime(raw, "%H:%M").time()
        candidate = datetime.combine(datetime.now().date(), parsed_time)
        if candidate <= datetime.now():
            candidate += timedelta(days=1)
        return candidate
    except ValueError as exc:
        raise ValueError("Use YYYY-MM-DD HH:MM, HH:MM, +30m, or +2h.") from exc


def reminder_label(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    now = datetime.now()
    today = now.date()
    if value.date() == today:
        return f"Today {value:%H:%M}"
    if value.date() == today + timedelta(days=1):
        return f"Tomorrow {value:%H:%M}"
    if value.year == now.year:
        return value.strftime("%b %d %H:%M")
    return value.strftime(USER_DATETIME_FORMAT)


class TodoStore:
    def __init__(self, db_path: Path) -> None:
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def close(self) -> None:
        with self.lock:
            self.conn.close()

    def _init_schema(self) -> None:
        with self.lock:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    reminder_at TEXT,
                    reminder_shown_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_category_completed
                    ON tasks(category_id, completed);
                CREATE INDEX IF NOT EXISTS idx_tasks_reminder
                    ON tasks(completed, reminder_at, reminder_shown_at);
                """
            )
            if self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
                self.conn.execute(
                    "INSERT INTO categories(name, created_at) VALUES (?, ?)",
                    ("Inbox", db_datetime(datetime.now())),
                )
            self.conn.commit()

    def list_categories(self) -> list[Category]:
        with self.lock:
            rows = self.conn.execute(
                """
                SELECT
                    c.id,
                    c.name,
                    COUNT(t.id) AS total,
                    COALESCE(SUM(CASE WHEN t.completed = 0 THEN 1 ELSE 0 END), 0) AS pending
                FROM categories c
                LEFT JOIN tasks t ON t.category_id = c.id
                GROUP BY c.id, c.name
                ORDER BY lower(c.name)
                """
            ).fetchall()
        return [
            Category(
                id=int(row["id"]),
                name=str(row["name"]),
                pending=int(row["pending"]),
                total=int(row["total"]),
            )
            for row in rows
        ]

    def add_category(self, name: str) -> Category:
        clean = name.strip()
        if not clean:
            raise ValueError("Category name is required.")
        with self.lock:
            try:
                cursor = self.conn.execute(
                    "INSERT INTO categories(name, created_at) VALUES (?, ?)",
                    (clean, db_datetime(datetime.now())),
                )
                self.conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("That category already exists.") from exc
        return self.get_category(int(cursor.lastrowid))

    def get_category(self, category_id: int) -> Category:
        for category in self.list_categories():
            if category.id == category_id:
                return category
        raise ValueError("Category not found.")

    def rename_category(self, category_id: int, name: str) -> None:
        clean = name.strip()
        if not clean:
            raise ValueError("Category name is required.")
        with self.lock:
            try:
                self.conn.execute(
                    "UPDATE categories SET name = ? WHERE id = ?",
                    (clean, category_id),
                )
                self.conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("That category already exists.") from exc

    def delete_category(self, category_id: int) -> None:
        with self.lock:
            if self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] <= 1:
                raise ValueError("Keep at least one category.")
            self.conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self.conn.commit()

    def list_tasks(self, category_id: int) -> list[Task]:
        with self.lock:
            rows = self.conn.execute(
                """
                SELECT id, category_id, title, completed, reminder_at, reminder_shown_at
                FROM tasks
                WHERE category_id = ?
                ORDER BY
                    completed ASC,
                    CASE WHEN reminder_at IS NULL THEN 1 ELSE 0 END ASC,
                    datetime(reminder_at) ASC,
                    datetime(created_at) DESC
                """,
                (category_id,),
            ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def add_task(self, category_id: int, title: str, reminder_at: Optional[datetime]) -> int:
        clean = title.strip()
        if not clean:
            raise ValueError("Task title is required.")
        now = db_datetime(datetime.now())
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO tasks(category_id, title, completed, reminder_at, created_at, updated_at)
                VALUES (?, ?, 0, ?, ?, ?)
                """,
                (category_id, clean, db_datetime(reminder_at) if reminder_at else None, now, now),
            )
            self.conn.commit()
        return int(cursor.lastrowid)

    def update_task(self, task_id: int, title: str, reminder_at: Optional[datetime]) -> None:
        clean = title.strip()
        if not clean:
            raise ValueError("Task title is required.")
        with self.lock:
            self.conn.execute(
                """
                UPDATE tasks
                SET title = ?, reminder_at = ?, reminder_shown_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                (
                    clean,
                    db_datetime(reminder_at) if reminder_at else None,
                    db_datetime(datetime.now()),
                    task_id,
                ),
            )
            self.conn.commit()

    def set_completed(self, task_id: int, completed: bool) -> None:
        now = datetime.now()
        with self.lock:
            self.conn.execute(
                """
                UPDATE tasks
                SET completed = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    1 if completed else 0,
                    db_datetime(now) if completed else None,
                    db_datetime(now),
                    task_id,
                ),
            )
            self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()

    def due_reminders(self, now: datetime) -> list[Task]:
        with self.lock:
            rows = self.conn.execute(
                """
                SELECT
                    t.id,
                    t.category_id,
                    t.title,
                    t.completed,
                    t.reminder_at,
                    t.reminder_shown_at,
                    c.name AS category_name
                FROM tasks t
                JOIN categories c ON c.id = t.category_id
                WHERE
                    t.completed = 0
                    AND t.reminder_at IS NOT NULL
                    AND t.reminder_shown_at IS NULL
                    AND datetime(t.reminder_at) <= datetime(?)
                ORDER BY datetime(t.reminder_at) ASC
                """,
                (db_datetime(now),),
            ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def mark_reminders_shown(self, task_ids: list[int]) -> None:
        if not task_ids:
            return
        placeholders = ",".join("?" for _ in task_ids)
        with self.lock:
            self.conn.execute(
                f"UPDATE tasks SET reminder_shown_at = ? WHERE id IN ({placeholders})",
                [db_datetime(datetime.now()), *task_ids],
            )
            self.conn.commit()

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> Task:
        keys = row.keys()
        return Task(
            id=int(row["id"]),
            category_id=int(row["category_id"]),
            title=str(row["title"]),
            completed=bool(row["completed"]),
            reminder_at=parse_db_datetime(row["reminder_at"]),
            reminder_shown_at=parse_db_datetime(row["reminder_shown_at"]),
            category_name=row["category_name"] if "category_name" in keys else None,
        )


class TodoApi:
    def __init__(self) -> None:
        self.store = TodoStore(app_data_dir() / DB_FILENAME)
        self.main_window: Any = None
        self.category_windows: dict[int, Any] = {}
        self.accent = "#2563eb"

    def shutdown(self) -> None:
        for window in list(self.category_windows.values()):
            try:
                window.destroy()
            except Exception:
                pass
        self.category_windows.clear()
        self.store.close()

    def set_main_window(self, window: Any) -> None:
        self.main_window = window

    def list_categories(self) -> dict[str, Any]:
        return self._ok([category.to_dict() for category in self.store.list_categories()])

    def add_category(self, name: str) -> dict[str, Any]:
        return self._run(lambda: self.store.add_category(name).to_dict())

    def rename_category(self, category_id: int, name: str) -> dict[str, Any]:
        def action() -> None:
            clean_id = int(category_id)
            self.store.rename_category(clean_id, name)
            self._notify_category_window(clean_id)

        return self._run(action)

    def delete_category(self, category_id: int) -> dict[str, Any]:
        def action() -> None:
            clean_id = int(category_id)
            self.store.delete_category(clean_id)
            self._close_child(clean_id)

        return self._run(action)

    def list_tasks(self, category_id: int) -> dict[str, Any]:
        return self._run(lambda: [task.to_dict() for task in self.store.list_tasks(int(category_id))])

    def add_task(self, category_id: int, title: str, reminder: str) -> dict[str, Any]:
        def action() -> int:
            reminder_at = self._parse_future_reminder(reminder)
            return self.store.add_task(int(category_id), title, reminder_at)

        return self._run(action)

    def update_task(self, task_id: int, title: str, reminder: str) -> dict[str, Any]:
        def action() -> None:
            reminder_at = self._parse_future_reminder(reminder)
            self.store.update_task(int(task_id), title, reminder_at)

        return self._run(action)

    def set_completed(self, task_id: int, completed: bool) -> dict[str, Any]:
        return self._run(lambda: self.store.set_completed(int(task_id), bool(completed)))

    def delete_task(self, task_id: int) -> dict[str, Any]:
        return self._run(lambda: self.store.delete_task(int(task_id)))

    def get_due_reminders(self) -> dict[str, Any]:
        def action() -> list[dict[str, Any]]:
            due = self.store.due_reminders(datetime.now())
            self.store.mark_reminders_shown([task.id for task in due])
            if due:
                play_sound()
                self._notify_all_windows()
            return [task.to_dict() for task in due]

        return self._run(action)

    def set_accent(self, accent: str) -> dict[str, Any]:
        def action() -> str:
            self.accent = safe_accent(accent)
            for window in list(self.category_windows.values()):
                try:
                    window.evaluate_js(f"window.setAccentFromNative && window.setAccentFromNative('{self.accent}')")
                except Exception:
                    pass
            return self.accent

        return self._run(action)

    def open_category_window(self, category_id: int, accent: str = "#2563eb") -> dict[str, Any]:
        def action() -> int:
            import webview

            clean_id = int(category_id)
            self.accent = safe_accent(accent)
            category = self.store.get_category(clean_id)
            existing = self.category_windows.get(clean_id)
            if existing is not None:
                try:
                    existing.show()
                    existing.restore()
                    existing.evaluate_js("window.refreshFromNative && window.refreshFromNative()")
                    existing.evaluate_js(f"window.setAccentFromNative && window.setAccentFromNative('{self.accent}')")
                    return clean_id
                except Exception:
                    self.category_windows.pop(clean_id, None)

            child_api = CategoryWindowApi(self, clean_id)
            window = webview.create_window(
                category.name,
                html=category_window_html(category.id, category.name, self.accent),
                js_api=child_api,
                width=390,
                height=760,
                min_size=(320, 480),
                resizable=True,
                focus=True,
                background_color="#0b0d12",
                text_select=False,
            )
            if window is None:
                raise RuntimeError("Could not open category window.")
            child_api.set_window(window)
            self.category_windows[clean_id] = window
            window.events.closed += lambda: self._unregister_child(clean_id)
            return clean_id

        return self._run(action)

    def _notify_main(self) -> None:
        if self.main_window is None:
            return
        try:
            self.main_window.evaluate_js("window.refreshFromNative && window.refreshFromNative()")
        except Exception:
            pass

    def _notify_category_window(self, category_id: int) -> None:
        window = self.category_windows.get(category_id)
        if window is None:
            return
        try:
            window.evaluate_js("window.refreshFromNative && window.refreshFromNative()")
        except Exception:
            self.category_windows.pop(category_id, None)

    def _notify_all_windows(self) -> None:
        self._notify_main()
        for category_id in list(self.category_windows):
            self._notify_category_window(category_id)

    def _close_child(self, category_id: int) -> None:
        window = self.category_windows.pop(category_id, None)
        if window is None:
            return
        try:
            window.destroy()
        except Exception:
            pass

    def _unregister_child(self, category_id: int) -> None:
        self.category_windows.pop(category_id, None)

    @staticmethod
    def _parse_future_reminder(reminder: str) -> Optional[datetime]:
        reminder_at = parse_reminder(reminder)
        if reminder_at is not None and reminder_at <= datetime.now():
            raise ValueError("Reminder must be in the future.")
        return reminder_at

    @staticmethod
    def _ok(data: Any = None) -> dict[str, Any]:
        return {"ok": True, "data": data}

    def _run(self, action: Any) -> dict[str, Any]:
        try:
            return self._ok(action())
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class CategoryWindowApi:
    def __init__(self, parent: TodoApi, category_id: int) -> None:
        self.parent = parent
        self.category_id = category_id
        self.window: Any = None

    def set_window(self, window: Any) -> None:
        self.window = window

    def window_state(self) -> dict[str, Any]:
        def action() -> dict[str, Any]:
            category = self.parent.store.get_category(self.category_id)
            tasks = self.parent.store.list_tasks(self.category_id)
            return {
                "category": category.to_dict(),
                "tasks": [task.to_dict() for task in tasks],
            }

        return self.parent._run(action)

    def add_task(self, title: str, reminder: str) -> dict[str, Any]:
        def action() -> int:
            reminder_at = self.parent._parse_future_reminder(reminder)
            task_id = self.parent.store.add_task(self.category_id, title, reminder_at)
            self.parent._notify_main()
            return task_id

        return self.parent._run(action)

    def update_task(self, task_id: int, title: str, reminder: str) -> dict[str, Any]:
        def action() -> None:
            reminder_at = self.parent._parse_future_reminder(reminder)
            self.parent.store.update_task(int(task_id), title, reminder_at)
            self.parent._notify_main()

        return self.parent._run(action)

    def set_completed(self, task_id: int, completed: bool) -> dict[str, Any]:
        def action() -> None:
            self.parent.store.set_completed(int(task_id), bool(completed))
            self.parent._notify_main()

        return self.parent._run(action)

    def delete_task(self, task_id: int) -> dict[str, Any]:
        def action() -> None:
            self.parent.store.delete_task(int(task_id))
            self.parent._notify_main()

        return self.parent._run(action)

    def close_window(self) -> dict[str, Any]:
        return self.parent._run(lambda: self.parent._close_child(self.category_id))


def play_sound() -> None:
    if winsound is not None:
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return
        except RuntimeError:
            pass


def main() -> int:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit("pywebview is required to run from source. Install it or run the built exe.") from exc

    api = TodoApi()
    main_window = webview.create_window(
        APP_NAME,
        html=MAIN_HTML,
        js_api=api,
        width=920,
        height=680,
        min_size=(880, 560),
        background_color="#0b0d12",
        text_select=False,
    )
    api.set_main_window(main_window)
    try:
        webview.start(debug=False, gui="edgechromium", private_mode=False)
    finally:
        api.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
