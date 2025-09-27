import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.genre.analyzer import GenreAnalyzer
from src.services.session_manager import StorySessionManager
from src.mcp.handlers.genre_patterns_handler import GenrePatternsHandler
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

# Get the schema for the apply_genre_patterns tool
tool_schema = contract["mcp_tools"]["apply_genre_patterns"]


@pytest.mark.asyncio
async def test_apply_genre_patterns_contract():
    """
    Tests that the apply_genre_patterns tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    genre_loader = GenreLoader(config_path="config/genres")
    session_manager = StorySessionManager(redis_client)
    genre_analyzer = GenreAnalyzer(genre_loader)
    genre_patterns_handler = GenrePatternsHandler(genre_analyzer, session_manager)

    # Test data that conforms to the input schema
    test_project_id = "test-project"
    test_genre = "thriller"
    test_story_beats = [
        {"description": "Inciting incident", "position": 0.1, "type": "plot_point"}
    ]
    test_character_types = [
        {"name": "Hero", "role": "protagonist", "traits": ["brave", "determined"]}
    ]

    # Call the actual handler implementation
    result = await genre_patterns_handler.apply_genre_patterns(
        project_id=test_project_id,
        genre=test_genre,
        story_beats=test_story_beats,
        character_types=test_character_types,
    )

    # Validate the result conforms to the output schema
    assert "genre_guidance" in result
    guidance = result["genre_guidance"]

    # Check required fields from the contract
    assert "convention_compliance" in guidance
    assert "authenticity_improvements" in guidance
    assert "genre_specific_beats" in guidance

    # Validate convention compliance structure
    compliance = guidance["convention_compliance"]
    assert "score" in compliance
    assert "meets_threshold" in compliance
    assert "confidence_score" in compliance
    assert "met_conventions" in compliance
    assert "missing_conventions" in compliance

    # Validate data types
    assert isinstance(compliance["score"], (int, float))
    assert isinstance(compliance["meets_threshold"], bool)
    assert isinstance(compliance["confidence_score"], (int, float))
    assert isinstance(compliance["met_conventions"], list)
    assert isinstance(compliance["missing_conventions"], list)

    # Validate score ranges
    assert 0 <= compliance["score"] <= 1
    assert 0 <= compliance["confidence_score"] <= 1
