from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI, OpenAI

from app.config import get_settings
from app.db import create_llm_call, finish_llm_call
from app.schemas import ModelConfig


def build_client(config: ModelConfig) -> tuple[OpenAI, str]:
    settings = get_settings()
    api_key = config.api_key or settings.openai_api_key
    if not api_key:
        raise ValueError("缺少模型 API Key，请在页面或 .env 中配置。")

    base_url = config.base_url or settings.openai_base_url
    model = config.model or settings.openai_model
    return OpenAI(api_key=api_key, base_url=base_url), model


def build_async_client(config: ModelConfig) -> tuple[AsyncOpenAI, str]:
    settings = get_settings()
    api_key = config.api_key or settings.openai_api_key
    if not api_key:
        raise ValueError("缺少模型 API Key，请在页面或 .env 中配置。")

    base_url = config.base_url or settings.openai_base_url
    model = config.model or settings.openai_model
    return AsyncOpenAI(api_key=api_key, base_url=base_url), model


def complete_text(
    client: OpenAI,
    model: str,
    config: ModelConfig,
    system: str,
    user: str,
    task_id: str | None = None,
    step: str = "llm_call",
) -> str:
    call_id = create_llm_call(task_id, step, model, system, user) if task_id else None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        text = response.choices[0].message.content or ""
        if call_id is not None:
            finish_llm_call(call_id, response_text=text)
        return text
    except Exception as exc:
        if call_id is not None:
            finish_llm_call(call_id, error=str(exc))
        raise


async def async_complete_text(
    client: AsyncOpenAI,
    model: str,
    config: ModelConfig,
    system: str,
    user: str,
    task_id: str | None = None,
    step: str = "llm_call",
) -> str:
    call_id = create_llm_call(task_id, step, model, system, user) if task_id else None
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        text = response.choices[0].message.content or ""
        if call_id is not None:
            finish_llm_call(call_id, response_text=text)
        return text
    except Exception as exc:
        if call_id is not None:
            finish_llm_call(call_id, error=str(exc))
        raise


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def parse_json_list(text: str) -> list[Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.S)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, list):
        raise ValueError("模型没有返回 JSON 数组。")
    return value
