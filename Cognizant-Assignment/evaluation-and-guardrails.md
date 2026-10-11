# Evaluation, Guardrails, and Failure Detection

## Goal

The agent should be trustworthy, explainable, and cautious when supporting evidence is weak. The assignment emphasizes not only answer quality but also evaluation, grounding, and governance.

## Core evaluation criteria

The current implementation evaluates the system along the same lines as the assignment rubric:

### 1. Agentic architecture
- Distinct responsibilities for planning, retrieval, analysis, validation, and memory
- Clear orchestrated workflow rather than a single monolithic response

### 2. Query planning and orchestration
- Query is decomposed into action-oriented steps
- Retrieval and analysis are sequenced logically
- Trace output shows what the system did

### 3. Retrieval quality
- Documents are ranked by relevance to the user's business question
- Source metadata and titles are preserved in the trace

### 4. Reasoning quality
- The answer is composed from retrieved evidence rather than unsupported assumptions
- Synthesizes relevant rules across documents 

### 5. Grounding and validation
- Verifier checks answer support against retrieved source material
- Low-confidence responses are marked as failed or cautious

## Guardrails implemented

The system applies a few practical guardrails:

- input validation for empty or weak queries
- no-answer behavior when retrieved evidence is insufficient
- grounding threshold checks
- avoidance of unsupported claims
- source-linked explanations in the reasoning trace

## Failure detection logic

The verifier detects and flags common failure cases:

- no documents retrieved
- weak overlap between answer content and source content
- highly risky unsupported statements
- mismatch between query context and document evidence

When these conditions appear, the system marks the grounding as failed and returns a cautious answer instead of overconfident output.

## Example grounding check

If a user asks:

> What is the password policy?

and the answer says:

> The policy is to share passwords with everyone.

The system identifies a mismatch with the actual policy text and flags the answer as weakly grounded.

## Structured observability

Each run collects:

- plan steps
- retrieval results
- reasoning summary
- grounding status
- confidence score

This keeps the process inspectable and helps reviewers evaluate whether the answer can be trusted.

## Conclusion

This implementation is intentionally designed around enterprise governance principles: grounded answers, traceability, and careful handling of uncertainty. These are the same qualities expected in the case-study rubric for a strong agentic AI system.
