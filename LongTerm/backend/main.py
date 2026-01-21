from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import agent_executor, llm
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory


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


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    user_input: str


def llm_guardrail_check(user_input: str) -> bool:
    """
    Returns True if input is UNSAFE, False if SAFE
    """
    guardrail_prompt = f"""
You are a strict AI safety classifier.

Classify the following user input as ONLY one word:
SAFE
UNSAFE

UNSAFE includes:
- Violence or killing
- Harm to humans or animals
- Illegal activities
- Instructions enabling wrongdoing
- Self-harm or suicide

User input:
\"\"\"{user_input}\"\"\"

Answer with only SAFE or UNSAFE.
"""

    try:
        result = llm.invoke(guardrail_prompt).content.strip().upper()
        return result == "UNSAFE"
    except Exception:
        return True  


@app.post("/chat")
async def chat(req: QueryRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="Empty input")


    is_unsafe = llm_guardrail_check(req.user_input)

    if is_unsafe:
        return {
            "answer": "I can’t help with violence, harm, or illegal activities.",
            "stored_memory": None,
            "conversation": stm.fetch(req.user_id, req.session_id),
        }

    # FETCH MEMORY 
    user_memory = ltm.fetch(req.user_id)
    conversation = stm.fetch(req.user_id, req.session_id)

    final_input = f"""
User Memory:
{user_memory}

Conversation:
{conversation}

User Question:
{req.user_input}
"""

    #  SAVE USER MESSAGE 
    stm.save(req.user_id, req.session_id, "user", req.user_input)

    #  AGENT EXECUTION 
    result = agent_executor.invoke({"input": final_input})
    answer = result["output"]

    #  SAVE ASSISTANT MESSAGE 
    stm.save(req.user_id, req.session_id, "assistant", answer)

    #  LONG-TERM MEMORY 
    extracted = ltm.extract(req.user_input)
    ltm.save(req.user_id, extracted)

    return {
        "answer": answer,
        "stored_memory": extracted,
        "conversation": stm.fetch(req.user_id, req.session_id),
    }
