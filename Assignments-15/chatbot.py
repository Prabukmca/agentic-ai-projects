import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


load_dotenv()


def load_vector_store(persist_path: str = "./insurance_vectorstore"):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.load_local(persist_path, embeddings, allow_dangerous_deserialization=True)


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
conversation_history = []


def make_contextual_query(question: str) -> str:
    if not conversation_history:
        return question
    recent_history = "\n".join(conversation_history[-6:])
    return f"Previous conversation:\n{recent_history}\n\nCurrent question: {question}"


def ask_question(vectorstore, question: str, k: int = 4) -> str:
    relevant_docs = vectorstore.similarity_search(make_contextual_query(question), k=k)
    if not relevant_docs:
        return "I don’t have enough information in the provided documents."

    context_text = "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in relevant_docs
    )

    system_prompt = """You are a domain support assistant. Answer questions only using the context provided below.
If the context does not contain enough information to answer, reply exactly with:
I don’t have enough information in the provided documents.

Rules:
- Use only the retrieved document content.
- Do not rely on outside knowledge.
- If a follow-up question references prior context, combine it with the previous conversation.
- Keep the answer concise but specific.
- Cite the relevant document names at the end of the answer when supported by the source.

Retrieved context:
{context}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])

    formatted_prompt = prompt.format_messages(context=context_text, question=question)
    response = llm.invoke(formatted_prompt)
    answer = response.content.strip()

    conversation_history.append(f"User: {question}")
    conversation_history.append(f"Assistant: {answer}")
    return answer


def run_chatbot(vectorstore_path: str = "./insurance_vectorstore"):
    vectorstore = load_vector_store(vectorstore_path)
    print("Insurance Domain Support Assistant is ready. Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break
        if not user_input:
            continue

        answer = ask_question(vectorstore, user_input)
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing. Add it to a .env file or export it.")
    run_chatbot()
