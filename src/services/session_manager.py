from typing import Dict, Any
from src.models.story_session import (
    StorySession,
    PersistencePolicy,
    SessionData,
    ProcessContext,
)
from src.lib.redis_client import RedisClient
import uuid
from datetime import datetime
import json


class StorySessionManager:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    def get_session(self, project_id: str) -> StorySession:
        """
        Retrieves or creates a story session for the given project ID.
        """
        session_data = self.redis_client.get(f"session:{project_id}")
        if session_data:
            # Handle both string (old format) and dict (new format) data
            if isinstance(session_data, str):
                # Clear old malformed data and create fresh session
                self.redis_client.client.delete(f"session:{project_id}")
            else:
                # Deserialize the session data into a StorySession object
                return self._deserialize_session(session_data)

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
                confidence_thresholds={},
            ),
            persistence_policy=PersistencePolicy.UNTIL_COMPLETION,
            process_isolation_context=ProcessContext(
                process_id=str(uuid.uuid4()),
                isolation_boundary=project_id,
                resource_limits={},
                cleanup_policy="on_completion",
            ),
        )
        self.redis_client.set(f"session:{project_id}", self._serialize_session(session))
        return session

    def save_session(self, session: StorySession):
        """
        Saves the story session.
        """
        self.redis_client.set(
            f"session:{session.project_id}", self._serialize_session(session)
        )

    def _serialize_session(self, session: StorySession) -> Dict[str, Any]:
        """
        Serializes a StorySession object to a dictionary for JSON storage.
        """
        return {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "active_story_arcs": session.active_story_arcs,
            "analysis_cache": session.analysis_cache,
            "last_activity": session.last_activity.isoformat(),
            "session_data": {
                "user_preferences": session.session_data.user_preferences,
                "active_operations": session.session_data.active_operations,
                "temporary_modifications": session.session_data.temporary_modifications,
                "analysis_history": [
                    {
                        "tool_name": req.tool_name,
                        "parameters": req.parameters,
                        "timestamp": req.timestamp.isoformat(),
                    }
                    for req in session.session_data.analysis_history
                ],
                "confidence_thresholds": session.session_data.confidence_thresholds,
            },
            "persistence_policy": session.persistence_policy.value,
            "process_isolation_context": {
                "process_id": session.process_isolation_context.process_id,
                "isolation_boundary": session.process_isolation_context.isolation_boundary,
                "resource_limits": session.process_isolation_context.resource_limits,
                "cleanup_policy": session.process_isolation_context.cleanup_policy,
            },
        }

    def _deserialize_session(self, data: Dict[str, Any]) -> StorySession:
        """
        Deserializes a dictionary into a StorySession object.
        """
        return StorySession(
            session_id=data["session_id"],
            project_id=data["project_id"],
            active_story_arcs=data["active_story_arcs"],
            analysis_cache=data["analysis_cache"],
            last_activity=datetime.fromisoformat(data["last_activity"]),
            session_data=SessionData(
                user_preferences=data["session_data"]["user_preferences"],
                active_operations=data["session_data"]["active_operations"],
                temporary_modifications=data["session_data"]["temporary_modifications"],
                analysis_history=[
                    AnalysisRequest(
                        tool_name=req["tool_name"],
                        parameters=req["parameters"],
                        timestamp=datetime.fromisoformat(req["timestamp"]),
                    )
                    for req in data["session_data"]["analysis_history"]
                ],
                confidence_thresholds=data["session_data"]["confidence_thresholds"],
            ),
            persistence_policy=PersistencePolicy(data["persistence_policy"]),
            process_isolation_context=ProcessContext(
                process_id=data["process_isolation_context"]["process_id"],
                isolation_boundary=data["process_isolation_context"][
                    "isolation_boundary"
                ],
                resource_limits=data["process_isolation_context"]["resource_limits"],
                cleanup_policy=data["process_isolation_context"]["cleanup_policy"],
            ),
        )
