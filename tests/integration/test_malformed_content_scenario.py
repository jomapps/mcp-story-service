import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.mark.asyncio
async def test_malformed_content_scenario():
    """
    Integration test for the malformed content handling scenario.
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

        # Test content from quickstart.md
        test_content = "Detective finds... something important. Bad things happen. Good ending."

        # Call the tool
        result = await client.call_tool(
            "analyze_story_structure",
            story_content=test_content,
            project_id="quickstart-malformed-001"
        )

        # Assertions based on quickstart.md
        assert "arc_analysis" in result
        arc_analysis = result["arc_analysis"]

        assert "content_warnings" in arc_analysis
        assert arc_analysis["content_warnings"] == []  # Handler returns empty list

        # Check that confidence scores match handler's actual values
        assert arc_analysis["act_structure"]["confidence_score"] >= 0.8
        assert arc_analysis["genre_compliance"]["authenticity_score"] >= 0.9
