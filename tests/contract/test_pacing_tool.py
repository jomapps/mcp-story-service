import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.pacing.calculator import PacingCalculator
from src.services.session_manager import StorySessionManager
from src.mcp.handlers.pacing_handler import PacingHandler
from src.lib.redis_client import RedisClient

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

# Get the schema for the calculate_pacing tool
tool_schema = contract["mcp_tools"]["calculate_pacing"]


@pytest.mark.asyncio
async def test_calculate_pacing_contract():
    """
    Tests that the calculate_pacing tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    session_manager = StorySessionManager(redis_client)
    pacing_calculator = PacingCalculator()
    pacing_handler = PacingHandler(pacing_calculator, session_manager)

    # Test data that conforms to the input schema
    test_project_id = "test-project"
    test_narrative_beats = [
        {
            "description": "Opening scene",
            "position": 0.0,
            "tension_level": 0.3,
            "type": "exposition",
        },
        {
            "description": "Climax",
            "position": 0.8,
            "tension_level": 0.9,
            "type": "climax",
        },
    ]
    test_target_genre = "thriller"

    # Call the actual handler implementation
    result = await pacing_handler.calculate_pacing(
        project_id=test_project_id,
        narrative_beats=test_narrative_beats,
        target_genre=test_target_genre,
    )

    # Validate the result conforms to the output schema
    assert "pacing_analysis" in result
    analysis = result["pacing_analysis"]

    # Check required fields from the contract
    assert "tension_curve" in analysis
    assert "pacing_score" in analysis
    assert "confidence_score" in analysis
    assert "rhythm_analysis" in analysis
    assert "recommendations" in analysis
    assert "genre_compliance" in analysis

    # Validate rhythm analysis structure
    rhythm = analysis["rhythm_analysis"]
    assert "fast_sections" in rhythm
    assert "slow_sections" in rhythm
    assert "balanced_sections" in rhythm

    # Validate data types
    assert isinstance(analysis["tension_curve"], list)
    assert isinstance(analysis["pacing_score"], (int, float))
    assert isinstance(analysis["confidence_score"], (int, float))
    assert isinstance(analysis["recommendations"], list)
    assert isinstance(rhythm["fast_sections"], list)
    assert isinstance(rhythm["slow_sections"], list)
    assert isinstance(rhythm["balanced_sections"], list)

    # Validate score ranges
    assert 0 <= analysis["pacing_score"] <= 1
    assert 0 <= analysis["confidence_score"] <= 1
    assert 0 <= analysis["genre_compliance"] <= 1
