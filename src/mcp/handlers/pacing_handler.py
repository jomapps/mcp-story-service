from typing import List, Dict, Any
from src.services.pacing.calculator import PacingCalculator
from src.services.session_manager import StorySessionManager

class PacingHandler:
    def __init__(self, pacing_calculator: PacingCalculator, session_manager: StorySessionManager):
        self.pacing_calculator = pacing_calculator
        self.session_manager = session_manager

    async def calculate_pacing(self, project_id: str, narrative_beats: List[Dict[str, Any]], target_genre: str) -> dict:
        """
        Handles the calculate_pacing tool call.
        """
        session = self.session_manager.get_session(project_id)

        pacing_analysis = self.pacing_calculator.calculate_pacing(narrative_beats)
        
        # Update session
        session.analysis_cache["pacing_analysis"] = pacing_analysis
        self.session_manager.save_session(session)

        return {
            "pacing_analysis": pacing_analysis
        }
