from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path() -> Path:
    settings = get_settings()
    settings.distillation_data_dir.mkdir(parents=True, exist_ok=True)
    return settings.distillation_data_dir / "distillation.sqlite3"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                progress INTEGER,
                status TEXT,
                result_file TEXT,
                error TEXT,
                request_json TEXT,
                preview_json TEXT,
                rows_count INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                config_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_model_configs_updated_at ON model_configs(updated_at)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                step TEXT NOT NULL,
                model TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                user_prompt TEXT NOT NULL,
                response_text TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_task_id ON llm_calls(task_id)")


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    if data.get("preview_json"):
        data["preview"] = json.loads(data.pop("preview_json"))
    else:
        data.pop("preview_json", None)
        data["preview"] = []
    if data.get("request_json"):
        data["request"] = json.loads(data.pop("request_json"))
    else:
        data.pop("request_json", None)
        data["request"] = None
    return data


def create_task_record(task_id: str, request_payload: dict[str, Any]) -> None:
    payload = json.loads(json.dumps(request_payload, ensure_ascii=False))
    if isinstance(payload.get("model_config"), dict) and payload["model_config"].get("api_key"):
        payload["model_config"]["api_key"] = "***"

    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO tasks (
                task_id, state, progress, status, request_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                "PENDING",
                0,
                "任务已创建，等待 worker 执行。",
                json.dumps(payload, ensure_ascii=False),
                now,
                now,
            ),
        )


def update_task_record(task_id: str, **fields: Any) -> None:
    if not fields:
        return
    allowed = {"state", "progress", "status", "result_file", "error", "rows_count"}
    updates: dict[str, Any] = {key: value for key, value in fields.items() if key in allowed}
    if "preview" in fields:
        updates["preview_json"] = json.dumps(fields["preview"], ensure_ascii=False)
    updates["updated_at"] = _now()

    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [task_id]
    with connect() as conn:
        conn.execute(f"UPDATE tasks SET {assignments} WHERE task_id = ?", values)


def get_task_record(task_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    return _row_to_dict(row)


def list_task_records(limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def _model_config_row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    data["config"] = json.loads(data.pop("config_json"))
    return data


def save_model_config(name: str, config: dict[str, Any]) -> dict[str, Any]:
    normalized_name = name.strip()
    now = _now()
    config_json = json.dumps(config, ensure_ascii=False)
    with connect() as conn:
        existing = conn.execute(
            "SELECT id, created_at FROM model_configs WHERE name = ?",
            (normalized_name,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE model_configs
                SET config_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (config_json, now, existing["id"]),
            )
            config_id = existing["id"]
        else:
            cursor = conn.execute(
                """
                INSERT INTO model_configs (name, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (normalized_name, config_json, now, now),
            )
            config_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM model_configs WHERE id = ?", (config_id,)).fetchone()
    saved = _model_config_row_to_dict(row)
    if saved is None:
        raise RuntimeError("保存模型配置失败。")
    return saved


def list_model_configs() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM model_configs ORDER BY updated_at DESC").fetchall()
    return [_model_config_row_to_dict(row) for row in rows if row is not None]


def get_model_config(config_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM model_configs WHERE id = ?", (config_id,)).fetchone()
    return _model_config_row_to_dict(row)


def delete_model_config(config_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM model_configs WHERE id = ?", (config_id,))
    return cursor.rowcount > 0


def create_llm_call(task_id: str, step: str, model: str, system_prompt: str, user_prompt: str) -> int:
    now = _now()
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO llm_calls (
                task_id, step, model, system_prompt, user_prompt, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, step, model, system_prompt, user_prompt, now, now),
        )
    return int(cursor.lastrowid)


def finish_llm_call(call_id: int, response_text: str | None = None, error: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE llm_calls
            SET response_text = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (response_text, error, _now(), call_id),
        )


def list_llm_calls(task_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, task_id, step, model, system_prompt, user_prompt, response_text,
                   error, created_at, updated_at
            FROM llm_calls
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()
    return [dict(row) for row in rows]
