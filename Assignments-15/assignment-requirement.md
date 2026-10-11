Project Objective
Your objective is to build a Domain Support Assistant that:
• answers user questions only using the provided documents,
• supports follow-up questions using conversation history,
• avoids hallucination by refusing to answer when information is missing,
• and demonstrates a correct end-to-end RAG pipeline

Domain
Technology – Open-source documentation, API manuals

Functional Requirements
1) Document Ingestion
• Load documents from a local folder
• Split content into semantic chunks
• Generate embeddings using OpenAI embeddings
• Store embeddings in a vector store (e.g., FAISS or similar)
2) Retrieval-Augmented Chat
• Retrieve top-k relevant chunks per query
• Inject retrieved context into the LLM prompt
• Answer strictly based on retrieved content
3) Context Awareness
• Maintain conversation history
• Support follow-up questions (e.g., “What about eligibility?” / “Does this apply to
part-time users?”)
4) Safety & Accuracy
• If the answer is not in the documents, respond with:
“I don’t have enough information in the provided documents.”
Non-Functional Requirements
• Use OpenAI API
• Use LangChain
• Write modular, readable Python code
• Use environment variables for API keys (no hard-coded secrets)

Deliverables
Mandatory
• ingest.py – document ingestion and indexing
• chatbot.py or app.py – RAG chatbot implementation
• README.md – project explanation, setup, and run instructions
• Sample conversation screenshots or logs
Optional (Bonus)
• Streamlit UI
• Source document citation in answers
• Feedback mechanism

Constraints
• Do not use fine-tuning
• Do not hard-code answers
• Do not rely solely on LLM knowledge
• Retrieval must influence responses
Example Interactions (Expected)
• User: What is the return policy?
Bot: Based on the return policy document, ...
• User: Does this apply to discounted items?
Bot: Yes/No, according to the relevant section in the document, ...

 README.md with:
o Domain explanation
o Public data source links
o Setup & usage instructions

Source Links of those documents.
https://www.libertyinsurance.in/Docx/IC-38.pdf
https://www.iais.org/uploads/2025/06/IAIS-ICPs-and-ComFrame-December-2024.pdf
https://content.naic.org/sites/default/files/publication-hoi-pp-consumer-homeowners.pdf?utm_source=chatgpt.com
https://noc.irdai.gov.in/Content/docs/Insurance%20Regulatory%20and%20Development%20Authority%20(Registration%20of%20Indian%20Insurance%20Companies)%20Regulations,%202000%20(Updated%20upto%208th%20Amendment).pdf
https://www.iii.org/sites/default/files/docs/pdf/Insurance_Handbook_20103.pdf
