# Capstone Project - Complete Flow Diagram

This document explains the implemented Capstone architecture, how the agents connect, how documents become embeddings and a FAISS vectorstore, and how a user question becomes a response.

## 1. Project Purpose

The project implements a non-transactional banking support and advisory agent.

The agent can:
- Explain banking processes using curated knowledge.
- Guide users toward official support channels.
- Calculate safe arithmetic expressions.
- Refuse money movement, approvals, and legal advice.
- Escalate fraud and credential-sharing risks.
- Avoid writing common PII values into evidence logs.

The agent cannot:
- Transfer money.
- Approve payments.
- Access customer accounts.
- Verify identity.
- Provide customer-specific account status.
- Replace an authenticated bank employee or legal professional.

## 2. Current Primary Architecture

The primary application entrypoint is the Streamlit UI:

```mermaid
flowchart LR
    U[Banking customer] --> UI[streamlit_app.py]
    UI --> START[Startup checks]
    START -->|API key and FAISS files available| AGENT[Phase5ToolAgent]
    START -->|Missing prerequisite| ERR[Display setup error]
    AGENT --> SAFETY[safety_privacy.py]
    SAFETY -->|Refuse or escalate| SAFE[Safe response to UI]
    SAFETY -->|Safe request| PLAN[LLM tool planner]
    PLAN --> ROUTER[Deterministic fallback router]
    ROUTER --> CALC[calculator tool]
    ROUTER --> LOOKUP[policy_lookup tool]
    ROUTER --> NONE[No tool]
    CALC --> SYNTH[LLM answer synthesis]
    LOOKUP --> SYNTH
    NONE --> SYNTH
    SYNTH --> GUARD[Tool failure and decision safeguards]
    GUARD --> RESP[AgentResult]
    SAFE --> RESP
    RESP --> UI
    UI --> USER[Response displayed to user]
```

### Primary files

| Layer | File | Responsibility |
|---|---|---|
| UI | `streamlit_app.py` | Chat interface, startup checks, session display, status sidebar |
| Backend | `src/phase5_tool_agent.py` | Current tool-enabled orchestration agent |
| Safety/privacy | `src/safety_privacy.py` | PII redaction and deterministic safety classification |
| Retrieval data | `vectorstore/phase4_banking_faiss/` | Local FAISS index, pickle metadata, manifest |
| Tests | `tests/` | Unit and reliability regression tests |
| Evidence | `evidence/logs/` | PII-sanitized demo and evaluation outputs |

## 3. Application Startup Flow

When the user starts the application, Streamlit executes `streamlit_app.py`.

```mermaid
flowchart TD
    A[Run streamlit_app.py] --> B[Resolve Capstone-Project path]
    B --> C[Add src to Python import path]
    C --> D[Load .env files]
    D --> E{OPENAI_API_KEY exists?}
    E -->|No| X1[Show configuration error and stop]
    E -->|Yes| F{manifest.json, index.faiss, index.pkl exist?}
    F -->|No| X2[Show vectorstore build command and stop]
    F -->|Yes| G[Load manifest summary]
    G --> H[Create cached Phase5ToolAgent]
    H --> I[Initialize Streamlit chat_history]
    I --> J[Render UI and chat input]
```

The index can be created with:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_ingest.py
```

The UI uses Streamlit caching:
- `st.cache_data` caches the manifest summary.
- `st.cache_resource` caches the initialized agent and vectorstore connection, not conversation memory.
- `st.session_state.chat_history` keeps the visible conversation and short-term context for the current UI session.

Before each request, Streamlit passes the previous 20 role-tagged messages from that session to `agent.run`. The agent resolves follow-up tool arguments from the current request and this bounded context, without retaining history on the shared cached resource. **Clear Chat** removes the session's history and therefore resets context. No memory is persisted across chats or users.

## 4. User Request Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Agent as Phase5ToolAgent
    participant Safety as Safety/privacy module
    participant Planner as OpenAI planner
    participant Tool as Selected tool
    participant Model as OpenAI synthesis

    User->>UI: Enter banking question
    UI->>Agent: agent.run(prompt, prior session turns)
    Agent->>Safety: classify_banking_safety(prompt)
    alt Unsafe transaction, approval, or legal request
        Safety-->>Agent: refuse
        Agent-->>UI: AgentResult(refuse)
    else Fraud, OTP, PIN, CVV, or phishing risk
        Safety-->>Agent: escalate
        Agent-->>UI: AgentResult(escalate)
    else Safe request
        Safety-->>Agent: continue
        Agent->>Planner: Plan decision and optional tool
        Planner-->>Agent: JSON tool plan
        Agent->>Agent: Resolve current request using role-tagged context
        Agent->>Agent: Apply deterministic routing to resolved arguments
        Agent->>Tool: Execute at most one allowed tool
        Tool-->>Agent: ToolResult success or failure
        Agent->>Model: Synthesize answer with tool result
        Model-->>Agent: JSON decision, answer, reason
        Agent->>Agent: Apply failure and enum safeguards
        Agent-->>UI: AgentResult
    end
    UI->>UI: Append user and assistant turns to this session's history
    UI-->>User: Display answer, decision, tool, and status
```

## 5. Safety and Privacy Flow

The shared module `src/safety_privacy.py` is used by the baseline, Phase 3, Phase 4, and Phase 5 paths.

```mermaid
flowchart TD
    Q[Incoming text] --> CLASSIFY[classify_banking_safety]
    CLASSIFY --> TX{Money movement, beneficiary, payment, approval?}
    TX -->|Yes| REFUSE1[Refuse transactional action]
    TX -->|No| RISK{OTP, PIN, CVV, phishing, scam, hacked, verification code?}
    RISK -->|Yes| ESCALATE[Escalate to official fraud support]
    RISK -->|No| LEGAL{Lawsuit, sue, legal advice, consumer forum/court?}
    LEGAL -->|Yes| REFUSE2[Refuse legal advice]
    LEGAL -->|No| SAFE[Continue to planner, retrieval, or tool]

    LOG[Text to be persisted] --> REDACT[redact_pii]
    REDACT --> EMAIL[Redact email]
    REDACT --> PHONE[Redact phone]
    REDACT --> PAN[Redact PAN-like value]
    REDACT --> ID[Redact Aadhaar-like and long numeric values]
    EMAIL --> SAFELOG[PII-reduced evidence log]
    PHONE --> SAFELOG
    PAN --> SAFELOG
    ID --> SAFELOG
```

Safety decisions currently implemented:
- `refuse`: transaction execution, fund movement, payment approvals, beneficiary actions, and legal advice.
- `escalate`: OTP, one-time password, PIN/CVV sharing, phishing, scam, hacked account, and verification-code risks.
- `answer` or `clarify`: safe non-transactional guidance or missing-context cases.

The classifier deliberately allows ordinary official grievance/ombudsman process guidance unless the wording explicitly requests legal advice or legal action.

## 6. Tool Planner and Tool Routing

Phase 5 has two tools and a no-tool path.

```mermaid
flowchart TD
    SAFE[Safety check passed] --> P[LLM planner]
    P --> JSON[Parse planner JSON]
    JSON --> FALLBACK[Rule fallback router]
    FALLBACK --> ALLOW{Tool in allowlist?}
    ALLOW -->|No| NO_TOOL[Force tool_name = none]
    ALLOW -->|Yes| SELECT[Select one tool]
    SELECT --> CALC[calculator]
    SELECT --> LOOKUP[policy_lookup]
    SELECT --> NONE[none]
    CALC --> CALL_GUARD[Single-call guard]
    LOOKUP --> CALL_GUARD
    NONE --> CALL_GUARD
    CALL_GUARD --> SYNTH[LLM synthesis]
    SYNTH --> ENUM{Valid decision enum?}
    ENUM -->|No| CLARIFY[Safe clarify fallback]
    ENUM -->|Yes| RESULT[Return AgentResult]
```

### Tool 1: calculator

The calculator is intentionally restricted:
1. Rejects expressions longer than 120 characters.
2. Allows only numeric arithmetic characters.
3. Parses the expression with Python AST.
4. Allows only arithmetic AST nodes.
5. Disables Python built-ins during evaluation.
6. Converts exceptions such as division by zero into a `ToolResult` failure.
7. Converts tool failure into a user-safe `clarify` response.

Example:

```text
User: What is 12.5 * 3 + 10?
Router: calculator
Tool: result=47.5
Agent: The result is 47.5.
```

### Tool 2: policy_lookup

The policy lookup tool:
1. Receives a process or policy query.
2. Searches the local FAISS vectorstore.
3. Returns up to three document snippets and filenames.
4. Catches vectorstore runtime errors.
5. Returns a safe tool failure if the query is too long, unavailable, or unsupported.

Example:

```text
User: How do I block my lost debit card?
Router: policy_lookup
Tool: 03_card_blocking_process.md and related snippets
Agent: Process guidance based on the retrieved policy content.
```

### Tool misuse protection

The agent protects against:
- Unknown planner tools such as `sql_executor`.
- Missing or malformed planner JSON.
- Oversized policy queries.
- Empty calculator expressions.
- Multiple tool loops in one request.
- Tool execution failures.

## 7. Document Ingestion and Embedding Flow

The vectorstore is built offline before the application starts.

```mermaid
flowchart LR
    RAW[data/raw/banking_docs/*.md] --> READ[phase4_ingest.py reads Markdown]
    READ --> META[Extract source metadata]
    META --> SPLIT[RecursiveCharacterTextSplitter]
    SPLIT --> CHUNKS[Text chunks: size 600, overlap 120]
    CHUNKS --> EMBED[OpenAI text-embedding-3-small]
    EMBED --> FAISS[FAISS.from_documents]
    FAISS --> SAVE[index.faiss + index.pkl]
    META --> MANIFEST[manifest.json]
    SAVE --> APP[Phase 4 and Phase 5 agents]
    MANIFEST --> UI[Streamlit knowledge-base sidebar]
```

### Current corpus

- 15 curated Markdown documents.
- Provenance table: `data/raw/document_provenance.csv`.
- Each document contains a title, source URL, last-checked date, use case, and key points.
- Current manifest reports 15 files and 15 chunks because the short documents each fit within the configured chunk size.

### Main source topics

- OTP and phishing safety.
- Digital banking safety.
- Lost card blocking.
- Unauthorized transaction reporting.
- Grievance and ombudsman escalation.
- KYC updates.
- Deposit insurance basics.
- UPI fraud reporting.
- Salary account comparison.
- Card charge disputes.
- Dormant account reactivation.
- PII and data-sharing safety.
- Phishing email red flags.
- Scam-call response.
- Escalation channel matrix.

## 8. Retrieval and RAG Response Flow

Phase 4 direct RAG flow:

```mermaid
flowchart TD
    QUESTION[User question] --> SAFETY[Deterministic safety check]
    SAFETY -->|Unsafe| SAFE_RESPONSE[Refuse or escalate]
    SAFETY -->|Safe| SEARCH[FAISS similarity search]
    SEARCH --> CANDIDATES[Retrieve up to 2k candidates]
    CANDIDATES --> FILTER[Distance threshold <= 1.1]
    FILTER -->|No relevant documents| CLARIFY[Clarify: insufficient knowledge]
    FILTER -->|Relevant documents| CONTEXT[Build context with filenames]
    CONTEXT --> LLM[OpenAI RAG response]
    LLM --> PARSE[Parse JSON response]
    PARSE --> CITATIONS[Append deterministic Sources line]
    CITATIONS --> OUT[Decision + answer + reason]
```

The primary Streamlit UI reaches retrieval through Phase 5 `policy_lookup`. The direct Phase 4 agent remains available as a CLI and evaluation component.

Important distinction:
- Phase 4 direct RAG uses the relevance threshold and deterministic source citations.
- Phase 5 `policy_lookup` currently performs similarity lookup and returns snippets to synthesis but does not yet apply the Phase 4 distance threshold or append citations to the final answer.

## 9. Response Construction

The final response path is:

```mermaid
flowchart LR
    A[Safety result or model/tool result] --> N[Normalize decision]
    N --> F{Tool failed?}
    F -->|Yes| SAFEFAIL[Clarify with safe failure message]
    F -->|No| SOURCE{RAG answer?}
    SOURCE -->|Yes| CITE[Append Sources metadata]
    SOURCE -->|No| DISPLAY[Use answer text]
    CITE --> DISPLAY
    SAFEFAIL --> DISPLAY
    DISPLAY --> UI[Streamlit chat message]
    UI --> META[Decision, tool, tool status metadata]
```

The UI displays:
- Assistant answer.
- Decision: `answer`, `refuse`, `escalate`, or `clarify`.
- Selected tool.
- Tool status.
- Knowledge-base document and source summary in the sidebar.

## 10. Alternative Phase Entry Points

The project contains separate phase agents for demonstration and comparison:

```mermaid
flowchart TD
    P2[baseline_agent.py] --> RULES[Rules and templates]
    P3[phase3_llm_agent.py] --> LLMONLY[LLM prompt variants]
    P3C[phase3_prompt_comparison.py] --> COMPARE[Compare V1, V2, V3]
    INGEST[phase4_ingest.py] --> INDEX[Build FAISS]
    P4[phase4_rag_agent.py] --> RAG[Direct retrieval + LLM]
    P4C[phase4_retrieval_comparison.py] --> METRICS[With vs without retrieval]
    P5[phase5_tool_agent.py] --> TOOLS[Planner + tools + safeguards]
    UI[streamlit_app.py] --> P5
```

These are not separate deployed agents. They are phase-specific implementations and evaluation entrypoints that show how the system evolved.

## 11. Evidence and Testing Flow

```mermaid
flowchart LR
    DEMO[Phase demo scripts] --> LOGS[evidence/logs/*.jsonl]
    COMP[Comparison runners] --> SUMMARY[evidence/logs/*summary.json]
    TESTS[pytest tests] --> STATUS[Test pass/fail result]
    SOURCES[Raw docs + provenance] --> MANIFEST[Vectorstore manifest]
    LOGS --> REPORT[04_evaluation_report.md]
    SUMMARY --> REPORT
    STATUS --> REPORT
```

Current automated test groups:
- `test_baseline_agent.py`: Phase 2 decisions and legacy adversarial cases.
- `test_phase5_tools.py`: calculator, routing, misuse, and tool-failure safeguards.
- `test_safety_privacy.py`: PII redaction and safety classifier.
- `test_reliability_hardening.py`: runtime fallback, retrieval threshold, citations, and vectorstore failure.

Latest recorded full-suite result:

```text
44 passed, 3 xfailed
```

The three expected failures are legacy baseline keyword-matching gaps preserved as evidence of the original baseline limitations.

## 12. Folder and File Map

```text
Capstone-Project/
|-- streamlit_app.py                         Primary Streamlit application
|-- README.md                                Setup and run instructions
|-- requirement-spec.md                      Assignment requirements
|-- ReadMe-Flow-Diagram.d                   This architecture and flow document
|-- 01_problem_framing.md                    Phase 1 problem and safety contract
|-- 02_demo_script.md                        Phase 2 demo and limitation evidence
|-- 03_prompt_comparison.md                  Phase 3 prompt strategy results
|-- 04_evaluation_report.md                  Interim evaluation and hardening notes
|-- 05_engineering_justification.md          Reserved engineering rationale
|-- src/
|   |-- baseline_agent.py                    Phase 2 rules/templates
|   |-- safety_privacy.py                    Shared PII and safety controls
|   |-- phase3_llm_agent.py                  Phase 3 LLM agent
|   |-- phase3_prompt_comparison.py          Phase 3 prompt evaluation
|   |-- phase4_ingest.py                     Document embedding and FAISS build
|   |-- phase4_rag_agent.py                  Direct RAG agent
|   |-- phase4_retrieval_comparison.py       RAG evaluation
|   |-- phase5_tool_agent.py                 Active planner/tool backend
|-- data/
|   |-- raw/banking_docs/                    Curated source notes
|   |-- raw/document_provenance.csv          Source registry
|   |-- processed/                           Reserved processed-data output
|-- vectorstore/
|   |-- phase4_banking_faiss/
|       |-- index.faiss                     FAISS vector index
|       |-- index.pkl                        Metadata/docstore artifact
|       |-- manifest.json                    Corpus summary
|-- evidence/
|   |-- logs/                               JSONL and JSON evaluation evidence
|   |-- screenshots/                        Reserved UI evidence output
|-- tests/                                   Automated tests
```

## 13. Complete End-to-End Summary

```mermaid
flowchart TD
    DOCS[15 curated banking documents] --> INGEST[phase4_ingest.py]
    INGEST --> EMBEDDINGS[OpenAI embeddings]
    EMBEDDINGS --> INDEX[FAISS index + metadata]
    INDEX --> STARTUP[Streamlit startup]
    KEY[OPENAI_API_KEY] --> STARTUP
    STARTUP --> CHAT[User enters question]
    CHAT --> SAFETY[Shared safety classifier]
    SAFETY -->|Refuse/escalate| RESPONSE[Safe response]
    SAFETY -->|Continue| PLANNER[LLM tool planner]
    PLANNER --> ROUTER[Rule fallback + allowlist]
    ROUTER --> CALCULATOR[Calculator]
    ROUTER --> POLICY[Policy lookup]
    POLICY --> INDEX
    CALCULATOR --> SYNTHESIS[LLM answer synthesis]
    POLICY --> SYNTHESIS
    SYNTHESIS --> FAILURE[Failure and decision safeguards]
    FAILURE --> RESPONSE
    RESPONSE --> UI[Streamlit displays answer]
    UI --> USER[User]
    RESPONSE --> REDACT[PII redaction for persistent logs]
    REDACT --> EVIDENCE[evidence/logs]
```

## 14. Remaining Planned Work

The architecture above describes the current implementation. The following assignment phases remain incomplete or partial:

- Phase 6: multi-step planning, conversation memory, retention, and reset behavior.
- Phase 7: cross-session feedback learning and persistent personalization. Current feedback repair and adaptation are session-scoped only.
- Phase 8: deployment packaging, latency metrics, tracing, persistent error telemetry, and production logging policy.
- Phase 9: complete evaluation harness, quality consistency metrics, root-cause analysis, and final improvement roadmap.

Known implementation follow-ups:
- Apply Phase 4 relevance filtering and deterministic citations inside Phase 5 `policy_lookup`.
- Add Streamlit UI tests and screenshot evidence.
- Avoid retaining raw user text in UI session state if strict PII minimization is required.
- Replace trusted-local `allow_dangerous_deserialization=True` with a controlled artifact verification strategy for deployment.
- Complete [05_engineering_justification.md](05_engineering_justification.md).
