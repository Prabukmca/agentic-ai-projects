import os
import traceback
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("OPENAI_API_KEY is not set or is a placeholder. Set it in .env or the environment.")
        return 2

    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema import HumanMessage
    except Exception as e:
        print("Failed to import ChatOpenAI from langchain:", e)
        traceback.print_exc()
        return 3

    try:
        chat = ChatOpenAI(temperature=0.2, model_name="gpt-3.5-turbo")
        prompt = "Please reply with the single word 'ok' so we can verify the API key and setup."
        response = chat([HumanMessage(content=prompt)])

        # response can be an AIMessage or other object depending on langchain version
        if hasattr(response, 'content'):
            out = response.content
        elif isinstance(response, (list, tuple)) and len(response) > 0 and hasattr(response[0], 'content'):
            out = response[0].content
        else:
            out = str(response)

        print("Model response:\n", out)
        return 0
    except Exception as e:
        print("Error during model call:", e)
        traceback.print_exc()
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
