# Capstone Project: AI Banking Support and Advisory Agent

## Scope
This project implements an industry-style AI agent for **banking support and advisory (non-transactional)**.

The agent must:
- Refuse money movement, approvals, and legal advice
- Avoid hallucinating customer data
- Escalate ambiguous or high-risk cases
- Avoid storing PII in logs

## Phase Plan
- Phase 1: Problem framing, safety contract, success criteria, edge cases
- Phase 2: Baseline Python agent (rules/templates) with limitations
- Phase 3: LLM integration and prompt strategy comparison
- Phase 4: Retrieval augmentation (embeddings + vector store)
- Phase 5: Tool usage and safeguards
- Phase 6: Planning + memory behavior
- Phase 7: Adaptive behavior from feedback
- Phase 8: Deployment readiness and observability
- Phase 9: Evaluation and engineering review

## Artefacts
- `ReadMe-Flow-Diagram.d` - complete architecture, data, agent, retrieval, response, testing, and phase flow diagrams
- `01_problem_framing.md` - Phase 1 output
- `02_demo_script.md` - demo interactions and expected behavior
- `03_prompt_comparison.md` - prompt strategy experiment table
- `04_evaluation_report.md` - metrics, failure analysis, improvements
- `05_engineering_justification.md` - design and tradeoff rationale

## Project Structure
- `src/` - agent source code
- `tests/` - automated tests and harnesses
- `data/raw/` - downloaded source documents with provenance notes
- `data/processed/` - cleaned/chunked text outputs
- `vectorstore/` - embedding index storage
- `evidence/logs/` - interaction logs and evaluation traces
- `evidence/screenshots/` - UI screenshots and demo evidence

## Current Status
- Phase 1 completed (problem framing and safety contract)
- Phase 2 completed: baseline Python agent implemented with adversarial paraphrase tests
- Phase 3 completed: LLM integration, prompt comparison, and default prompt selection
- Phase 4 completed: curated corpus, FAISS ingestion, RAG agent, and retrieval comparison logs generated
- Phase 5 started: tool-enabled agent with safeguards and failed tool-call evidence
- Streamlit UI implemented as the primary application entrypoint
- Sample interaction logs generated under evidence/logs

## Setup
Run all commands below from the repository root (`Assignment-3`).

1. Activate the existing virtual environment:

```powershell
& d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/Activate.ps1
```

2. Create a `.env` file in the repository root or in `Capstone-Project` with:

```text
OPENAI_API_KEY=your_openai_api_key
```

3. Build the local FAISS index before running retrieval or tool-enabled modes:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_ingest.py
```

## Run The Application
The primary application is now a Streamlit UI backed by the hardened Phase 5 agent.

### Primary: Streamlit Banking Advisory UI

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m streamlit run Capstone-Project/streamlit_app.py
```

What this UI provides:
- chat interface over the Phase 5 tool-enabled agent
- deterministic banking safety checks
- retrieval-backed policy guidance
- sidebar visibility into safety contract and knowledge base summary

If startup checks fail in UI, it will show exact missing prerequisites (API key / vectorstore files).

### Alternate: Terminal Agent Modes
Type `exit` to end an interactive terminal session.

### Recommended: Tool-Enabled Banking Agent

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase5_tool_agent.py
```

This mode provides:
- deterministic banking safety checks
- calculator tool for safe arithmetic
- loan EMI calculator for numeric loan estimates
- loan process lookup for personal/home loan eligibility and application guidance
- ATM usage and safety lookup for withdrawal limits and ATM security guidance
- online transfer limit lookup for UPI/IMPS/NEFT/RTGS caps and daily thresholds
- foreign transfer fee lookup for remittance charges and FX cost considerations
- policy lookup tool backed by the FAISS knowledge base
- PII-safe evidence logging when demo mode is used

Note: the FAISS index must be rebuilt when new banking documents are added. In the current environment, OpenAI re-embedding and ingestion is blocked by a billing/quota issue (`429 credit_balance_exhausted`), so the vector store cannot be rebuilt until the OpenAI account has available credits.

Run its scripted demo and write an evidence log:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase5_tool_agent.py --demo
```

### Retrieval-Only Banking Agent

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_rag_agent.py
```

### LLM-Only Banking Agent

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase3_llm_agent.py
```

## Run Tests
Run all Capstone tests:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests -q
```

Run a specific test group:

```bash
# Baseline and adversarial safety tests
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_baseline_agent.py -q

# Tool routing, misuse, and safeguard tests
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_phase5_tools.py -q

# PII redaction and deterministic banking safety tests
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_safety_privacy.py -q

# Retrieval relevance, source citation, and runtime fallback tests
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_reliability_hardening.py -q
```

## Phase 2 Quick Run
From repository root:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/baseline_agent.py --demo
```

This generates:
- `Capstone-Project/evidence/logs/phase2_baseline_sample_runs.jsonl`

Run tests:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_baseline_agent.py -q
```

## Phase 3 Quick Run
Run prompt strategy comparison:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase3_prompt_comparison.py
```

This generates:
- `Capstone-Project/evidence/logs/phase3_prompt_comparison_runs.jsonl`
- `Capstone-Project/evidence/logs/phase3_prompt_comparison_summary.json`

Run LLM demo with selected prompt variant:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase3_llm_agent.py --demo
```

This generates:
- `Capstone-Project/evidence/logs/phase3_llm_demo_runs.jsonl`

## Phase 4 Quick Run
Build embeddings and FAISS index from curated corpus:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_ingest.py
```

This generates:
- `Capstone-Project/vectorstore/phase4_banking_faiss/index.faiss`
- `Capstone-Project/vectorstore/phase4_banking_faiss/manifest.json`

Run retrieval comparison (with vs without retrieval):

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_retrieval_comparison.py
```

This generates:
- `Capstone-Project/evidence/logs/phase4_retrieval_comparison_runs.jsonl`
- `Capstone-Project/evidence/logs/phase4_retrieval_comparison_summary.json`

Run interactive RAG agent:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase4_rag_agent.py
```

## Phase 5 Quick Run
Run tool-enabled demo (calculator + policy + banking process tools):

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe Capstone-Project/src/phase5_tool_agent.py --demo
```

This generates:
- `Capstone-Project/evidence/logs/phase5_tool_usage_runs.jsonl`

Available Phase 5 tools:
- `calculator` for safe arithmetic
- `loan_calculator` for EMI and repayment estimation
- `loan_process_lookup` for personal/home loan application guidance
- `atm_usage_lookup` for ATM usage, safety, and limits
- `transfer_limit_lookup` for online transfer ceilings
- `foreign_transfer_fee_lookup` for foreign remittance costs and FX considerations
- `policy_lookup` for general banking process guidance
- `none` for safe no-tool fallback when no action is needed

Run Phase 5 tests:

```bash
d:/Technicals/Emeritus/Assignment-3/.venv/Scripts/python.exe -m pytest Capstone-Project/tests/test_phase5_tools.py -q
```
