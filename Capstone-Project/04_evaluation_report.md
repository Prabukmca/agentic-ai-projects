# Evaluation Report

## Phase 4 Interim Evaluation: Retrieval Impact

### Objective
Measure response-quality and grounding change with retrieval enabled versus disabled, using the same prompt set.

### Artefacts
- Run rows: `evidence/logs/phase4_retrieval_comparison_runs.jsonl`
- Summary: `evidence/logs/phase4_retrieval_comparison_summary.json`
- Corpus provenance: `data/raw/document_provenance.csv`

### Test Set
6 prompts covering:
- Lost card guidance
- Transaction refusal
- OTP fraud escalation
- Charge dispute details
- Complaint escalation path
- Missing-information case (exact 2026 dormant-account penalty slab)

### Scorecard
| Mode | Total Cases | Decision Accuracy | Groundedness Alignment |
|---|---:|---:|---:|
| With Retrieval | 6 | 0.667 | 0.667 |
| Without Retrieval | 6 | 0.333 | 0.333 |

### Key Observations
- Retrieval improved decision accuracy from 0.333 to 0.667.
- Retrieval improved groundedness alignment from 0.333 to 0.667.
- The stricter relevance filter lowers apparent accuracy versus the earlier run, but prevents unsupported answers from being treated as grounded.

### Failure Analysis (Phase 4)
1. Missing-info decision label mismatch
- Case: exact dormant-account penalty slab in 2026.
- Observed: response text correctly said insufficient information, but decision label was `refuse` instead of expected `clarify`.

2. Groundedness metric inflation for policy-only refusals
- For pure safety refusals, retrieval may still return unrelated chunks and mark `grounded=true`, reducing alignment precision.

### Root Causes
- Decision taxonomy instruction in the system prompt does not explicitly map "insufficient context" to `clarify`.
- Current groundedness proxy is retrieval-presence-based, not citation-quality-based.

### Implemented Reliability Fixes
- Added similarity-score threshold before a retrieved chunk is treated as usable context.
- Unsupported factual queries now return `clarify` with an insufficient-context response.
- Source citations are appended deterministically from retrieved file metadata.
- Groundedness now requires both retrieved context and a Sources citation.
- Added runtime fallbacks for LLM calls and policy lookup/vector-store errors.

### Interim Conclusion
Phase 4 integration shows measurable improvement over non-retrieval behavior and is ready to carry forward into Phase 5 tool-calling enhancements.

## Phase 5 Interim Evaluation: Tool Usage and Safeguards

### Objective
Validate tool selection, execution, and guardrails for a tool-enabled banking assistant.

### Tooling Scope
- Tool 1: calculator (safe arithmetic evaluator)
- Tool 2: policy_lookup (retrieval-backed policy/process snippet lookup)

### Artefacts
- Run rows: `evidence/logs/phase5_tool_usage_runs.jsonl`
- Tests: `tests/test_phase5_tools.py`

### Observed Demo Outcomes (6 Runs)
- Successful calculator call for arithmetic request.
- Successful policy_lookup calls for process guidance requests.
- Safety shortcut refusal for transaction request.
- Safety shortcut escalation for OTP-risk request.
- Failed calculator call demonstrated (`10/0`) and mitigated by safeguard response (`decision=clarify`, `reason=tool_failure_safeguard`).

### Safeguards Implemented
1. Allowed-tool guardrail (`calculator`, `policy_lookup`, `none`).
2. Input validation guardrail for calculator expressions.
3. Single-step loop prevention (max one tool call per request path).
4. Safety pre-routing that blocks transaction/legal/fraud-risk misuse before tools.
5. Tool-failure fallback response with safe user guidance.
6. Deterministic fallback router for ambiguous planner outputs.
7. Implicit arithmetic detection (math routing without explicit "calculate/compute" keyword).
8. Legal-adjacent keyword hardening (`consumer forum`) in safety shortcut.

### Test Status
- `16 passed` for Phase 5 tool, routing, and misuse tests.

### Additional Negative/Misuse Coverage
- Unsupported planner-selected tool is reduced to `none` by the allowlist.
- Malformed/empty planner output safely defaults to no tool.
- Oversized policy lookup query triggers the tool-failure safeguard.
- Missing calculator expression triggers the tool-failure safeguard.

### Interim Conclusion
Phase 5 implementation is started with required tool usage, failed tool-call evidence, and foundational safeguards in place.

## Phase 5 Loan and EMI Calculation Enhancement

### Capability
Phase 5 now includes a dedicated validated `loan_calculator` path for estimate-only calculations. It supports a principal or loan amount, annual interest rate, tenure in months or years, and monthly payment frequency. The result includes monthly EMI, total repayment, and total interest using the standard reducing-balance formula. Zero-interest loans use principal divided by the number of months.

### Routing and Clarification Behavior
- Complete loan/EMI requests are routed to `loan_calculator`, never to the arithmetic calculator.
- Successful loan estimates are rendered as Markdown bullets with labeled amount, rate, tenure, frequency, EMI, total repayment, and total interest fields, including thousands separators.
- Incomplete requests do not invoke a tool or invent planner arguments. For example, `Will you do loan interest calculation?` returns: `Yes. Please provide the loan amount, annual interest rate, tenure, and payment frequency. I can provide an estimate only.`
- The planner contract requires strict JSON and forbids placeholders such as `...`, `TBD`, and `unknown` in tool arguments.
- Invalid, negative, non-numeric, or unsupported-frequency inputs receive a safe validation response without exposing Python exceptions.
- This remains an estimate only and does not provide financial, legal, approval, or transaction advice.

### Sample Prompt
`Calculate the monthly EMI for a loan of ₹500,000 at 8.5% annual interest for 5 years with monthly payments. Show the EMI, total repayment, and total interest. This is an estimate only.`

### Test Evidence
Focused Phase 5 validation: `29 passed` in `tests/test_phase5_tools.py`, covering valid EMI and zero-interest calculations, missing loan inputs, invalid values, placeholder rejection, incomplete-request clarification, complete-loan routing, no-percent annual-rate parsing, formatted Markdown output, and unchanged arithmetic behavior. The full Capstone suite was run after this focused check.

## Safety and Privacy Hardening Update

### Objective
Address cross-phase deviations identified in the audit: incomplete PII redaction and non-deterministic safety handling.

### Implemented Changes
1. Added shared module: `src/safety_privacy.py`.
2. Centralized PII redaction (`redact_pii`) and applied it to baseline, Phase 3, Phase 4, and Phase 5 logging paths.
3. Added deterministic safety classifier (`classify_banking_safety`) and integrated it into:
	- Phase 3 LLM response path
	- Phase 4 RAG response path
	- Phase 5 tool-agent safety shortcut path
4. Expanded regression tests for privacy/safety adversarial phrases.

### Validation
- Full capstone test suite result: `40 passed, 3 xfailed`.
- New tests added: `tests/test_safety_privacy.py`.

### Notes
- The 3 xfailed tests remain intentionally marked from baseline adversarial expectations pre-upgrade and are unchanged.

## Retrieval and Runtime Hardening Update

### Validation
- New reliability regression tests: `tests/test_reliability_hardening.py`.
- Full capstone test suite after hardening: `44 passed, 3 xfailed`.

### Covered Behaviors
- Phase 3 model-runtime fallback.
- Phase 4 relevance threshold for retrieved chunks.
- Phase 4 deterministic source citation injection.
- Phase 5 policy lookup runtime fallback.

## Phase 7 Feedback Repair Update

### Implemented Behavior
- Thumbs-down now opens a response-specific reason and optional correction flow; the user explicitly requests a retry.
- Retry passes the previous answer and feedback to synthesis as unverified context while preserving original-request routing and deterministic safety checks.
- Session-scoped style preferences can guide later turns and are removed by Clear Chat.
- Feedback logs now contain only timestamp, rating, tool name, and response ID; user/assistant text and free-text corrections are not persisted in this log.
- Removed cached tool-wide suppression after repeated negative ratings so one user's feedback cannot disable a tool for unrelated requests.

### Validation
- Focused Phase 5 and Phase 7 suites: `52 passed`.
- Full Capstone suite: `80 passed, 3 xfailed`.
- Manual Streamlit click-through remains outstanding; backend retry, privacy, and safety behavior are covered by automated tests.
