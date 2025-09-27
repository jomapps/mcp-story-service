"""Story session management service with process isolation."""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..models.story import StoryData
from ..models.analysis import AnalysisResult


class SessionConfig(BaseModel):
    """Configuration for story analysis sessions."""
    session_id: str = Field(..., description="Unique session identifier")
    project_id: str = Field(..., description="Project identifier for isolation")
    max_session_duration: int = Field(default=3600, description="Max session duration in seconds")
    auto_persist: bool = Field(default=True, description="Auto-persist session data")
    isolation_level: str = Field(default="process", description="Isolation level: process/thread")
    workspace_path: Optional[str] = Field(None, description="Dedicated workspace path")


class SessionState(BaseModel):
    """Current state of a story analysis session."""
    session_id: str
    project_id: str
    created_at: datetime
    last_accessed: datetime
    status: str = Field(default="active")  # active, paused, completed, expired
    story_data: Optional[StoryData] = None
    analysis_results: List[AnalysisResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessIsolationPolicy(BaseModel):
    """Policy for process isolation between projects."""
    enabled: bool = Field(default=True, description="Enable process isolation")
    max_concurrent_processes: int = Field(default=5, description="Max concurrent processes")
    process_timeout: int = Field(default=300, description="Process timeout in seconds")
    memory_limit_mb: int = Field(default=512, description="Memory limit per process")
    cleanup_interval: int = Field(default=60, description="Cleanup interval in seconds")


class PersistencePolicy(BaseModel):
    """Policy for session data persistence."""
    enabled: bool = Field(default=True, description="Enable session persistence")
    persist_interval: int = Field(default=30, description="Persist interval in seconds")
    max_session_age: int = Field(default=86400, description="Max session age in seconds")
    storage_backend: str = Field(default="file", description="Storage backend: file/redis/db")
    compression: bool = Field(default=True, description="Enable data compression")


class StorySessionManager:
    """Manages story analysis sessions with process isolation and persistence."""
    
    def __init__(
        self,
        workspace_dir: str = "workspaces",
        process_policy: Optional[ProcessIsolationPolicy] = None,
        persistence_policy: Optional[PersistencePolicy] = None
    ):
        """Initialize session manager.
        
        Args:
            workspace_dir: Base directory for session workspaces
            process_policy: Process isolation policy
            persistence_policy: Data persistence policy
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.process_policy = process_policy or ProcessIsolationPolicy()
        self.persistence_policy = persistence_policy or PersistencePolicy()
        
        self._sessions: Dict[str, SessionState] = {}
        self._active_processes: Dict[str, asyncio.subprocess.Process] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start background tasks
        if self.persistence_policy.enabled:
            asyncio.create_task(self._persistence_worker())
        
        if self.process_policy.enabled:
            asyncio.create_task(self._cleanup_worker())
    
    async def create_session(
        self,
        project_id: str,
        session_config: Optional[SessionConfig] = None
    ) -> str:
        """Create a new story analysis session.
        
        Args:
            project_id: Project identifier for isolation
            session_config: Optional session configuration
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        if session_config is None:
            session_config = SessionConfig(
                session_id=session_id,
                project_id=project_id
            )
        
        # Create dedicated workspace
        workspace_path = self.workspace_dir / project_id / session_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize session state
        session_state = SessionState(
            session_id=session_id,
            project_id=project_id,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # Store session
        self._sessions[session_id] = session_state
        self._session_locks[session_id] = asyncio.Lock()
        
        self.logger.info(f"Created session {session_id} for project {project_id}")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session state by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session state or None if not found
        """
        if session_id not in self._sessions:
            # Try to load from persistence
            await self._load_session(session_id)
        
        session = self._sessions.get(session_id)
        if session:
            session.last_accessed = datetime.now()
        
        return session
    
    async def update_session(
        self,
        session_id: str,
        story_data: Optional[StoryData] = None,
        analysis_result: Optional[AnalysisResult] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session with new data.
        
        Args:
            session_id: Session identifier
            story_data: Updated story data
            analysis_result: New analysis result to add
            metadata: Additional metadata
            
        Returns:
            True if updated successfully
        """
        async with self._session_locks.get(session_id, asyncio.Lock()):
            session = await self.get_session(session_id)
            if not session:
                return False
            
            if story_data:
                session.story_data = story_data
            
            if analysis_result:
                session.analysis_results.append(analysis_result)
            
            if metadata:
                session.metadata.update(metadata)
            
            session.last_accessed = datetime.now()
            
            # Auto-persist if enabled
            if self.persistence_policy.enabled and self.persistence_policy.persist_interval == 0:
                await self._persist_session(session_id)
            
            return True
    
    async def start_isolated_analysis(
        self,
        session_id: str,
        analysis_command: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """Start analysis in isolated process.
        
        Args:
            session_id: Session identifier
            analysis_command: Command to execute
            timeout: Process timeout (uses policy default if None)
            
        Returns:
            Process ID or None if failed
        """
        if not self.process_policy.enabled:
            self.logger.warning("Process isolation disabled")
            return None
        
        session = await self.get_session(session_id)
        if not session:
            return None
        
        # Check process limits
        if len(self._active_processes) >= self.process_policy.max_concurrent_processes:
            self.logger.warning("Maximum concurrent processes reached")
            return None
        
        try:
            # Create process environment
            env = os.environ.copy()
            env["SESSION_ID"] = session_id
            env["PROJECT_ID"] = session.project_id
            env["WORKSPACE_PATH"] = str(self.workspace_dir / session.project_id / session_id)
            
            # Start isolated process
            process = await asyncio.create_subprocess_shell(
                analysis_command,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=env["WORKSPACE_PATH"]
            )
            
            process_id = f"{session_id}_{int(time.time())}"
            self._active_processes[process_id] = process
            
            self.logger.info(f"Started isolated process {process_id} for session {session_id}")
            
            # Set timeout
            process_timeout = timeout or self.process_policy.process_timeout
            asyncio.create_task(self._monitor_process(process_id, process_timeout))
            
            return process_id
            
        except Exception as e:
            self.logger.error(f"Failed to start isolated process: {e}")
            return None
    
    async def get_process_output(self, process_id: str) -> Optional[tuple[str, str]]:
        """Get output from isolated process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Tuple of (stdout, stderr) or None if process not found
        """
        process = self._active_processes.get(process_id)
        if not process:
            return None
        
        try:
            stdout, stderr = await process.communicate()
            return stdout.decode(), stderr.decode()
        except Exception as e:
            self.logger.error(f"Failed to get process output: {e}")
            return None
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate session and cleanup resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if terminated successfully
        """
        async with self._session_locks.get(session_id, asyncio.Lock()):
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            # Terminate associated processes
            for process_id in list(self._active_processes.keys()):
                if process_id.startswith(session_id):
                    await self._terminate_process(process_id)
            
            # Final persistence
            if self.persistence_policy.enabled:
                await self._persist_session(session_id)
            
            # Update status
            session.status = "completed"
            
            # Cleanup
            del self._sessions[session_id]
            if session_id in self._session_locks:
                del self._session_locks[session_id]
            
            self.logger.info(f"Terminated session {session_id}")
            
            return True
    
    async def list_active_sessions(self, project_id: Optional[str] = None) -> List[SessionState]:
        """List active sessions.
        
        Args:
            project_id: Filter by project ID (optional)
            
        Returns:
            List of active session states
        """
        sessions = []
        for session in self._sessions.values():
            if session.status == "active":
                if project_id is None or session.project_id == project_id:
                    sessions.append(session)
        
        return sessions
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session manager statistics.
        
        Returns:
            Statistics dictionary
        """
        active_sessions = len([s for s in self._sessions.values() if s.status == "active"])
        
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active_sessions,
            "active_processes": len(self._active_processes),
            "workspace_size_mb": await self._calculate_workspace_size(),
            "policies": {
                "process_isolation": self.process_policy.dict(),
                "persistence": self.persistence_policy.dict()
            }
        }
    
    # Private methods
    
    async def _persistence_worker(self):
        """Background worker for session persistence."""
        while True:
            try:
                await asyncio.sleep(self.persistence_policy.persist_interval)
                
                for session_id in list(self._sessions.keys()):
                    await self._persist_session(session_id)
                    
            except Exception as e:
                self.logger.error(f"Persistence worker error: {e}")
    
    async def _cleanup_worker(self):
        """Background worker for cleanup tasks."""
        while True:
            try:
                await asyncio.sleep(self.process_policy.cleanup_interval)
                
                # Clean up expired sessions
                now = datetime.now()
                expired_sessions = []
                
                for session_id, session in self._sessions.items():
                    age = (now - session.created_at).total_seconds()
                    if age > self.persistence_policy.max_session_age:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.terminate_session(session_id)
                
                # Clean up orphaned processes
                for process_id in list(self._active_processes.keys()):
                    process = self._active_processes[process_id]
                    if process.returncode is not None:
                        del self._active_processes[process_id]
                        
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")
    
    async def _monitor_process(self, process_id: str, timeout: int):
        """Monitor process for timeout."""
        try:
            await asyncio.sleep(timeout)
            
            if process_id in self._active_processes:
                self.logger.warning(f"Process {process_id} timed out, terminating")
                await self._terminate_process(process_id)
                
        except Exception as e:
            self.logger.error(f"Process monitor error: {e}")
    
    async def _terminate_process(self, process_id: str):
        """Terminate a process."""
        process = self._active_processes.get(process_id)
        if process:
            try:
                process.terminate()
                await process.wait()
            except Exception as e:
                self.logger.error(f"Failed to terminate process {process_id}: {e}")
            finally:
                if process_id in self._active_processes:
                    del self._active_processes[process_id]
    
    async def _persist_session(self, session_id: str):
        """Persist session data."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        try:
            # Simple file-based persistence
            if self.persistence_policy.storage_backend == "file":
                session_file = self.workspace_dir / session.project_id / f"{session_id}.json"
                session_file.parent.mkdir(parents=True, exist_ok=True)
                
                session_data = session.dict()
                session_data["created_at"] = session_data["created_at"].isoformat()
                session_data["last_accessed"] = session_data["last_accessed"].isoformat()
                
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                    
        except Exception as e:
            self.logger.error(f"Failed to persist session {session_id}: {e}")
    
    async def _load_session(self, session_id: str):
        """Load session from persistence."""
        try:
            # Search for session file in all project directories
            for project_dir in self.workspace_dir.iterdir():
                if project_dir.is_dir():
                    session_file = project_dir / f"{session_id}.json"
                    if session_file.exists():
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                        
                        # Parse timestamps
                        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
                        session_data["last_accessed"] = datetime.fromisoformat(session_data["last_accessed"])
                        
                        session = SessionState(**session_data)
                        self._sessions[session_id] = session
                        self._session_locks[session_id] = asyncio.Lock()
                        
                        return
                        
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
    
    async def _calculate_workspace_size(self) -> float:
        """Calculate total workspace size in MB."""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.workspace_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            self.logger.error(f"Failed to calculate workspace size: {e}")
            return 0.0