import redis
import hashlib
from config.config import settings

class RedisCache:
    def __init__(self, host=settings.REDIS_HOST, port=settings.REDIS_PORT, ttl=300):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )
        self.ttl = ttl

    def _key(self, prompt: str) -> str:
        normalized = prompt.lower().strip()
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        return f"qa:{digest}"

    def get(self, prompt: str):
        return self.client.get(self._key(prompt))
    
    def set(self, prompt: str, value: str):
        self.client.setex(self._key(prompt), self.ttl, value)
