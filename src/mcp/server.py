import asyncio
import logging
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
from src.lib.error_handler import setup_logging, McpStoryServiceError


async def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP Story Service...")

    try:
        # Initialize dependencies
        logger.info("Initializing dependencies...")
        redis_client = RedisClient()
        genre_loader = GenreLoader(config_path="config/genres")
        session_manager = StorySessionManager(redis_client)
        narrative_analyzer = NarrativeAnalyzer(genre_loader)
        consistency_validator = ConsistencyValidator()
        genre_analyzer = GenreAnalyzer(genre_loader)
        pacing_calculator = PacingCalculator()
        logger.info("Dependencies initialized successfully")

        # Initialize handlers
        story_structure_handler = StoryStructureHandler(
            narrative_analyzer, session_manager
        )
        plot_threads_handler = PlotThreadsHandler(narrative_analyzer, session_manager)
        consistency_handler = ConsistencyHandler(consistency_validator, session_manager)
        genre_patterns_handler = GenrePatternsHandler(genre_analyzer, session_manager)
        session_handler = SessionHandler(session_manager)
        pacing_handler = PacingHandler(pacing_calculator, session_manager)

        # Create MCP server
        server = Server("mcp-story-service")

        # Register tools with error handling
        @server.call_tool()
        async def analyze_story_structure(arguments):
            try:
                logger.info(
                    f"Analyzing story structure for project: {arguments.get('project_id', 'unknown')}"
                )
                return await story_structure_handler.analyze_story_structure(
                    **arguments
                )
            except Exception as e:
                logger.error(f"Error in analyze_story_structure: {str(e)}")
                raise McpStoryServiceError(f"Story structure analysis failed: {str(e)}")

        @server.call_tool()
        async def track_plot_threads(arguments):
            try:
                logger.info(
                    f"Tracking plot threads for project: {arguments.get('project_id', 'unknown')}"
                )
                return await plot_threads_handler.track_plot_threads(**arguments)
            except Exception as e:
                logger.error(f"Error in track_plot_threads: {str(e)}")
                raise McpStoryServiceError(f"Plot thread tracking failed: {str(e)}")

        @server.call_tool()
        async def validate_consistency(arguments):
            try:
                logger.info(
                    f"Validating consistency for project: {arguments.get('project_id', 'unknown')}"
                )
                return await consistency_handler.validate_consistency(**arguments)
            except Exception as e:
                logger.error(f"Error in validate_consistency: {str(e)}")
                raise McpStoryServiceError(f"Consistency validation failed: {str(e)}")

        @server.call_tool()
        async def apply_genre_patterns(arguments):
            try:
                logger.info(
                    f"Applying genre patterns for project: {arguments.get('project_id', 'unknown')}"
                )
                return await genre_patterns_handler.apply_genre_patterns(**arguments)
            except Exception as e:
                logger.error(f"Error in apply_genre_patterns: {str(e)}")
                raise McpStoryServiceError(f"Genre pattern analysis failed: {str(e)}")

        @server.call_tool()
        async def get_story_session(arguments):
            try:
                logger.info(
                    f"Getting story session for project: {arguments.get('project_id', 'unknown')}"
                )
                return await session_handler.get_story_session(**arguments)
            except Exception as e:
                logger.error(f"Error in get_story_session: {str(e)}")
                raise McpStoryServiceError(f"Session retrieval failed: {str(e)}")

        @server.call_tool()
        async def calculate_pacing(arguments):
            try:
                logger.info(
                    f"Calculating pacing for project: {arguments.get('project_id', 'unknown')}"
                )
                return await pacing_handler.calculate_pacing(**arguments)
            except Exception as e:
                logger.error(f"Error in calculate_pacing: {str(e)}")
                raise McpStoryServiceError(f"Pacing calculation failed: {str(e)}")

        # Start the server using stdio
        logger.info("Starting MCP server...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    except Exception as e:
        logger.error(f"Failed to start MCP Story Service: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
