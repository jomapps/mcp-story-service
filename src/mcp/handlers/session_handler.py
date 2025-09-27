import logging
from src.services.session_manager import StorySessionManager
from src.lib.error_handler import McpStoryServiceError

class SessionHandler:
    def __init__(self, session_manager: StorySessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)

    async def get_story_session(self, project_id: str) -> dict:
        """
        Handles the get_story_session tool call.
        """
        if not project_id or not isinstance(project_id, str):
            raise McpStoryServiceError("project_id must be a non-empty string")

        try:
            self.logger.info(f"Retrieving session for project: {project_id}")
            session = self.session_manager.get_session(project_id)

            if not session:
                raise McpStoryServiceError(f"Failed to create or retrieve session for project: {project_id}")

            # Serialize the StorySession object to match the contract
            return {
                "session": {
                    "session_id": session.session_id,
                    "project_id": session.project_id,
                    "active_story_arcs": session.active_story_arcs,
                    "last_activity": session.last_activity.isoformat(),
                    "session_status": "active",
                    "process_isolation_active": True,
                    "persistence_policy": "until_completion"
                }
            }
        except Exception as e:
            self.logger.error(f"Error retrieving session for project {project_id}: {str(e)}")
            raise McpStoryServiceError(f"Session retrieval failed: {str(e)}")
