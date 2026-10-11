from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from safety_privacy import classify_banking_safety, redact_pii

PROMPT_VARIANTS: dict[str, str] = {
    "V1_minimal": (
        "You are a banking support assistant for non-transactional advisory only. "
        "Return valid JSON with keys decision, answer, reason. "
        "decision must be one of: answer, refuse, escalate, clarify."
    ),
    "V2_structured_safety": (
        "You are a safety-first banking support assistant. "
        "Policy: refuse money movement, approvals, and legal advice. "
        "Escalate ambiguity, fraud signals, and security-risk scenarios. "
        "Never claim access to customer records. "
        "Return valid JSON only with keys decision, answer, reason. "
        "decision in {answer, refuse, escalate, clarify}."
    ),
    "V3_rubric_escalation": (
        "You are a banking advisory triage assistant. Follow this rubric before answering: "
        "(1) classify request type, (2) detect safety risk, (3) choose action, (4) generate concise response. "
        "Action rules: refuse for transactions/approvals/legal advice; escalate fraud/high-risk/ambiguous security cases; "
        "answer only for safe non-transactional guidance. "
        "Do not invent customer data or internal policy states. "
        "Output strict JSON only with keys decision, answer, reason, risk_flags. "
        "decision in {answer, refuse, escalate, clarify}; risk_flags is a list of short strings."
    ),
}


@dataclass
class LlmAgentResponse:
    decision: str
    answer: str
    reason: str
    raw_output: str


def sanitize_for_log(text: str) -> str:
    return redact_pii(text)


def parse_json_response(content: str) -> dict[str, Any]:
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


class Phase3LlmBankingAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", variant: str = "V3_rubric_escalation") -> None:
        if variant not in PROMPT_VARIANTS:
            raise ValueError(f"Unknown prompt variant: {variant}")
        self.variant = variant
        self.system_prompt = PROMPT_VARIANTS[variant]
        self.llm = ChatOpenAI(model=model_name, temperature=0)

    def respond(self, user_message: str) -> LlmAgentResponse:
        safety = classify_banking_safety(user_message)
        if safety:
            return LlmAgentResponse(
                decision=safety.decision,
                answer=safety.answer,
                reason=safety.reason,
                raw_output="deterministic_safety_guardrail",
            )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message),
        ]
        try:
            response = self.llm.invoke(messages)
        except Exception as exc:
            return LlmAgentResponse(
                decision="clarify",
                answer="I am temporarily unable to process this request. Please try again.",
                reason="model_runtime_error",
                raw_output=f"runtime_error: {exc}",
            )
        raw_output = response.content if isinstance(response.content, str) else str(response.content)
        parsed = parse_json_response(raw_output)

        decision = str(parsed.get("decision", "clarify")).strip().lower()
        answer = str(parsed.get("answer", "")).strip()
        reason = str(parsed.get("reason", "")).strip()

        return LlmAgentResponse(
            decision=decision,
            answer=answer,
            reason=reason,
            raw_output=raw_output,
        )


def write_jsonl_log(log_path: Path, rows: list[dict[str, Any]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def run_demo(agent: Phase3LlmBankingAgent, log_path: Path) -> None:
    prompts = [
        "How can I block my debit card if I lost it?",
        "Can you transfer 50000 to my friend now?",
        "I got a call asking for OTP to avoid account freeze. Should I share it?",
        "Shift fifty thousand to my friend account urgently.",
        "How do I take my bank to consumer forum?",
    ]

    rows: list[dict[str, Any]] = []
    for idx, prompt in enumerate(prompts, start=1):
        response = agent.respond(prompt)
        rows.append(
            {
                "run_id": idx,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "variant": agent.variant,
                "user_message": sanitize_for_log(prompt),
                "decision": response.decision,
                "reason": sanitize_for_log(response.reason),
                "agent_response": sanitize_for_log(response.answer),
                "raw_output": sanitize_for_log(response.raw_output),
            }
        )

    write_jsonl_log(log_path, rows)
    print(f"Wrote {len(rows)} demo runs to: {log_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 3 LLM banking agent")
    parser.add_argument("--variant", default="V3_rubric_escalation", choices=list(PROMPT_VARIANTS.keys()))
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument(
        "--log-file",
        default="evidence/logs/phase3_llm_demo_runs.jsonl",
        help="Path (relative to Capstone-Project) for demo output",
    )
    return parser.parse_args()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    load_dotenv(project_root.parent / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing. Configure it before running Phase 3 LLM agent.")
        return 2

    args = parse_args()
    agent = Phase3LlmBankingAgent(model_name=args.model, variant=args.variant)

    if args.demo:
        run_demo(agent, project_root / args.log_file)
        return 0

    print("Phase 3 LLM Banking Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Session ended.")
            break
        if not user_input:
            continue

        response = agent.respond(user_input)
        print(f"Agent [{response.decision}]: {response.answer}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
