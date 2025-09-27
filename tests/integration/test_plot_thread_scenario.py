import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.plot_threads_handler import PlotThreadsHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.mark.asyncio
async def test_plot_thread_tracking_scenario():
    """
    Integration test for the plot thread tracking scenario.
    """
    # Initialize dependencies
    genre_loader = GenreLoader(config_path="config/genres")
    narrative_analyzer = NarrativeAnalyzer(genre_loader)

    # Create a lightweight session manager for testing
    from src.services.session.manager import StorySessionManager
    from unittest.mock import Mock
    mock_redis_client = Mock()
    session_manager = StorySessionManager(mock_redis_client)

    plot_threads_handler = PlotThreadsHandler(narrative_analyzer, session_manager)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("track_plot_threads", plot_threads_handler.track_plot_threads)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Test threads from quickstart.md
        test_threads = [
            {
                "name": "Corporate conspiracy investigation",
                "type": "main",
                "episodes": [1, 2, 3, 4, 5],
                "current_stage": "developing"
            },
            {
                "name": "Sarah's relationship with partner",
                "type": "character_arc",
                "episodes": [1, 3, 5],
                "current_stage": "introduced"
            },
            {
                "name": "City government corruption",
                "type": "subplot",
                "episodes": [2, 4, 5],
                "current_stage": "developing"
            }
        ]

        # Call the tool
        result = await client.call_tool(
            "track_plot_threads",
            project_id="quickstart-test-002",
            threads=test_threads,
            episode_range={"start": 1, "end": 5}
        )

        # Assertions based on quickstart.md
        assert "thread_analysis" in result
        thread_analysis = result["thread_analysis"]

        assert len(thread_analysis) == 3
        assert "overall_assessment" in result
        assert result["overall_assessment"]["total_threads"] == 3
