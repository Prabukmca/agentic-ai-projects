"""Agent combining a chat model, conversation memory, and a calculator tool.

By default this script uses a local DummyLLM so it can be run without OpenAI
quota. To use a real model, set the environment variable `USE_REAL_MODEL=1`
and ensure `OPENAI_API_KEY` is set.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

USE_REAL = os.getenv("USE_REAL_MODEL", "0") in ("1", "true", "True")

from langchain.memory import ConversationBufferMemory

# Tools
from tools.calculator_tool import evaluate as calc_evaluate


def calc_tool_func(input_str: str) -> str:
    """Tool wrapper that accepts a plain expression string and returns JSON."""
    out = calc_evaluate({"expression": input_str})
    return json.dumps(out)


def get_llm():
    if USE_REAL:
        from langchain.chat_models import ChatOpenAI

        return ChatOpenAI(temperature=0.2, model_name="gpt-3.5-turbo")

    # Fallback Dummy LLM for local testing
    from langchain.llms.base import LLM

    class DummyLLM(LLM):
        @property
        def _llm_type(self) -> str:
            return "dummy"

        def _call(self, prompt: str, stop=None) -> str:
            # Emulate ReACT-style agent outputs so the agent's parser and tool loop work.
            lower = prompt.lower()
            # If the agent is being asked to compute, return an Action for the calculator tool
            if "please compute" in lower or "please calculate" in lower or "compute:" in lower:
                # attempt to extract the expression after a colon or from the last line
                expr = ""
                if ":" in prompt:
                    expr = prompt.split(":")[-1].strip()
                else:
                    expr = prompt.splitlines()[-1].strip()
                return f"Thought: I should compute this using the calculator.\nAction: calculator\nAction Input: {expr}"

            # If the prompt contains an Observation from the tool, produce a Final Answer
            if "observation:" in lower:
                # Attempt to find a JSON blob after 'Observation:'
                try:
                    after = prompt.split("Observation:", 1)[1]
                    # crude extraction of first JSON object
                    import re, json

                    m = re.search(r"(\{.*\})", after, re.S)
                    if m:
                        data = json.loads(m.group(1))
                        # data is the tool output JSON string or dict
                        if isinstance(data, dict) and data.get("result") is not None:
                            return f"Final Answer: The computation result is {data.get('result')}"
                except Exception:
                    pass
                return "Final Answer: I observed the tool output."

            return "Thought: I will respond directly.\nFinal Answer: ok"

        @property
        def _identifying_params(self):
            return {"name": "dummy"}

    return DummyLLM()


def build_agent():
    from langchain.agents import Tool, initialize_agent, AgentType

    memory = ConversationBufferMemory(memory_key="history", return_messages=True)

    calc_tool = Tool(
        name="calculator",
        func=calc_tool_func,
        description=(
            "Performs arithmetic expressions. Input: a single arithmetic expression string. "
            "Output: JSON string with keys 'result', 'success', 'error'. Call only when you need to compute."
        ),
    )

    llm = get_llm()

    system_prompt = (
        "You are an assistant that should use conversation memory to remember prior turns. "
        "Only call the 'calculator' tool when you need to perform arithmetic; otherwise reply directly. "
        "Keep replies concise."
    )

    # Many initialize_agent wrappers accept a 'system_message' or can read from LLM prompt.
    # We'll use the agent type that supports tool usage.
    agent = initialize_agent(
        tools=[calc_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        memory=memory,
    )

    return agent, memory


def run_demo():
    agent, memory = build_agent()

    print("USE_REAL_MODEL=" + os.getenv("USE_REAL_MODEL", "0"))

    # First prompt: ask to compute something (agent should call tool)
    q1 = "Please compute: 12 / 4"
    print("User:", q1)
    r1 = agent.run(q1)
    print("Agent:", r1)

    # Second prompt: ask for reminder of previous question (memory should store it)
    q2 = "What did I ask you to compute earlier?"
    print("\nUser:", q2)
    r2 = agent.run(q2)
    print("Agent:", r2)

    print("\nMemory snapshot:")
    mv = memory.load_memory_variables({})
    print(mv)


if __name__ == "__main__":
    run_demo()
