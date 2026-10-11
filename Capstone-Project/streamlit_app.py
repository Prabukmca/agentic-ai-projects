from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import traceback

import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phase5_tool_agent import Phase5ToolAgent


VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore" / "phase4_banking_faiss"
MANIFEST_PATH = VECTORSTORE_DIR / "manifest.json"
INDEX_FAISS_PATH = VECTORSTORE_DIR / "index.faiss"
INDEX_PKL_PATH = VECTORSTORE_DIR / "index.pkl"


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env")


st.set_page_config(
    page_title="Capstone Banking Advisory Agent",
    page_icon="🏦",
    layout="wide",
)

st.markdown(
    """
    <style>
      :root {
        --bg-top: #fff7ed;
        --bg-bottom: #ecfeff;
        --card: #ffffff;
        --ink: #0f172a;
        --muted: #475569;
        --accent: #0f766e;
        --accent-2: #0284c7;
        --border: #dbeafe;
      }
      .stApp {
        background: linear-gradient(135deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
      }
      .main-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 8px 22px rgba(2, 132, 199, 0.08);
        margin-bottom: 12px;
      }
      .kpi {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 600;
        color: white;
        background: linear-gradient(90deg, var(--accent), var(--accent-2));
        margin-right: 8px;
        font-size: 12px;
      }
      .meta {
        color: var(--muted);
        font-size: 12px;
      }
      .title {
        font-size: 1.95rem;
        font-weight: 800;
        color: var(--ink);
        letter-spacing: 0.2px;
      }
      .subtitle {
        color: var(--muted);
        margin-top: 4px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def startup_errors() -> list[str]:
    issues: list[str] = []
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY is missing. Add it to .env in repository root or Capstone-Project.")

    missing_files = [
        path.name
        for path in [MANIFEST_PATH, INDEX_FAISS_PATH, INDEX_PKL_PATH]
        if not path.exists()
    ]
    if missing_files:
        issues.append(
            "Vectorstore is incomplete. Missing: " + ", ".join(missing_files)
        )
    return issues


@st.cache_data
def load_manifest_summary() -> dict:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    docs = payload.get("documents", [])
    sources = sorted({doc.get("source", "unknown") for doc in docs})
    sample_docs = [doc.get("file_name", "unknown") for doc in docs[:7]]
    return {
        "files_count": payload.get("files_count", len(docs)),
        "chunks_count": payload.get("chunks_count", 0),
        "sources": sources,
        "sample_docs": sample_docs,
    }


@st.cache_resource
def load_agent() -> Phase5ToolAgent:
    return Phase5ToolAgent(vectorstore_dir=VECTORSTORE_DIR, model_name="gpt-4o-mini")


def init_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("feedback_submitted", {})
    st.session_state.setdefault("feedback_preferences", [])
    st.session_state.setdefault("feedback_retry_done", {})
    st.session_state.setdefault("pending_feedback_retry", None)


def render_feedback_buttons(item: dict, idx: int, agent: Phase5ToolAgent) -> None:
    if not item.get("response_id"):
        item["response_id"] = uuid4().hex
    feedback_key = item["response_id"]
    submitted = st.session_state.feedback_submitted.get(feedback_key)

    def handle_feedback(rating: str) -> None:
        nonlocal submitted
        if submitted is not None:
            return
        tool_name = item.get("tool", "none") or "none"
        agent.record_feedback(
            rating=rating,
            tool_name=tool_name,
            response_id=feedback_key,
        )
        st.session_state.feedback_submitted[feedback_key] = rating
        st.rerun()

    with st.container(horizontal=True, gap="small", width="content"):
        if st.button(
            " ",
            icon=(":material/thumb_up:" if submitted == "helpful" else ":material/thumb_up_off_alt:"),
            key=f"feedback_helpful_{feedback_key}",
            help="Mark this response as helpful",
            disabled=submitted is not None,
            width="content",
        ):
            handle_feedback("helpful")

        if st.button(
            " ",
            icon=(":material/thumb_down:" if submitted == "not_helpful" else ":material/thumb_down_off_alt:"),
            key=f"feedback_not_helpful_{feedback_key}",
            help="Mark this response as not helpful",
            disabled=submitted is not None,
            width="content",
        ):
            handle_feedback("not_helpful")

    if submitted == "helpful":
        st.caption("Thanks, your feedback was recorded.")
    elif submitted == "not_helpful":
        st.caption("Sorry this answer missed the mark. What should I improve?")
        reason = st.selectbox(
            "What missed the mark?",
            ["incorrect", "incomplete", "unclear", "not relevant"],
            index=None,
            placeholder="Choose a reason",
            key=f"feedback_reason_{feedback_key}",
        )
        correction = st.text_area(
            "What should be corrected? (optional)",
            max_chars=500,
            key=f"feedback_correction_{feedback_key}",
        )
        retry_done = st.session_state.feedback_retry_done.get(feedback_key, False)
        if st.button(
            "Retry with feedback",
            key=f"feedback_retry_{feedback_key}",
            disabled=reason is None or retry_done,
            width="content",
        ):
            preferences = set(st.session_state.feedback_preferences)
            if reason == "unclear":
                preferences.add("plain_language")
            elif reason == "incomplete":
                preferences.add("more_detail")
            elif reason == "not relevant":
                preferences.add("stay_on_question")
            st.session_state.feedback_preferences = sorted(preferences)
            st.session_state.pending_feedback_retry = {
                "response_id": feedback_key,
                "reason": reason,
                "correction": correction,
            }
            st.rerun()
        if retry_done:
            st.caption("A revised response was added below.")


def add_history(role: str, text: str, **kwargs) -> None:
    entry = {
        "role": role,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    entry.update(kwargs)
    if role == "assistant":
        entry.setdefault("response_id", uuid4().hex)
    st.session_state.chat_history.append(entry)


def process_pending_feedback_retry(agent: Phase5ToolAgent) -> None:
    pending = st.session_state.pop("pending_feedback_retry", None)
    if not pending:
        return

    response_id = pending.get("response_id")
    response_index = next(
        (
            index
            for index, item in enumerate(st.session_state.chat_history)
            if item.get("response_id") == response_id
        ),
        None,
    )
    if response_index is None:
        return

    original = st.session_state.chat_history[response_index]
    user_message = original.get("user_context", "")
    feedback_context = {
        "reason": pending.get("reason", ""),
        "correction": pending.get("correction", ""),
        "previous_response": original.get("text", ""),
        "style_preferences": st.session_state.feedback_preferences,
    }
    conversation_history = original.get("conversation_context", [])

    with st.spinner("Rechecking the answer with your feedback..."):
        try:
            result = agent.run(
                user_message,
                conversation_history=conversation_history,
                feedback_context=feedback_context,
            )
            add_history(
                "assistant",
                result.answer,
                decision=result.decision,
                reason=result.reason,
                tool=result.planned_tool,
                tool_status=result.tool_status,
                user_context=user_message,
                conversation_context=conversation_history,
                feedback_repair_of=response_id,
            )
        except Exception:
            add_history(
                "assistant",
                "I could not retry that answer right now. Please try again later or contact official bank support if this is urgent.",
                decision="clarify",
                reason="feedback_retry_runtime_error",
                tool="none",
                tool_status="failed",
                user_context=user_message,
                conversation_context=conversation_history,
                feedback_repair_of=response_id,
            )
        st.session_state.feedback_retry_done[response_id] = True
    st.rerun()


issues = startup_errors()
if issues:
    st.error("Startup checks failed. Fix the following before using the app:")
    for issue in issues:
        st.write(f"- {issue}")
    st.code(
        "d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe "
        "Capstone-Project/src/phase4_ingest.py"
    )
    st.stop()

summary = load_manifest_summary()
agent = load_agent()
init_state()
process_pending_feedback_retry(agent)

st.markdown("<div class='title'>Banking Advisory Agent</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>"
    "Streamlit interface for the Phase 5 tool-enabled banking support agent. "
    "Safety-first, non-transactional, and retrieval-grounded guidance."
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### System Status")
    st.markdown("<span class='kpi'>UI READY</span>", unsafe_allow_html=True)
    st.caption("Phase 5 backend + Phase 4 FAISS vectorstore loaded")

    st.markdown("### Safety Contract")
    st.markdown(
        "- Refuses money movement and approvals\n"
        "- Escalates OTP/fraud-risk scenarios\n"
        "- Refuses legal advice\n"
        "- Redacts common PII in stored logs"
    )

    st.markdown("### Knowledge Base")
    st.write(f"Documents: **{summary['files_count']}**")
    st.write(f"Chunks: **{summary['chunks_count']}**")

    with st.expander("Sources"):
        for source in summary["sources"]:
            st.markdown(f"- {source}")

    with st.expander("Sample Documents"):
        for name in summary["sample_docs"]:
            st.markdown(f"- {name}")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.feedback_submitted = {}
        st.session_state.feedback_preferences = []
        st.session_state.feedback_retry_done = {}
        st.session_state.pending_feedback_retry = None
        st.rerun()

for idx, item in enumerate(st.session_state.chat_history):
    with st.chat_message(item["role"]):
        st.markdown(item["text"])
        if item["role"] == "assistant":
            if item.get("feedback_repair_of"):
                st.caption("Revised response based on your feedback.")
            st.markdown(
                f"<div class='meta'>Decision: {item.get('decision', '-') } | "
                f"Tool: {item.get('tool', '-') } | "
                f"Tool status: {item.get('tool_status', '-') }</div>",
                unsafe_allow_html=True,
            )
            render_feedback_buttons(item, idx, agent)

prompt = st.chat_input("Ask a banking support/advisory question")
if prompt:
    conversation_history = st.session_state.chat_history[-20:]
    add_history("user", prompt)

    try:
        result = agent.run(
            prompt,
            conversation_history=conversation_history,
            feedback_context={"style_preferences": st.session_state.feedback_preferences},
        )
        add_history(
            "assistant",
            result.answer,
            decision=result.decision,
            reason=result.reason,
            tool=result.planned_tool,
            tool_status=result.tool_status,
            user_context=prompt,
            conversation_context=conversation_history,
        )
    except Exception as exc:
        error_details = traceback.format_exc()
        add_history(
            "assistant",
            f"Backend runtime error: {type(exc).__name__}: {exc}",
            decision="clarify",
            reason=f"ui_runtime_error: {type(exc).__name__}",
            tool="none",
            tool_status="failed",
        )
        sync_agent_memory(agent)
        st.error("The backend raised an exception. See the details below for debugging.")
        with st.expander("Backend exception details"):
            st.code(error_details, language="python")

    st.rerun()
