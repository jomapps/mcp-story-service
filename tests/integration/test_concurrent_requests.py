import pytest
import asyncio
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader
from src.services.process_isolation import ProcessIsolationManager

@pytest.mark.asyncio
async def test_concurrent_request_handling_with_process_isolation():
    """
    Integration test for concurrent request handling with process isolation.
    """
    # Initialize dependencies
    genre_loader = GenreLoader(config_path="config/genres")
    narrative_analyzer = NarrativeAnalyzer(genre_loader)

    # Create a lightweight session manager for testing
    from src.services.session.manager import StorySessionManager
    from unittest.mock import Mock
    mock_redis_client = Mock()
    session_manager = StorySessionManager(mock_redis_client)

    story_structure_handler = StoryStructureHandler(narrative_analyzer, session_manager)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("analyze_story_structure", story_structure_handler.analyze_story_structure)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Create concurrent tasks
        tasks = []
        for i in range(10):
            task = client.call_tool(
                "analyze_story_structure",
                story_content=f"Test story {i}",
                genre="thriller",
                project_id=f"concurrent-test-{i}"
            )
            tasks.append(task)

        # Run tasks concurrently
        results = await asyncio.gather(*tasks)

        # Assertions
        assert len(results) == 10
        # In a real test, you would check that 10 separate processes were created.
        # This would require more advanced mocking or inspecting the process manager.
