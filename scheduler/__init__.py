"""Task scheduler — cron/interval/once execution with background polling.

Reverse-engineered from OpenJarvis `scheduler/scheduler.py` + `scheduler/store.py`.
SQLite-backed persistence with background daemon thread.
"""

from __future__ import annotations
import json
import logging
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── SQLite Store ──────────────────────────────────────────────

class SchedulerStore:
    """SQLite CRUD store for scheduled tasks and run logs."""

    def __init__(self, db_path: str = "~/.nova/scheduler.db") -> None:
        resolved = Path(db_path).expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(resolved), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id              TEXT PRIMARY KEY,
                prompt          TEXT NOT NULL,
                schedule_type   TEXT NOT NULL,
                schedule_value  TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'active',
                next_run        TEXT,
                last_run        TEXT,
                metadata        TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS task_run_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     TEXT NOT NULL,
                started_at  TEXT NOT NULL,
                finished_at TEXT,
                success     INTEGER NOT NULL DEFAULT 0,
                result      TEXT NOT NULL DEFAULT '',
                error       TEXT NOT NULL DEFAULT ''
            );
        """)
        self._conn.commit()

    def save_task(self, task: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO scheduled_tasks "
            "(id, prompt, schedule_type, schedule_value, status, next_run, last_run, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task["id"], task["prompt"], task["schedule_type"],
                task["schedule_value"], task.get("status", "active"),
                task.get("next_run"), task.get("last_run"),
                json.dumps(task.get("metadata", {})),
            ),
        )
        self._conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM scheduled_tasks WHERE status = ?", (status,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM scheduled_tasks").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_due_tasks(self, now_iso: str) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM scheduled_tasks WHERE status = 'active' "
            "AND next_run IS NOT NULL AND next_run <= ?",
            (now_iso,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def log_run(self, task_id: str, started_at: str, finished_at: str,
                success: bool, result: str = "", error: str = "") -> None:
        self._conn.execute(
            "INSERT INTO task_run_logs (task_id, started_at, finished_at, success, result, error) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, started_at, finished_at, int(success), result, error),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if "metadata" in d and isinstance(d["metadata"], str):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except (json.JSONDecodeError, TypeError):
                d["metadata"] = {}
        return d


# ── Scheduled Task ────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """A task scheduled for future or recurring execution."""
    id: str
    prompt: str
    schedule_type: str   # "cron" | "interval" | "once"
    schedule_value: str  # cron expression, interval seconds, ISO datetime
    status: str = "active"
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "prompt": self.prompt,
            "schedule_type": self.schedule_type,
            "schedule_value": self.schedule_value,
            "status": self.status, "next_run": self.next_run,
            "last_run": self.last_run, "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ScheduledTask:
        return cls(
            id=d["id"], prompt=d["prompt"],
            schedule_type=d["schedule_type"],
            schedule_value=d["schedule_value"],
            status=d.get("status", "active"),
            next_run=d.get("next_run"),
            last_run=d.get("last_run"),
            metadata=d.get("metadata", {}),
        )


# ── Task Scheduler ────────────────────────────────────────────

class TaskScheduler:
    """Background scheduler that polls for due tasks.

    From OpenJarvis `scheduler/scheduler.py:TaskScheduler`.
    """

    def __init__(
        self,
        store: SchedulerStore,
        *,
        poll_interval: int = 60,
        task_handler: Optional[Callable[[ScheduledTask], str]] = None,
    ) -> None:
        self._store = store
        self._poll_interval = poll_interval
        self._task_handler = task_handler
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start background polling thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="nova-scheduler"
        )
        self._thread.start()
        logger.info("Scheduler started (poll=%ds)", self._poll_interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 5)
            self._thread = None

    def create_task(self, prompt: str, schedule_type: str, schedule_value: str,
                    **kwargs: Any) -> ScheduledTask:
        task = ScheduledTask(
            id=uuid.uuid4().hex[:16], prompt=prompt,
            schedule_type=schedule_type, schedule_value=schedule_value,
            metadata=kwargs.get("metadata", {}),
        )
        task.next_run = self._compute_next_run(task)
        self._store.save_task(task.to_dict())
        return task

    def list_tasks(self, status: Optional[str] = None) -> List[ScheduledTask]:
        return [ScheduledTask.from_dict(r) for r in self._store.list_tasks(status)]

    def cancel_task(self, task_id: str) -> None:
        d = self._store.get_task(task_id)
        if d:
            d["status"] = "cancelled"
            d["next_run"] = None
            self._store.save_task(d)

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                now = datetime.now(timezone.utc).isoformat()
                for task_dict in self._store.get_due_tasks(now):
                    task = ScheduledTask.from_dict(task_dict)
                    self._execute_task(task)
            except Exception:
                logger.exception("Scheduler poll error")
            self._stop_event.wait(timeout=self._poll_interval)

    def _execute_task(self, task: ScheduledTask) -> None:
        started = datetime.now(timezone.utc).isoformat()
        result_text, error_text, success = "", "", False
        try:
            if self._task_handler:
                result_text = self._task_handler(task) or ""
            else:
                result_text = f"[dry-run] Would execute: {task.prompt}"
            success = True
        except Exception as exc:
            error_text = str(exc)
            logger.error("Task %s failed: %s", task.id, exc)

        finished = datetime.now(timezone.utc).isoformat()
        self._store.log_run(task.id, started, finished, success, result_text, error_text)

        d = self._store.get_task(task.id)
        if d:
            d["last_run"] = finished
            d["next_run"] = self._compute_next_run(ScheduledTask.from_dict(d))
            if d["next_run"] is None:
                d["status"] = "completed"
            self._store.save_task(d)

    @staticmethod
    def _compute_next_run(task: ScheduledTask) -> Optional[str]:
        now = datetime.now(timezone.utc)
        if task.schedule_type == "once":
            return None if task.last_run else task.schedule_value
        if task.schedule_type == "interval":
            return (now + timedelta(seconds=float(task.schedule_value))).isoformat()
        if task.schedule_type == "cron":
            try:
                from croniter import croniter
                return croniter(task.schedule_value, now).get_next(datetime).isoformat()
            except ImportError:
                return (now + timedelta(hours=1)).isoformat()
        return None


__all__ = ["ScheduledTask", "SchedulerStore", "TaskScheduler"]
