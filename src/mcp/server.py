import asyncio
import mcp.server.stdio
from mcp.server import Server
from src.mcp.handlers.story_structure_handler import StoryStructureHandler
from src.mcp.handlers.plot_threads_handler import PlotThreadsHandler
from src.mcp.handlers.consistency_handler import ConsistencyHandler
from src.mcp.handlers.genre_patterns_handler import GenrePatternsHandler
from src.mcp.handlers.session_handler import SessionHandler
from src.mcp.handlers.pacing_handler import PacingHandler
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.consistency.validator import ConsistencyValidator
from src.services.genre.analyzer import GenreAnalyzer
from src.services.pacing.calculator import PacingCalculator
from src.services.session_manager import StorySessionManager
from src.lib.genre_loader import GenreLoader
from src.lib.redis_client import RedisClient


async def main():
    # Initialize dependencies
    redis_client = RedisClient()
    genre_loader = GenreLoader(config_path="config/genres")
    session_manager = StorySessionManager(redis_client)
    narrative_analyzer = NarrativeAnalyzer(genre_loader)
    consistency_validator = ConsistencyValidator()
    genre_analyzer = GenreAnalyzer(genre_loader)
    pacing_calculator = PacingCalculator()

    # Initialize handlers
    story_structure_handler = StoryStructureHandler(narrative_analyzer, session_manager)
    plot_threads_handler = PlotThreadsHandler(narrative_analyzer, session_manager)
    consistency_handler = ConsistencyHandler(consistency_validator, session_manager)
    genre_patterns_handler = GenrePatternsHandler(genre_analyzer, session_manager)
    session_handler = SessionHandler(session_manager)
    pacing_handler = PacingHandler(pacing_calculator, session_manager)

    # Create MCP server
    server = Server("mcp-story-service")

    # Register tools
    @server.call_tool()
    async def analyze_story_structure(arguments):
        return await story_structure_handler.analyze_story_structure(arguments)

    @server.call_tool()
    async def track_plot_threads(arguments):
        return await plot_threads_handler.track_plot_threads(arguments)

    @server.call_tool()
    async def validate_consistency(arguments):
        return await consistency_handler.validate_consistency(arguments)

    @server.call_tool()
    async def apply_genre_patterns(arguments):
        return await genre_patterns_handler.apply_genre_patterns(arguments)

    @server.call_tool()
    async def get_story_session(arguments):
        return await session_handler.get_story_session(arguments)

    @server.call_tool()
    async def calculate_pacing(arguments):
        return await pacing_handler.calculate_pacing(arguments)

    # Start the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
