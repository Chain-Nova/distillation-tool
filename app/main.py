from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import DistillationRequest, PositiveGenerationRequest, SavedModelConfig, SaveModelConfigRequest, TaskCreated, TaskStatus
from app.taxonomy import DEFAULT_TAXONOMY, POSITIVE_TAXONOMY
from app.db import (
    create_task_record,
    delete_model_config,
    get_model_config,
    get_task_record,
    init_db,
    list_llm_calls,
    list_model_configs,
    list_task_records,
    save_model_config,
    update_task_record,
)
from app.worker import celery_app, run_distillation_task, run_positive_task

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="DistillationToll", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
init_db()


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/taxonomy")
def get_taxonomy():
    return [item.model_dump() for item in DEFAULT_TAXONOMY]


@app.get("/api/positive-taxonomy")
def get_positive_taxonomy():
    return [item.model_dump() for item in POSITIVE_TAXONOMY]


@app.get("/api/model-configs", response_model=list[SavedModelConfig])
def get_model_configs():
    return [SavedModelConfig(**record) for record in list_model_configs()]


@app.post("/api/model-configs", response_model=SavedModelConfig)
def create_or_update_model_config(request: SaveModelConfigRequest):
    record = save_model_config(request.name, request.config.model_dump())
    return SavedModelConfig(**record)


@app.get("/api/model-configs/{config_id}", response_model=SavedModelConfig)
def load_model_config(config_id: int):
    record = get_model_config(config_id)
    if record is None:
        raise HTTPException(status_code=404, detail="模型配置不存在。")
    return SavedModelConfig(**record)


@app.delete("/api/model-configs/{config_id}")
def remove_model_config(config_id: int):
    if not delete_model_config(config_id):
        raise HTTPException(status_code=404, detail="模型配置不存在。")
    return {"deleted": True}


@app.post("/api/tasks", response_model=TaskCreated)
def create_task(request: DistillationRequest):
    payload = request.model_dump(by_alias=True)
    task_id = uuid4().hex
    create_task_record(task_id, payload)
    run_distillation_task.apply_async(args=[payload], task_id=task_id)
    return TaskCreated(task_id=task_id)


@app.post("/api/positive-tasks", response_model=TaskCreated)
def create_positive_task(request: PositiveGenerationRequest):
    payload = request.model_dump(by_alias=True)
    payload["workflow"] = "positive_non_refusal"
    task_id = uuid4().hex
    create_task_record(task_id, payload)
    run_positive_task.apply_async(args=[payload], task_id=task_id)
    return TaskCreated(task_id=task_id)


@app.get("/api/tasks", response_model=list[TaskStatus])
def list_tasks(limit: int = 20):
    return [TaskStatus(**record) for record in list_task_records(limit=limit)]


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
def get_task(task_id: str):
    record = get_task_record(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    result = AsyncResult(task_id, app=celery_app)
    info = result.info if isinstance(result.info, dict) else {}
    if result.state in {"PROGRESS", "SUCCESS", "FAILURE"}:
        updates = {
            "state": result.state,
            "progress": info.get("progress", record.get("progress")),
            "status": info.get("status", record.get("status")),
            "result_file": info.get("result_file", record.get("result_file")),
            "rows_count": info.get("rows", record.get("rows_count")),
            "error": str(result.info) if result.failed() else record.get("error"),
        }
        update_task_record(task_id, **updates)
        record = get_task_record(task_id) or record

    return TaskStatus(**record)


@app.get("/api/tasks/{task_id}/details")
def get_task_details(task_id: str):
    record = get_task_record(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return {
        "task": TaskStatus(**record).model_dump(),
        "request": record.get("request"),
        "llm_calls": list_llm_calls(task_id),
        "preview": record.get("preview", []),
    }


@app.get("/api/tasks/{task_id}/download")
def download_result(task_id: str):
    record = get_task_record(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    result_file = record.get("result_file")
    if not result_file:
        raise HTTPException(status_code=404, detail="任务尚未生成 Excel。")
    path = Path(result_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Excel 文件不存在。")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{task_id}-distillation.xlsx",
    )
