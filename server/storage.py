import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Storage:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    action_hash TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    approval_expires_at INTEGER,
                    pubkey TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    executed_at INTEGER,
                    approved_event TEXT,
                    note_event TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS relay_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    relay_url TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    error_message TEXT
                );
                """
            )

    def create_action(self, row: dict):
        with self.conn() as conn:
            conn.execute(
                """INSERT INTO actions(action_id,status,action_hash,payload,expires_at,pubkey,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (
                    row["action_id"],
                    row["status"],
                    row["action_hash"],
                    json.dumps(row["payload"]),
                    row["expires_at"],
                    row["pubkey"],
                    row["created_at"],
                ),
            )

    def get_action(self, action_id: str):
        with self.conn() as conn:
            res = conn.execute("SELECT * FROM actions WHERE action_id=?", (action_id,)).fetchone()
            return dict(res) if res else None

    def update_action(self, action_id: str, **fields):
        keys = list(fields.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        sets = ",".join(f"{k}=?" for k in keys)
        with self.conn() as conn:
            conn.execute(f"UPDATE actions SET {sets} WHERE action_id=?", (*values, action_id))

    def add_audit(self, timestamp: int, event_type: str, action_id: str, metadata: dict):
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO audit_log(timestamp,event_type,action_id,metadata) VALUES(?,?,?,?)",
                (timestamp, event_type, action_id, json.dumps(metadata)),
            )

    def add_relay_result(self, action_id: str, relay_url: str, success: bool, error_message: str | None):
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO relay_results(action_id,relay_url,success,error_message) VALUES(?,?,?,?)",
                (action_id, relay_url, 1 if success else 0, error_message),
            )

    def list_audit(self, action_id: str):
        with self.conn() as conn:
            rows = conn.execute("SELECT * FROM audit_log WHERE action_id=? ORDER BY id", (action_id,)).fetchall()
            return [dict(r) for r in rows]
