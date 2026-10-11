# Enterprise Knowledge Ops Agent

This project implements a local enterprise knowledge assistant for the Cognizant case study. It combines policy retrieval, multi-agent reasoning, source-grounded analysis, and a Streamlit interface for interactive business Q&A.

## Quick Start (< 2 minutes)

```powershell
# 1. Activate the virtual environment
& 'd:\Technicals\Emeritus\Assignment-3\.venv\Scripts\Activate.ps1'

# 2. Run the Streamlit app
streamlit run app.py

# 3. Open http://localhost:8501 in your browser
```

Then ask a question like *"What is the policy on remote work?"* or *"Can I get reimbursed for travel meals?"*

## Overview

The application is built around a lightweight enterprise workflow:

- Planner: breaks the question into reasoning steps
- Retriever: finds the most relevant policy documents
- Analyst: synthesizes the answer from retrieved evidence
- Verifier: checks whether the answer is grounded in source material
- Memory: preserves recent context across turns

The app is designed to answer questions about governance, compliance, ethics, HR, and corporate policies using local PDFs from the project document folder.

## Current implementation

The current version includes:

- local PDF ingestion from the `documents` folder
- document deduplication and metadata tracking
- FAISS vectorstore creation and reuse when an OpenAI API key is configured
- LLM-assisted reasoning when available
- fallback keyword-based retrieval when the LLM/vectorstore path is unavailable
- clear UI status for `vectorstore active` vs `fallback mode`
- citation-aware reasoning and grounding checks
- a Streamlit chat interface for testing the agent end-to-end
- **multi-source answer aggregation**: when multiple documents contain relevant info, all are synthesized with proper source attribution

### Multi-Source Answer Aggregation

When multiple documents contain relevant information for a question:

- The agent retrieves **5-6 documents** instead of just the top 1-2
- **All matching documents** are processed and their answers combined
- **Duplicate answers** are intelligently deduplicated while preserving **source attribution**
- Each answer point shows **all contributing sources**

Example output from the agent:
```
1. The policy allows remote work up to three days per week, subject to manager approval and business needs.
   📄 Source: HR Remote Work Policy, Compliance Guidelines

2. Meals are reimbursable only for overnight travel or when business-approved.
   📄 Source: Travel Policy, Expense Guidelines
```

Retrieval parameters:
- **Keyword-based fallback**: retrieves k=5 documents
- **Vectorstore LLM mode**: retrieves k=6 documents
- **Synthesis**: all scoring documents contribute to the final answer, not just the highest-ranked one

## Agent Architecture

The system orchestrates five specialized agents that work together in a fixed pipeline:

### 1. **Memory Agent**
- Maintains conversation history across turns
- Provides context for subsequent queries
- Keeps the last 5 Q&A pairs for reference

### 2. **Planning Agent**
- Analyzes the incoming question
- Generates a step-by-step execution plan
- Identifies special reasoning needs (e.g., comparisons, policy combinations)
- Plan is logged in the reasoning trace for explainability

### 3. **Retriever Agent**
Has two operating modes depending on environment:

- **Vectorstore Mode** (when OPENAI_API_KEY is configured)
  - Uses FAISS local vector index
  - Performs semantic similarity search via OpenAI embeddings
  - Expands queries with synonyms for broader coverage
  - Retrieves top-4 relevant document chunks

- **Fallback Mode** (no API key or no vectorstore)
  - Token-based keyword matching
  - Title and content overlap scoring
  - Domain-specific boosts for key terms (remote, travel, reimburse, meal)
  - Retrieves top-2 documents

### 4. **Analyst Agent**
Has two reasoning paths:

- **LLM Mode** (when vectorstore is active)
  - Uses GPT-4o-mini for grounded synthesis
  - Reasons directly over retrieved document chunks
  - Includes system prompt to prevent hallucination
  - Rephrases both questions and answers for clarity

- **Fallback Mode** (no vectorstore)
  - Pattern-matching based on domain rules
  - Looks for specific keywords (remote, travel, retention, etc.)
  - Falls back to extracting first sentence from best-matching document
  - No LLM cost, purely local inference

### 5. **Verifier Agent**
- Checks if the answer is grounded in source material
- Computes grounding score via:
  - Lexical overlap (answer tokens vs source tokens)
  - Semantic boost for related terms
  - Keyword penalty for unsupported claims (share, all, guarantee, etc.)
- Threshold: 0.35 (can be tuned)
- Returns status: `passed` or `failed` with confidence score

### Execution Pipeline

```
Question
   ↓
Memory Agent (get context)
   ↓
Planning Agent (create plan)
   ↓
[Vectorstore available?]
   ├─→ YES: Retriever (vectorstore + semantic search)
   │        ↓
   │        Analyst (LLM synthesis)
   │
   └─→ NO: Retriever (keyword matching)
          ↓
          Analyst (pattern matching)
   ↓
Verifier (grounding check)
   ↓
Memory Agent (store result)
   ↓
Return Answer + Trace
```

### Trace Output
Every response includes a detailed trace with:
- **Plan**: reasoning steps generated by planner
- **Agent Sequence**: ["planner", "retriever", "analyst", "verifier"]
- **Retrieval**: list of matched documents with scores
- **Reasoning**: answer, citations, and synthesis notes
- **Grounding**: pass/fail status with confidence score (0-1)

## Project structure

- `enterprise_knowledge_ops_agent.py` - main agent logic, retrieval, verification, and local vectorstore handling
- `app.py` - Streamlit dashboard and chat UI
- `test_agentic_knowledge_ops.py` - regression checks for planning and grounding behavior
- `documents/` - source PDF policy documents
- `enterprise_vectorstore/` - local FAISS index created at runtime
- `Agentic_AI_Developer_Case_Study.md` - assignment brief and scoring guidance

## Packages to install for this assignment

The current implementation depends on the following Python packages:

```bash
pip install streamlit python-dotenv openai langchain langchain-openai langchain-community langchain-text-splitters faiss-cpu pymupdf pypdf
```

If you want to install the project requirements in one step, use:

```bash
pip install -r requirements.txt
```

### Why these packages are needed

- `streamlit` - user interface
- `python-dotenv` - loads environment variables from `.env`
- `openai` - OpenAI SDK used for LLM calls
- `langchain` - orchestration and document-processing helpers
- `langchain-openai` - chat and embedding integrations
- `langchain-community` - PDF loaders and FAISS integration
- `langchain-text-splitters` - chunking documents for retrieval
- `faiss-cpu` - local vector search / indexing
- `pymupdf` and `pypdf` - PDF extraction support

## Environment setup

1. Create and activate a virtual environment.
2. Install the packages above.
3. Add your OpenAI API key in a `.env` file in the project root or in the same folder as the app.

Example `.env`:

```env
OPENAI_API_KEY=your_key_here
```

## Run the app

From the project folder:

```powershell
Set-Location -Path 'D:\Technicals\Emeritus\Assignment-3\Cognizant-Assignment'
& 'd:\Technicals\Emeritus\Assignment-3\.venv\Scripts\streamlit.exe' run app.py --server.headless true --server.port 8501

 Set-Location -Path 'D:\Technicals\Emeritus\Assignment-3\Cognizant-Assignment'; & 'd:\Technicals\Emeritus\Assignment-3\.venv\Scripts\streamlit.exe' run app.py --server.headless true --server.port 8501
 
```

Then open:

- http://localhost:8501

## Example questions

- Can employees work remotely and still be eligible for travel meal reimbursement?
- What is the policy on remote work approval and manager discretion?
- Are there rules governing business travel and reimbursement claims?
- What retention or compliance responsibilities apply to customer records?

## Validation and guardrails

The agent includes checks to prevent unsupported or weakly grounded answers:

- low-grounding detection
- retrieval relevance tracking
- source-aware answer verification
- failure states when the retrieved context is insufficient
- explainability through plan, retrieval, and reasoning traces

## Notes

This project is intentionally designed as a transparent, local enterprise knowledge system rather than a generic chatbot. It prioritizes grounded answers, traceability, and operational explainability.

## Future improvements

- stronger semantic-grounding checks using embedding similarity
- richer memory and session persistence
- expanded enterprise document coverage
- improved evaluation dashboard and score reporting

