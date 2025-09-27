from typing import List, Dict, Any
from src.services.genre.analyzer import GenreAnalyzer
from src.services.session_manager import StorySessionManager

class GenrePatternsHandler:
    def __init__(self, genre_analyzer: GenreAnalyzer, session_manager: StorySessionManager):
        self.genre_analyzer = genre_analyzer
        self.session_manager = session_manager

    async def apply_genre_patterns(self, project_id: str, genre: str, story_beats: List[Dict[str, Any]], character_types: List[Dict[str, Any]]) -> dict:
        """
        Handles the apply_genre_patterns tool call.
        """
        session = self.session_manager.get_session(project_id)

        genre_guidance = self.genre_analyzer.analyze_genre(story_beats, character_types, genre)
        
        # Update session
        session.analysis_cache["genre_guidance"] = genre_guidance
        self.session_manager.save_session(session)

        return {
            "genre_guidance": genre_guidance
        }
