import os
import redis
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_community.cache import RedisCache
from langchain_core.globals import set_llm_cache


load_dotenv()

# Custom Redis Cache (HIT / MISS)
class DebugRedisCache(RedisCache):
    def lookup(self, prompt, llm_string):
        result = super().lookup(prompt, llm_string)
        
        key = self._key(prompt, llm_string)
        self.redis.expire(key, 120)
        
        if result is not None:
            print("🟢 CACHE HIT")
        else:
            print("🔴 CACHE MISS")
        return result
    
       

# Redis configuration
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

set_llm_cache(
    DebugRedisCache(redis_=redis_client)
)


llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    model="gpt-4.1",
    temperature=0,
)

# Cached Chatbot
print("\nCached LLM Chatbot (type 'exit' to quit)\n")

while True:
    user_input = input("You: ").strip().lower()

    if user_input == "exit":
        print("Thank You 🤗")
        break

    response = llm.invoke(user_input)

    print("Bot:", response.content)
