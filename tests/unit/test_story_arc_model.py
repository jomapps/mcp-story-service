import pytest
from src.models.story_arc import StoryArc, Act, ActStructure, PacingProfile, ArcStatus, TurningPoint
from datetime import datetime

def test_story_arc_creation():
    """
    Tests the creation of a StoryArc object.
    """
    act_one = Act(start_position=0.0, end_position=0.25, purpose="Setup", key_events=["Inciting Incident"], character_arcs=[])
    act_two = Act(start_position=0.25, end_position=0.75, purpose="Confrontation", key_events=["Midpoint"], character_arcs=[])
    act_three = Act(start_position=0.75, end_position=1.0, purpose="Resolution", key_events=["Climax"], character_arcs=[])
    
    turning_points = [
        TurningPoint(position=0.25, description="Plot Point 1"),
        TurningPoint(position=0.75, description="Plot Point 2")
    ]

    act_structure = ActStructure(
        act_one=act_one,
        act_two=act_two,
        act_three=act_three,
        turning_points=turning_points,
        confidence_score=0.8
    )

    pacing_profile = PacingProfile(
        tension_curve=[0.2, 0.5, 0.4, 0.8, 0.6, 0.9, 1.0],
        pacing_issues=[],
        suggested_improvements=[],
        confidence_score=0.85
    )

    story_arc = StoryArc(
        id="story-arc-1",
        project_id="project-1",
        title="Test Story",
        genre="thriller",
        act_structure=act_structure,
        pacing_profile=pacing_profile,
        confidence_score=0.82,
        status=ArcStatus.ANALYZED
    )

    assert story_arc.id == "story-arc-1"
    assert story_arc.confidence_score == 0.82
    assert story_arc.status == ArcStatus.ANALYZED
    assert isinstance(story_arc.created_at, datetime)
