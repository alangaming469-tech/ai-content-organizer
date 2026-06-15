from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class SummaryMode(str, Enum):
    brief = "brief"
    detailed = "detailed"
    keypoints = "keypoints"


class SupportedFormat(str, Enum):
    pdf = "pdf"
    txt = "txt"
    md = "md"
    html = "html"


class AppConfig(BaseModel):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    api_key: str = Field(..., validation_alias="GOOGLE_API_KEY")
    model_name: str = Field(default="gemini-2.5-flash")
    default_mode: SummaryMode = Field(default=SummaryMode.brief)
    supported_formats: List[SupportedFormat] = Field(
        default_factory=lambda: [
            SupportedFormat.pdf,
            SupportedFormat.txt,
            SupportedFormat.md,
        ]
    )
    max_input_chars: int = Field(default=12000, gt=0)
    max_output_tokens: int = Field(default=2048, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    rate_limit_rps: float = Field(default=1.0, gt=0.0)

    @classmethod
    def from_env(cls) -> AppConfig:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required in environment or .env file")
        return cls(api_key=api_key)


class SummaryOutput(BaseModel):
    mode: str
    summary: str = Field(min_length=1)
    key_points: Optional[List[str]] = Field(default=None)
    metadata: dict = Field(default_factory=dict)
