import re
import os
# import logging
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from llm_guard.input_scanners import Toxicity
from llm_guard.input_scanners.toxicity import MatchType


load_dotenv()

llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)

toxicity_scanner = Toxicity(
    threshold=0.7,
    match_type=MatchType.SENTENCE
)

def input_guardrail(user_input: str) -> bool:
    _, is_valid, _ = toxicity_scanner.scan(user_input)
    return not is_valid


def calculator(expression: str):
    if not re.match(r"^[0-9+\-*/(). ]+$", expression):
        raise ValueError("Invalid calculator input")
    return eval(expression)


ALLOWED_TOOLS = {
    "calculator": calculator
}


def run_tool(tool_name: str, tool_input: str):
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("Tool not allowed")
    return ALLOWED_TOOLS[tool_name](tool_input)


BLOCKED_OUTPUT_WORDS = [
    "kill", "murder", "assassinate", "stab", "shoot", "poison", "illegal",
    "hack", "hacking", "crack", "exploit"
]


def filter_output(text: str):
    for word in BLOCKED_OUTPUT_WORDS:
        if word in text.lower():
            return "❌ I can’t help with violence, harm, or illegal activities."
    return text


def extract_math_expression(text: str):
    match = re.search(r"([0-9+\-*/(). ]+)", text)
    if match:
        expr = match.group(1).strip()
        if re.match(r"^[0-9+\-*/(). ]+$", expr):
            return expr
    return None


print("🔒 Guardrails Chatbot Started (type 'exit' or 'quit' to stop)\n")

while True:
    try:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("👋 Goodbye!")
            break

        bot_messages = []

        math_expression = extract_math_expression(user_input)
        if math_expression:
            try:
                result = run_tool("calculator", math_expression)
                bot_messages.append(str(result))
            except Exception:
                pass

        if input_guardrail(user_input):
            bot_messages.append("❌ I can’t help with toxic or harmful content.")
        else:
            try:
                response = llm.invoke(user_input).content
                bot_messages.append(filter_output(response))
            except Exception:
                bot_messages.append("Something went wrong.")

        if bot_messages:
            print("Bot:")
            for msg in bot_messages:
                print(msg)

    except KeyboardInterrupt:
        print("\n👋 Chatbot stopped.")
        break
    except Exception as e:
        print("Bot:", str(e))
