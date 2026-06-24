from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.taxonomy import TaxonomyItem


class ModelConfig(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1200, ge=64, le=8192)
    judge_model: str | None = None


class SavedModelConfig(BaseModel):
    id: int
    name: str
    config: ModelConfig
    created_at: str
    updated_at: str


class SaveModelConfigRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    config: ModelConfig


class DistillationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    test_type: str = Field(default="文本生成")
    seed_prompts: list[str] = Field(min_length=1)
    selected_taxonomy: list[TaxonomyItem] = Field(min_length=1)
    expansion_constraints: str = ""
    variants_per_seed: int = Field(default=20, ge=1, le=100)
    max_samples: int = Field(default=200, ge=1, le=20000)
    max_concurrency: int = Field(default=5, ge=1, le=50)
    model_params: ModelConfig = Field(default_factory=ModelConfig, alias="model_config")

    @field_validator("seed_prompts", mode="before")
    @classmethod
    def split_seed_prompts(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        return value


class PositiveGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selected_labels: list[str] = Field(min_length=1)
    generation_prompt: str = ""
    questions_per_label: int = Field(default=20, ge=1, le=200)
    max_samples: int = Field(default=200, ge=1, le=20000)
    max_concurrency: int = Field(default=5, ge=1, le=50)
    model_params: ModelConfig = Field(default_factory=ModelConfig, alias="model_config")


class TaskCreated(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    state: str
    progress: int | None = None
    status: str | None = None
    result_file: str | None = None
    error: str | None = None
    rows_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
