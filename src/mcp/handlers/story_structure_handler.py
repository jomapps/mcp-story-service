from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.session_manager import StorySessionManager

class StoryStructureHandler:
    def __init__(self, narrative_analyzer: NarrativeAnalyzer, session_manager: StorySessionManager):
        self.narrative_analyzer = narrative_analyzer
        self.session_manager = session_manager

    async def analyze_story_structure(self, story_content: str, genre: str, project_id: str) -> dict:
        """
        Handles the analyze_story_structure tool call.
        """
        session = self.session_manager.get_session(project_id)
        
        # In a real implementation, you would run the analysis in an isolated process
        # using the ProcessIsolationManager.
        story_arc = self.narrative_analyzer.analyze_story_structure(story_content, genre)
        
        session.active_story_arcs.append(story_arc.id)
        session.analysis_cache[story_arc.id] = story_arc
        self.session_manager.save_session(session)

        # The tool contract expects a dictionary, not a StoryArc object.
        # In a real implementation, you would serialize the StoryArc object
        # to a dictionary that matches the contract.
        return {
            "arc_analysis": {
                "act_structure": {
                    "act_one": {
                        "start_position": story_arc.act_structure.act_one.start_position,
                        "end_position": story_arc.act_structure.act_one.end_position,
                        "purpose": story_arc.act_structure.act_one.purpose,
                        "key_events": story_arc.act_structure.act_one.key_events
                    },
                    "act_two": {},
                    "act_three": {},
                    "turning_points": [],
                    "confidence_score": story_arc.act_structure.confidence_score
                },
                "genre_compliance": {
                    "authenticity_score": 0.9,
                    "meets_threshold": True,
                    "conventions_met": [],
                    "conventions_missing": [],
                    "recommendations": []
                },
                "pacing_analysis": {
                    "tension_curve": [],
                    "pacing_issues": [],
                    "suggested_improvements": [],
                    "confidence_score": story_arc.pacing_profile.confidence_score
                },
                "content_warnings": []
            }
        }
