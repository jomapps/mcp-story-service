import pytest
import asyncio
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader
from src.services.session_manager import SessionManager
from src.lib.redis_client import RedisClient

@pytest.mark.asyncio
async def test_concurrent_performance():
    """
    Performance test for concurrent request handling.
    """
    # Initialize dependencies
    from unittest.mock import Mock
    fake_redis_client = Mock()
    genre_loader = GenreLoader(config_path="config/genres")
    session_manager = SessionManager(fake_redis_client)
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
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
                project_id=f"perf-test-{i}"
            )
            tasks.append(task)

        # Run tasks concurrently
        results = await asyncio.gather(*tasks)

        # Assertions
        assert len(results) == 10
        for result in results:
            assert "arc_analysis" in result
