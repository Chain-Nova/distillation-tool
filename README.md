# DistillationTool

用于生成大模型评测题的蒸馏工具。后端使用 FastAPI，后台任务使用 Celery，核心生成流程使用 LangGraph，并通过 OpenAI 兼容接口调用模型，最终导出 Excel。

## 功能

- 拒答题蒸馏：根据母题扩展同向变体，生成回答、风险标签和 Judge 结果。
- 非拒答题生成：根据正向标签生成可回答的问题和参考答案。
- 支持保存/加载 OpenAI 兼容模型配置。
- 支持 SQLite 持久化任务，刷新页面后仍可查看历史任务。
- 支持查看每个任务提交参数、每次大模型请求和输出。
- 支持下载 Excel 结果。

## 环境要求

- Python 3.11 推荐
- Docker，用于启动 Redis
- OpenAI 兼容模型服务，例如 OpenAI、DashScope 兼容模式或其他兼容 `/v1/chat/completions` 的服务

## 安装

```bash

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

如果本机没有 `python3.11`，可以用 Homebrew 安装：

```bash
brew install python@3.11
```

## 启动

先启动 Redis：

```bash
docker compose up -d redis
```

再开两个终端。

终端 1，启动 Celery worker：

```bash
cd /Users/luofengge/Documents/DistillationToll
source .venv/bin/activate
celery -A app.worker.celery_app worker --loglevel=info
```

终端 2，启动 Web：

```bash
cd /Users/luofengge/Documents/DistillationToll
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 停止

停止 Web 和 worker：

```bash
pkill -f 'uvicorn app.main'
pkill -f 'celery -A app.worker'
```

停止 Redis：

```bash
docker compose down
```

## 配置模型

页面中填写 OpenAI 兼容模型参数：

- Base URL，例如 `https://api.openai.com/v1`
- API Key
- 生成模型
- Judge 模型，可留空，留空时使用生成模型
- Temperature
- Max tokens

填写“配置名称”后点击“保存配置”，之后可以从“已保存配置”下拉列表加载回来。

注意：保存模型配置会把 API Key 写入本地 SQLite，路径为 `data/distillation.sqlite3`。

## 使用流程

### 拒答题蒸馏

1. 选择顶部模式“拒答题蒸馏”。
2. 在“拒答题标签体系”中选择一个或多个标签。
3. 填写母题，一行一条。
4. 配置扩展约束 Prompt、每条母题扩展数量、最大样本数和并发请求数。
5. 配置或加载模型参数。
6. 点击“生成评测题”。
7. 在左侧“最近任务”中点击任务，查看任务详情。
8. 任务完成后，在详情页点击“下载 Excel”。

拒答题 Excel 列结构：

- 测试类型
- 题目-拒答题
- 语料及生成内容的主要安全风险项
- 类别
- 回答
- 是否合格

### 非拒答题生成

1. 选择顶部模式“非拒答题生成”。
2. 在“非拒答题标签体系”中选择标签。
3. 配置生成 Prompt、每个标签生成数量、最大样本数和并发请求数。
4. 配置或加载模型参数。
5. 点击“生成非拒答题”。
6. 在左侧“最近任务”中点击任务，查看任务详情。
7. 任务完成后，在详情页点击“下载 Excel”。

非拒答题 Excel 列结构：

- 问题
- 类别（标签）
- 答案

## 任务详情

点击左侧“最近任务”中的任务后，右侧会显示：

- 任务状态
- 下载 Excel
- 提交参数
- 每次大模型请求的 System / User / Output

任务执行中详情会自动刷新。页面会尽量保留当前滚动位置。

## 数据位置

默认数据目录：

```text
./data
```

主要内容：

- `data/distillation.sqlite3`：任务、模型配置和 LLM 调用日志
- `data/jobs/<task_id>/request.json`：任务请求
- `data/jobs/<task_id>/result.json`：任务结果
- `data/jobs/<task_id>/*.xlsx`：导出的 Excel

## 环境变量

`.env.example` 默认配置：

```bash
CELERY_BROKER_URL=redis://localhost:6390/0
CELERY_RESULT_BACKEND=redis://localhost:6390/1
DISTILLATION_DATA_DIR=./data
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

页面任务表单中的模型配置优先级高于 `.env`。
