from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings


def job_dir(task_id: str) -> Path:
    path = get_settings().jobs_dir / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(task_id: str, name: str, payload: Any) -> Path:
    path = job_dir(task_id) / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_json(task_id: str, name: str) -> Any:
    path = job_dir(task_id) / name
    return json.loads(path.read_text(encoding="utf-8"))


def result_xlsx_path(task_id: str) -> Path:
    return job_dir(task_id) / "distillation_result.xlsx"
