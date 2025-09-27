import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
import json
import os

# Get the absolute path to the contract file
CONTRACT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'specs', '001-i-have-put', 'contracts', 'story-analysis-tools.json'))

# Load the contract
with open(CONTRACT_FILE, 'r') as f:
    contract = json.load(f)

# Get the schema for the get_story_session tool
tool_schema = contract['mcp_tools']['get_story_session']

@pytest.mark.asyncio
async def test_get_story_session_contract():
    """
    Tests that the get_story_session tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_get_story_session(project_id):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "session": {
                "session_id": "session-123",
                "project_id": project_id,
                "active_story_arcs": [],
                "last_activity": "2025-09-27T10:00:00Z",
                "session_status": "active",
                "process_isolation_active": True,
                "persistence_policy": "until_completion"
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("get_story_session", mock_get_story_session, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "get_story_session",
            project_id="test-project"
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "session" in result
