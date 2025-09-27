import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.consistency.validator import ConsistencyValidator
from src.services.session_manager import StorySessionManager
from src.mcp.handlers.consistency_handler import ConsistencyHandler
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

# Get the schema for the validate_consistency tool
tool_schema = contract["mcp_tools"]["validate_consistency"]


@pytest.mark.asyncio
async def test_validate_consistency_contract():
    """
    Tests that the validate_consistency tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    session_manager = StorySessionManager(redis_client)
    consistency_validator = ConsistencyValidator()
    consistency_handler = ConsistencyHandler(consistency_validator, session_manager)

    # Test data that conforms to the input schema
    test_project_id = "test-project"
    test_story_elements = {
        "characters": [
            {
                "name": "John Doe",
                "role": "protagonist",
                "attributes": {"age": 30, "occupation": "detective"},
            }
        ],
        "events": [
            {
                "description": "John investigates the crime scene",
                "timestamp": "day_1_morning",
                "characters": ["John Doe"],
            }
        ],
        "world_details": [
            {
                "aspect": "setting",
                "description": "Modern city police department",
                "consistency_rule": "Realistic police procedures",
            }
        ],
    }
    test_validation_scope = ["timeline", "character"]

    # Call the actual handler implementation
    result = await consistency_handler.validate_consistency(
        project_id=test_project_id,
        story_elements=test_story_elements,
        validation_scope=test_validation_scope,
    )

    # Validate the result conforms to the output schema
    assert "consistency_report" in result
    report = result["consistency_report"]

    # Check required fields from the contract
    assert "overall_score" in report
    assert "confidence_score" in report
    assert "issues" in report
    assert "strengths" in report
    assert "recommendations" in report

    # Validate data types
    assert isinstance(report["overall_score"], (int, float))
    assert isinstance(report["confidence_score"], (int, float))
    assert isinstance(report["issues"], list)
    assert isinstance(report["strengths"], list)
    assert isinstance(report["recommendations"], list)

    # Validate score ranges
    assert 0 <= report["overall_score"] <= 1
    assert 0 <= report["confidence_score"] <= 1

    # Validate issues structure if present
    for issue in report["issues"]:
        assert "type" in issue
        assert "severity" in issue
        assert "description" in issue
