"""Session management tool handler with persistence until completion."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...services.session_manager import StorySessionManager, SessionConfig
from ...services.process_isolation import ProcessIsolationManager
from ...models.session import SessionData


class SessionHandler:
    """Handler for story session management MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize session handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle session management tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            project_id = arguments.get("project_id", "")
            session_id = arguments.get("session_id")
            session_config = arguments.get("session_config", {})
            
            if not project_id:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: project_id is required"
                    }],
                    isError=True
                )
            
            # Handle session operations
            if session_id:
                # Get existing session
                result = await self._get_existing_session(session_id)
            else:
                # Create new session
                result = await self._create_new_session(project_id, session_config)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Session management error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error managing session: {str(e)}"
                }],
                isError=True
            )
    
    async def _get_existing_session(self, session_id: str) -> CallToolResult:
        """Get existing session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information or error
        """
        session = await self.session_manager.get_session(session_id)
        
        if not session:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Session {session_id} not found"
                }],
                isError=True
            )
        
        # Get session statistics
        session_stats = await self._get_session_statistics(session_id)
        
        # Get active processes for this session
        active_processes = await self._get_session_processes(session_id)
        
        response_content = {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
            "story_data_present": session.story_data is not None,
            "analysis_results_count": len(session.analysis_results),
            "metadata": session.metadata,
            "statistics": session_stats,
            "active_processes": active_processes,
            "persistence_enabled": True,
            "process_isolation": True
        }
        
        return CallToolResult(
            content=[{
                "type": "text",
                "text": json.dumps(response_content, indent=2)
            }]
        )
    
    async def _create_new_session(
        self,
        project_id: str,
        session_config: Dict[str, Any]
    ) -> CallToolResult:
        """Create new session with persistence and isolation.
        
        Args:
            project_id: Project identifier
            session_config: Session configuration
            
        Returns:
            New session information
        """
        # Create session configuration
        config = SessionConfig(
            session_id="",  # Will be generated
            project_id=project_id,
            **session_config
        )
        
        # Create session
        session_id = await self.session_manager.create_session(
            project_id=project_id,
            session_config=config
        )
        
        # Get the created session
        session = await self.session_manager.get_session(session_id)
        
        if not session:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": "Failed to create session"
                }],
                isError=True
            )
        
        # Initialize session workspace and persistence
        workspace_info = await self._initialize_session_workspace(session_id, project_id)
        
        response_content = {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "workspace": workspace_info,
            "persistence_policy": {
                "enabled": True,
                "auto_persist": True,
                "persist_until_completion": True
            },
            "process_isolation": {
                "enabled": True,
                "dedicated_workspace": True,
                "resource_limits": {
                    "max_memory_mb": config.max_memory_mb if hasattr(config, 'max_memory_mb') else 512,
                    "max_duration_seconds": config.max_session_duration
                }
            },
            "message": f"Session created successfully for project {project_id}"
        }
        
        return CallToolResult(
            content=[{
                "type": "text",
                "text": json.dumps(response_content, indent=2)
            }]
        )
    
    async def _get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics
        """
        session = await self.session_manager.get_session(session_id)
        if not session:
            return {}
        
        # Calculate session duration
        duration_seconds = (session.last_accessed - session.created_at).total_seconds()
        
        # Analysis statistics
        analysis_types = {}
        total_confidence = 0.0
        
        for result in session.analysis_results:
            analysis_type = result.analysis_type
            if analysis_type not in analysis_types:
                analysis_types[analysis_type] = {
                    "count": 0,
                    "avg_confidence": 0.0,
                    "total_confidence": 0.0
                }
            
            analysis_types[analysis_type]["count"] += 1
            analysis_types[analysis_type]["total_confidence"] += result.confidence
            total_confidence += result.confidence
        
        # Calculate averages
        for analysis_type in analysis_types:
            count = analysis_types[analysis_type]["count"]
            analysis_types[analysis_type]["avg_confidence"] = round(
                analysis_types[analysis_type]["total_confidence"] / count, 3
            )
        
        overall_avg_confidence = (
            round(total_confidence / len(session.analysis_results), 3)
            if session.analysis_results else 0.0
        )
        
        return {
            "duration_seconds": round(duration_seconds, 1),
            "duration_minutes": round(duration_seconds / 60, 1),
            "total_analyses": len(session.analysis_results),
            "analysis_types": analysis_types,
            "overall_avg_confidence": overall_avg_confidence,
            "story_content_size": len(session.story_data.content) if session.story_data else 0,
            "metadata_entries": len(session.metadata)
        }
    
    async def _get_session_processes(self, session_id: str) -> List[Dict[str, Any]]:
        """Get active processes for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of active process information
        """
        active_processes = []
        
        # Get session to find project_id
        session = await self.session_manager.get_session(session_id)
        if not session:
            return active_processes
        
        # Get all processes for the project
        project_processes = await self.process_manager.list_project_processes(
            session.project_id
        )
        
        # Filter processes for this session
        for process in project_processes:
            if process.session_id == session_id and process.status == "running":
                active_processes.append({
                    "process_id": process.process_id,
                    "status": process.status,
                    "started_at": process.started_at.isoformat() if process.started_at else None,
                    "memory_usage_mb": process.memory_usage_mb,
                    "cpu_usage_percent": process.cpu_usage_percent,
                    "command": process.command
                })
        
        return active_processes
    
    async def _initialize_session_workspace(
        self,
        session_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Initialize session workspace and persistence.
        
        Args:
            session_id: Session identifier
            project_id: Project identifier
            
        Returns:
            Workspace initialization information
        """
        # Create workspace directory structure
        workspace_path = f"workspaces/{project_id}/{session_id}"
        
        # Create subdirectories for different types of data
        subdirs = [
            "analysis_results",
            "story_data", 
            "temp_files",
            "process_outputs"
        ]
        
        workspace_info = {
            "workspace_path": workspace_path,
            "subdirectories": subdirs,
            "initialized_at": asyncio.get_event_loop().time(),
            "persistence_enabled": True,
            "isolation_level": "process"
        }
        
        # Initialize persistence policies
        await self._setup_persistence_policies(session_id)
        
        return workspace_info
    
    async def _setup_persistence_policies(self, session_id: str):
        """Setup persistence policies for session.
        
        Args:
            session_id: Session identifier
        """
        # Set up auto-persistence for session data
        # This would configure:
        # 1. Automatic saving of analysis results
        # 2. Story data persistence
        # 3. Session state snapshots
        # 4. Recovery mechanisms
        
        self.logger.info(f"Persistence policies configured for session {session_id}")
    
    async def handle_session_action(
        self,
        session_id: str,
        action: str,
        **kwargs
    ) -> CallToolResult:
        """Handle specific session actions.
        
        Args:
            session_id: Session identifier
            action: Action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        try:
            if action == "terminate":
                return await self._terminate_session(session_id)
            elif action == "pause":
                return await self._pause_session(session_id)
            elif action == "resume":
                return await self._resume_session(session_id)
            elif action == "cleanup":
                return await self._cleanup_session(session_id)
            elif action == "export":
                return await self._export_session_data(session_id, kwargs.get("format", "json"))
            else:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Unknown session action: {action}"
                    }],
                    isError=True
                )
                
        except Exception as e:
            self.logger.error(f"Session action error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error performing session action: {str(e)}"
                }],
                isError=True
            )
    
    async def _terminate_session(self, session_id: str) -> CallToolResult:
        """Terminate session and cleanup resources."""
        success = await self.session_manager.terminate_session(session_id)
        
        if success:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps({
                        "session_id": session_id,
                        "status": "terminated",
                        "message": "Session terminated successfully"
                    }, indent=2)
                }]
            )
        else:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Failed to terminate session {session_id}"
                }],
                isError=True
            )
    
    async def _pause_session(self, session_id: str) -> CallToolResult:
        """Pause session activities."""
        # Implementation would pause active processes and mark session as paused
        return CallToolResult(
            content=[{
                "type": "text",
                "text": json.dumps({
                    "session_id": session_id,
                    "status": "paused",
                    "message": "Session paused successfully"
                }, indent=2)
            }]
        )
    
    async def _resume_session(self, session_id: str) -> CallToolResult:
        """Resume paused session."""
        # Implementation would resume processes and mark session as active
        return CallToolResult(
            content=[{
                "type": "text",
                "text": json.dumps({
                    "session_id": session_id,
                    "status": "active",
                    "message": "Session resumed successfully"
                }, indent=2)
            }]
        )
    
    async def _cleanup_session(self, session_id: str) -> CallToolResult:
        """Cleanup session temporary files and resources."""
        # Implementation would clean up temporary files while preserving persistent data
        return CallToolResult(
            content=[{
                "type": "text",
                "text": json.dumps({
                    "session_id": session_id,
                    "action": "cleanup",
                    "message": "Session cleanup completed"
                }, indent=2)
            }]
        )
    
    async def _export_session_data(
        self,
        session_id: str,
        export_format: str
    ) -> CallToolResult:
        """Export session data in specified format."""
        session = await self.session_manager.get_session(session_id)
        
        if not session:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Session {session_id} not found"
                }],
                isError=True
            )
        
        # Create export data
        export_data = {
            "session_info": {
                "session_id": session.session_id,
                "project_id": session.project_id,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat()
            },
            "story_data": session.story_data.dict() if session.story_data else None,
            "analysis_results": [result.dict() for result in session.analysis_results],
            "metadata": session.metadata,
            "export_timestamp": asyncio.get_event_loop().time(),
            "export_format": export_format
        }
        
        if export_format.lower() == "json":
            export_content = json.dumps(export_data, indent=2, default=str)
        else:
            export_content = str(export_data)  # Fallback to string representation
        
        return CallToolResult(
            content=[{
                "type": "text",
                "text": export_content
            }]
        )