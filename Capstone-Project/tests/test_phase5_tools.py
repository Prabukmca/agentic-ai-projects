from pathlib import Path
import importlib
import sys
import json

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
phase5_tool_agent = importlib.import_module("phase5_tool_agent")


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLlm:
    def __init__(self, decision: str = "clarify") -> None:
        self.decision = decision
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        payload = {
            "decision": self.decision,
            "answer": "stub",
            "reason": "stub_reason",
        }
        return _FakeResponse(json.dumps(payload))


def _build_fake_agent(planner_output: dict):
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.allowed_tools = {
        "calculator",
        "loan_calculator",
        "loan_process_lookup",
        "atm_usage_lookup",
        "transfer_limit_lookup",
        "foreign_transfer_fee_lookup",
        "policy_lookup",
        "none",
    }
    agent.llm = _FakeLlm(decision="answer")
    agent.plan_tool = lambda _msg, conversation_history=None: planner_output
    return agent


def test_calculator_valid_expression() -> None:
    value = phase5_tool_agent.evaluate_expression("12.5 * 3 + 10")
    assert value == 47.5


def test_loan_calculator_returns_emi_totals() -> None:
    result = phase5_tool_agent.calculate_loan_emi(500000, 8.5, 5, "years", "monthly")

    assert result["monthly_emi"] == 10258.27
    assert result["total_repayment"] == 615495.94
    assert result["total_interest"] == 115495.94


def test_loan_calculator_handles_zero_interest() -> None:
    result = phase5_tool_agent.calculate_loan_emi(120000, 0, 12, "months", "monthly")

    assert result["monthly_emi"] == 10000.0
    assert result["total_repayment"] == 120000.0
    assert result["total_interest"] == 0.0


def test_validated_number_rejects_empty_string() -> None:
    with pytest.raises(ValueError, match="must be numeric"):
        phase5_tool_agent._validated_number("", "Loan amount")


def test_run_formats_loan_result_as_markdown_bullets() -> None:
    agent = _build_fake_agent({"tool_name": "loan_calculator", "tool_args": {}})
    prompt = "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi."

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, prompt)

    assert result.decision == "answer"
    assert result.reason == "loan_estimate"
    assert "**Loan estimate**" in result.answer
    assert "- Monthly EMI: **92,829.44**" in result.answer
    assert "- Total repayment: **44,558,131.28**" in result.answer
    assert "- Total interest: **34,558,131.28**" in result.answer
    assert "estimate only" in result.answer


def test_format_answer_for_display_supports_generic_formats() -> None:
    assert "- First: **10**\n- Second: **20**" in phase5_tool_agent.format_answer_for_display(
        "summary",
        response_format="bullets",
        data={"First": 10, "Second": 20},
        title="Summary",
    )
    assert "1. Step one" in phase5_tool_agent.format_answer_for_display(
        "steps",
        response_format="numbered",
        data=["Step one", "Step two"],
        title="Process",
    )


@pytest.mark.parametrize(
    "inputs",
    [
        (0, 8.5, 60, "months", "monthly"),
        (-1000, 8.5, 60, "months", "monthly"),
        (1000, -1, 60, "months", "monthly"),
        (1000, 8.5, 0, "months", "monthly"),
        (1000, 8.5, "not-a-number", "months", "monthly"),
    ],
)
def test_loan_calculator_rejects_invalid_values(inputs) -> None:
    with pytest.raises(ValueError):
        phase5_tool_agent.calculate_loan_emi(*inputs)


def test_calculator_rejects_placeholder_expression_safely() -> None:
    result = phase5_tool_agent.Phase5ToolAgent.calculator(
        phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent), "..."
    )

    assert not result.ok
    assert result.error == "calculator_error: invalid numeric expression"


@pytest.mark.parametrize(
    "expr",
    [
        "10 + abc",
        "__import__('os').system('dir')",
        "(1 + 2",
    ],
)
def test_calculator_rejects_unsafe_or_invalid_expression(expr: str) -> None:
    with pytest.raises(Exception):
        phase5_tool_agent.evaluate_expression(expr)


def test_safety_shortcut_refuses_transaction() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    out = phase5_tool_agent.Phase5ToolAgent._safety_shortcut(fake, "Please transfer money now")
    assert out is not None
    assert out.decision == "refuse"


def test_safety_shortcut_escalates_otp() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    out = phase5_tool_agent.Phase5ToolAgent._safety_shortcut(fake, "caller asked for OTP")
    assert out is not None
    assert out.decision == "escalate"


def test_safety_shortcut_refuses_consumer_forum() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    out = phase5_tool_agent.Phase5ToolAgent._safety_shortcut(
        fake, "How do I take my bank to consumer forum?"
    )
    assert out is not None
    assert out.decision == "refuse"


def test_extract_expression_empty_when_no_math() -> None:
    assert phase5_tool_agent.extract_expression("please calculate quickly") == ""


def test_rule_router_prefers_calculator_on_math_prompt() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake, "Please calculate 22 / 7", "none"
    )
    assert selected == "calculator"


def test_rule_router_selects_loan_calculator_for_complete_inputs() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake,
        "Calculate the monthly EMI for a loan of ₹500,000 at 8.5% annual interest for 5 years with monthly payments.",
        "calculator",
    )

    assert selected == "loan_calculator"


def test_rule_router_accepts_annual_rate_without_percent_sign() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake,
        "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi.",
        "none",
    )

    assert selected == "loan_calculator"
    assert phase5_tool_agent.extract_loan_inputs(
        "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi."
    )["annual_rate"] == 11.0


def test_conversation_history_resolves_previous_loan_values_for_follow_up() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    conversation_history = [
        {
            "role": "user",
            "text": "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi.",
        },
    ]

    resolved = agent._resolve_loan_inputs(
        "decrease the tenure to 20 years and calculate the emi", conversation_history
    )

    assert resolved["principal"] == 10000000.0
    assert resolved["annual_rate"] == 11.0
    assert resolved["tenure"] == 20.0
    assert resolved["tenure_unit"] == "years"


def test_generic_conversation_history_tracks_recent_chat_context() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    conversation_history = [
        {"role": "user", "text": "Convert 20 USD to INR."},
        {"role": "assistant", "text": "That is approximately 1,660 INR."},
        {"role": "user", "text": "What is 12 + 5?"},
    ]

    context = agent._session_context(conversation_history)
    assert "Convert 20 USD to INR." in context
    assert "What is 12 + 5?" in context
    assert "assistant: That is approximately 1,660 INR." in context


def test_safety_classifier_allows_loan_tenure_calculation() -> None:
    safety = __import__("safety_privacy", fromlist=["classify_banking_safety"]).classify_banking_safety(
        "Decrease the tenure to 20 years and calculate the EMI."
    )
    assert safety is None


def test_incomplete_loan_question_returns_clarification() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "Will you do loan interest calculation?")

    assert result.decision == "clarify"
    assert result.planned_tool == "none"
    assert result.tool_status == "not_used"
    assert result.answer == phase5_tool_agent.LOAN_CLARIFICATION


def test_generic_block_card_question_is_currently_a_failed_policy_flow() -> None:
    class _ExplodingLlm:
        def invoke(self, messages):
            raise RuntimeError("temporary model outage")

    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.allowed_tools = {"calculator", "loan_calculator", "policy_lookup", "none"}
    agent.api_key_missing = False
    agent.llm = _ExplodingLlm()
    agent.feedback_profile = {
        "calculator": {"helpful": 0, "not_helpful": 0},
        "loan_calculator": {"helpful": 0, "not_helpful": 0},
        "policy_lookup": {"helpful": 0, "not_helpful": 0},
        "none": {"helpful": 0, "not_helpful": 0},
    }
    agent.policy_lookup = lambda query: phase5_tool_agent.ToolResult(
        False, "policy_lookup", "", "policy_lookup_runtime_error"
    )

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "How do I block my card?")

    assert result.decision == "clarify"
    assert result.planned_tool == "policy_lookup"
    assert result.tool_status == "failed"
    assert "temporarily unable" in result.answer.lower()


def test_personal_loan_question_routes_to_process_lookup() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake,
        "How to get the personal loan?",
        "none",
    )

    assert selected == "loan_process_lookup"


def test_run_personal_loan_process_question_avoids_emi_clarification() -> None:
    agent = _build_fake_agent({"tool_name": "none", "tool_args": {}})

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "How to get the personal loan?")

    assert result.planned_tool == "loan_process_lookup"
    assert result.reason != "missing_loan_inputs"


def test_atm_and_transfer_questions_route_to_specialized_tools() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    assert (
        phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
            fake,
            "What is the daily ATM withdrawal limit?",
            "none",
        )
        == "atm_usage_lookup"
    )
    assert (
        phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
            fake,
            "What is the online transfer limit for my account?",
            "none",
        )
        == "transfer_limit_lookup"
    )
    assert (
        phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
            fake,
            "What are the charges for foreign money transfer?",
            "none",
        )
        == "foreign_transfer_fee_lookup"
    )


def test_two_turn_loan_flow_clarify_then_estimate() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    agent.allowed_tools = {"calculator", "loan_calculator", "policy_lookup", "none"}
    agent.llm = _FakeLlm(decision="answer")

    first_message = "will you do loan calculation?"
    first = phase5_tool_agent.Phase5ToolAgent.run(agent, first_message)
    conversation_history = [
        {"role": "user", "text": first_message},
        {"role": "assistant", "text": first.answer},
    ]
    second_message = "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi."
    second = phase5_tool_agent.Phase5ToolAgent.run(
        agent,
        second_message,
        conversation_history=conversation_history,
    )

    assert first.decision == "clarify"
    assert first.planned_tool == "none"
    assert first.tool_status == "not_used"
    assert first.answer == phase5_tool_agent.LOAN_CLARIFICATION

    assert second.decision == "answer"
    assert second.reason == "loan_estimate"
    assert second.planned_tool == "loan_calculator"
    assert second.tool_status == "ok"
    assert "- Monthly EMI: **92,829.44**" in second.answer


def test_completed_loan_can_be_revised_using_prior_turns() -> None:
    agent = _build_fake_agent({"tool_name": "none", "tool_args": {}})
    conversation_history = [
        {
            "role": "user",
            "text": "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi.",
        },
        {"role": "assistant", "text": "Monthly EMI: 92,829.44"},
    ]

    result = phase5_tool_agent.Phase5ToolAgent.run(
        agent,
        "reduce the tenure to 20 years and calculate the monthly emi",
        conversation_history=conversation_history,
    )

    assert result.decision == "answer"
    assert result.planned_tool == "loan_calculator"
    assert result.tool_status == "ok"
    assert "20 years (240 months)" in result.answer
    assert "40 years" not in result.answer


def test_contextual_calculator_arguments_reach_the_tool() -> None:
    agent = _build_fake_agent({"tool_name": "calculator", "tool_args": {"expression": "17 * 2"}})
    expressions = []
    agent.calculator = lambda expression: (
        expressions.append(expression) or phase5_tool_agent.ToolResult(True, "calculator", "result=34")
    )
    history = [
        {"role": "user", "text": "What is 12 + 5?"},
        {"role": "assistant", "text": "17"},
    ]

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "double that", conversation_history=history)

    assert result.planned_tool == "calculator"
    assert result.tool_status == "ok"
    assert expressions == ["17 * 2"]


def test_contextual_policy_follow_up_uses_planner_query() -> None:
    agent = _build_fake_agent(
        {"tool_name": "policy_lookup", "tool_args": {"query": "card dispute process"}}
    )
    captured_queries = []
    agent.policy_lookup = lambda query: (
        captured_queries.append(query)
        or phase5_tool_agent.ToolResult(True, "policy_lookup", "Dispute process details")
    )
    history = [
        {"role": "user", "text": "How do I dispute a card transaction?"},
        {"role": "assistant", "text": "You can raise a card dispute."},
    ]

    result = phase5_tool_agent.Phase5ToolAgent.run(
        agent, "What about that?", conversation_history=history
    )

    assert result.planned_tool == "policy_lookup"
    assert result.tool_status == "ok"
    assert captured_queries == ["card dispute process"]
    synthesis = json.loads(agent.llm.messages[-1][1].content)
    assert "How do I dispute a card transaction?" in synthesis["conversation_context"]


def test_history_is_isolated_between_calls_to_same_agent() -> None:
    agent = _build_fake_agent({"tool_name": "none", "tool_args": {}})
    received_histories = []
    agent.plan_tool = lambda _message, conversation_history=None: (
        received_histories.append(conversation_history)
        or {"tool_name": "none", "tool_args": {}}
    )

    first_history = [{"role": "user", "text": "First session's topic."}]
    second_history = [{"role": "user", "text": "Second session's topic."}]
    phase5_tool_agent.Phase5ToolAgent.run(
        agent, "Please explain more.", conversation_history=first_history
    )
    phase5_tool_agent.Phase5ToolAgent.run(
        agent, "Please explain more.", conversation_history=second_history
    )

    assert received_histories == [first_history, second_history]
    assert not hasattr(agent, "session_memory")


def test_unresolved_contextual_calculation_does_not_call_tool() -> None:
    agent = _build_fake_agent({"tool_name": "calculator", "tool_args": {}})
    agent.calculator = lambda _expression: pytest.fail("calculator must not run without an expression")

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "double that")

    assert result.decision == "clarify"
    assert result.reason == "missing_calculator_expression"
    assert result.planned_tool == "none"
    assert result.tool_status == "not_used"


def test_contextual_safety_check_covers_referential_follow_up() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    history = [
        {"role": "user", "text": "Please transfer 10000 to my friend now."},
        {"role": "assistant", "text": "I cannot execute money transfers."},
    ]

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "Go ahead and do it.", conversation_history=history)

    assert result.decision == "refuse"
    assert result.tool_status == "skipped_safety"


def test_complete_loan_request_works_even_if_planner_falls_back_to_none() -> None:
    agent = _build_fake_agent({"tool_name": "none", "tool_args": {}})

    result = phase5_tool_agent.Phase5ToolAgent.run(
        agent,
        "loan amount : 10000000, annual interest rate : 11, tenure: 40 years, monthly emi.",
    )

    assert result.decision == "answer"
    assert result.reason == "loan_estimate"
    assert result.planned_tool == "loan_calculator"
    assert result.tool_status == "ok"


def test_existing_arithmetic_calculator_behavior_remains_unchanged() -> None:
    agent = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)

    result = phase5_tool_agent.Phase5ToolAgent.calculator(agent, "22 / 7")

    assert result.ok
    assert result.tool_name == "calculator"
    assert result.output == "result=3.142857142857143"


def test_rule_router_prefers_calculator_for_implicit_math_query() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake, "What is 12.5 * 3 + 10?", "policy_lookup"
    )
    assert selected == "calculator"


def test_rule_router_handles_ambiguous_short_prompt() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(fake, "help", "policy_lookup")
    assert selected == "none"


def test_rule_router_prefers_policy_lookup_for_process_prompt() -> None:
    fake = phase5_tool_agent.Phase5ToolAgent.__new__(phase5_tool_agent.Phase5ToolAgent)
    selected = phase5_tool_agent.Phase5ToolAgent._route_tool_by_rules(
        fake, "What are the steps for card dispute complaint?", "none"
    )
    assert selected == "policy_lookup"


def test_run_disallows_unknown_tool_from_planner() -> None:
    agent = _build_fake_agent(
        {
            "tool_name": "sql_executor",
            "tool_args": {"query": "drop table users"},
        }
    )

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "status check")

    assert result.planned_tool == "none"
    assert result.tool_status == "not_used"


def test_run_handles_malformed_planner_json_as_no_tool() -> None:
    agent = _build_fake_agent({})

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "I need guidance")

    assert result.planned_tool == "none"
    assert result.tool_status == "not_used"


def test_run_policy_lookup_query_too_long_triggers_safeguard() -> None:
    very_long_query = "q" * 260
    agent = _build_fake_agent(
        {
            "tool_name": "policy_lookup",
            "tool_args": {"query": very_long_query},
        }
    )
    agent.policy_lookup = lambda query: phase5_tool_agent.ToolResult(
        False, "policy_lookup", "", "query_too_long"
    )

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "How do complaints work?")

    assert result.tool_status == "failed"
    assert result.decision == "clarify"
    assert result.reason == "tool_failure_safeguard"


def test_run_calculator_missing_expression_triggers_safeguard() -> None:
    agent = _build_fake_agent(
        {
            "tool_name": "calculator",
            "tool_args": {"expression": ""},
        }
    )
    agent.calculator = lambda expression: phase5_tool_agent.ToolResult(
        False, "calculator", "", f"calculator_error: missing expression ({expression})"
    )

    result = phase5_tool_agent.Phase5ToolAgent.run(agent, "please compute")

    assert result.tool_status == "not_used"
    assert result.decision == "clarify"
    assert result.reason == "missing_calculator_expression"
