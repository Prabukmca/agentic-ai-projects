Fix 1: Improve Chunk Granularity

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " "],
)

This ensures each conceptual block (like “assess your current policy”) becomes its own retrievable unit.

Fix 2: Use Larger Embedding Model

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

This model captures richer semantic relationships — “assess” and “review” will align better.

Fix 3: Query Expansion or Rewriting

Before retrieval, rephrase the user’s question using synonyms:

expanded_query = f"{question} OR review OR evaluate OR compare life insurance policy"
relevant_docs = vectorstore.similarity_search(expanded_query, k=4)

This broadens the semantic net without hallucination.

Fix 4: Inspect Similarity Scores

docs_with_scores = vectorstore.similarity_search_with_score(question, k=4)
for doc, score in docs_with_scores:
    print(score, doc.page_content[:200])

If scores are low (<0.3), your embeddings or chunking need adjustment.

Fix 5: Hybrid Retrieval

Combine keyword search and vector similarity:

vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10})

MMR (Maximal Marginal Relevance) balances relevance and diversity — ideal for short, factual paragraphs.