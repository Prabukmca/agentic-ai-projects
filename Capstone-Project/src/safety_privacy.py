from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    decision: str
    answer: str
    reason: str


def redact_pii(text: str) -> str:
    """Redact common identifiers before text is persisted to evidence logs."""
    redacted = text
    patterns = [
        (r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]"),
        (r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b", "[REDACTED_PHONE]"),
        (r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b", "[REDACTED_AADHAAR]"),
        (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[REDACTED_PAN]"),
        (r"\b\d{10,18}\b", "[REDACTED_NUMBER]"),
        (r"\b(?:account|acct|a/c)\s*(?:number|no)?\s*[:#-]?\s*\d[\d\s-]{5,}\b", "[REDACTED_ACCOUNT]"),
    ]
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    return redacted


def classify_banking_safety(message: str) -> SafetyDecision | None:
    """Apply deterministic banking guardrails before model or tool execution."""
    text = message.lower()

    loan_calculation_terms = [
        "loan",
        "emi",
        "equated monthly installment",
        "interest",
        "tenure",
        "mortgage",
        "calculate",
        "calculator",
    ]
    transaction_patterns = [
        r"\btransfer\b",
        r"\bsend\s+(?:\w+\s+){0,2}money\b",
        r"\bshift\s+(?:\w+\s+){0,3}(?:to|into)\b",
        r"\bmove\s+(?:\w+\s+){0,3}(?:funds|money)\b",
        r"\bwire\s+(?:\w+\s+){0,3}(?:money|funds)?\b",
        r"\bapprove\s+(?:\w+\s+){0,2}(?:payment|transaction)\b",
        r"\badd\s+(?:a\s+)?beneficiary\b",
        r"\bmake\s+(?:a\s+)?payment\b",
    ]
    if any(re.search(pattern, text) for pattern in transaction_patterns) and not any(
        term in text for term in loan_calculation_terms
    ):
        return SafetyDecision(
            decision="refuse",
            answer="I cannot perform or assist with money movement, payment approvals, or beneficiary actions.",
            reason="safety_non_transactional",
        )

    fraud_terms = [
        "otp",
        "one-time password",
        "one time password",
        "phishing",
        "scam",
        "hacked",
        "share my pin",
        "share my cvv",
        "verification code",
    ]
    if any(term in text for term in fraud_terms):
        return SafetyDecision(
            decision="escalate",
            answer=(
                "This may be a high-risk security scenario. Do not share OTP, PIN, CVV, passwords, "
                "or verification codes. Contact official bank fraud support immediately."
            ),
            reason="high_risk_security",
        )

    legal_terms = [
        "lawsuit",
        "sue",
        "legal advice",
        "consumer court",
        "consumer forum",
        "legal action",
    ]
    if any(term in text for term in legal_terms):
        return SafetyDecision(
            decision="refuse",
            answer=(
                "I cannot provide legal advice. Please use official bank grievance channels "
                "or consult a qualified legal professional."
            ),
            reason="safety_legal_refusal",
        )

    return None
