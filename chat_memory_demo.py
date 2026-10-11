from dotenv import load_dotenv
import os

load_dotenv()

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.llms.base import LLM


class DummyLLM(LLM):
    """A tiny local LLM that echoes the last user message for testing memory."""

    @property
    def _llm_type(self) -> str:
        return "dummy"

    def _call(self, prompt: str, stop=None) -> str:
        # Simple behavior: return a predictable reply referencing the prompt
        return "[dummy reply] " + (prompt.splitlines()[-1] if prompt else "")

    @property
    def _identifying_params(self):
        return {"name": "dummy"}


def run_demo():
    # ConversationChain's default prompt expects memory key 'history'
    memory = ConversationBufferMemory(memory_key="history", return_messages=True)

    # Attach memory to a ConversationChain with the DummyLLM
    chain = ConversationChain(llm=DummyLLM(), memory=memory)

    # Perform two round-trips
    out1 = chain.predict(input="Hello, what's your name?")
    out2 = chain.predict(input="Can you remind me what I asked earlier?")

    print("--- Chain outputs ---")
    print("1:", out1)
    print("2:", out2)

    # Inspect memory
    mem_vars = memory.load_memory_variables({})
    print("\n--- Memory variables ---")
    for k, v in mem_vars.items():
        print(f"{k}: {v}")

    # If return_messages=True, `chat_history` is a list of messages
    if isinstance(mem_vars.get("history"), list):
        print("\n--- Stored turns (message-level) ---")
        for msg in mem_vars["history"]:
            t = getattr(msg, 'type', None) or getattr(msg, 'role', None)
            c = getattr(msg, 'content', None) or getattr(msg, 'message', None) or str(msg)
            print(f"{t}: {c}")


if __name__ == '__main__':
    run_demo()
