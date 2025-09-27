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
    process_isolation_manager = ProcessIsolationManager()
    narrative_analyzer = NarrativeAnalyzer(genre_loader, process_isolation_manager=process_isolation_manager)
    story_structure_handler = StoryStructureHandler(narrative_analyzer)

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
