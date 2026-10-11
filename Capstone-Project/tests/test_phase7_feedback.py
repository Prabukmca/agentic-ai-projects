from __future__ import annotations

import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import phase5_tool_agent


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLlm:
    def __init__(self, decision: str = "answer") -> None:
        self.decision = decision

    def invoke(self, messages):
        payload = {
            "decision": self.decision,
            "answer": "stub answer",
            "reason": "stub_reason",
            "format": "paragraph",
        }
        return _FakeResponse(json.dumps(payload))


def _make_agent(tmp_path: Path):
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.allowed_tools = {"calculator", "loan_calculator", "policy_lookup", "none"}
    agent.api_key_missing = False
    agent.llm = _FakeLlm()
    agent.feedback_log_path = tmp_path / "phase7_feedback.jsonl"
    agent.feedback_log_path.parent.mkdir(parents=True, exist_ok=True)
    return agent


def test_record_feedback_persists_entries(tmp_path):
    agent = _make_agent(tmp_path)

    agent.record_feedback(
        rating="not_helpful",
        tool_name="policy_lookup",
        response_id="response-123",
    )

    assert agent.feedback_log_path.exists()
    rows = [json.loads(line) for line in agent.feedback_log_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["rating"] == "not_helpful"
    assert rows[0]["tool_name"] == "policy_lookup"
    assert rows[0]["response_id"] == "response-123"
    assert set(rows[0]) == {"timestamp_utc", "rating", "tool_name", "response_id"}


def test_negative_feedback_does_not_disable_policy_lookup_globally(tmp_path):
    agent = _make_agent(tmp_path)
    agent.record_feedback("not_helpful", "policy_lookup", "response-1")
    agent.record_feedback("not_helpful", "policy_lookup", "response-2")
    agent.plan_tool = lambda user_message, conversation_history=None: {
        "tool_name": "policy_lookup",
        "tool_args": {"query": user_message},
        "reason": "policy_request",
    }
    agent._route_tool_by_rules = lambda user_message, planned_tool, resolved_loan_inputs=None: planned_tool
    agent.policy_lookup = lambda query: phase5_tool_agent.ToolResult(True, "policy_lookup", "supported guidance")

    result = agent.run("How do I block my lost debit card?")

    assert result.planned_tool == "policy_lookup"
    assert result.tool_status == "ok"


def test_retry_feedback_is_passed_to_synthesis_as_unverified_context(tmp_path):
    class _CapturingLlm:
        def __init__(self):
            self.messages = None

        def invoke(self, messages):
            self.messages = messages
            return _FakeResponse(json.dumps({
                "decision": "answer",
                "answer": "Revised stub answer",
                "reason": "feedback_retry",
                "format": "paragraph",
            }))

    agent = _make_agent(tmp_path)
    agent.llm = _CapturingLlm()
    agent.plan_tool = lambda user_message, conversation_history=None: {
        "tool_name": "none",
        "tool_args": {},
        "reason": "no_tool_needed",
    }
    agent._route_tool_by_rules = lambda user_message, planned_tool, resolved_loan_inputs=None: "none"

    result = agent.run(
        "How do I block my debit card?",
        feedback_context={
            "reason": "incomplete",
            "correction": "Please include what to do if the app is unavailable.",
            "previous_response": "Block it in the app.",
            "style_preferences": ["more_detail", "invalid_preference"],
        },
    )

    synthesis_input = json.loads(agent.llm.messages[1].content)
    assert result.answer == "Revised stub answer"
    assert synthesis_input["response_feedback"] == {
        "reason": "incomplete",
        "correction": "Please include what to do if the app is unavailable.",
        "previous_response": "Block it in the app.",
        "style_preferences": ["more_detail"],
    }


def test_retry_correction_with_otp_risk_is_escalated_before_model_call(tmp_path):
    class _NeverCalledLlm:
        def invoke(self, messages):
            raise AssertionError("model must not run after safety escalation")

    agent = _make_agent(tmp_path)
    agent.llm = _NeverCalledLlm()

    result = agent.run(
        "How do I block my debit card?",
        feedback_context={"correction": "A caller asked me to share my OTP."},
    )

    assert result.decision == "escalate"
    assert result.reason == "high_risk_security"
    assert result.tool_status == "skipped_safety"


def test_missing_api_key_returns_clear_configuration_message():
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.api_key_missing = True

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "How do I block my card?")

    assert result.decision == "clarify"
    assert "OPENAI_API_KEY" in result.answer
    assert "missing" in result.answer.lower()


def test_llm_quota_exhaustion_returns_actionable_message():
    class _QuotaLlm:
        def invoke(self, messages):
            raise Exception("Error code: 429 - {'error': {'code': 'credit_balance_exhausted'}}")

    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.allowed_tools = {"calculator", "loan_calculator", "policy_lookup", "none"}
    agent.api_key_missing = False
    agent.llm = _QuotaLlm()

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "How do I block my card?")

    assert result.decision == "clarify"
    assert "credits" in result.answer.lower() or "quota" in result.answer.lower()
