from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from enterprise_knowledge_ops_agent import MemoryAgent, OrchestratorAgent, SourceDocument, load_pdf_documents


st.set_page_config(page_title="Enterprise Knowledge Ops Agent", page_icon="🧠", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "draft_question" not in st.session_state:
    st.session_state.draft_question = ""

if "clear_history" not in st.session_state:
    st.session_state.clear_history = False

if "scroll_to_bottom" not in st.session_state:
    st.session_state.scroll_to_bottom = False


DOCS_DIR = Path(__file__).resolve().parent / "documents"
VECTORSTORE_DIR = Path(__file__).resolve().parent / "enterprise_vectorstore"
llm_mode_active = bool(os.getenv("OPENAI_API_KEY"))
vectorstore_status = "fallback mode"


@st.cache_data
def load_knowledge_base():
    documents: list[SourceDocument] = []
    try:
        raw_docs = load_pdf_documents(DOCS_DIR)
    except Exception:
        raw_docs = []

    for index, doc in enumerate(raw_docs):
        source_name = doc.metadata.get("source") or f"document-{index + 1}.pdf"
        title = Path(source_name).stem

        content = (doc.page_content or "").strip().replace("\n", " ")
        if not content:
            continue

        page_number = doc.metadata.get("page", index + 1)
        documents.append(SourceDocument(
            id=f"doc-{len(documents) + 1}",
            title=title,
            source=source_name,
            content=content,
            metadata={"page": page_number},
        ))

    if not documents:
        return [
            SourceDocument(
                id="fallback-doc",
                title="No PDFs found",
                source="documents",
                content="The document folder is empty or inaccessible. Configure the source documents before running the agent.",
            )
        ]

    return documents


@st.cache_resource
def build_agent():
    return OrchestratorAgent(memory=MemoryAgent())


if llm_mode_active:
    try:
        from enterprise_knowledge_ops_agent import ensure_vectorstore
        VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
        ensure_vectorstore(DOCS_DIR, VECTORSTORE_DIR)
        vectorstore_status = "vectorstore active" if (VECTORSTORE_DIR / "index.faiss").exists() else "fallback mode"
    except Exception:
        vectorstore_status = "fallback mode"
else:
    vectorstore_status = "fallback mode"

st.title("Enterprise Knowledge Ops Agent")
status_label = "vectorstore active" if vectorstore_status == "vectorstore active" else "fallback mode"
status_color = "green" if status_label == "vectorstore active" else "orange"

st.markdown(
    f"<div style='display:flex; align-items:center; gap:10px; margin-bottom: 0.5rem;'>"
    f"<span style='display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; "
    f"background-color:{status_color}; color:white;'>{status_label}</span>"
    f"<span style='color:#666; font-size:14px;'>Multi-agent reasoning, grounded retrieval, validation, and explainability for enterprise knowledge questions.</span>"
    f"</div>",
    unsafe_allow_html=True,
)

knowledge_base = load_knowledge_base()


def trigger_scroll_to_bottom():
    st.session_state.scroll_to_bottom = True


if st.session_state.get("scroll_to_bottom"):
    st.components.v1.html(
        """
        <script>
        function scrollToBottom() {
            const scrollable = document.querySelector('.stMainBlock');
            if (scrollable) {
                scrollable.scrollTop = scrollable.scrollHeight;
            }
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }
        setTimeout(scrollToBottom, 150);
        </script>
        """,
        height=0,
    )
    st.session_state.scroll_to_bottom = False

with st.sidebar:
    st.header("System Overview")
    if llm_mode_active and vectorstore_status == "vectorstore active":
        st.success("Vectorstore active")
    else:
        st.warning("Vectorstore active: no")
        if llm_mode_active:
            st.caption("API key present, but local FAISS index is not available yet.")
        else:
            st.caption("No OPENAI_API_KEY configured; local vector retrieval is unavailable.")

    st.markdown(
        """
        - Source documents: loaded from the real PDF folder under Cognizant-Assignment/documents
        - Retrieval: PDF content is indexed for semantic matching and keyword expansion when the vectorstore is available
        - Analyst: LLM-grounded synthesis over retrieved evidence when available
        - Verifier: checks whether the answer stays tied to the source material
        - Memory: keeps recent evidence across turns
        """
    )

    st.header("Knowledge Base")
    st.caption(f"{len(knowledge_base)} unique source documents loaded")

    source_names = [doc.title for doc in knowledge_base[:5]]
    source_summary = ", ".join(source_names)
    if len(knowledge_base) > 5:
        source_summary += f", +{len(knowledge_base) - 5} more"
    st.write(source_summary)

    with st.expander("View exact source PDFs"):
        for doc in knowledge_base:
            st.markdown(f"- **{doc.source}**")

    with st.expander("View loaded document titles"):
        for doc in knowledge_base:
            st.markdown(f"- **{doc.title}**")

    st.divider()

    st.header("Chat History")
    if not st.session_state.chat_history:
        st.caption("No questions asked yet")
    else:
        st.caption(f"{len(st.session_state.chat_history)} conversation(s)")
        
        # Display each chat entry
        for idx, chat_item in enumerate(reversed(st.session_state.chat_history), 1):
            # Create a clickable section for each chat
            with st.expander(f"#{len(st.session_state.chat_history) - idx + 1}: {chat_item['question'][:50]}...", expanded=False):
                st.markdown("**Question:**")
                st.write(chat_item["question"])
                
                st.markdown("**Answer:**")
                st.write(chat_item["answer"])
                
                col1, col2 = st.columns(2)
                with col1:
                    # Show grounding info
                    grounding_status = chat_item['grounding']['status']
                    grounding_score = chat_item['grounding']['grounding_score']
                    st.caption(f"📊 Grounding: **{grounding_status}** ({grounding_score:.2%})")
                
                with col2:
                    # Show mode info
                    mode = chat_item.get("mode", "fallback")
                    mode_icon = "🤖" if mode == "llm" else "📋"
                    st.caption(f"{mode_icon} Mode: **{mode}**")
                
                # Quick delete button for this chat
                if st.button("🗑️ Delete", key=f"delete_{idx}_{len(st.session_state.chat_history)}"):
                    chat_index = len(st.session_state.chat_history) - idx
                    st.session_state.chat_history.pop(chat_index)
                    st.rerun()

chat_container = st.container(height=320)
with chat_container:
    if not st.session_state.chat_history:
        st.info("Ask a business question to begin.")
    else:
        for item in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(item["question"])

            with st.chat_message("assistant"):
                st.markdown(item["answer"])
                mode_label = "OpenAI LLM + vector retrieval" if item.get("mode") == "llm" else "Local retrieval fallback"
                grounding_label = f"Grounding: {item['grounding']['status']} | Score: {item['grounding']['grounding_score']:.3f}"
                st.caption(f"{mode_label} · {grounding_label}")
                with st.expander("View reasoning trace", expanded=False):
                    st.json(item["trace"])

with st.form("question_form", clear_on_submit=True):
    st.text_area(
        "Ask a business question",
        key="draft_question",
        height=120,
        placeholder="Type your question here...",
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        submitted = st.form_submit_button("Run agent", use_container_width=True)
    with col2:
        clear_clicked = st.form_submit_button("Clear history", use_container_width=True)

if clear_clicked:
    st.session_state.chat_history = []
    st.session_state.scroll_to_bottom = False
    st.rerun()

if submitted:
    question = st.session_state.draft_question.strip()
    if not question:
        st.warning("Please enter a question.")
    else:
        trigger_scroll_to_bottom()
        with st.spinner("🔄 Processing your question... Analyzing documents, retrieving context, and generating response..."):
            agent = build_agent()
            active_documents = [] if vectorstore_status == "vectorstore active" else knowledge_base
            result = agent.run(question, active_documents)
            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "grounding": result["grounding"],
                "trace": result["trace"],
                "mode": "llm" if llm_mode_active else "fallback",
            })
        st.rerun()
