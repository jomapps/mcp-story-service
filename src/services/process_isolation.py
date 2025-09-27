"""Process isolation manager for separate analysis processes per project."""

import asyncio
import json
import logging
import os
import psutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ..models.story import StoryData
from ..models.analysis import AnalysisResult


class ProcessConfig(BaseModel):
    """Configuration for isolated analysis processes."""
    process_id: str = Field(..., description="Unique process identifier")
    project_id: str = Field(..., description="Project identifier")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    max_memory_mb: int = Field(default=512, description="Memory limit in MB")
    timeout_seconds: int = Field(default=300, description="Process timeout")
    priority: int = Field(default=0, description="Process priority (-20 to 19)")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class ProcessState(BaseModel):
    """Current state of an isolated process."""
    process_id: str
    project_id: str
    session_id: Optional[str]
    pid: Optional[int] = None
    status: str = Field(default="created")  # created, running, completed, failed, killed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    command: Optional[str] = None
    output_file: Optional[str] = None
    error_file: Optional[str] = None


class ResourceLimits(BaseModel):
    """Resource limits for process isolation."""
    max_concurrent_processes: int = Field(default=5, description="Max concurrent processes")
    max_memory_per_process_mb: int = Field(default=512, description="Memory limit per process")
    max_cpu_percent: float = Field(default=80.0, description="CPU usage limit")
    max_total_memory_mb: int = Field(default=2048, description="Total memory limit")
    cleanup_threshold_percent: float = Field(default=90.0, description="Resource cleanup threshold")


class ProcessIsolationManager:
    """Manages separate analysis processes per project with resource isolation."""
    
    def __init__(
        self,
        workspace_dir: str = "process_workspaces",
        resource_limits: Optional[ResourceLimits] = None,
        monitoring_interval: float = 1.0
    ):
        """Initialize process isolation manager.
        
        Args:
            workspace_dir: Base directory for process workspaces
            resource_limits: Resource limits configuration
            monitoring_interval: Process monitoring interval in seconds
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.resource_limits = resource_limits or ResourceLimits()
        self.monitoring_interval = monitoring_interval
        
        self._processes: Dict[str, ProcessState] = {}
        self._process_handles: Dict[str, subprocess.Popen] = {}
        self._project_processes: Dict[str, Set[str]] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start background monitoring
        asyncio.create_task(self._resource_monitor())
        asyncio.create_task(self._cleanup_worker())
    
    async def start_isolated_process(
        self,
        config: ProcessConfig,
        command: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Start a new isolated analysis process.
        
        Args:
            config: Process configuration
            command: Command to execute
            input_data: Input data for the process
            
        Returns:
            Process ID if successful, None otherwise
        """
        # Check resource limits
        if not await self._check_resource_availability():
            self.logger.warning("Resource limits exceeded, cannot start new process")
            return None
        
        try:
            # Create process workspace
            workspace_path = self.workspace_dir / config.project_id / config.process_id
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Prepare input file
            input_file = None
            if input_data:
                input_file = workspace_path / "input.json"
                with open(input_file, 'w') as f:
                    json.dump(input_data, f, indent=2)
            
            # Prepare output files
            output_file = workspace_path / "output.json"
            error_file = workspace_path / "error.log"
            
            # Set up environment
            env = os.environ.copy()
            env.update(config.env_vars)
            env.update({
                "PROCESS_ID": config.process_id,
                "PROJECT_ID": config.project_id,
                "WORKSPACE_PATH": str(workspace_path),
                "INPUT_FILE": str(input_file) if input_file else "",
                "OUTPUT_FILE": str(output_file),
                "ERROR_FILE": str(error_file),
                "MEMORY_LIMIT_MB": str(config.max_memory_mb),
                "TIMEOUT_SECONDS": str(config.timeout_seconds)
            })
            
            if config.session_id:
                env["SESSION_ID"] = config.session_id
            
            # Build command with resource limits
            full_command = self._build_limited_command(command, config)
            
            # Start process
            with open(error_file, 'w') as stderr_file:
                process = subprocess.Popen(
                    full_command,
                    env=env,
                    cwd=workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=stderr_file,
                    shell=True,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
            
            # Create process state
            process_state = ProcessState(
                process_id=config.process_id,
                project_id=config.project_id,
                session_id=config.session_id,
                pid=process.pid,
                status="running",
                started_at=datetime.now(),
                command=command,
                output_file=str(output_file),
                error_file=str(error_file)
            )
            
            # Store process
            self._processes[config.process_id] = process_state
            self._process_handles[config.process_id] = process
            
            # Track by project
            if config.project_id not in self._project_processes:
                self._project_processes[config.project_id] = set()
            self._project_processes[config.project_id].add(config.process_id)
            
            self.logger.info(f"Started isolated process {config.process_id} (PID: {process.pid})")
            
            # Set timeout
            asyncio.create_task(self._process_timeout(config.process_id, config.timeout_seconds))
            
            return config.process_id
            
        except Exception as e:
            self.logger.error(f"Failed to start isolated process: {e}")
            return None
    
    async def get_process_status(self, process_id: str) -> Optional[ProcessState]:
        """Get current status of a process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Process state or None if not found
        """
        process_state = self._processes.get(process_id)
        if not process_state:
            return None
        
        # Update process state
        await self._update_process_state(process_id)
        
        return process_state
    
    async def get_process_output(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get output from a completed process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Process output data or None if not available
        """
        process_state = self._processes.get(process_id)
        if not process_state or not process_state.output_file:
            return None
        
        try:
            output_path = Path(process_state.output_file)
            if output_path.exists():
                with open(output_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read process output: {e}")
        
        return None
    
    async def get_process_error(self, process_id: str) -> Optional[str]:
        """Get error output from a process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Error output or None if not available
        """
        process_state = self._processes.get(process_id)
        if not process_state or not process_state.error_file:
            return None
        
        try:
            error_path = Path(process_state.error_file)
            if error_path.exists():
                with open(error_path, 'r') as f:
                    return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read process error: {e}")
        
        return None
    
    async def terminate_process(self, process_id: str, force: bool = False) -> bool:
        """Terminate a running process.
        
        Args:
            process_id: Process identifier
            force: Force termination (SIGKILL vs SIGTERM)
            
        Returns:
            True if terminated successfully
        """
        process_handle = self._process_handles.get(process_id)
        process_state = self._processes.get(process_id)
        
        if not process_handle or not process_state:
            return False
        
        try:
            if process_handle.poll() is None:  # Process still running
                if os.name == 'nt':  # Windows
                    if force:
                        process_handle.kill()
                    else:
                        process_handle.terminate()
                else:  # Unix-like
                    sig = signal.SIGKILL if force else signal.SIGTERM
                    os.killpg(os.getpgid(process_handle.pid), sig)
                
                # Wait for termination
                try:
                    process_handle.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if not force:
                        # Force kill if graceful termination failed
                        return await self.terminate_process(process_id, force=True)
            
            # Update process state
            process_state.status = "killed"
            process_state.completed_at = datetime.now()
            process_state.exit_code = process_handle.returncode
            
            # Cleanup
            await self._cleanup_process(process_id)
            
            self.logger.info(f"Terminated process {process_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to terminate process {process_id}: {e}")
            return False
    
    async def list_project_processes(self, project_id: str) -> List[ProcessState]:
        """List all processes for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of process states
        """
        process_ids = self._project_processes.get(project_id, set())
        processes = []
        
        for process_id in process_ids:
            process_state = self._processes.get(process_id)
            if process_state:
                await self._update_process_state(process_id)
                processes.append(process_state)
        
        return processes
    
    async def cleanup_project_processes(self, project_id: str) -> int:
        """Cleanup all processes for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of processes cleaned up
        """
        process_ids = list(self._project_processes.get(project_id, set()))
        cleaned_count = 0
        
        for process_id in process_ids:
            if await self.terminate_process(process_id):
                cleaned_count += 1
        
        # Remove project tracking
        if project_id in self._project_processes:
            del self._project_processes[project_id]
        
        # Cleanup workspace
        project_workspace = self.workspace_dir / project_id
        if project_workspace.exists():
            try:
                import shutil
                shutil.rmtree(project_workspace)
            except Exception as e:
                self.logger.error(f"Failed to cleanup project workspace: {e}")
        
        return cleaned_count
    
    async def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics.
        
        Returns:
            Resource usage information
        """
        total_memory = 0.0
        total_cpu = 0.0
        process_count = 0
        
        for process_id in list(self._processes.keys()):
            await self._update_process_state(process_id)
            process_state = self._processes[process_id]
            
            if process_state.status == "running":
                total_memory += process_state.memory_usage_mb
                total_cpu += process_state.cpu_usage_percent
                process_count += 1
        
        return {
            "active_processes": process_count,
            "total_memory_mb": total_memory,
            "total_cpu_percent": total_cpu,
            "memory_limit_mb": self.resource_limits.max_total_memory_mb,
            "process_limit": self.resource_limits.max_concurrent_processes,
            "memory_usage_percent": (total_memory / self.resource_limits.max_total_memory_mb) * 100,
            "process_usage_percent": (process_count / self.resource_limits.max_concurrent_processes) * 100
        }
    
    # Private methods
    
    def _build_limited_command(self, command: str, config: ProcessConfig) -> str:
        """Build command with resource limits."""
        if os.name == 'nt':  # Windows
            # Use Windows job objects for resource limits (simplified)
            return command
        else:  # Unix-like
            # Use ulimit for resource limits
            limits = []
            
            # Memory limit (in KB)
            memory_kb = config.max_memory_mb * 1024
            limits.append(f"ulimit -v {memory_kb}")
            
            # CPU time limit (in seconds)
            limits.append(f"ulimit -t {config.timeout_seconds}")
            
            # Priority
            if config.priority != 0:
                limits.append(f"nice -n {config.priority}")
            
            return " && ".join(limits + [command])
    
    async def _check_resource_availability(self) -> bool:
        """Check if resources are available for new process."""
        usage = await self.get_resource_usage()
        
        # Check process limit
        if usage["active_processes"] >= self.resource_limits.max_concurrent_processes:
            return False
        
        # Check memory limit
        if usage["memory_usage_percent"] >= self.resource_limits.cleanup_threshold_percent:
            return False
        
        return True
    
    async def _update_process_state(self, process_id: str):
        """Update process state with current metrics."""
        process_handle = self._process_handles.get(process_id)
        process_state = self._processes.get(process_id)
        
        if not process_handle or not process_state:
            return
        
        try:
            # Check if process is still running
            if process_handle.poll() is not None:
                # Process completed
                if process_state.status == "running":
                    process_state.status = "completed" if process_handle.returncode == 0 else "failed"
                    process_state.completed_at = datetime.now()
                    process_state.exit_code = process_handle.returncode
                return
            
            # Get resource usage
            if process_state.pid:
                try:
                    proc = psutil.Process(process_state.pid)
                    process_state.memory_usage_mb = proc.memory_info().rss / (1024 * 1024)
                    process_state.cpu_usage_percent = proc.cpu_percent()
                    
                    # Check memory limit
                    if process_state.memory_usage_mb > self.resource_limits.max_memory_per_process_mb:
                        self.logger.warning(f"Process {process_id} exceeded memory limit")
                        await self.terminate_process(process_id)
                        
                except psutil.NoSuchProcess:
                    # Process no longer exists
                    process_state.status = "failed"
                    process_state.completed_at = datetime.now()
                    
        except Exception as e:
            self.logger.error(f"Failed to update process state for {process_id}: {e}")
    
    async def _process_timeout(self, process_id: str, timeout_seconds: int):
        """Handle process timeout."""
        await asyncio.sleep(timeout_seconds)
        
        process_state = self._processes.get(process_id)
        if process_state and process_state.status == "running":
            self.logger.warning(f"Process {process_id} timed out")
            await self.terminate_process(process_id)
    
    async def _cleanup_process(self, process_id: str):
        """Cleanup process resources."""
        # Remove from tracking
        if process_id in self._process_handles:
            del self._process_handles[process_id]
        
        process_state = self._processes.get(process_id)
        if process_state:
            # Remove from project tracking
            project_processes = self._project_processes.get(process_state.project_id, set())
            project_processes.discard(process_id)
            
            if not project_processes and process_state.project_id in self._project_processes:
                del self._project_processes[process_state.project_id]
    
    async def _resource_monitor(self):
        """Background resource monitoring."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)
                
                # Update all process states
                for process_id in list(self._processes.keys()):
                    await self._update_process_state(process_id)
                
                # Check resource usage
                usage = await self.get_resource_usage()
                
                if usage["memory_usage_percent"] > self.resource_limits.cleanup_threshold_percent:
                    self.logger.warning("High memory usage detected, triggering cleanup")
                    await self._emergency_cleanup()
                    
            except Exception as e:
                self.logger.error(f"Resource monitor error: {e}")
    
    async def _cleanup_worker(self):
        """Background cleanup worker."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Cleanup completed processes older than 1 hour
                cutoff_time = datetime.now().timestamp() - 3600
                
                to_remove = []
                for process_id, process_state in self._processes.items():
                    if (process_state.status in ["completed", "failed", "killed"] and
                        process_state.completed_at and
                        process_state.completed_at.timestamp() < cutoff_time):
                        to_remove.append(process_id)
                
                for process_id in to_remove:
                    await self._cleanup_process(process_id)
                    del self._processes[process_id]
                    
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")
    
    async def _emergency_cleanup(self):
        """Emergency cleanup when resources are exhausted."""
        # Find oldest completed processes
        completed_processes = [
            (pid, state) for pid, state in self._processes.items()
            if state.status in ["completed", "failed", "killed"]
        ]
        
        # Sort by completion time
        completed_processes.sort(key=lambda x: x[1].completed_at or datetime.min)
        
        # Remove oldest processes
        cleanup_count = max(1, len(completed_processes) // 4)
        for i in range(min(cleanup_count, len(completed_processes))):
            process_id = completed_processes[i][0]
            await self._cleanup_process(process_id)
            del self._processes[process_id]
        
        self.logger.info(f"Emergency cleanup removed {cleanup_count} processes")