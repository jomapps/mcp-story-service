import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.consistency_handler import ConsistencyHandler
from src.services.consistency.validator import ConsistencyValidator

@pytest.mark.asyncio
async def test_consistency_validation_scenario():
    """
    Integration test for the consistency validation scenario.
    """
    # Initialize dependencies
    consistency_validator = ConsistencyValidator()
    consistency_handler = ConsistencyHandler(consistency_validator)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("validate_consistency", consistency_handler.validate_consistency)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Test story elements from quickstart.md
        test_story_elements = {
            "characters": [
                {"name": "Sarah Chen", "role": "detective", "introduced": "episode_1"},
                {"name": "Partner Mike", "role": "corrupt_cop", "introduced": "episode_1"}
            ],
            "events": [
                {"description": "Sarah discovers evidence", "episode": 1, "timestamp": "day_1"},
                {"description": "Mike warns conspirators", "episode": 2, "timestamp": "day_1"},  # ISSUE: How did he know?
                {"description": "Sarah confronts Mike", "episode": 3, "timestamp": "day_5"}
            ],
            "timeline": [
                {"event": "Discovery", "day": 1},
                {"event": "Warning", "day": 1},
                {"event": "Confrontation", "day": 5}
            ]
        }

        # Call the tool
        result = await client.call_tool(
            "validate_consistency",
            project_id="quickstart-test-003",
            story_elements=test_story_elements,
            validation_scope=["timeline", "character", "plot"]
        )

        # Assertions based on quickstart.md
        assert "consistency_report" in result
        consistency_report = result["consistency_report"]

        assert len(consistency_report["issues"]) > 0
        assert "How did Mike know to warn conspirators?" in consistency_report["issues"][0]["description"]
