import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from mcp.mcp_exceptions import McpError
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader
from src.lib.integration_manager import IntegrationManager

@pytest.mark.asyncio
async def test_integration_failure_handling_scenario():
    """
    Integration test for the integration failure handling scenario.
    """
    # Initialize dependencies
    genre_loader = GenreLoader(config_path="config/genres")
    # Mock the integration manager to simulate failure
    integration_manager = IntegrationManager(brain_service_url="http://localhost:9999") # Unavailable port
    narrative_analyzer = NarrativeAnalyzer(genre_loader, integration_manager)
    story_structure_handler = StoryStructureHandler(narrative_analyzer)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("analyze_story_structure", story_structure_handler.analyze_story_structure)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Call the tool and expect an McpError
        with pytest.raises(McpError) as excinfo:
            await client.call_tool(
                "analyze_story_structure",
                story_content="Test story requiring Brain service coordination",
                project_id="integration-failure-test"
            )

        # Assertions based on quickstart.md
        assert "brain.ft.tc:8002" in str(excinfo.value)
        assert "unavailable" in str(excinfo.value).lower()
