from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from ai_content_organizer.models.schemas import SupportedFormat


logger = logging.getLogger(__name__)


class ParserPort(Protocol):
    def parse(self, path: Path) -> str:
        raise NotImplementedError


class TextParser:
    def parse(self, path: Path) -> str:
        logger.info("Parsing text file: %s", path)
        return path.read_text(encoding="utf-8", errors="replace")


class MarkdownParser:
    def parse(self, path: Path) -> str:
        logger.info("Parsing markdown file: %s", path)
        return path.read_text(encoding="utf-8", errors="replace")


class PdfParser:
    def parse(self, path: Path) -> str:
        logger.info("Parsing PDF file: %s", path)
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "pypdf is required to parse PDF files. Install it with: pip install pypdf"
            ) from exc

        reader = PdfReader(str(path))
        pages = len(reader.pages)
        logger.debug("PDF has %d pages", pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise RuntimeError("Extracted text is empty; the PDF may be image-based / scanned.")
        return text


class HtmlParser:
    def parse(self, path: Path) -> str:
        logger.info("Parsing HTML file: %s", path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        # Minimal HTML to text extraction without external deps
        import re
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text).strip()
        return text


def _parser_for(path: Path) -> ParserPort:
    suffix = path.suffix.lower().lstrip(".")
    mapping = {
        SupportedFormat.txt: TextParser,
        SupportedFormat.md: MarkdownParser,
        SupportedFormat.pdf: PdfParser,
        SupportedFormat.html: HtmlParser,
    }
    key = SupportedFormat(suffix) if suffix in {e.value for e in SupportedFormat} else None
    if key is None:
        raise ValueError(f"Unsupported file format: .{suffix}")
    return mapping[key]()


def build_parser(path: Path) -> ParserPort:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Input path is not a valid file: {path}")
    return _parser_for(path)
