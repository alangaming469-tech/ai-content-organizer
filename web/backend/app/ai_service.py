from __future__ import annotations

import os
from typing import Any, Dict

from ai_content_organizer.src.models.schemas import AppConfig
from ai_content_organizer.src.core.ai_provider import GeminiProvider


class AIService:
    def __init__(self) -> None:
        self.config = AppConfig.from_env()
        self.provider = GeminiProvider(self.config)

    def analyze(self, text: str, query: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("text is required")
        if not query:
            raise ValueError("query is required")

        prompt = (
            "Dokumen:\n"
            f"{text}\n\n"
            "Instruksi ringkas:\n"
            f"{query}\n\n"
            "Berikan jawaban dalam JSON dengan format: "
            "{\"summary\": string, \"key_points\": string[], \"action_items\": string[]}"
        )
        return self.provider.generate(prompt)
