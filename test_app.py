import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app import TodoStore, parse_reminder
from ui_templates import MAIN_HTML, category_window_html, safe_accent


class TodoStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = TodoStore(Path(self.temp_dir.name) / "test.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.temp_dir.cleanup()

    def test_category_task_and_completion_flow(self) -> None:
        category_id = self.store.add_category("Work").id
        task_id = self.store.add_task(category_id, "Send status", None)

        tasks = self.store.list_tasks(category_id)
        self.assertEqual([task.title for task in tasks], ["Send status"])
        self.assertFalse(tasks[0].completed)

        self.store.set_completed(task_id, True)
        tasks = self.store.list_tasks(category_id)
        self.assertTrue(tasks[0].completed)

    def test_due_reminder_is_shown_once(self) -> None:
        category_id = self.store.add_category("Timers").id
        task_id = self.store.add_task(
            category_id,
            "Stretch",
            datetime.now() - timedelta(minutes=1),
        )

        due = self.store.due_reminders(datetime.now())
        self.assertEqual([task.id for task in due], [task_id])

        self.store.mark_reminders_shown([task_id])
        self.assertEqual(self.store.due_reminders(datetime.now()), [])

    def test_quick_reminder_parser(self) -> None:
        reminder = parse_reminder("+30m")
        self.assertIsNotNone(reminder)
        self.assertGreater(reminder, datetime.now() + timedelta(minutes=20))

    def test_category_window_template_escapes_values(self) -> None:
        html = category_window_html(1, 'Work <Admin>', "not-a-color")
        self.assertIn("Work &lt;Admin&gt;", html)
        self.assertIn("--accent: #2563eb;", html)
        self.assertEqual(safe_accent("#10b981"), "#10b981")

    def test_category_window_uses_clean_vertical_task_layout(self) -> None:
        html = category_window_html(1, "Work", "#10b981")
        self.assertIn('id="taskTime" type="time"', html)
        self.assertIn('id="taskPeriod"', html)
        self.assertIn('id="todoHeader" class="section-heading"', html)
        self.assertIn('id="completedHeader" class="section-heading"', html)
        self.assertIn('id="completedList" class="list collapsed"', html)
        self.assertIn('class="section-heading"', html)
        self.assertIn('class="icon-button"', html)
        self.assertIn("selectedReminderDateTime", html)
        self.assertIn("bindHeaderToggle", html)
        self.assertIn("toggleTodo", html)
        self.assertIn("renderTodoState", html)
        self.assertNotIn("Reminder or +30m", html)
        self.assertNotIn("+15m", html)
        self.assertNotIn("<details", html)
        self.assertNotIn("pinButton", html)
        self.assertNotIn("toggle_pin", html)

    def test_add_category_button_is_disabled_until_text_exists(self) -> None:
        self.assertIn('onsubmit="return false;"', MAIN_HTML)
        self.assertIn('id="addCategoryButton"', MAIN_HTML)
        self.assertIn('type="button" onclick="addCategory(event)" disabled>Add Category</button>', MAIN_HTML)
        self.assertIn('onclick="addCategory(event)"', MAIN_HTML)
        self.assertIn('oninput="document.getElementById', MAIN_HTML)
        self.assertIn("disabled>Add Category</button>", MAIN_HTML)
        self.assertIn("updateCategoryButtonState", MAIN_HTML)
        self.assertIn("waitForApi", MAIN_HTML)
        self.assertIn("bindMainUi", MAIN_HTML)


if __name__ == "__main__":
    unittest.main()
