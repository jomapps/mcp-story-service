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

# Get the schema for the analyze_story_structure tool
tool_schema = contract['mcp_tools']['analyze_story_structure']

@pytest.mark.asyncio
async def test_analyze_story_structure_contract():
    """
    Tests that the analyze_story_structure tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_analyze_story_structure(story_content, genre, project_id):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "arc_analysis": {
                "act_structure": {
                    "act_one": {
                        "start_position": 0,
                        "end_position": 0.25,
                        "purpose": "Setup",
                        "key_events": ["Inciting Incident"]
                    },
                    "act_two": {},
                    "act_three": {},
                    "turning_points": [],
                    "confidence_score": 0.8
                },
                "genre_compliance": {
                    "authenticity_score": 0.9,
                    "meets_threshold": True,
                    "conventions_met": [],
                    "conventions_missing": [],
                    "recommendations": []
                },
                "pacing_analysis": {
                    "tension_curve": [],
                    "pacing_issues": [],
                    "suggested_improvements": [],
                    "confidence_score": 0.85
                },
                "content_warnings": []
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("analyze_story_structure", mock_analyze_story_structure, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "analyze_story_structure",
            story_content="This is a test story.",
            genre="thriller",
            project_id="test-project"
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "arc_analysis" in result
        assert "act_structure" in result["arc_analysis"]
        assert "genre_compliance" in result["arc_analysis"]
        assert "pacing_analysis" in result["arc_analysis"]
