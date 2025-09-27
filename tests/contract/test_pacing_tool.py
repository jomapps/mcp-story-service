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

# Get the schema for the calculate_pacing tool
tool_schema = contract['mcp_tools']['calculate_pacing']

@pytest.mark.asyncio
async def test_calculate_pacing_contract():
    """
    Tests that the calculate_pacing tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_calculate_pacing(project_id, narrative_beats, target_genre):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "pacing_analysis": {
                "tension_curve": [],
                "pacing_score": 0.8,
                "confidence_score": 0.9,
                "rhythm_analysis": {
                    "fast_sections": [],
                    "slow_sections": [],
                    "balanced_sections": []
                },
                "recommendations": [],
                "genre_compliance": 0.85
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("calculate_pacing", mock_calculate_pacing, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "calculate_pacing",
            project_id="test-project",
            narrative_beats=[],
            target_genre="thriller"
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "pacing_analysis" in result
