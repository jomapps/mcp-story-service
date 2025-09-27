from src.lib.redis_client import RedisClient
from src.services.session_manager import StorySessionManager
from dataclasses import asdict
import json

redis_client = RedisClient()
session_manager = StorySessionManager(redis_client)

# Test what gets stored
session = session_manager.get_session("test-debug")
print("Session object type:", type(session))
print("Session object:", session)

# Test what Redis returns
raw_data = redis_client.get("session:test-debug")
print("Raw data from Redis:", type(raw_data))
print("Raw data content:", raw_data)

# Test what our serialization produces
serialized = session_manager._serialize_session(session)
print("Serialized type:", type(serialized))
print("Serialized content:", serialized)

# Test direct Redis set/get with dict
test_dict = {"test": "value", "number": 42}
redis_client.set("test-dict", test_dict)
retrieved_dict = redis_client.get("test-dict")
print("Test dict type:", type(retrieved_dict))
print("Test dict content:", retrieved_dict)
