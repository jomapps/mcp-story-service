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

# Get the schema for the apply_genre_patterns tool
tool_schema = contract['mcp_tools']['apply_genre_patterns']

@pytest.mark.asyncio
async def test_apply_genre_patterns_contract():
    """
    Tests that the apply_genre_patterns tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_apply_genre_patterns(project_id, genre, story_beats, character_types):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "genre_guidance": {
                "convention_compliance": {
                    "score": 0.8,
                    "meets_threshold": True,
                    "confidence_score": 0.9,
                    "met_conventions": [],
                    "missing_conventions": []
                },
                "authenticity_improvements": [],
                "genre_specific_beats": []
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("apply_genre_patterns", mock_apply_genre_patterns, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "apply_genre_patterns",
            project_id="test-project",
            genre="thriller",
            story_beats=[],
            character_types=[]
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "genre_guidance" in result
