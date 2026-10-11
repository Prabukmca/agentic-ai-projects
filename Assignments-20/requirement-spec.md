Introduction

This Week 20 Graded Mini Project asks you to build a Flowise-powered jewellery retail 
chatbot for a fictional brand, Ornativa Jewels (Hyderabad, India). The chatbot must 
answer customer questions by reading and using the product catalogue provided 
in Jewellery Details.pdf. The goal is to practise building a retrieval-based chatbot using 
a visual pipeline (document loading, chunking, embeddings, retrieval, prompting, 
memory, and testing) without relying on hard-coded answers. 

Project Objective 
Your objective is to create and test a Jewellery Chatbot that: 
• answers customer questions using the catalogue content provided 
in Jewellery Details.pdf, 
• supports follow-up questions using short-term conversation context 
(memory), 
• remains polite, concise, and factual in tone, 
• and suggests a relevant alternative when an item is out of stock (based on 
the catalogue). 

Tasks 
Task 1 – Data Setup 
1. Upload the provided file Jewellery Details.pdf into Flowise. 
2. Use a Document Loader node to read the contents of the PDF.
3. Connect it to a Text Splitter node (e.g., RecursiveCharacterTextSplitter) to 
chunk the content. 
4. Store embeddings using a Vector Store node (e.g., Chroma, FAISS, or 
Supabase). 
Deliverable: A Flowise flow that successfully ingests and indexes the jewellery 
catalogue. 

Task 2 – Create the Query Chain 
1. Add a Chat Model node (e.g., OpenAI GPT-4o-mini). 
2. Create a Prompt Template node with the instruction: 
“You are a jewellery store assistant. Use the catalogue data to answer 
questions accurately.” 
3. Connect Prompt Template → Retriever → Chat Model to form a retrieval-
based pipeline. 
4. Add Chat Input and Chat Output nodes to complete the conversation flow. 

Deliverable: A working query-response flow that can answer questions such as: 
• “List all available diamond items.” 
• “What is the price of the Pearl Necklace?” 
• “Which products are made of 22K gold?”

Task 3 – Add Conversational Memory 
1. Insert a Memory node (e.g., Buffer Memory) between the input and model 
nodes. 
2. Ensure the chatbot can remember the previous query context. Example: 

User: Show me diamond products. 
Bot: Classic Diamond Ring, Diamond Stud Earrings, and Lotus Pendant are available. 
User: What’s the price of the ring? 

3. Test multiple turns of conversation to confirm memory retention. 
Deliverable: A Flowise chatbot that maintains short-term conversation context.

Task 4 – Customisation and Testing 
1. Customise the system prompt to reflect the brand’s tone, e.g.: 
“You are Ornativa’s virtual jewellery expert. Be polite, concise, and 
factual.” 
2. Test at least five queries, including price, material, category, and stock-
related questions. 
3. If an item is out of stock, configure the chatbot to suggest an alternative 
product. Example: 
“Ruby Solitaire Ring is currently out of stock. You may like the Classic 
Diamond Ring instead.” 

Deliverable: Evidence of testing (queries + responses) and out-of-stock handling with an 
appropriate alternative suggestion (based on the catalogue).

Once Implemented this - I need following files.
1. Flowise chatflow export (JSON), or a clearly captured set of screenshots 
showing the full node pipeline and connections.
2. Short write-up README, describing: your node choices, chunking 
approach, prompt design, memory setup, and how you handled out-of-stock 
suggestions. 

1. update the requirements.txt - if you installed any new packages.
2. for each method, class, berief about what that method/class going to do.
3. I have the valid Open API key, please check in .env
4. Use LLM, if required please refer the previous implementations
  Assignments-15\domain-expert-agent.ipynb
  Cognizant-Assignment\enterprise_knowledge_ops_agent.py



## Implement this
The instruction was very clear, we should not hard code the question, but you hard coded, why?
we should build chat bot, why you didn't build chatbot?
Can we use Streamlit UI to build chatbot UI?, keep the files inside the Assignments-20 folder for the assignment, except the requirement.txt and env files.

