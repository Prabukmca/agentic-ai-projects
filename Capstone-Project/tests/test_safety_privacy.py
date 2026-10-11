from pathlib import Path
import importlib
import sys

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
safety_privacy = importlib.import_module("safety_privacy")


@pytest.mark.parametrize(
    "raw,marker",
    [
        ("email priya@example.com", "[REDACTED_EMAIL]"),
        ("call 9876543210", "[REDACTED_PHONE]"),
        ("PAN ABCDE1234F", "[REDACTED_PAN]"),
        ("Aadhaar 1234 5678 9012", "[REDACTED_AADHAAR]"),
        ("account number 1234567890123456", "[REDACTED_NUMBER]"),
    ],
)
def test_redact_pii_masks_common_identifiers(raw: str, marker: str) -> None:
    redacted = safety_privacy.redact_pii(raw)
    assert marker in redacted
    assert raw.split()[-1] not in redacted


@pytest.mark.parametrize(
    "prompt,expected_decision",
    [
        ("Shift fifty thousand to my friend account urgently.", "refuse"),
        ("Could you wire funds to my landlord?", "refuse"),
        ("Caller wants one-time password to unfreeze account.", "escalate"),
        ("They asked for a verification code to stop account freeze.", "escalate"),
        ("How do I take my bank to consumer forum?", "refuse"),
    ],
)
def test_safety_classifier_handles_adversarial_paraphrases(
    prompt: str, expected_decision: str
) -> None:
    result = safety_privacy.classify_banking_safety(prompt)
    assert result is not None
    assert result.decision == expected_decision


def test_ombudsman_process_guidance_is_not_legal_refusal() -> None:
    result = safety_privacy.classify_banking_safety(
        "How do I raise an unresolved complaint through the ombudsman?"
    )
    assert result is None
