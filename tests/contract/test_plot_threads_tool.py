import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.session_manager import StorySessionManager
from src.mcp.handlers.plot_threads_handler import PlotThreadsHandler
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

# Get the schema for the track_plot_threads tool
tool_schema = contract["mcp_tools"]["track_plot_threads"]


@pytest.mark.asyncio
async def test_track_plot_threads_contract():
    """
    Tests that the track_plot_threads tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    genre_loader = GenreLoader(config_path="config/genres")
    session_manager = StorySessionManager(redis_client)
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
    plot_threads_handler = PlotThreadsHandler(narrative_analyzer, session_manager)

    # Test data that conforms to the input schema
    test_project_id = "test-project"
    test_threads = [
        {
            "id": "thread-1",
            "name": "Main Mystery",
            "type": "main",
            "episodes": [1, 2, 3],
            "current_stage": "developing",
        },
        {
            "id": "thread-2",
            "name": "Romantic Subplot",
            "type": "subplot",
            "episodes": [1, 3, 5],
            "current_stage": "introduced",
        },
    ]
    test_episode_range = {"start": 1, "end": 5}

    # Call the actual handler implementation
    result = await plot_threads_handler.track_plot_threads(
        project_id=test_project_id,
        threads=test_threads,
        episode_range=test_episode_range,
    )

    # Validate the result conforms to the output schema
    assert "thread_analysis" in result
    assert "overall_assessment" in result

    # Validate thread analysis structure
    for thread in result["thread_analysis"]:
        assert "thread_id" in thread
        assert "lifecycle_stage" in thread
        assert "confidence_score" in thread
        assert "resolution_opportunities" in thread
        assert "dependencies" in thread
        assert "importance_score" in thread
        assert "suggested_actions" in thread

        # Validate data types
        assert isinstance(thread["confidence_score"], (int, float))
        assert isinstance(thread["importance_score"], (int, float))
        assert isinstance(thread["resolution_opportunities"], list)
        assert isinstance(thread["dependencies"], list)
        assert isinstance(thread["suggested_actions"], list)

        # Validate score ranges
        assert 0 <= thread["confidence_score"] <= 1
        assert 0 <= thread["importance_score"] <= 1

    # Validate overall assessment structure
    assessment = result["overall_assessment"]
    assert "total_threads" in assessment
    assert "unresolved_threads" in assessment
    assert "abandoned_threads" in assessment
    assert "narrative_cohesion_score" in assessment
    assert "confidence_score" in assessment

    # Validate data types
    assert isinstance(assessment["total_threads"], int)
    assert isinstance(assessment["unresolved_threads"], int)
    assert isinstance(assessment["abandoned_threads"], int)
    assert isinstance(assessment["narrative_cohesion_score"], (int, float))
    assert isinstance(assessment["confidence_score"], (int, float))

    # Validate score ranges
    assert 0 <= assessment["narrative_cohesion_score"] <= 1
    assert 0 <= assessment["confidence_score"] <= 1
