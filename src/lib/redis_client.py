import redis
import json
from typing import Any, Dict
from dataclasses import asdict


class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def get(self, key: str) -> Any:
        """
        Gets a value from Redis and deserializes it from JSON.
        """
        value = self.client.get(key)
        if value:
            # In a real implementation, you would handle deserialization errors.
            return json.loads(value)
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Serializes a value to JSON and sets it in Redis.
        """
        # In a real implementation, you would handle serialization errors.
        # If value is a dataclass, convert it to dict first
        if hasattr(value, "__dataclass_fields__"):
            value = asdict(value)
        self.client.set(key, json.dumps(value, default=str))
