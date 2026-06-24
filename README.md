# DistillationTool

用于从大模型生成评测题的蒸馏工具。流程由 FastAPI 提供接口和静态页面，Celery 执行后台任务，LangGraph 编排核心生成链路，最终导出 Excel。

## 功能

- 选择语料安全风险项和类别标签
- 填写 50~200 条母题、扩展约束和测试类型
- 配置 OpenAI 兼容模型地址与参数
- 后台执行四步任务：
  - Seed prompts
  - Self-Instruct 扩展
  - Answer + Risk labeling 结构化生成
  - LLM-as-a-Judge 二次过滤
- 生成与示例一致的 Excel 列结构

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d redis
celery -A app.worker.celery_app worker --loglevel=info
uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000

## 环境变量

```bash
CELERY_BROKER_URL=redis://localhost:6390/0
CELERY_RESULT_BACKEND=redis://localhost:6390/1
DISTILLATION_DATA_DIR=./data
```

模型配置也可以在页面任务表单中填写。任务表单中的值优先级最高。
