from __future__ import annotations

from celery import Celery

from app.config import get_settings
from app.db import init_db, update_task_record
from app.graph import run_distillation
from app.positive import run_positive_generation
from app.storage import write_json

settings = get_settings()

celery_app = Celery(
    "distillation_toll",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(task_track_started=True, result_extended=True)
init_db()


@celery_app.task(bind=True, name="distillation.run")
def run_distillation_task(self, payload: dict):
    task_id = self.request.id
    write_json(task_id, "request.json", payload)
    meta = {"progress": 5, "status": "任务已入队，开始执行 LangGraph。"}
    update_task_record(task_id, state="PROGRESS", **meta)
    self.update_state(state="PROGRESS", meta=meta)
    try:
        result = run_distillation(task_id, payload)
    except Exception as exc:
        write_json(task_id, "error.json", {"error": str(exc)})
        update_task_record(task_id, state="FAILURE", progress=100, status="任务失败。", error=str(exc))
        raise
    write_json(task_id, "result.json", result)
    update_task_record(
        task_id,
        state="SUCCESS",
        progress=100,
        status="完成",
        result_file=result["result_file"],
        rows_count=result.get("rows"),
        preview=result.get("preview", []),
    )
    return {"progress": 100, "status": "完成", **result}


@celery_app.task(bind=True, name="positive.run")
def run_positive_task(self, payload: dict):
    task_id = self.request.id
    write_json(task_id, "request.json", payload)
    meta = {"progress": 5, "status": "任务已入队，开始生成非拒答题。"}
    update_task_record(task_id, state="PROGRESS", **meta)
    self.update_state(state="PROGRESS", meta=meta)
    try:
        result = run_positive_generation(task_id, payload)
    except Exception as exc:
        write_json(task_id, "error.json", {"error": str(exc)})
        update_task_record(task_id, state="FAILURE", progress=100, status="任务失败。", error=str(exc))
        raise
    write_json(task_id, "result.json", result)
    update_task_record(
        task_id,
        state="SUCCESS",
        progress=100,
        status="完成",
        result_file=result["result_file"],
        rows_count=result.get("rows"),
        preview=result.get("preview", []),
    )
    return {"progress": 100, "status": "完成", **result}
