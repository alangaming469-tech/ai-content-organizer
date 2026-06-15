from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_content_organizer.parsers.file_parsers import build_parser
from ai_content_organizer.summarizers.summarizer import SummarizerService


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def build_parser_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-content-organizer",
        description="AI-powered content organizer and summarizer.",
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to input file.")
    parser.add_argument("--output", required=True, type=Path, help="Path to write JSON output.")
    parser.add_argument(
        "--mode",
        choices=["brief", "detailed", "keypoints"],
        default="brief",
        help="Summary mode.",
    )
    parser.add_argument("--model", default=None, help="Model name override.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def run_cli() -> int:
    configure_logging()
    args = build_parser_cli().parse_args()
    logger = logging.getLogger("cli")

    if not args.input.exists() or not args.input.is_file():
        logger.error("Input file missing: %s", args.input)
        return 1

    try:
        parser_wrapper = build_parser(args.input)
        raw_text = parser_wrapper.parse(args.input)
    except Exception as exc:
        logger.error("Parsing failed: %s", exc)
        return 1

    try:
        service = SummarizerService()
        result = service.summarize(raw_text, args.mode, model=args.model)
    except Exception as exc:
        logger.error("Summarization failed: %s", exc)
        return 1

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("Write failed: %s", exc)
        return 1

    logger.info("Done: %s", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
