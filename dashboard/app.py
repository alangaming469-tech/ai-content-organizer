import io
import json
import logging
import textwrap
from pathlib import Path
from typing import Optional

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx



# ─── Page configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Content Organizer — Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dashboard")

# ─── Local imports ───────────────────────────────────────────────────
from ai_content_organizer.models.schemas import AppConfig, SummaryMode
from ai_content_organizer.parsers.file_parsers import build_parser
from ai_content_organizer.summarizers.summarizer import SummarizerService


# ─── Constants / UI copy ─────────────────────────────────────────────
SIDEBAR_TITLE = "⚙️ Configuration"
MODE_DESCRIPTIONS = {
    SummaryMode.brief: "Concise 2–3 sentence executive summary. Best for quick scanning.",
    SummaryMode.detailed: "Multi-paragraph summary preserving context, structure, and nuances.",
    SummaryMode.keypoints: "Bullet-point extraction of actionable insights and key facts.",
}


# ─── Helper functions ────────────────────────────────────────────────
def sidebar_config_form() -> AppConfig:
    """Render sidebar and return validated AppConfig."""
    st.sidebar.title(SIDEBAR_TITLE)

    # ── Mode selector ────────────────────────────────────────────────
    mode = st.sidebar.selectbox(
        "Summary mode",
        options=[m.value for m in SummaryMode],
        index=0,
        format_func=lambda m: f"{m.capitalize()} — {MODE_DESCRIPTIONS[SummaryMode(m)]}",
        help="Select the summarization style. Brief = fastest/cheapest; Detailed = richest; Keypoints = actionable.",
    )

    # ── Model override ───────────────────────────────────────────────
    model_name = st.sidebar.text_input(
        "Model override",
        value="gemini-2.5-flash",
        help="Optional: exact model name (e.g. 'gemini-1.5-pro'). Leave empty to use default.",
    )

    # ── Advanced parameters ──────────────────────────────────────────
    with st.sidebar.expander("🔧 Advanced parameters", expanded=False):
        max_input_chars = st.number_input(
            "Max input characters",
            min_value=1_000,
            max_value=100_000,
            value=12_000,
            step=1_000,
            help="Truncate input to this many characters before sending to the model. Prevents cost overruns.",
        )
        max_output_tokens = st.number_input(
            "Max output tokens",
            min_value=256,
            max_value=8_192,
            value=2_048,
            step=256,
            help="Cap the model’s response length.",
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="0.0 = deterministic, 1.0 = creative. Low values recommended for summarization.",
        )
        rate_limit_rps = st.number_input(
            "Rate limit (req/s)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Throttle API calls to avoid 429 errors.",
        )

    # ── API Key ──────────────────────────────────────────────────────
    api_key = st.secrets.get("GOOGLE_API_KEY") or st.session_state.get("GOOGLE_API_KEY", "")
    if not api_key:
        with st.sidebar.expander("🔐 Provide GOOGLE_API_KEY", expanded=True):
            st.info(
                "Create an API key at https://aistudio.google.com/apikey "
                "and paste it below. It is **never logged** and only kept in-memory for this session."
            )
            api_key = st.text_input("GOOGLE_API_KEY", type="password", placeholder="AIza...")
            if api_key:
                st.session_state["GOOGLE_API_KEY"] = api_key

    return AppConfig(
        api_key=api_key,
        model_name=model_name.strip() or "gemini-2.5-flash",
        default_mode=SummaryMode(mode),
        max_input_chars=int(max_input_chars),
        max_output_tokens=int(max_output_tokens),
        temperature=float(temperature),
        rate_limit_rps=float(rate_limit_rps),
    )


def activity_log(message: str, level: str = "info") -> None:
    """Write to both Python logger and Streamlit activity panel."""
    getattr(logger, level)(message)
    st.session_state.setdefault("activity_log", []).append(
        {"ts": logger.handlers[0].formatter.formatTime(logging.LogRecord("", 0, "", 0, "", (), None)), "msg": message, "level": level}
    )


def render_activity_panel() -> None:
    """Render the activity log panel in the sidebar."""
    with st.sidebar.expander("📜 Activity Log", expanded=True):
        logs = st.session_state.get("activity_log", [])
        if not logs:
            st.caption("No activity yet.")
        else:
            for entry in reversed(logs[-20:]):  # show last 20
                color = {"info": "🔵", "warning": "🟡", "error": "🔴"}.get(entry["level"], "⚪")
                st.markdown(f"`{entry['ts']}` {color} {entry['msg']}")


def parse_input(uploaded, raw_text: str, config: AppConfig) -> str:
    """Parse uploaded file or raw text into plain text."""
    if uploaded is not None:
        activity_log(f"Uploaded file: {uploaded.name} ({uploaded.size:,} bytes)")
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in [f".{fmt.value}" for fmt in config.supported_formats]:
            raise ValueError(f"Unsupported format: {suffix}. Allowed: {config.supported_formats}")
        tmp = Path("/tmp") / f"uploaded{suffix}"
        tmp.write_bytes(uploaded.getbuffer())
        parser = build_parser(tmp)
        text = parser.parse(tmp)
        activity_log(f"Parsed {len(text):,} characters from {suffix.upper()} file")
        return text
    elif raw_text.strip():
        activity_log(f"Using pasted text ({len(raw_text):,} chars)")
        return raw_text
    else:
        raise ValueError("No input provided. Upload a file or paste text.")


# ─── Main rendering ──────────────────────────────────────────────────
def render_header() -> None:
    st.markdown(
        """
        # AI Content Organizer
        **Transform documents into structured, actionable summaries — powered by Google Gemini.**
        """
    )
    st.caption("v0.1.0 • Open Source • MIT License")


def render_input_section(config: AppConfig) -> tuple[Optional[str], bool]:
    """Render file uploader + text area. Returns (text, submitted)."""
    with st.container(border=True):
        st.subheader("📥 Input")
        col1, col2 = st.columns([1, 3])

        with col1:
            uploaded = st.file_uploader(
                "Upload a file",
                type=[fmt.value for fmt in config.supported_formats],
                help="Supported: PDF, TXT, Markdown. Max size: 200 MB.",
            )

        with col2:
            text_area = st.text_area(
                "Or paste text directly",
                height=220,
                placeholder="Paste article, report, transcript…\n\nTip: You can also drag a file into the uploader above.",
            )

        submitted = st.button("🚀 Generate Summary", type="primary", use_container_width=True)
        return text_area, uploaded, submitted


def render_result(output) -> None:
    """Render the summary output with tabs."""
    st.success("✅ Summary generated")

    tabs = st.tabs(["📄 Summary", "🔑 Key Points", "📊 Metadata", "🧾 Raw JSON"])

    with tabs[0]:
        st.markdown(output.summary)
        st.caption(f"Mode: {output.mode} • Model: {output.metadata.get('model', 'unknown')}")

    with tabs[1]:
        if output.key_points:
            for i, point in enumerate(output.key_points, 1):
                st.markdown(f"{i}. {point}")
        else:
            st.info("No key points extracted (try **Keypoints** mode).")

    with tabs[2]:
        cols = st.columns(4)
        meta = output.metadata
        cols[0].metric("Input chars", f"{meta.get('chars_in', 0):,}")
        cols[1].metric("Output chars", f"{meta.get('chars_out', 0):,}")
        cols[2].metric("Tokens (est.)", f"{meta.get('tokens_est', 0):,}")
        cols[3].metric("Latency", f"{meta.get('latency_ms', 0)} ms")

    with tabs[3]:
        st.code(output.model_dump_json(indent=2), language="json")


def render_architecture_section() -> None:
    """Detailed architecture documentation in an expander."""
    with st.expander("🏗️ Architecture & Design Decisions", expanded=False):
        st.markdown(
            textwrap.dedent(
                """
                ## High-Level Architecture
                ```
                ┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
                │   CLI /     │────▶│ SummarizerService│────▶│  AIProviderPort     │
                │  Dashboard  │     │ (orchestration)  │     │  (abstraction)      │
                └─────────────┘     └──────────────────┘     └─────────┬───────────┘
                                                                    │
                                                          ┌─────────┴─────────┐
                                                          ▼                   ▼
                                                  ┌─────────────┐    ┌─────────────┐
                                                  │GeminiProvider│    │ OpenAI/Local│
                                                  │ (concrete)   │    │ (pluggable) │
                                                  └─────────────┘    └─────────────┘
                ```

                ### Key Design Principles
                1. **Dependency Inversion**: `SummarizerService` depends on `AIProviderPort` (Protocol), not concrete `GeminiProvider`. Swap providers without touching orchestration.
                2. **Adapter Pattern for Parsers**: `ParserPort` protocol → `PdfParser`, `TextParser`. Add new formats (DOCX, HTML) by implementing the protocol.
                3. **Pydantic v2 Contracts**: All inputs/outputs are validated. `AppConfig` loads from `.env` + CLI flags + UI.
                4. **Structured Logging**: Zero `print()`. All observability goes through `logging` with timestamp + level.
                5. **Fail-Fast + Graceful Degradation**: Every layer wraps exceptions, logs context, returns structured error.

                ### Security & Prompt Safety
                - **System Prompt** enforces JSON-only output and explicitly forbids leaking system instructions.
                - **Input Sanitization**: Removes `{{...}}`, `{%...%}`, `<script>`, and other injection patterns.
                - **Output Validation**: JSON schema enforced; on parse failure, falls back to raw text + warning.
                - **Hallucination Guard**: Cross-checks numeric claims and URLs against source text (optional strict mode).

                ### Why These Libraries?
                | Layer | Library | Rationale |
                |-------|---------|-----------|
                | PDF Parsing | `pypdf` | Pure Python, no compiled extensions → works on ARM/Termux. |
                | AI SDK | `google-generativeai` | Official, typed, supports streaming & function calling. |
                | Config | `pydantic-settings` | `.env` + env vars + CLI merging, validation built-in. |
                | Retry | `tenacity` | Exponential backoff + jitter for 429/5xx handling. |
                | CLI | `argparse` (stdlib) | Zero deps, works everywhere (incl. Termux). |
                | Dashboard | `streamlit` | 1-file app, auto-reload, built-in widgets. |
                """
            )
        )


def render_usage_guide() -> None:
    """Comprehensive usage guide."""
    with st.expander("📖 Usage Guide (CLI + Dashboard)", expanded=False):
        st.markdown(
            textwrap.dedent(
                """
                ## Dashboard (Streamlit)
                1. Install deps: `pip install -e .[dashboard]`
                2. Run: `streamlit run dashboard/app.py`
                3. Open http://localhost:8501
                4. Paste text **or** upload PDF/TXT/MD
                5. Choose mode (Brief / Detailed / Keypoints)
                6. Click **Generate Summary**

                ## CLI (Terminal / CI / Scripts)
                ```bash
                # Install
                pip install -e .[cli]   # or just: pip install -e .

                # Basic usage
                ai-content-organizer --input report.pdf --output summary.json --mode brief

                # Detailed mode with custom model
                ai-content-organizer \\\\
                  --input transcript.txt \\\\
                  --output out.json \\\\
                  --mode detailed \\\\
                  --model gemini-1.5-pro \\\\
                  --verbose
                ```

                ### Exit Codes
                | Code | Meaning |
                |------|---------|
                | 0 | Success |
                | 1 | Config / Input / AI / Output error (see logs) |

                ### Output JSON Schema
                ```json
                {
                  "mode": "brief|detailed|keypoints",
                  "summary": "string (≥1 char)",
                  "key_points": ["string", ...] | null,
                  "metadata": {
                    "model": "gemini-2.5-flash",
                    "chars_in": 4321,
                    "chars_out": 987,
                    "tokens_est": 245,
                    "latency_ms": 1234
                  }
                }
                ```

                ### Environment Variables
                Create `.env` (copy from `.env.example`):
                ```bash
                GOOGLE_API_KEY=AIza...
                # Optional overrides:
                # MODEL_NAME=gemini-2.5-flash
                # DEFAULT_MODE=brief
                # MAX_INPUT_CHARS=12000
                ```
                """
            )
        )


def render_contributing() -> None:
    """Contributing guide."""
    with st.expander("🤝 Contributing", expanded=False):
        st.markdown(
            textwrap.dedent(
                """
                ## How to Contribute
                1. Fork → create branch `feat/your-feature`
                2. Run tests: `pytest -v`
                3. Lint: `ruff check .`
                4. Open PR with clear description + screenshots (if UI)

                ## Development Setup
                ```bash
                python -m venv .venv && source .venv/bin/activate
                pip install -e .[dev,all]
                pre-commit install  # optional
                ```

                ## Adding a New Parser
                1. Create `src/ai_content_organizer/parsers/your_parser.py`
                2. Implement `ParserPort` protocol
                3. Register in `build_parser()` factory
                4. Add tests in `tests/unit/test_parsers.py`

                ## Adding a New AI Provider
                1. Implement `AIProviderPort` in `summarizers/your_provider.py`
                2. Register in `build_provider()`
                3. No changes to `SummarizerService` needed.
                """
            )
        )


def main() -> None:
    # ── Sidebar config ──────────────────────────────────────────────
    config = sidebar_config_form()
    render_activity_panel()

    # ── Header ──────────────────────────────────────────────────────
    render_header()

    # ── Input section ───────────────────────────────────────────────
    raw_text, uploaded, submitted = render_input_section(config)

    if submitted:
        if not config.api_key:
            st.error("❌ GOOGLE_API_KEY is required. Provide it in the sidebar.")
            return

        try:
            # Parse
            text = parse_input(uploaded, raw_text, config)

            # Summarize
            with st.spinner("Generating summary…"):
                service = SummarizerService(config=config)
                output = service.summarize(
                    text,
                    config.default_mode,
                    model=config.model_name,
                )

            # Render
            render_result(output)
            activity_log(
                f"Completed: {output.mode} | {output.metadata.get('chars_in', 0)}→{output.metadata.get('chars_out', 0)} chars | {output.metadata.get('latency_ms', 0)} ms"
            )

        except Exception as exc:
            logger.exception("Summarization failed")
            activity_log(f"Error: {exc}", "error")
            st.error(f"❌ Failed: {exc}")

    # ── Documentation sections ──────────────────────────────────────
    st.divider()
    render_architecture_section()
    st.divider()
    render_usage_guide()
    st.divider()
    render_contributing()

    # ── Footer ──────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "AI Content Organizer v0.1.0 • "
        "[GitHub](https://github.com/alangaming469-tech/ai-content-organizer) • "
        "[Issues](https://github.com/alangaming469-tech/ai-content-organizer/issues) • "
        "MIT License"
    )


if __name__ == "__main__":
    main()