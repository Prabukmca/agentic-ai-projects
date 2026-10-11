# Engineering and Product Justification

## Scenario and User Need
The project targets customers seeking general banking-process and product guidance. It is deliberately non-transactional: the assistant can explain processes and estimate loan repayments, but cannot move money, approve products, or act on customer accounts. This scope makes the agent useful while limiting the impact of incorrect or unauthorized actions.

## Architecture and Framework Choices
The interface uses Streamlit because it supports a small, interactive chat application with session state and a simple local run workflow. LangChain integrations provide the OpenAI chat model, message abstractions, embeddings, and FAISS vector-store adapter. FAISS keeps the curated document index local to the project.

The agent orchestration is custom Python rather than a full agent framework. The model proposes a tool using a JSON prompt contract; deterministic routing rules, an allowlist, input validation, and a single-tool execution path control what actually runs. This keeps routing and failure behavior inspectable and testable. The tradeoff is that the planner contract is prompt-based rather than a provider-enforced structured tool schema, so parsing and deterministic checks remain necessary.

## Safety and Escalation
`src/safety_privacy.py` applies deterministic checks before model planning or tool execution. Money movement and approval requests are refused, security-risk requests such as OTP sharing are escalated, and legal-advice requests are refused. Tool allowlisting, validated calculator inputs, and the one-call limit reduce the risk of unsafe or repeated actions. The assistant is advisory only and must direct customers to official bank channels for account-specific or high-risk issues.

## Retrieval and Data Freshness
Banking guidance is curated in Markdown under `data/raw/banking_docs/`, with provenance tracked in `data/raw/document_provenance.csv`. `src/phase4_ingest.py` chunks and embeds these documents into the local FAISS index in `vectorstore/phase4_banking_faiss/`; the lookup tools retrieve relevant snippets for answer synthesis.

This design grounds answers in project-controlled material, but it does not guarantee that a policy is current or applicable to every bank. Document owners must verify sources and dates, update the corpus, and rebuild the index when policies change. If retrieval is unavailable or insufficient, the agent should clarify or direct the user to official support rather than invent policy details.

## Memory, Privacy, and Observability
Conversation context is short-term and bounded to recent turns passed by the UI; Clear Chat removes that session's history and feedback preferences. Feedback is attached to a specific response and can guide an explicit retry plus limited style preferences in the current chat. It is not persistent user memory, shared across users, or model training. Feedback logs store only timestamp, rating, tool name, and a random response ID; this minimization does not replace access controls or a production data-retention policy.

Evaluation and troubleshooting evidence is stored under `evidence/logs/`, with behavior covered by tests under `tests/`. This supports repeatable local validation, but is not a centralized production tracing or monitoring system.

## Deployment Assumptions and Limitations
The app requires a valid OpenAI API key with available quota and a compatible local FAISS index. LLM and embedding calls depend on external service availability and billing. The current design is intended for a capstone demonstration, not production banking use: it has no authenticated customer identity, live bank-system integration, human-agent console, managed secrets service, or guaranteed policy-update pipeline. It must not be used to execute transactions or provide individualized financial, legal, or credit-approval advice.
