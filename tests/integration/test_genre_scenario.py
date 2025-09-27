import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.genre_patterns_handler import GenrePatternsHandler
from src.services.genre.analyzer import GenreAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.mark.asyncio
async def test_genre_pattern_application_scenario():
    """
    Integration test for the genre pattern application scenario.
    """
    # Initialize dependencies
    genre_loader = GenreLoader(config_path="config/genres")
    genre_analyzer = GenreAnalyzer(genre_loader)

    # Create a lightweight session manager for testing
    from src.services.session.manager import StorySessionManager
    from unittest.mock import Mock
    mock_redis_client = Mock()
    session_manager = StorySessionManager(mock_redis_client)

    genre_patterns_handler = GenrePatternsHandler(genre_analyzer, session_manager)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("apply_genre_patterns", genre_patterns_handler.apply_genre_patterns)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Test elements from quickstart.md
        test_story_beats = [
            {"position": 0.1, "type": "inciting_incident", "description": "Discovery of corruption"},
            {"position": 0.5, "type": "midpoint", "description": "Personal threat emerges"},
            {"position": 0.9, "type": "climax", "description": "Final confrontation"}
        ]
        test_character_types = [
            {"name": "Sarah", "role": "protagonist", "archetype": "noir_detective"},
            {"name": "Mike", "role": "antagonist", "archetype": "corrupt_authority"}
        ]

        # Call the tool
        result = await client.call_tool(
            "apply_genre_patterns",
            project_id="quickstart-test-004",
            genre="thriller",
            story_beats=test_story_beats,
            character_types=test_character_types
        )

        # Assertions based on quickstart.md
        assert "genre_guidance" in result
        genre_guidance = result["genre_guidance"]

        assert genre_guidance["convention_compliance"]["meets_threshold"] is True
        assert genre_guidance["convention_compliance"]["score"] >= 0.75
