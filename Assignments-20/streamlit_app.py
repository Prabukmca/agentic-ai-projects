from pathlib import Path

import streamlit as st

from ornativa_chatbot import UniversalDocumentAgent


def get_chatbot() -> UniversalDocumentAgent:
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = UniversalDocumentAgent(
            Path(__file__).resolve().parent / "catalogue_documents"
        )
    return st.session_state.chatbot


st.set_page_config(page_title="Ornativa Jewels Assistant", page_icon="💍", layout="wide")

st.title("Ornativa Jewels Chatbot")
st.caption("Ask questions about the jewellery catalogue using the product details in the PDF.")

chatbot = get_chatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about a product, material, price, or stock status")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    answer = chatbot.answer(prompt)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
