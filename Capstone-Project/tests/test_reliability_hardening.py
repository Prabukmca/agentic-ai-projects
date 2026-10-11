from pathlib import Path
import importlib
import json
import sys
from types import SimpleNamespace


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
phase3_llm_agent = importlib.import_module("phase3_llm_agent")
phase4_rag_agent = importlib.import_module("phase4_rag_agent")
phase5_tool_agent = importlib.import_module("phase5_tool_agent")


class _FailingLlm:
    def invoke(self, _messages):
        raise RuntimeError("provider unavailable")


class _JsonLlm:
    def invoke(self, _messages):
        return SimpleNamespace(
            content=json.dumps(
                {
                    "decision": "answer",
                    "answer": "Use the official bank channel.",
                    "reason": "grounded guidance",
                }
            )
        )


class _FakeVectorstore:
    def __init__(self, pairs):
        self.pairs = pairs

    def similarity_search_with_score(self, _query, k):
        return self.pairs[:k]

    def similarity_search(self, _query, k):
        return [doc for doc, _score in self.pairs[:k]]


def _doc(name: str):
    return SimpleNamespace(
        page_content="Trusted process guidance.",
        metadata={"file_name": name, "source": "https://example.org"},
    )


def _rag_agent(vectorstore, llm, threshold=1.1):
    agent = phase4_rag_agent.Phase4RagBankingAgent.__new__(
        phase4_rag_agent.Phase4RagBankingAgent
    )
    agent.vectorstore = vectorstore
    agent.llm = llm
    agent.k = 2
    agent.relevance_threshold = threshold
    return agent


def test_phase3_returns_safe_fallback_when_model_fails() -> None:
    agent = phase3_llm_agent.Phase3LlmBankingAgent.__new__(
        phase3_llm_agent.Phase3LlmBankingAgent
    )
    agent.system_prompt = "test"
    agent.llm = _FailingLlm()

    response = agent.respond("How do I block my card?")

    assert response.decision == "clarify"
    assert response.reason == "model_runtime_error"


def test_phase4_rejects_irrelevant_retrieval_results() -> None:
    agent = _rag_agent(_FakeVectorstore([(_doc("unrelated.md"), 1.5)]), _JsonLlm())

    response, retrieved = agent.respond("What is the exact penalty slab?")

    assert response.decision == "clarify"
    assert response.reason == "insufficient_retrieval_context"
    assert retrieved == []


def test_phase4_appends_deterministic_source_citations() -> None:
    agent = _rag_agent(_FakeVectorstore([(_doc("card_blocking.md"), 0.2)]), _JsonLlm())

    response, retrieved = agent.respond("How do I block a card?")

    assert response.decision == "answer"
    assert "Sources: card_blocking.md" in response.answer
    assert retrieved[0]["file_name"] == "card_blocking.md"


def test_phase5_policy_lookup_returns_safe_tool_error_on_vectorstore_failure() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.vectorstore = _FailingLlm()

    result = agent.policy_lookup("How do I block my card?")

    assert result.ok is False
    assert result.error.startswith("policy_lookup_runtime_error:")
