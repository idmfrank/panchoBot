import json
import sqlite3
from contextlib import contextmanager


class Storage:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    @contextmanager
    def conn(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self):
        with self.conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    args_json TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    approval_expires_at INTEGER,
                    action_hash TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    action_hash TEXT NOT NULL,
                    approved_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )

    def create_action(self, row: dict):
        with self.conn() as conn:
            conn.execute(
                """INSERT INTO actions(action_id,tool_name,args_json,requested_by,created_at,expires_at,approval_expires_at,action_hash,status)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    row["action_id"],
                    row["tool_name"],
                    json.dumps(row["args"]),
                    row["requested_by"],
                    row["created_at"],
                    row["expires_at"],
                    row.get("approval_expires_at"),
                    row["action_hash"],
                    row["status"],
                ),
            )

    def get_action(self, action_id: str):
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM actions WHERE action_id=?", (action_id,)).fetchone()
        return dict(row) if row else None

    def update_action(self, action_id: str, **fields):
        keys = list(fields.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        with self.conn() as conn:
            conn.execute(f"UPDATE actions SET {','.join(f'{k}=?' for k in keys)} WHERE action_id=?", (*values, action_id))

    def create_approval(self, row: dict):
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO approvals(action_id,action_hash,approved_at,expires_at,used) VALUES(?,?,?,?,0)",
                (row["action_id"], row["action_hash"], row["approved_at"], row["expires_at"]),
            )

    def get_latest_approval(self, action_id: str):
        with self.conn() as conn:
            row = conn.execute(
                "SELECT * FROM approvals WHERE action_id=? ORDER BY id DESC LIMIT 1",
                (action_id,),
            ).fetchone()
        return dict(row) if row else None

    def mark_approval_used(self, approval_id: int):
        with self.conn() as conn:
            conn.execute("UPDATE approvals SET used=1 WHERE id=?", (approval_id,))

    def add_audit(self, action_id: str, event_type: str, created_at: int, metadata: dict):
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO audit_log(action_id,event_type,created_at,metadata_json) VALUES(?,?,?,?)",
                (action_id, event_type, created_at, json.dumps(metadata)),
            )

    def list_audit(self, action_id: str):
        with self.conn() as conn:
            rows = conn.execute("SELECT * FROM audit_log WHERE action_id=? ORDER BY id", (action_id,)).fetchall()
        return [dict(r) for r in rows]

    def save_tool_result(self, action_id: str, result: dict, created_at: int):
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO tool_results(action_id,result_json,created_at) VALUES(?,?,?)",
                (action_id, json.dumps(result), created_at),
            )
