from __future__ import annotations

from typing import Any

from ai_content_organizer.src.core.ai_provider import GeminiProvider
from ai_content_organizer.src.models.schemas import AppConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


class AIService:
    def __init__(self) -> None:
        self.config = AppConfig.from_env()
        self.provider = GeminiProvider(self.config)

    def analyze(self, text: str, query: str) -> dict[str, Any]:
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


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/summarize", response_model=dict[str, Any])
def summarize(payload: dict[str, str]) -> dict[str, Any]:
    text = payload.get("text")
    query = payload.get("query")
    service = AIService()
    return service.analyze(text=text or "", query=query or "")


# Minimal health check route to verify connectivity.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
