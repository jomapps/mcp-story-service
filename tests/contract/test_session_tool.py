import pytest
import json
import os
import sys

sys.path.append(".")

from src.services.session_manager import StorySessionManager
from src.mcp.handlers.session_handler import SessionHandler
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

# Get the schema for the get_story_session tool
tool_schema = contract["mcp_tools"]["get_story_session"]


@pytest.mark.asyncio
async def test_get_story_session_contract():
    """
    Tests that the get_story_session tool conforms to its contract.
    """
    # Initialize actual dependencies
    redis_client = RedisClient()
    session_manager = StorySessionManager(redis_client)
    session_handler = SessionHandler(session_manager)

    # Test data that conforms to the input schema
    test_project_id = "test-project"

    # Call the actual handler implementation
    result = await session_handler.get_story_session(project_id=test_project_id)

    # Validate the result conforms to the output schema
    assert "session" in result
    session = result["session"]

    # Check required fields from the contract
    assert "session_id" in session
    assert "project_id" in session
    assert "active_story_arcs" in session
    assert "last_activity" in session
    assert "session_status" in session
    assert "process_isolation_active" in session
    assert "persistence_policy" in session

    # Validate data types
    assert isinstance(session["session_id"], str)
    assert isinstance(session["project_id"], str)
    assert isinstance(session["active_story_arcs"], list)
    assert isinstance(session["last_activity"], str)
    assert isinstance(session["session_status"], str)
    assert isinstance(session["process_isolation_active"], bool)
    assert isinstance(session["persistence_policy"], str)

    # Validate project ID matches
    assert session["project_id"] == test_project_id

    # Validate session status is one of expected values
    assert session["session_status"] in ["active", "inactive", "completed"]

    # Validate persistence policy is one of expected values
    assert session["persistence_policy"] in [
        "until_completion",
        "ephemeral",
        "persistent",
    ]
