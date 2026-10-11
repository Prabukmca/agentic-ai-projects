from openai import OpenAI
import faiss
import numpy as np

client = OpenAI(api_key="YOUR_OPENAI_KEY")

# Step 1: Documents
docs = [
    "RAG stands for Retrieval-Augmented Generation.",
    "It combines a retriever (vector search) with a generator (LLM).",
    "The retriever finds relevant context, and the LLM generates answers."
]

# Step 2: Embed documents
def embed(text):
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(resp.data[0].embedding, dtype="float32")

embeddings = [embed(d) for d in docs]

# Step 3: Build FAISS index
dim = len(embeddings[0])
index = faiss.IndexFlatL2(dim)
index.add(np.array(embeddings))

# Step 4: Query
query = "Explain RAG"
q_emb = embed(query)
D, I = index.search(np.array([q_emb]), k=2)

context = " ".join([docs[i] for i in I[0]])

# Step 5: Generate answer with context
completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Answer using context: {context}\n\nQuestion: {query}"}
    ]
)

print("Q:", query)
print("A:", completion.choices[0].message.content)
