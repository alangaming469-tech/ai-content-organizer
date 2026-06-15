import io
import json
import logging
from pathlib import Path
from typing import Optional

import streamlit as st

from ai_content_organizer.models.schemas import AppConfig, SummaryMode
from ai_content_organizer.parsers.file_parsers import build_parser
from ai_content_organizer.summarizers.summarizer import SummarizerService



def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def render_sidebar() -> AppConfig:
    configure_logging()
    st.sidebar.title("Pengaturan")
    default_mode = st.sidebar.selectbox(
        "Mode summarization",
        options=[mode.value for mode in SummaryMode],
        index=0,
    )
    model_name = st.sidebar.text_input("Model (override)", value="gemini-2.5-flash")
    max_chars = st.sidebar.number_input("Batas input chars", min_value=1000, max_value=50000, value=12000)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    max_tokens = st.sidebar.number_input("Max output tokens", min_value=256, max_value=8192, value=2048, step=256)

    api_key = st.secrets.get("GOOGLE_API_KEY") or st.session_state.get("GOOGLE_API_KEY", "")
    if not api_key:
        with st.sidebar.expander("Konfigurasi API", expanded=True):
            api_key = st.text_input("GOOGLE_API_KEY", type="password")

    return AppConfig(
        api_key=api_key,
        model_name=model_name,
        default_mode=SummaryMode(default_mode),
        max_input_chars=int(max_chars),
        max_output_tokens=int(max_tokens),
        temperature=temperature,
    )


def render_dashboard() -> None:
    st.set_page_config(page_title="AI Content Organizer", layout="wide")
    config = render_sidebar()
    st.title("AI Content Organizer")
    mode = st.selectbox("Mode", options=[mode.value for mode in SummaryMode], index=0)
    input_text: Optional[str] = None
    uploaded = st.file_uploader("Unggah file (PDF/TXT/MD)", type=["pdf", "txt", "md"])
    text_area = st.text_area("Atau tempel teks di sini", height=220)

    if st.button("Jalankan summarization", type="primary"):
        if uploaded or text_area.strip():
            with st.spinner("Sedang memproses..."):
                try:
                    if uploaded is not None:
                        suffix = Path(uploaded.name).suffix.lower()
                        tmp = Path("/tmp") / f"uploaded{suffix}"
                        tmp.write_bytes(uploaded.getbuffer())
                        parser_wrapper = build_parser(tmp)
                        raw_text = parser_wrapper.parse(tmp)
                    else:
                        raw_text = text_area

                    service = SummarizerService(config=config)
                    output = service.summarize(raw_text, SummaryMode(mode), model=config.model_name)
                    st.success("Selesai")
                    log_placeholder = st.empty()
                    log_placeholder.info(
                        "Aktivitas: input=%d chars | mode=%s | model=%s",
                        len(raw_text),
                        mode,
                        output.metadata.get("model"),
                    )
                    st.subheader("Hasil")
                    st.write(output.summary)
                    if output.key_points:
                        st.subheader("Poin kunci")
                        for point in output.key_points:
                            st.write(f"- {point}")
                    with st.expander("JSON output"):
                        st.json(json.loads(output.model_dump_json(indent=2)))
                except Exception as exc:
                    logging.getLogger("dashboard").exception("Summarization failed")
                    st.error(f"Gagal: {exc}")
        else:
            st.warning("Silakan unggah file atau tempel teks terlebih dahulu")


if __name__ == "__main__":
    render_dashboard()
