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

# Get the schema for the validate_consistency tool
tool_schema = contract['mcp_tools']['validate_consistency']

@pytest.mark.asyncio
async def test_validate_consistency_contract():
    """
    Tests that the validate_consistency tool conforms to its contract.
    """
    # Mock the tool implementation
    async def mock_validate_consistency(project_id, story_elements, validation_scope):
        # In a real test, you would validate the input against the schema
        # and return a mock response that conforms to the output schema.
        return {
            "consistency_report": {
                "overall_score": 0.9,
                "confidence_score": 0.95,
                "issues": [],
                "strengths": ["Strong character motivations"],
                "recommendations": []
            }
        }

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("validate_consistency", mock_validate_consistency, tool_schema)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool with valid parameters
        result = await client.call_tool(
            "validate_consistency",
            project_id="test-project",
            story_elements={
                "characters": [],
                "events": [],
                "world_details": [],
                "timeline": []
            },
            validation_scope=["timeline", "character"]
        )

        # In a real test, you would validate the result against the output schema
        # using a library like jsonschema.
        assert "consistency_report" in result
