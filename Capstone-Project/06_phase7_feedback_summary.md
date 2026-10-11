# Phase 7: Response-Level Feedback and Repair

## Objective
Make feedback visible and useful while keeping adaptation explainable, session-scoped, and subordinate to banking safety and policy evidence.

## User Interaction
Every assistant response has Helpful and Not helpful controls.

- Helpful records the rating and displays a confirmation.
- Not helpful displays an apology and asks for a reason: `incorrect`, `incomplete`, `unclear`, or `not relevant`.
- The user may add a correction and must explicitly select **Retry with feedback** before another answer is generated.
- The original answer remains visible. The retry appears as a separate response and can receive its own feedback.

The retry receives the original question and conversation context, the answer being reviewed, and the selected reason/correction. Feedback is treated as unverified input. The deterministic safety classifier runs before planning or tools, the tool is selected from the original request, and factual corrections must be supported by retrieved policy material. If evidence is insufficient, the assistant should say so instead of presenting the correction as verified.

## Session-Scoped Adaptation
When the user retries with `unclear`, `incomplete`, or `not relevant`, the selected preference may guide later responses in that chat toward plainer language, more detail, or closer relevance. An `incorrect` rating does not make the correction a fact. Preferences live in Streamlit session state and are cleared by **Clear Chat**; they are not shared across sessions or persisted across app restarts. Feedback never changes tool permissions or disables a tool globally.

## Privacy and Evidence
`record_feedback()` appends only timestamp, rating, tool name, and a random response ID to `evidence/logs/phase7_feedback.jsonl`. User messages, assistant responses, selected reasons, and free-text corrections are not written to this feedback log. The nine legacy rows were migrated to remove their text fields while retaining timestamp, rating, and tool name. The Streamlit session still contains the active conversation and correction while the chat is open.

## Tests and Validation
Focused tests in `Capstone-Project/tests/test_phase7_feedback.py` cover:
1. minimized feedback-log fields
2. negative feedback not suppressing policy lookup globally
3. feedback reason, correction, previous answer, and allowed style preferences reaching synthesis
4. OTP-risk content in a correction being escalated before model/tool execution

Latest automated validation: `80 passed, 3 xfailed` across the full Capstone test suite. The focused Phase 5 and Phase 7 suites passed with `52 passed`.

The UI also needs a manual click-through check for rating acknowledgment, reason selection, retry gating, distinct revised output, and Clear Chat reset. No feedback-driven behavior may override safety classification, source grounding, identity boundaries, or the non-transactional scope.

## Limitations
This is a lightweight feedback loop, not model training or persistent personalization. It does not establish that an answer is factually wrong, and it cannot guarantee that a corrected answer will be better when the knowledge base lacks supporting information.
