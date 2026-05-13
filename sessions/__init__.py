"""Session management — SQLite-backed persistent conversation sessions.

Reverse-engineered from OpenJarvis `sessions/session.py`.
Provides session persistence, consolidation, and decay for Nova.
"""

from __future__ import annotations
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionMessage:
    """A single message within a session."""
    role: str       # "user" | "assistant" | "system"
    content: str
    channel: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """A conversation session with history."""
    session_id: str = ""
    user_id: str = ""
    messages: List[SessionMessage] = field(default_factory=list)
    created_at: float = 0.0
    last_activity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(
            SessionMessage(role=role, content=content, timestamp=time.time())
        )
        self.last_activity = time.time()


class SessionStore:
    """SQLite-backed session persistence with consolidation and decay.

    From OpenJarvis `sessions/session.py:SessionStore`.
    """

    def __init__(
        self,
        db_path: str = "~/.nova/sessions.db",
        *,
        max_age_hours: float = 24.0,
        consolidation_threshold: int = 50,
    ) -> None:
        resolved = Path(db_path).expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(resolved), check_same_thread=False)
        self._max_age_hours = max_age_hours
        self._consolidation_threshold = consolidation_threshold
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id    TEXT PRIMARY KEY,
                user_id       TEXT,
                created_at    REAL,
                last_activity REAL,
                metadata      TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS session_messages (
                id         INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                timestamp  REAL,
                metadata   TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );
            CREATE INDEX IF NOT EXISTS idx_msg_session
                ON session_messages(session_id);
        """)
        self._conn.commit()

    def get_or_create(self, user_id: str = "default") -> Session:
        """Get existing session or create a new one."""
        row = self._conn.execute(
            "SELECT session_id, user_id, created_at, last_activity, metadata "
            "FROM sessions WHERE user_id = ? ORDER BY last_activity DESC LIMIT 1",
            (user_id,),
        ).fetchone()

        if row:
            session_id = row[0]
            age_hours = (time.time() - (row[3] or 0)) / 3600
            if age_hours > self._max_age_hours:
                return self._create_session(user_id)
            messages = self._load_messages(session_id)
            return Session(
                session_id=session_id,
                user_id=row[1],
                messages=messages,
                created_at=row[2] or 0.0,
                last_activity=row[3] or 0.0,
                metadata=json.loads(row[4]) if row[4] else {},
            )
        return self._create_session(user_id)

    def _create_session(self, user_id: str) -> Session:
        session_id = uuid.uuid4().hex[:16]
        now = time.time()
        self._conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at, last_activity) "
            "VALUES (?, ?, ?, ?)",
            (session_id, user_id, now, now),
        )
        self._conn.commit()
        return Session(session_id=session_id, user_id=user_id, created_at=now, last_activity=now)

    def save_message(self, session_id: str, role: str, content: str) -> None:
        """Persist a message to a session."""
        self._conn.execute(
            "INSERT INTO session_messages (session_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, time.time()),
        )
        self._conn.execute(
            "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
            (time.time(), session_id),
        )
        self._conn.commit()

        # Auto-consolidate if too many messages
        count = self._conn.execute(
            "SELECT COUNT(*) FROM session_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        if count > self._consolidation_threshold:
            self.consolidate(session_id)

    def consolidate(self, session_id: str) -> None:
        """Summarize oldest half of messages, keep recent half."""
        messages = self._load_messages(session_id)
        if len(messages) <= self._consolidation_threshold // 2:
            return
        split = len(messages) // 2
        old_messages = messages[:split]

        summary_parts = [f"[{m.role}] {m.content[:100]}" for m in old_messages[:10]]
        summary = "Session history summary:\n" + "\n".join(summary_parts)

        oldest_ts = old_messages[-1].timestamp if old_messages else 0
        self._conn.execute(
            "DELETE FROM session_messages WHERE session_id = ? AND timestamp <= ?",
            (session_id, oldest_ts),
        )
        self._conn.execute(
            "INSERT INTO session_messages (session_id, role, content, timestamp) "
            "VALUES (?, 'system', ?, ?)",
            (session_id, summary, time.time()),
        )
        self._conn.commit()

    def decay(self, max_age_hours: Optional[float] = None) -> int:
        """Remove sessions older than max_age_hours."""
        age = max_age_hours or self._max_age_hours
        cutoff = time.time() - (age * 3600)
        rows = self._conn.execute(
            "SELECT session_id FROM sessions WHERE last_activity < ?", (cutoff,)
        ).fetchall()
        for (sid,) in rows:
            self._conn.execute("DELETE FROM session_messages WHERE session_id = ?", (sid,))
            self._conn.execute("DELETE FROM sessions WHERE session_id = ?", (sid,))
        self._conn.commit()
        return len(rows)

    def _load_messages(self, session_id: str) -> List[SessionMessage]:
        rows = self._conn.execute(
            "SELECT role, content, timestamp, metadata FROM session_messages "
            "WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        ).fetchall()
        return [
            SessionMessage(
                role=r[0], content=r[1], timestamp=r[2] or 0.0,
                metadata=json.loads(r[3]) if r[3] else {},
            )
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()


__all__ = ["Session", "SessionMessage", "SessionStore"]
