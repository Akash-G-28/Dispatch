import json
import sqlite3
from pathlib import Path
from threading import Lock

from app.state.models import RunStatus, WorkflowRun, utcnow
from app.state.transitions import validate_transition


class RunNotFoundError(KeyError):
    pass


class SQLiteRunRepository:
    def __init__(self, database_url: str) -> None:
        raw_path = database_url.removeprefix("sqlite+aiosqlite:///").removeprefix("sqlite:///")
        self.path = raw_path if raw_path == ":memory:" else str(Path(raw_path).resolve())
        self._lock = Lock()
        self._connection: sqlite3.Connection | None = None
        if self.path == ":memory:":
            self._connection = sqlite3.connect(":memory:", check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock:
            db = self._connect()
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS side_effects (
                    action_key TEXT PRIMARY KEY, run_id TEXT NOT NULL, result TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
                    event TEXT NOT NULL, details TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)
            db.commit()
            if self._connection is None:
                db.close()

    def save(self, run: WorkflowRun) -> WorkflowRun:
        run.updated_at = utcnow()
        # The token hash is excluded from public API serialization but must survive persistence.
        persisted = run.model_dump(mode="json")
        persisted["approval_token_hash"] = run.approval_token_hash
        payload = json.dumps(persisted)
        with self._lock:
            db = self._connect()
            db.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, payload=excluded.payload",
                (run.run_id, run.idempotency_key, run.status.value, payload),
            )
            db.commit()
            if self._connection is None:
                db.close()
        return run

    def get(self, run_id: str) -> WorkflowRun:
        db = self._connect()
        row = db.execute("SELECT payload FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if self._connection is None:
            db.close()
        if not row:
            raise RunNotFoundError(run_id)
        return WorkflowRun.model_validate_json(row["payload"])

    def get_by_idempotency_key(self, key: str) -> WorkflowRun | None:
        db = self._connect()
        row = db.execute("SELECT payload FROM runs WHERE idempotency_key = ?", (key,)).fetchone()
        if self._connection is None:
            db.close()
        return WorkflowRun.model_validate_json(row["payload"]) if row else None

    def transition(self, run: WorkflowRun, target: RunStatus, details: dict | None = None) -> None:
        validate_transition(run.status, target)
        previous = run.status
        run.status = target
        self.save(run)
        self.audit(run.run_id, "state_transition", {"from": previous, "to": target, **(details or {})})

    def audit(self, run_id: str, event: str, details: dict) -> None:
        with self._lock:
            db = self._connect()
            db.execute(
                "INSERT INTO audit_events(run_id,event,details,created_at) VALUES (?,?,?,?)",
                (run_id, event, json.dumps(details, default=str), utcnow().isoformat()),
            )
            db.commit()
            if self._connection is None:
                db.close()

    def effect(self, action_key: str, run_id: str, operation) -> tuple[dict, bool]:
        with self._lock:
            db = self._connect()
            row = db.execute("SELECT result FROM side_effects WHERE action_key = ?", (action_key,)).fetchone()
            if row:
                if self._connection is None:
                    db.close()
                return json.loads(row["result"]), False
            result = operation()
            db.execute("INSERT INTO side_effects VALUES (?, ?, ?)", (action_key, run_id, json.dumps(result)))
            db.commit()
            if self._connection is None:
                db.close()
            return result, True
