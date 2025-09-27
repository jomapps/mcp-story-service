import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.session_handler import SessionHandler
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.session_manager import SessionManager
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader
from src.lib.redis_client import RedisClient

@pytest.mark.asyncio
async def test_session_continuity_with_process_isolation_scenario():
    """
    Integration test for the session continuity with process isolation scenario.
    """
    # Initialize dependencies
    redis_client = RedisClient()
    session_manager = SessionManager(redis_client)
    genre_loader = GenreLoader(config_path="config/genres")
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
    session_handler = SessionHandler(session_manager)
    story_structure_handler = StoryStructureHandler(narrative_analyzer, session_manager)

    # Create a mock server and register the tools
    server = McpServer()
    server.register_tool("get_story_session", session_handler.get_story_session)
    server.register_tool("analyze_story_structure", story_structure_handler.analyze_story_structure)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Project 1
        project_1_id = "quickstart-session-test-1"
        session_1 = await client.call_tool("get_story_session", project_id=project_1_id)
        assert session_1["session"]["project_id"] == project_1_id

        await client.call_tool(
            "analyze_story_structure",
            story_content="Story for project 1",
            genre="thriller",
            project_id=project_1_id
        )

        # Project 2
        project_2_id = "quickstart-session-test-2"
        session_2 = await client.call_tool("get_story_session", project_id=project_2_id)
        assert session_2["session"]["project_id"] == project_2_id

        await client.call_tool(
            "analyze_story_structure",
            story_content="Story for project 2",
            genre="comedy",
            project_id=project_2_id
        )

        # Verify isolation
        updated_session_1 = await client.call_tool("get_story_session", project_id=project_1_id)
        assert len(updated_session_1["session"]["active_story_arcs"]) == 1

        updated_session_2 = await client.call_tool("get_story_session", project_id=project_2_id)
        assert len(updated_session_2["session"]["active_story_arcs"]) == 1
