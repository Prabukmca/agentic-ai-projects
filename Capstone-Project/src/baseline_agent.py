from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from safety_privacy import redact_pii

@dataclass
class AgentResponse:
    intent: str
    decision: str
    answer: str
    reason: str


class BaselineBankingAgent:
    """Rule/template baseline for Phase 2 (no LLM, no retrieval)."""

    PROHIBITED_PATTERNS = [
        r"\btransfer\b",
        r"\bsend\b.*\bmoney\b",
        r"\bpay\b.*\b(now|immediately)\b",
        r"\bapprove\b",
        r"\bbeneficiary\b",
        r"\bupi\b.*\bpin\b",
    ]

    LEGAL_PATTERNS = [
        r"\blegal\b",
        r"\blawsuit\b",
        r"\bcourt\b",
        r"\bfile a case\b",
    ]

    FRAUD_RISK_PATTERNS = [
        r"\botp\b",
        r"\bscam\b",
        r"\bfraud\b",
        r"\bhacked\b",
        r"\bphishing\b",
    ]

    def respond(self, user_message: str) -> AgentResponse:
        text = user_message.strip()
        lower = text.lower()

        if self._matches_any(lower, self.PROHIBITED_PATTERNS):
            return AgentResponse(
                intent="transaction_or_approval",
                decision="refuse",
                reason="safety_non_transactional",
                answer=(
                    "I cannot perform or assist with money movement, approvals, or credential handling. "
                    "Please use official bank channels (app, branch, or hotline) for transactional requests."
                ),
            )

        if self._matches_any(lower, self.LEGAL_PATTERNS):
            return AgentResponse(
                intent="legal_request",
                decision="refuse",
                reason="safety_no_legal_advice",
                answer=(
                    "I cannot provide legal advice. Please contact the bank's official grievance/legal support "
                    "or a qualified legal professional."
                ),
            )

        if self._matches_any(lower, self.FRAUD_RISK_PATTERNS):
            return AgentResponse(
                intent="fraud_or_high_risk",
                decision="escalate",
                reason="high_risk_signal_detected",
                answer=(
                    "This may be a high-risk fraud scenario. Do not share OTP, PIN, CVV, or passwords. "
                    "Immediately contact your bank's official fraud helpline and block affected cards/accounts."
                ),
            )

        if "block" in lower and "card" in lower:
            return AgentResponse(
                intent="card_block_guidance",
                decision="answer",
                reason="known_template",
                answer=(
                    "To block a lost card: open your bank app and choose Cards > Block/Hotlist, "
                    "or call the official customer care number. After blocking, request replacement "
                    "and review recent transactions."
                ),
            )

        if any(word in lower for word in ["account", "salary", "fees", "charges"]):
            return AgentResponse(
                intent="product_or_fee_guidance",
                decision="answer",
                reason="generic_template",
                answer=(
                    "For account comparison, check monthly balance requirements, debit card charges, ATM limits, "
                    "and branch/service availability. If you share your usage pattern, I can suggest what to compare."
                ),
            )

        return AgentResponse(
            intent="unclear",
            decision="clarify",
            reason="insufficient_context",
            answer=(
                "I need a bit more detail to help. Please share whether your question is about cards, accounts, "
                "fees, disputes, or fraud safety."
            ),
        )

    @staticmethod
    def _matches_any(text: str, patterns: Iterable[str]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)


def sanitize_for_log(text: str) -> str:
    """Redact common PII before writing interaction evidence."""
    return redact_pii(text)


def write_jsonl_log(log_path: Path, rows: list[dict]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def run_demo(log_file: Path) -> list[dict]:
    agent = BaselineBankingAgent()
    prompts = [
        "How can I block my debit card if I lost it?",
        "Can you transfer 50000 to my friend now?",
        "I got a call asking for OTP to avoid account freeze. Should I share it?",
        "Which salary account has low fees?",
        "Please advise legal steps to sue my bank.",
    ]

    rows: list[dict] = []
    for idx, prompt in enumerate(prompts, start=1):
        response = agent.respond(prompt)
        rows.append(
            {
                "run_id": idx,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "user_message": sanitize_for_log(prompt),
                "agent_response": sanitize_for_log(response.answer),
                "decision": response.decision,
                "intent": response.intent,
                "reason": response.reason,
            }
        )

    write_jsonl_log(log_file, rows)
    return rows


def run_interactive() -> None:
    agent = BaselineBankingAgent()
    print("Phase 2 Baseline Banking Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Session ended.")
            break
        if not user_input:
            continue

        response = agent.respond(user_input)
        print(f"Agent [{response.decision}]: {response.answer}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline banking agent.")
    parser.add_argument("--demo", action="store_true", help="Run canned demo and write JSONL log file.")
    parser.add_argument(
        "--log-file",
        default="evidence/logs/phase2_baseline_sample_runs.jsonl",
        help="Path (relative to Capstone-Project) for demo log output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]

    if args.demo:
        log_file = project_root / args.log_file
        rows = run_demo(log_file)
        print(f"Wrote {len(rows)} sample runs to: {log_file}")
        return 0

    run_interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
