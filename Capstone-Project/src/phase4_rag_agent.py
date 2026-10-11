from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from safety_privacy import classify_banking_safety, redact_pii

RAG_SYSTEM_PROMPT = """You are a banking support and advisory assistant.

Safety rules:
- Refuse money movement, approvals, and legal advice.
- Escalate fraud, OTP/PIN sharing requests, and high-risk security scenarios.
- Do not invent customer data.
- If retrieved context is insufficient, say: I do not have enough information in the curated knowledge base.

Answer rules:
- Use only the provided context for product/process guidance.
- Keep responses concise and practical.
- End with a Sources line containing short file names from retrieved context.

Return strict JSON with keys: decision, answer, reason.
decision must be one of: answer, refuse, escalate, clarify.
"""


@dataclass
class RagResponse:
    decision: str
    answer: str
    reason: str


def parse_json_response(content: str) -> dict:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, flags=re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {
        "decision": "clarify",
        "answer": content,
        "reason": "non_json_output",
    }


def sanitize_for_log(text: str) -> str:
    return redact_pii(text)


class Phase4RagBankingAgent:
    def __init__(
        self,
        vectorstore_dir: Path,
        model_name: str = "gpt-4o-mini",
        k: int = 4,
        relevance_threshold: float = 1.1,
    ) -> None:
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.k = k
        self.relevance_threshold = relevance_threshold
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = FAISS.load_local(
            str(vectorstore_dir), embeddings, allow_dangerous_deserialization=True
        )

    def _retrieve_relevant_docs(self, query: str) -> list:
        try:
            pairs = self.vectorstore.similarity_search_with_score(query, k=self.k * 2)
        except Exception:
            return []

        relevant = [doc for doc, score in pairs if score <= self.relevance_threshold]
        return relevant[: self.k]

    @staticmethod
    def _append_sources(answer: str, retrieved: list[dict]) -> str:
        source_names = sorted(
            {item.get("file_name", "unknown") for item in retrieved if item.get("file_name")}
        )
        if not source_names:
            return answer
        return f"{answer}\n\nSources: {', '.join(source_names)}"

    def respond(self, user_message: str, use_retrieval: bool = True) -> tuple[RagResponse, list[dict]]:
        safety = classify_banking_safety(user_message)
        if safety:
            return (
                RagResponse(
                    decision=safety.decision,
                    answer=safety.answer,
                    reason=safety.reason,
                ),
                [],
            )

        retrieved = []
        context = "No retrieval context provided."

        if use_retrieval:
            docs = self._retrieve_relevant_docs(user_message)
            retrieved = [doc.metadata for doc in docs]
            if not docs:
                return (
                    RagResponse(
                        decision="clarify",
                        answer="I do not have enough information in the curated knowledge base.",
                        reason="insufficient_retrieval_context",
                    ),
                    [],
                )
            context = "\n\n".join(
                [
                    f"[File: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
                    for doc in docs
                ]
            )

        user_prompt = (
            f"User question:\n{user_message}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Return only JSON."
        )

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(content=RAG_SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )
        except Exception:
            return (
                RagResponse(
                    decision="clarify",
                    answer="I am temporarily unable to process this request. Please try again.",
                    reason="model_runtime_error",
                ),
                retrieved,
            )
        parsed = parse_json_response(response.content if isinstance(response.content, str) else str(response.content))
        decision = str(parsed.get("decision", "clarify")).strip().lower()
        if decision not in {"answer", "refuse", "escalate", "clarify"}:
            decision = "clarify"

        answer = str(parsed.get("answer", "")).strip()
        if retrieved and decision == "answer":
            answer = self._append_sources(answer, retrieved)

        return (
            RagResponse(
                decision=decision,
                answer=answer,
                reason=str(parsed.get("reason", "")).strip(),
            ),
            retrieved,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 4 RAG agent")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--vectorstore-dir", default="vectorstore/phase4_banking_faiss")
    parser.add_argument("--no-retrieval", action="store_true")
    return parser.parse_args()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    load_dotenv(project_root.parent / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing. Configure it before running Phase 4 RAG agent.")
        return 2

    args = parse_args()
    agent = Phase4RagBankingAgent(
        vectorstore_dir=project_root / args.vectorstore_dir,
        model_name=args.model,
    )

    print("Phase 4 RAG agent ready (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Session ended.")
            break
        if not user_input:
            continue

        response, retrieved = agent.respond(user_input, use_retrieval=not args.no_retrieval)
        print(f"Agent [{response.decision}]: {response.answer}")
        print(f"Reason: {response.reason}")
        print(
            "Retrieved: "
            + ", ".join(sorted({item.get('file_name', 'unknown') for item in retrieved}))
            if retrieved
            else "Retrieved: none"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
