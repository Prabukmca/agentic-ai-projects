# Domain Support Assistant for Insurance Documents

## Overview
This project implements a Retrieval-Augmented Generation (RAG) assistant that answers questions using only the content of local insurance-related documents. It is built with Python, LangChain and OpenAI models.

## Domain
The assistant is designed for insurance and regulatory documentation, including:
- insurer registration requirements
- regulatory guidance and compliance references
- home insurance coverage and policy concepts

## Source documents used
- IC-38: https://www.libertyinsurance.in/Docx/IC-38.pdf
- IAIS ICPs and ComFrame: https://www.iais.org/uploads/2025/06/IAIS-ICPs-and-ComFrame-December-2024.pdf
- NAIC homeowners consumer guide: https://content.naic.org/sites/default/files/publication-hoi-pp-consumer-homeowners.pdf
- IRDAI registration regulations: https://noc.irdai.gov.in/Content/docs/Insurance%20Regulatory%20and%20Development%20Authority%20(Registration%20of%20Indian%20Insurance%20Companies)%20Regulations,%202000%20(Updated%20upto%208th%20Amendment).pdf
- Insurance Handbook: https://www.iii.org/sites/default/files/docs/pdf/Insurance_Handbook_20103.pdf

## Features
- Loads PDFs from a local folder
- Splits large documents into semantic chunks
- Generates embeddings using OpenAI
- Stores them in a FAISS vector index
- Retrieves the top relevant chunks for each user query
- Injects context into the LLM prompt
- Maintains simple follow-up conversation history
- Refuses to answer if the information is missing from the provided documents

## Setup
1. Create a virtual environment and activate it.
2. Install dependencies:
   ```bash
   pip install python-dotenv langchain langchain-openai langchain-community faiss-cpu pymupdf pypdf langchain-text-splitters
   ```
3. Create a `.env` file in the project folder with:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```
4. Place the PDF files in the `documents/` folder.
5. Open the notebook `Assignments-15/domain-expert-agent.ipynb` in VS Code or Jupyter and run the cells from top to bottom.

## Notebook workflow
The project is implemented as a notebook-first solution. The notebook contains the complete workflow:
- load insurance documents
- split into chunks
- generate embeddings
- create FAISS index
- retrieve relevant content
- ask follow-up questions with conversation memory
- answer only from retrieved context

## Alternative script workflow
If you want to run the helper scripts, use:
```bash
python ingest.py --doc-dir ./documents --persist-path ./insurance_vectorstore
python chatbot.py
```

## Example questions
- What are the main requirements for registering an insurance company in India?
- Does this apply to foreign insurers?
- What policy protections are discussed for homeowners insurance?
- What if the information is not in the documents?

## Important note
This assistant is intentionally conservative: if the answer is not present in the uploaded documents, it responds with:

"I don’t have enough information in the provided documents."

This ensures the responses remain grounded in the actual source material and reduce hallucination.
