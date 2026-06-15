from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AI Content Organizer API")
    api_v1_prefix: str = Field(default="/api/v1")
    debug: bool = Field(default=False)


settings = Settings()
