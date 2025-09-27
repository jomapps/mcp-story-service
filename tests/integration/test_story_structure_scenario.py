import pytest
from mcp.mcp_server import McpServer
from mcp.mcp_client import McpClient
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.mark.asyncio
async def test_story_structure_analysis_scenario():
    """
    Integration test for the story structure analysis scenario.
    """
    # Initialize dependencies
    genre_loader = GenreLoader(config_path="config/genres")
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
    story_structure_handler = StoryStructureHandler(narrative_analyzer)

    # Create a mock server and register the tool
    server = McpServer()
    server.register_tool("analyze_story_structure", story_structure_handler.analyze_story_structure)

    # Create a client and connect to the server
    async with McpClient() as client:
        await client.connect_to_server(server)

        # Test story from quickstart.md
        test_story = """
        Detective Sarah Chen discovers her partner's involvement in a corporate conspiracy.
        As she investigates deeper, she realizes the conspiracy reaches the highest levels of city government.
        When her own life is threatened, she must choose between her career and exposing the truth.
        In a final confrontation, she brings down the corrupt officials but at great personal cost.
        """

        # Call the tool
        result = await client.call_tool(
            "analyze_story_structure",
            story_content=test_story,
            genre="thriller",
            project_id="quickstart-test-001"
        )

        # Assertions based on quickstart.md
        assert "arc_analysis" in result
        arc_analysis = result["arc_analysis"]

        # Act 1
        assert arc_analysis["act_structure"]["act_one"]["start_position"] == 0
        assert arc_analysis["act_structure"]["act_one"]["end_position"] <= 0.25
        assert "Discovery of partner's involvement" in arc_analysis["act_structure"]["act_one"]["purpose"]

        # Genre
        assert arc_analysis["genre_compliance"]["meets_threshold"] is True
        assert arc_analysis["genre_compliance"]["authenticity_score"] >= 0.75

        # Pacing
        assert "tension_curve" in arc_analysis["pacing_analysis"]
