from typing import Dict, Any
from src.models.story_session import StorySession, PersistencePolicy, SessionData, ProcessContext
from src.lib.redis_client import RedisClient
import uuid
from datetime import datetime

class StorySessionManager:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    def get_session(self, project_id: str) -> StorySession:
        """
        Retrieves or creates a story session for the given project ID.
        """
        session_data = self.redis_client.get(f"session:{project_id}")
        if session_data:
            # In a real implementation, you would deserialize the session data
            # into a StorySession object.
            return session_data

        # Create a new session
        session_id = str(uuid.uuid4())
        session = StorySession(
            session_id=session_id,
            project_id=project_id,
            active_story_arcs=[],
            analysis_cache={},
            last_activity=datetime.utcnow(),
            session_data=SessionData(
                user_preferences={},
                active_operations=[],
                temporary_modifications=[],
                analysis_history=[],
                confidence_thresholds={}
            ),
            persistence_policy=PersistencePolicy.UNTIL_COMPLETION,
            process_isolation_context=ProcessContext(
                process_id=str(uuid.uuid4()),
                isolation_boundary=project_id,
                resource_limits={},
                cleanup_policy="on_completion"
            )
        )
        self.redis_client.set(f"session:{project_id}", session)
        return session

    def save_session(self, session: StorySession):
        """
        Saves the story session.
        """
        self.redis_client.set(f"session:{session.project_id}", session)
