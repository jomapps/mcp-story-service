from typing import List, Dict, Any
from src.services.consistency.validator import ConsistencyValidator
from src.services.session_manager import StorySessionManager

class ConsistencyHandler:
    def __init__(self, consistency_validator: ConsistencyValidator, session_manager: StorySessionManager):
        self.consistency_validator = consistency_validator
        self.session_manager = session_manager

    async def validate_consistency(self, project_id: str, story_elements: Dict[str, Any], validation_scope: List[str]) -> dict:
        """
        Handles the validate_consistency tool call.
        """
        session = self.session_manager.get_session(project_id)

        # This is a mock implementation.
        consistency_report = self.consistency_validator.validate(story_elements)
        
        # Update session
        session.analysis_cache["consistency_report"] = consistency_report
        self.session_manager.save_session(session)

        return {
            "consistency_report": consistency_report
        }
