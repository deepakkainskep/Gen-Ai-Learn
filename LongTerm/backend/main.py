from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import agent_executor, llm
from memory.long_term_memory import LongTermMemory
from memory.short_term_memory import ShortTermMemory
from guardrails.toxicity_guardrails import ToxicityGuardrails
from cache.redis_cache import RedisCache


app = FastAPI(title="LLM Agent with Redis Cache")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# components
ltm = LongTermMemory(llm)

stm = ShortTermMemory()

guardrails = ToxicityGuardrails()

cache = RedisCache()


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    user_input: str


@app.post("/chat")
async def chat(req: QueryRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="Empty input")

    # Input guardrail
    sanitized_prompt, input_valid, input_risk = guardrails.check_input(req.user_input)

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
""".strip()

    # Redis cache
    cached_answer = cache.get(sanitized_prompt)

    if cached_answer:
        answer = cached_answer
        cache_status = "hit"
        print("🟢 CACHE HIT")
    else:
        result = agent_executor.invoke({"input": final_input})
        answer = result["output"]
        cache.set(sanitized_prompt, answer)
        cache_status = "miss"
        print("🔴 CACHE MISS")

    # Save user message
    stm.save(req.user_id, req.session_id, "user", sanitized_prompt)

    # Output guardrail
    sanitized_answer, output_valid, output_risk = guardrails.check_output(
        sanitized_prompt, answer
    )

    if not output_valid:
        stm.save(
            req.user_id,
            req.session_id,
            "assistant",
            "[BLOCKED BY OUTPUT GUARDRAIL]",
        )
        return {
            "answer": "I can’t help with harmful, abusive, or unsafe content.",
            "stored_memory": None,
            "input_risk_score": input_risk,
            "output_risk_score": output_risk,
            "conversation": stm.fetch(req.user_id, req.session_id),
            "cache": cache_status,
        }

    stm.save(req.user_id, req.session_id, "assistant", sanitized_answer)

    extracted = ltm.extract(sanitized_prompt)
    ltm.save(req.user_id, extracted)

    return {
        "answer": sanitized_answer,
        "stored_memory": extracted,
        "input_risk_score": input_risk,
        "output_risk_score": output_risk,
        "conversation": stm.fetch(req.user_id, req.session_id),
        "cache": cache_status,
    }
