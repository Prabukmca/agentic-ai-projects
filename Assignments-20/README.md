# Ornativa Jewels Chatbot

This assignment builds a retrieval-based jewellery assistant for Ornativa Jewels using the PDF product catalogues in `catalogue_documents/` as the source of truth.

## Objective

The chatbot should:
- answer questions using the catalogue data
- handle short-term follow-up questions
- stay polite, concise, and factual
- suggest an alternative when a product is out of stock
- provide a simple Streamlit UI for user interaction

## Project structure

- `catalogue_documents/`: PDF catalogue folder; every PDF inside is processed
- `ornativa_chatbot.py`: active universal hybrid agent with normalized records, query planning, deterministic execution, semantic retrieval, and result-set memory
- `generic_rag_chatbot.py`: legacy PDF-only RAG implementation retained for comparison
- `streamlit_app.py`: Streamlit UI for the chatbot
- `ornativa_flowise_chatflow.json`: Flowise-style node export
- `test_universal_document_agent.py`: no-network acceptance tests for the active hybrid agent

## Architecture

### 1. Document ingestion
`UniversalIngestor` reads PDF, CSV, JSON, Excel, Word, TXT, and Markdown sources. Structured rows are normalized into common fields, while unstructured text remains available for semantic retrieval.

### 2. Query planning and execution
`QueryPlanner` uses the LLM to convert structured questions into a generic JSON query plan. It receives the fields and known values discovered from the loaded records, so it can select actual catalogue values without question-specific rules. `QueryEngine` then performs filters, numeric comparisons, sorting, limits, and aggregation against the normalized records. The LLM plans the request; deterministic code remains the source of catalogue facts.

### 3. Response generation
Product selection, filtering, and ranking responses show names only. Explicit requests for price, weight, material, category, or stock read only those verified fields. An unqualified request for details asks the user to choose fields.

### 4. Memory
The agent stores selected record IDs, rather than parsing rendered answer text. Follow-ups such as "highest price product from these list", "show me the price for this one", and a field-only request after a selection run against exactly the prior selected records. History resolves references only and cannot introduce catalogue facts.

### 5. Streamlit UI
The Streamlit app provides a chat interface where users can ask price, material, stock, and category questions.

## Running the app

From the project root, activate the Python environment and launch the app:

```bash
cd d:\Technicals\Emeritus\Assignment-3
.venv\Scripts\activate
streamlit run Assignments-20/streamlit_app.py
```

If you are already in the project root in PowerShell, the shorter version is:

```bash
streamlit run Assignments-20/streamlit_app.py
```

Then open the local URL shown by Streamlit in the browser, typically:

```text
http://localhost:8501
```

The Streamlit app starts the universal agent once per browser session. An OpenAI key enables LLM query planning and semantic embeddings; structured catalogue questions still use deterministic execution when those services are unavailable.

## Flowise design

The Flowise JSON file includes the required node flow:
- PDF document loader
- text splitter
- embeddings
- vector store
- retriever
- prompt template
- memory
- chat model
- chat input/output

## Class and method summary

### `Record`
- Stores normalized source fields and provides key-normalized access.

### `UniversalIngestor`
- Loads supported document formats and separates structured records from unstructured text records.

### `QueryPlanner`
- Generates and validates query plans, with deterministic fallback planning when the model is unavailable.

### `QueryEngine`
- Executes validated conditions, numeric comparisons, sorting, limits, and aggregates against `Record` objects.

### `SemanticRetriever`
- Searches unstructured text with FAISS when available, with a lexical fallback.

### `UniversalDocumentAgent`
- Coordinates structured execution and semantic retrieval.
- `_catalogue_schema`: derives available fields and values from loaded structured records for query planning.
- Preserves selected record IDs for grounded follow-up queries.
- `answer`: resolves the request, renders verified output, and stores the conversation turn.

## Testing

Run:

```bash
python -m pytest Assignments-20/test_universal_document_agent.py -q
```

This test suite validates names-only selections, record-ID-scoped ranking and field follow-ups, ambiguous detail handling, and deterministic combined filters without network access.

## Notes

The implementation is grounded in the actual catalogue rather than fixed question-answer pairs, which keeps it consistent with the assignment requirement not to hard-code answers.
