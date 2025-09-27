from src.services.session_manager import StorySessionManager

class SessionHandler:
    def __init__(self, session_manager: StorySessionManager):
        self.session_manager = session_manager

    async def get_story_session(self, project_id: str) -> dict:
        """
        Handles the get_story_session tool call.
        """
        session = self.session_manager.get_session(project_id)

        # The tool contract expects a dictionary, not a StorySession object.
        # In a real implementation, you would serialize the StorySession object
        # to a dictionary that matches the contract.
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
