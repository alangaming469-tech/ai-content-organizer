"""Unit tests for schemas and parsers (no API calls required)."""

import json
from pathlib import Path

import pytest

from ai_content_organizer.models.schemas import (
    AppConfig,
    SummaryMode,
    SupportedFormat,
)
from ai_content_organizer.parsers.file_parsers import TextParser


def test_summary_mode_enum():
    assert SummaryMode.brief.value == "brief"
    assert SummaryMode.detailed.value == "detailed"
    assert SummaryMode.keypoints.value == "keypoints"
    assert len(SummaryMode) == 3


def test_supported_format_enum():
    assert SupportedFormat.pdf.value == "pdf"
    assert SupportedFormat.txt.value == "txt"
    assert SupportedFormat.md.value == "md"


def test_app_config_defaults():
    cfg = AppConfig(
        api_key="test-key",
    )
    assert cfg.model_name == "gemini-2.5-flash"
    assert cfg.default_mode == SummaryMode.brief
    assert cfg.max_input_chars == 12000


def test_text_parser(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Hello world\nSecond line", encoding="utf-8")

    parser = TextParser()
    result = parser.parse(sample)

    assert "Hello world" in result
    assert "Second line" in result


def test_text_parser_missing_file(tmp_path: Path):
    parser = TextParser()
    with pytest.raises(FileNotFoundError):
        parser.parse(tmp_path / "nonexistent.txt")


def test_app_config_from_env_monkeypatch(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "env-test-key")
    cfg = AppConfig.from_env()
    assert cfg.api_key == "env-test-key"


def test_summarize_result_serialization():
    from ai_content_organizer.summarizers.summarizer import SummarizeResult

    result = SummarizeResult(
        mode="brief",
        summary="Test summary",
        key_points=["point 1", "point 2"],
        metadata={"model": "test", "chars_in": 100, "chars_out": 50},
    )
    json_str = result.model_dump_json()
    data = json.loads(json_str)
    assert data["mode"] == "brief"
    assert data["summary"] == "Test summary"
    assert len(data["key_points"]) == 2


def test_validate_json_output_valid():
    from ai_content_organizer.summarizers.summarizer import validate_json_output

    text = '{"summary": "ok", "key_points": ["a"], "metadata": {"model": "m"}}'
    result = validate_json_output(text, "brief")
    assert result["summary"] == "ok"
    assert result["key_points"] == ["a"]


def test_validate_json_output_invalid_fallback():
    from ai_content_organizer.summarizers.summarizer import validate_json_output

    text = "not json at all"
    result = validate_json_output(text, "brief")
    assert "Model output was not valid JSON" in result["key_points"][0]
