


# Week 20 Graded Mini Project – Ornativa Jewels Chatbot

## Project Overview
This project implements a jewellery retail chatbot for Ornativa Jewels using **Langflow**.  
The chatbot answers customer questions by retrieving information from the provided catalogue (*Jewellery Details.pdf*), supports multi‑turn conversations with memory, and suggests alternatives when items are out of stock.

---

## Node Choices
- **File Loader** – loads the jewellery catalogue PDF.  
- **Text Splitter** – chunks catalogue text into manageable segments.  
- **Vector Store (Chroma/FAISS)** – stores embeddings for retrieval.  
- **Retriever** – fetches relevant chunks based on user queries.  
- **Parser (Stringify)** – converts JSON outputs into plain text.  
- **Message History** – maintains short‑term conversation memory.  
- **Prompt Template** – defines system instructions and injects context, history, and user question.  
- **Chat Model (GPT‑4/5)** – generates responses.  
- **Chat Input/Output** – user interface for queries and answers.

---

## Chunking Approach
- Used **RecursiveCharacterTextSplitter** with chunk size ~500 tokens.  
- Ensures catalogue entries are preserved with enough detail for retrieval.  
- Overlap of ~50 tokens to maintain context across chunks.

---

## Prompt Design

You are Ornativa's virtual jewellery expert. Be polite, concise, and factual.
Always use the catalogue data to answer questions.
If an item is out of stock, suggest a relevant alternative from the catalogue.
When listing products, only provide their names unless the user explicitly asks for full details.

If the requested product is out of stock:
- Inform the customer politely.
- Suggest a similar alternative from the catalogue.
Example:
"Ruby Solitaire Ring is currently out of stock. You may like the Classic Diamond Ring instead."


{context}

---

Given the context above, answer the question as best as possible.

Question: {question}

Answer:



## Memory Setup
- Implemented using **Message History node**.  
- Retains last 3–5 turns of conversation.  
- Injects `{history}` into the Prompt for multi‑turn recall.

---

## Out‑of‑Stock Handling
- Prompt instructs the chatbot to suggest alternatives when requested items are unavailable.  
- Example:  
  *“Ruby Solitaire Ring is currently out of stock. You may like the Classic Diamond Ring instead.”*

---

## Testing Evidence
Five queries tested:
1. **List all diamond items** → returns catalogue entries.  
2. **Price of Pearl Necklace** → returns correct price.  
3. **Products made of 22K gold** → lists relevant items.  
4. **Out‑of‑stock item suggestion** → provides fallback recommendation.  
5. **Multi‑turn memory test** → remembers previous query context.

---

## Deliverables
- **Langflow export (JSON)** or full pipeline screenshots.  
- **Test evidence**: screenshots/logs of five queries + responses.  
- **README/PDF**: this document explaining node choices, chunking, prompt design, memory setup, and fallback handling.


## Sample Questions
List all diamond items  
Expected: Classic Diamond Ring, Diamond Stud Earrings, Lotus Pendant.

Price of Pearl Necklace  
Expected: ₹245,000.

Products made of 22K gold  
Expected: Ruby Solitaire Ring, Emerald Choker, Daily Wear Gold Earrings, Gold Chain Bracelet, Om Symbol Pendant.

Check Ruby Solitaire Ring availability  
Expected: Out of Stock → Suggest Classic Diamond Ring.

Multi‑turn memory test

User: “Show me diamond products.”

Bot: “Classic Diamond Ring, Diamond Stud Earrings, Lotus Pendant are available.”

User: “What’s the price of the ring?”

Bot: “The Classic Diamond Ring is ₹135,000.”