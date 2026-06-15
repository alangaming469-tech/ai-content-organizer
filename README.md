# AI Content Organizer

**AI-powered content summarization & organization tool** with CLI and Web Dashboard.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcomeorange)

---

## 🎯 Overview

AI Content Organizer helps you transform long documents (PDF, TXT, Markdown) into structured summaries with key points extraction. It provides two interfaces:

- **CLI** — Lightweight, scriptable, runs on any Python environment (including Termux)
- **Web Dashboard** — Interactive Streamlit UI with file upload, real-time logging, and JSON export

---

## 🏗️ Architecture

```
src/
├── cli/              # CLI entrypoint (argparse + logging)
├── models/           # Pydantic schemas (data contracts)
├── parsers/          # File parsing adapters (Protocol-based)
├── summarizers/      # AI orchestration + provider abstraction
└── core/             # Shared utilities (future)

dashboard/
├── app.py            # Streamlit dashboard
└── assets/           # Static assets
```

**Key design principles:**
- **Single Source of Truth**: All logic in `src/`, UI layers are thin
- **Abstraction over Implementation**: `AIProviderPort` lets you swap Gemini ↔ OpenAI ↔ Local LLM
- **Security by Default**: Prompt injection sanitization, hallucination guards, strict JSON output
- **Observability**: Structured logging everywhere, no `print()`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google AI API key ([Get one](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone
git clone https://github.com/<your-org>/ai-content-organizer
cd ai-content-organizer

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .[all]  # Or: pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

---

## 🖥️ CLI Usage

```bash
# Basic usage
python -m ai_content_organizer.src.cli.cli \
  --input data/input/document.pdf \
  --output data/output/summary.json \
  --mode brief

# Detailed mode with custom model
python -m ai_content_organizer.src.cli.cli \
  --input data/input/report.txt \
  --output data/output/report-detailed.json \
  --mode detailed \
  --model gemini-2.5-pro

# Verbose logging
python -m ai_content_organizer.src.cli.cli -v --input file.md --output out.json
```

**Modes:**
- `brief` — 1-2 paragraphs, 3-5 key points
- `detailed` — Multi-section, 5-10 key points
- `keypoints` — Bullet points only

**Exit codes:** `0` = success, `1` = error (check logs)

---

## 🌐 Dashboard Usage

```bash
streamlit run dashboard/app.py
```

Then open `http://localhost:8501` in browser.

**Features:**
- Drag-and-drop file upload (PDF, TXT, MD)
- Or paste text directly
- Mode selector + model override
- Real-time activity log
- JSON result with download

---

## 📦 Requirements

| Package | Purpose |
|---------|---------|
| `pydantic>=2.7` | Data validation & settings |
| `pypdf>=4.0` | PDF text extraction (pure Python) |
| `google-generativeai>=0.7` | Gemini API client |
| `python-dotenv>=1.0` | `.env` file loading |
| `streamlit>=1.35` | Web dashboard |
| `tenacity>=8.2` | Retry logic (Fase 4) |
| `typer>=0.12` | Optional: richer CLI |

Core: `pip install -e .` — installs only CLI deps.  
Full: `pip install -e .[dashboard]` — includes Streamlit.

---

## 🔒 Security Features

1. **Prompt Injection Sanitization** — Strips common injection patterns before sending to model
2. **Strict JSON Output** — System prompt enforces JSON-only; parser validates schema
3. **Hallucination Guard** — Post-process checks numbers/claims against source text
4. **No Secrets in Logs** — API keys never logged; truncation for large inputs
5. **Input Boundaries** — `max_input_chars` config prevents cost overruns

---

## 🧪 Testing

```bash
# Unit tests (no API calls)
pytest tests/unit -v

# Integration tests (requires API key)
pytest tests/integration -v --api-key=$GOOGLE_API_KEY
```

---

## 🤝 Contributing

1. Fork → Create branch: `git checkout -b feat/amazing-feature`
2. Make changes with type hints, logging, tests
3. Run: `ruff check . && pytest tests/unit`
4. Commit: `git commit -m "feat: add amazing feature"`
5. Push → Open PR

**Standards:**
- Python 3.11+, type hints required
- No `print()` — use `logging`
- Pydantic v2 for all data boundaries
- Max 120 chars line length (Ruff)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Google Gemini team for accessible API
- Streamlit for rapid dashboard prototyping
- Pydantic for excellent validation UX
- `pypdf` maintainers for pure-Python PDF parsing

---

**Made with ❤️ for open source**
