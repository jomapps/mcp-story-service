import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.session_manager import StorySessionManager
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.lib.redis_client import RedisClient
from src.lib.genre_loader import GenreLoader

# Get the absolute path to the contract file
CONTRACT_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "specs",
        "001-i-have-put",
        "contracts",
        "story-analysis-tools.json",
    )
)

# Load the contract
with open(CONTRACT_FILE, "r") as f:
    contract = json.load(f)

# Get the schema for the analyze_story_structure tool
tool_schema = contract["mcp_tools"]["analyze_story_structure"]


@pytest.mark.asyncio
async def test_analyze_story_structure_contract():
    """
    Tests that the analyze_story_structure tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    genre_loader = GenreLoader(config_path="config/genres")
    session_manager = StorySessionManager(redis_client)
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
    story_structure_handler = StoryStructureHandler(narrative_analyzer, session_manager)

    # Test data that conforms to the input schema
    test_story_content = """
    In a quiet town, a detective discovers a mysterious clue that leads her on a dangerous investigation.
    As she digs deeper, she uncovers a conspiracy that threatens the entire community.
    With time running out, she must confront the mastermind behind the plot.
    """
    test_genre = "thriller"
    test_project_id = "test-project"

    # Call the actual handler implementation
    result = await story_structure_handler.analyze_story_structure(
        story_content=test_story_content, genre=test_genre, project_id=test_project_id
    )

    # Validate the result conforms to the output schema
    assert "arc_analysis" in result
    analysis = result["arc_analysis"]

    # Check required fields from the contract
    assert "act_structure" in analysis
    assert "genre_compliance" in analysis
    assert "pacing_analysis" in analysis
    assert "content_warnings" in analysis

    # Validate act structure
    act_structure = analysis["act_structure"]
    assert "act_one" in act_structure
    assert "act_two" in act_structure
    assert "act_three" in act_structure
    assert "turning_points" in act_structure
    assert "confidence_score" in act_structure

    # Validate genre compliance
    genre_compliance = analysis["genre_compliance"]
    assert "authenticity_score" in genre_compliance
    assert "meets_threshold" in genre_compliance
    assert "conventions_met" in genre_compliance
    assert "conventions_missing" in genre_compliance
    assert "recommendations" in genre_compliance

    # Validate pacing analysis
    pacing_analysis = analysis["pacing_analysis"]
    assert "tension_curve" in pacing_analysis
    assert "pacing_issues" in pacing_analysis
    assert "suggested_improvements" in pacing_analysis
    assert "confidence_score" in pacing_analysis

    # Validate data types
    assert isinstance(act_structure["confidence_score"], (int, float))
    assert isinstance(genre_compliance["authenticity_score"], (int, float))
    assert isinstance(genre_compliance["meets_threshold"], bool)
    assert isinstance(genre_compliance["conventions_met"], list)
    assert isinstance(genre_compliance["conventions_missing"], list)
    assert isinstance(genre_compliance["recommendations"], list)
    assert isinstance(pacing_analysis["tension_curve"], list)
    assert isinstance(pacing_analysis["pacing_issues"], list)
    assert isinstance(pacing_analysis["suggested_improvements"], list)
    assert isinstance(pacing_analysis["confidence_score"], (int, float))
    assert isinstance(analysis["content_warnings"], list)

    # Validate score ranges
    assert 0 <= act_structure["confidence_score"] <= 1
    assert 0 <= genre_compliance["authenticity_score"] <= 1
    assert 0 <= pacing_analysis["confidence_score"] <= 1
