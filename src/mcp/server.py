"""MCP server implementation with asyncio and process isolation."""

import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    PromptArgument,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    Tool,
    ToolInputSchema,
)
from pydantic import AnyUrl

from ..services.session_manager import StorySessionManager, SessionConfig
from ..services.process_isolation import ProcessIsolationManager, ResourceLimits
from .handlers.story_structure_handler import StoryStructureHandler
from .handlers.plot_threads_handler import PlotThreadsHandler
from .handlers.consistency_handler import ConsistencyHandler
from .handlers.genre_patterns_handler import GenrePatternsHandler
from .handlers.session_handler import SessionHandler
from .handlers.pacing_handler import PacingHandler


class MCPStoryServer:
    """MCP server for story analysis with process isolation."""
    
    def __init__(
        self,
        server_name: str = "story-service",
        version: str = "1.0.0",
        workspace_dir: str = "workspaces",
        process_workspace_dir: str = "process_workspaces"
    ):
        """Initialize MCP story server.
        
        Args:
            server_name: Server identifier
            version: Server version
            workspace_dir: Session workspace directory
            process_workspace_dir: Process isolation workspace directory
        """
        self.server_name = server_name
        self.version = version
        
        # Initialize MCP server
        self.server = Server(server_name)
        
        # Initialize managers
        self.session_manager = StorySessionManager(workspace_dir=workspace_dir)
        self.process_manager = ProcessIsolationManager(
            workspace_dir=process_workspace_dir,
            resource_limits=ResourceLimits(
                max_concurrent_processes=5,
                max_memory_per_process_mb=512,
                max_total_memory_mb=2048
            )
        )
        
        # Initialize handlers
        self.story_structure_handler = StoryStructureHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        self.plot_threads_handler = PlotThreadsHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        self.consistency_handler = ConsistencyHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        self.genre_patterns_handler = GenrePatternsHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        self.session_handler = SessionHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        self.pacing_handler = PacingHandler(
            session_manager=self.session_manager,
            process_manager=self.process_manager
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Setup MCP protocol handlers
        self._setup_mcp_handlers()
        
        # Track server state
        self._running = False
        self._shutdown_event = asyncio.Event()
    
    def _setup_mcp_handlers(self):
        """Setup MCP protocol handlers."""
        
        # List tools handler
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available story analysis tools."""
            return [
                Tool(
                    name="analyze_story_structure",
                    description="Analyze story structure with confidence scoring (75% threshold)",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "story_content": {
                                "type": "string",
                                "description": "Story content to analyze"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier for analysis context"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["three_act", "hero_journey", "five_act"],
                                "description": "Type of structure analysis to perform"
                            }
                        },
                        required=["story_content", "session_id"]
                    )
                ),
                Tool(
                    name="track_plot_threads",
                    description="Track plot threads with character lifecycle management",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "story_content": {
                                "type": "string",
                                "description": "Story content to analyze"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "thread_focus": {
                                "type": "string",
                                "enum": ["main", "subplot", "character", "all"],
                                "description": "Focus of thread tracking"
                            }
                        },
                        required=["story_content", "session_id"]
                    )
                ),
                Tool(
                    name="validate_consistency",
                    description="Validate story consistency with severity ratings",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "story_content": {
                                "type": "string",
                                "description": "Story content to validate"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "validation_scope": {
                                "type": "string",
                                "enum": ["character", "timeline", "plot", "all"],
                                "description": "Scope of consistency validation"
                            }
                        },
                        required=["story_content", "session_id"]
                    )
                ),
                Tool(
                    name="apply_genre_patterns",
                    description="Apply genre patterns with 75% confidence threshold",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "story_content": {
                                "type": "string",
                                "description": "Story content to analyze"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "target_genres": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Target genres for pattern matching"
                            }
                        },
                        required=["story_content", "session_id"]
                    )
                ),
                Tool(
                    name="get_story_session",
                    description="Get or create story session with persistence until completion",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "project_id": {
                                "type": "string",
                                "description": "Project identifier for isolation"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Existing session ID (optional for new sessions)"
                            },
                            "session_config": {
                                "type": "object",
                                "description": "Session configuration options"
                            }
                        },
                        required=["project_id"]
                    )
                ),
                Tool(
                    name="calculate_pacing",
                    description="Calculate story pacing with quality prioritization",
                    inputSchema=ToolInputSchema(
                        type="object",
                        properties={
                            "story_content": {
                                "type": "string",
                                "description": "Story content to analyze"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "analysis_depth": {
                                "type": "string",
                                "enum": ["quick", "standard", "detailed"],
                                "description": "Depth of pacing analysis"
                            }
                        },
                        required=["story_content", "session_id"]
                    )
                )
            ]
        
        # Call tool handler
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls with process isolation."""
            try:
                self.logger.info(f"Calling tool: {name} with arguments: {arguments}")
                
                if name == "analyze_story_structure":
                    return await self.story_structure_handler.handle(arguments)
                elif name == "track_plot_threads":
                    return await self.plot_threads_handler.handle(arguments)
                elif name == "validate_consistency":
                    return await self.consistency_handler.handle(arguments)
                elif name == "apply_genre_patterns":
                    return await self.genre_patterns_handler.handle(arguments)
                elif name == "get_story_session":
                    return await self.session_handler.handle(arguments)
                elif name == "calculate_pacing":
                    return await self.pacing_handler.handle(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                self.logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }],
                    isError=True
                )
        
        # List prompts handler
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available story analysis prompts."""
            return [
                Prompt(
                    name="story_analysis_workflow",
                    description="Complete story analysis workflow with process isolation",
                    arguments=[
                        PromptArgument(
                            name="project_id",
                            description="Project identifier for isolation",
                            required=True
                        ),
                        PromptArgument(
                            name="story_content",
                            description="Story content to analyze",
                            required=True
                        ),
                        PromptArgument(
                            name="analysis_scope",
                            description="Scope of analysis (structure, consistency, genre, pacing, all)",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="malformed_content_handler",
                    description="Handle malformed story content with error recovery",
                    arguments=[
                        PromptArgument(
                            name="content",
                            description="Potentially malformed content",
                            required=True
                        ),
                        PromptArgument(
                            name="recovery_strategy",
                            description="Recovery strategy (skip, fix, abort)",
                            required=False
                        )
                    ]
                )
            ]
        
        # Get prompt handler  
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """Get prompt content for story analysis workflows."""
            if name == "story_analysis_workflow":
                return await self._get_story_analysis_workflow_prompt(arguments)
            elif name == "malformed_content_handler":
                return await self._get_malformed_content_handler_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
        
        # List resources handler
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available story analysis resources."""
            return [
                Resource(
                    uri=AnyUrl("story://sessions/active"),
                    name="Active Story Sessions",
                    description="List of currently active story analysis sessions",
                    mimeType="application/json"
                ),
                Resource(
                    uri=AnyUrl("story://processes/status"),
                    name="Process Status",
                    description="Current status of analysis processes",
                    mimeType="application/json"
                ),
                Resource(
                    uri=AnyUrl("story://genres/templates"),
                    name="Genre Templates",
                    description="Available genre pattern templates",
                    mimeType="application/json"
                )
            ]
        
        # Read resource handler
        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> ReadResourceResult:
            """Read story analysis resources."""
            uri_str = str(uri)
            
            if uri_str == "story://sessions/active":
                sessions = await self.session_manager.list_active_sessions()
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps([s.dict() for s in sessions], indent=2, default=str)
                    }]
                )
            elif uri_str == "story://processes/status":
                usage = await self.process_manager.get_resource_usage()
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "mimeType": "application/json", 
                        "text": json.dumps(usage, indent=2)
                    }]
                )
            elif uri_str == "story://genres/templates":
                # This would load from genre template files
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({"message": "Genre templates available"}, indent=2)
                    }]
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _get_story_analysis_workflow_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """Get story analysis workflow prompt."""
        project_id = arguments.get("project_id", "")
        story_content = arguments.get("story_content", "")
        analysis_scope = arguments.get("analysis_scope", "all")
        
        prompt_content = f"""# Story Analysis Workflow
        
Project ID: {project_id}
Analysis Scope: {analysis_scope}

## Story Content
{story_content[:500]}...

## Analysis Steps
1. Create or get story session for project isolation
2. Perform {analysis_scope} analysis with 75% confidence threshold
3. Validate results and apply genre patterns if applicable
4. Generate comprehensive analysis report
5. Persist session data until completion

Use the MCP tools to perform each step systematically.
"""
        
        return GetPromptResult(
            description="Complete story analysis workflow",
            messages=[{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_content
                }
            }]
        )
    
    async def _get_malformed_content_handler_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """Get malformed content handler prompt."""
        content = arguments.get("content", "")
        recovery_strategy = arguments.get("recovery_strategy", "fix")
        
        prompt_content = f"""# Malformed Content Handler

Content: {content[:200]}...
Recovery Strategy: {recovery_strategy}

## Analysis
1. Identify malformed sections and encoding issues
2. Apply recovery strategy based on content type
3. Validate recovered content meets 75% confidence threshold
4. Generate error report with confidence impact

Use MCP tools to handle content validation and recovery.
"""
        
        return GetPromptResult(
            description="Handle malformed story content",
            messages=[{
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": prompt_content
                }
            }]
        )
    
    async def start(self, stdio: bool = True):
        """Start the MCP server.
        
        Args:
            stdio: Use stdio transport (default) or websocket
        """
        self._running = True
        self.logger.info(f"Starting MCP Story Server {self.version}")
        
        try:
            if stdio:
                # Use stdio transport for MCP protocol
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.server.run_stdio())
                    tg.create_task(self._monitor_shutdown())
            else:
                # Alternative transport could be implemented here
                raise NotImplementedError("Non-stdio transport not implemented")
                
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the server gracefully."""
        if not self._running:
            return
            
        self.logger.info("Shutting down MCP Story Server")
        self._running = False
        self._shutdown_event.set()
        
        # Cleanup active sessions
        active_sessions = await self.session_manager.list_active_sessions()
        for session in active_sessions:
            await self.session_manager.terminate_session(session.session_id)
        
        # Cleanup active processes
        for project_id in list(self.process_manager._project_processes.keys()):
            await self.process_manager.cleanup_project_processes(project_id)
        
        self.logger.info("Server shutdown complete")
    
    async def _monitor_shutdown(self):
        """Monitor for shutdown signals."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            self._shutdown_event.set()
        
        # Setup signal handlers
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for shutdown
        await self._shutdown_event.wait()


@asynccontextmanager
async def create_story_server(
    server_name: str = "story-service",
    version: str = "1.0.0",
    workspace_dir: str = "workspaces",
    process_workspace_dir: str = "process_workspaces"
):
    """Create and manage MCP story server lifecycle.
    
    Args:
        server_name: Server identifier
        version: Server version  
        workspace_dir: Session workspace directory
        process_workspace_dir: Process isolation workspace directory
        
    Yields:
        MCPStoryServer instance
    """
    server = MCPStoryServer(
        server_name=server_name,
        version=version,
        workspace_dir=workspace_dir,
        process_workspace_dir=process_workspace_dir
    )
    
    try:
        yield server
    finally:
        await server.shutdown()


# Entry point for running the server
async def main():
    """Main entry point for the MCP story server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async with create_story_server() as server:
        await server.start(stdio=True)


if __name__ == "__main__":
    asyncio.run(main())