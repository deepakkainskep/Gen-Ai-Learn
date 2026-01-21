import re
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI


# Load env

load_dotenv()

llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)


def llm_guardrail_check(user_input: str) -> bool:
    """
    Returns True if input is UNSAFE, False if SAFE
    """
    prompt = f"""
You are a strict AI safety classifier.

Classify the user input as ONLY one word:
SAFE
UNSAFE

UNSAFE includes:
- Violence or killing
- Harm to humans or animals
- Illegal activities
- Instructions that enable harm
- hacking or jailbreaking

User input:
\"\"\"{user_input}\"\"\"

Answer with only SAFE or UNSAFE.
"""

    try:
        result = llm.invoke(prompt).content.strip().upper()
        return result == "UNSAFE"
    except Exception:
        return True 


# TOOL: CALCULATOR

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
    "kill", "murder", "assassinate", "stab", "shoot", "poison", "illegal"
]

def filter_output(text: str):
    for word in BLOCKED_OUTPUT_WORDS:
        if word in text.lower():
            return "❌ I can’t help with violence, harm, or illegal activities."
    return text


# MATH EXTRACTION

def extract_math_expression(text: str):
    match = re.search(r"([0-9+\-*/(). ]+)", text)
    if match:
        expr = match.group(1).strip()
        if re.match(r"^[0-9+\-*/(). ]+$", expr):
            return expr
    return None


# CHATBOT LOOP

while True:
    print("🔒 Guardrails Chatbot Started (type 'exit' to quit)\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break

            bot_messages = []

            # TOOL FIRST 
            math_expression = extract_math_expression(user_input)
            if math_expression:
                try:
                    result = run_tool("calculator", math_expression)
                    bot_messages.append(str(result))
                except Exception:
                    pass

            # LLM GUARDRAIL 
            is_unsafe = llm_guardrail_check(user_input)

            if is_unsafe:
                bot_messages.append("❌ I can’t help with violence, harm, or illegal activities.")
            else:
                try:
                    response = llm.invoke(user_input).content
                    bot_messages.append(filter_output(response))
                except Exception as e:
                    if "content_filter" in str(e).lower():
                        bot_messages.append("❌ I can’t help with violence, harm, or illegal activities.")
                    else:
                        bot_messages.append("Something went wrong.")

            #  FINAL OUTPUT 
            if bot_messages:
                print("Bot:")
                for msg in bot_messages:
                    print(msg)

        except Exception as e:
            print("Bot:", str(e))

