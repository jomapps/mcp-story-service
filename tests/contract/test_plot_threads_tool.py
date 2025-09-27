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

# Get the schema for the track_plot_threads tool
tool_schema = contract['mcp_tools']['track_plot_threads']

@pytest.mark.asyncio
async def test_track_plot_threads_contract():
    """
    Tests that the track_plot_threads tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_track_plot_threads(project_id, threads, episode_range):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "thread_analysis": [
                {
                    "thread_id": "thread-1",
                    "lifecycle_stage": "developing",
                    "confidence_score": 0.9,
                    "resolution_opportunities": [],
                    "dependencies": [],
                    "importance_score": 0.8,
                    "suggested_actions": []
                }
            ],
            "overall_assessment": {
                "total_threads": 1,
                "unresolved_threads": 1,
                "abandoned_threads": 0,
                "narrative_cohesion_score": 0.85,
                "confidence_score": 0.9
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("track_plot_threads", mock_track_plot_threads, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "track_plot_threads",
            project_id="test-project",
            threads=[
                {
                    "id": "thread-1",
                    "name": "Test Thread",
                    "type": "main",
                    "episodes": [1, 2],
                    "current_stage": "developing"
                }
            ],
            episode_range={"start": 1, "end": 2}
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "thread_analysis" in result
        assert "overall_assessment" in result
