from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import agent_executor, llm
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory

from llm_guard.input_scanners import Toxicity as InputToxicity
from llm_guard.input_scanners.toxicity import MatchType as InputMatchType

from llm_guard.output_scanners import Toxicity as OutputToxicity
from llm_guard.output_scanners.toxicity import MatchType as OutputMatchType


app = FastAPI(title="LLM Memory System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stm = ShortTermMemory()
ltm = LongTermMemory(llm)

#  input guardrail 
input_toxicity_scanner = InputToxicity(
    threshold=0.5,
    match_type=InputMatchType.SENTENCE
)

#  output guardrail 
output_toxicity_scanner = OutputToxicity(
    threshold=0.5,
    match_type=OutputMatchType.SENTENCE
)


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    user_input: str


def input_guardrail_check(text: str):
    sanitized, is_valid, risk_score = input_toxicity_scanner.scan(text)
    return sanitized, is_valid, risk_score


def output_guardrail_check(prompt: str, output: str):
    sanitized, is_valid, risk_score = output_toxicity_scanner.scan(prompt, output)
    return sanitized, is_valid, risk_score


@app.post("/chat")
async def chat(req: QueryRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="Empty input")

    #  input guardrail 
    sanitized_prompt, input_valid, input_risk = input_guardrail_check(req.user_input)

    if not input_valid:
        return {
            "answer": "I can’t help with harmful, abusive, or unsafe content.",
            "stored_memory": None,
            "input_risk_score": input_risk,
            "output_risk_score": None,
            "conversation": stm.fetch(req.user_id, req.session_id),
        }

    user_memory = ltm.fetch(req.user_id)
    conversation = stm.fetch(req.user_id, req.session_id)

    final_input = f"""
User Memory:
{user_memory}

Conversation:
{conversation}

User Question:
{sanitized_prompt}
"""

    stm.save(req.user_id, req.session_id, "user", sanitized_prompt)

    result = agent_executor.invoke({"input": final_input})
    answer = result["output"]

    #  output guardrail 
    sanitized_answer, output_valid, output_risk = output_guardrail_check(
        sanitized_prompt,
        answer
    )

    if not output_valid:
        stm.save(req.user_id, req.session_id, "assistant", "[BLOCKED BY OUTPUT GUARDRAIL]")
        return {
            "answer": "I can’t help with harmful, abusive, or unsafe content.",
            "stored_memory": None,
            "input_risk_score": input_risk,
            "output_risk_score": output_risk,
            "conversation": stm.fetch(req.user_id, req.session_id),
        }

    answer = sanitized_answer
    stm.save(req.user_id, req.session_id, "assistant", answer)

    #  memory extraction 
    extracted = ltm.extract(answer)
    ltm.save(req.user_id, extracted)

    return {
        "answer": answer,
        "stored_memory": extracted,
        "input_risk_score": input_risk,
        "output_risk_score": output_risk,
        "conversation": stm.fetch(req.user_id, req.session_id),
    }
