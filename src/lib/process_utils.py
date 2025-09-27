"""Process isolation utilities with cleanup policies."""

import asyncio
import logging
import os
import psutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel

from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity


class ProcessResource(BaseModel):
    """Resource usage information for a process."""
    pid: int
    memory_mb: float
    cpu_percent: float
    open_files: int
    threads: int
    status: str
    start_time: datetime


class ProcessCleanupPolicy(BaseModel):
    """Policy for process cleanup operations."""
    max_age_seconds: int = 3600  # 1 hour
    max_memory_mb: int = 1024   # 1 GB
    max_cpu_percent: float = 90.0
    max_processes_per_project: int = 10
    cleanup_interval_seconds: int = 300  # 5 minutes
    force_kill_timeout: int = 30  # 30 seconds for graceful shutdown
    orphan_detection: bool = True
    resource_monitoring: bool = True


class ProcessWorkspace(BaseModel):
    """Workspace configuration for isolated processes."""
    base_path: Path
    project_id: str
    process_id: str
    temp_dir: Optional[Path] = None
    log_file: Optional[Path] = None
    input_file: Optional[Path] = None
    output_file: Optional[Path] = None
    error_file: Optional[Path] = None


class ProcessMonitor:
    """Monitors process resource usage and health."""
    
    def __init__(self, cleanup_policy: ProcessCleanupPolicy):
        """Initialize process monitor.
        
        Args:
            cleanup_policy: Cleanup policy configuration
        """
        self.cleanup_policy = cleanup_policy
        self.monitored_processes: Dict[int, ProcessResource] = {}
        self.process_projects: Dict[int, str] = {}  # pid -> project_id
        self.project_processes: Dict[str, Set[int]] = {}  # project_id -> {pids}
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start process monitoring and cleanup tasks."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        # Start monitoring task
        if self.cleanup_policy.resource_monitoring:
            self._monitor_task = asyncio.create_task(self._monitoring_worker())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        self.logger.info("Process monitoring started")
    
    async def stop_monitoring(self):
        """Stop process monitoring and cleanup tasks."""
        self._monitoring_active = False
        
        # Cancel tasks
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Process monitoring stopped")
    
    def register_process(self, pid: int, project_id: str):
        """Register a process for monitoring.
        
        Args:
            pid: Process ID
            project_id: Project identifier
        """
        self.process_projects[pid] = project_id
        
        if project_id not in self.project_processes:
            self.project_processes[project_id] = set()
        
        self.project_processes[project_id].add(pid)
        
        # Update process resource info
        self._update_process_resource(pid)
        
        self.logger.debug(f"Registered process {pid} for project {project_id}")
    
    def unregister_process(self, pid: int):
        """Unregister a process from monitoring.
        
        Args:
            pid: Process ID
        """
        project_id = self.process_projects.get(pid)
        
        if project_id and project_id in self.project_processes:
            self.project_processes[project_id].discard(pid)
            
            # Clean up empty project entries
            if not self.project_processes[project_id]:
                del self.project_processes[project_id]
        
        self.process_projects.pop(pid, None)
        self.monitored_processes.pop(pid, None)
        
        self.logger.debug(f"Unregistered process {pid}")
    
    def get_process_resource(self, pid: int) -> Optional[ProcessResource]:
        """Get resource information for a process.
        
        Args:
            pid: Process ID
            
        Returns:
            Process resource information or None if not found
        """
        return self.monitored_processes.get(pid)
    
    def get_project_processes(self, project_id: str) -> List[ProcessResource]:
        """Get all processes for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of process resources
        """
        pids = self.project_processes.get(project_id, set())
        return [
            self.monitored_processes[pid]
            for pid in pids
            if pid in self.monitored_processes
        ]
    
    async def cleanup_project_processes(self, project_id: str) -> int:
        """Cleanup all processes for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of processes cleaned up
        """
        pids = list(self.project_processes.get(project_id, set()))
        cleanup_count = 0
        
        for pid in pids:
            if await self._terminate_process(pid):
                cleanup_count += 1
        
        # Clean up project tracking
        self.project_processes.pop(project_id, None)
        
        self.logger.info(f"Cleaned up {cleanup_count} processes for project {project_id}")
        return cleanup_count
    
    async def cleanup_by_policy(self) -> Dict[str, int]:
        """Cleanup processes based on policy rules.
        
        Returns:
            Cleanup statistics
        """
        stats = {
            "age_violations": 0,
            "memory_violations": 0,
            "cpu_violations": 0,
            "orphaned_processes": 0,
            "project_limit_violations": 0,
            "total_cleaned": 0
        }
        
        current_time = datetime.now()
        
        # Check each monitored process
        pids_to_cleanup = set()
        
        for pid, resource in self.monitored_processes.items():
            # Age-based cleanup
            age_seconds = (current_time - resource.start_time).total_seconds()
            if age_seconds > self.cleanup_policy.max_age_seconds:
                pids_to_cleanup.add(pid)
                stats["age_violations"] += 1
                continue
            
            # Memory-based cleanup
            if resource.memory_mb > self.cleanup_policy.max_memory_mb:
                pids_to_cleanup.add(pid)
                stats["memory_violations"] += 1
                continue
            
            # CPU-based cleanup
            if resource.cpu_percent > self.cleanup_policy.max_cpu_percent:
                pids_to_cleanup.add(pid)
                stats["cpu_violations"] += 1
                continue
        
        # Check for orphaned processes
        if self.cleanup_policy.orphan_detection:
            orphaned_pids = await self._detect_orphaned_processes()
            pids_to_cleanup.update(orphaned_pids)
            stats["orphaned_processes"] = len(orphaned_pids)
        
        # Check project process limits
        for project_id, pids in self.project_processes.items():
            if len(pids) > self.cleanup_policy.max_processes_per_project:
                # Remove oldest processes
                sorted_pids = sorted(
                    pids,
                    key=lambda p: self.monitored_processes.get(p, ProcessResource(
                        pid=p, memory_mb=0, cpu_percent=0, open_files=0,
                        threads=0, status="unknown", start_time=datetime.now()
                    )).start_time
                )
                
                excess_pids = sorted_pids[:-self.cleanup_policy.max_processes_per_project]
                pids_to_cleanup.update(excess_pids)
                stats["project_limit_violations"] += len(excess_pids)
        
        # Perform cleanup
        cleanup_tasks = [self._terminate_process(pid) for pid in pids_to_cleanup]
        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            stats["total_cleaned"] = sum(1 for result in results if result is True)
        
        return stats
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics.
        
        Returns:
            Monitoring statistics
        """
        total_memory = sum(r.memory_mb for r in self.monitored_processes.values())
        total_cpu = sum(r.cpu_percent for r in self.monitored_processes.values())
        
        return {
            "total_processes": len(self.monitored_processes),
            "total_projects": len(self.project_processes),
            "total_memory_mb": round(total_memory, 2),
            "total_cpu_percent": round(total_cpu, 2),
            "monitoring_active": self._monitoring_active,
            "policy": self.cleanup_policy.dict(),
            "processes_by_project": {
                project_id: len(pids)
                for project_id, pids in self.project_processes.items()
            }
        }
    
    # Private methods
    
    async def _monitoring_worker(self):
        """Background worker for process monitoring."""
        while self._monitoring_active:
            try:
                # Update resource information for all monitored processes
                for pid in list(self.monitored_processes.keys()):
                    self._update_process_resource(pid)
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Process monitoring error: {e}")
                await asyncio.sleep(5)  # Shorter sleep on error
    
    async def _cleanup_worker(self):
        """Background worker for process cleanup."""
        while self._monitoring_active:
            try:
                await asyncio.sleep(self.cleanup_policy.cleanup_interval_seconds)
                
                if self._monitoring_active:  # Check again after sleep
                    stats = await self.cleanup_by_policy()
                    
                    if stats["total_cleaned"] > 0:
                        self.logger.info(f"Cleanup completed: {stats}")
                
            except Exception as e:
                self.logger.error(f"Process cleanup error: {e}")
    
    def _update_process_resource(self, pid: int):
        """Update resource information for a process.
        
        Args:
            pid: Process ID
        """
        try:
            proc = psutil.Process(pid)
            
            # Get memory info
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get CPU percent
            cpu_percent = proc.cpu_percent()
            
            # Get other stats
            open_files = len(proc.open_files())
            threads = proc.num_threads()
            status = proc.status()
            start_time = datetime.fromtimestamp(proc.create_time())
            
            self.monitored_processes[pid] = ProcessResource(
                pid=pid,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                open_files=open_files,
                threads=threads,
                status=status,
                start_time=start_time
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process no longer exists or access denied
            self.unregister_process(pid)
        except Exception as e:
            self.logger.error(f"Error updating process {pid} resource info: {e}")
    
    async def _detect_orphaned_processes(self) -> Set[int]:
        """Detect orphaned processes that should be cleaned up.
        
        Returns:
            Set of orphaned process IDs
        """
        orphaned = set()
        
        for pid in list(self.monitored_processes.keys()):
            try:
                proc = psutil.Process(pid)
                
                # Check if parent process exists and is reasonable
                try:
                    parent = proc.parent()
                    if parent is None or parent.pid == 1:  # Init process
                        orphaned.add(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    orphaned.add(pid)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process already gone
                self.unregister_process(pid)
        
        return orphaned
    
    async def _terminate_process(self, pid: int) -> bool:
        """Terminate a process gracefully, then forcefully if needed.
        
        Args:
            pid: Process ID
            
        Returns:
            True if process was terminated
        """
        try:
            proc = psutil.Process(pid)
            
            # Try graceful termination first
            proc.terminate()
            
            # Wait for graceful termination
            try:
                proc.wait(timeout=self.cleanup_policy.force_kill_timeout)
                self.unregister_process(pid)
                return True
            except psutil.TimeoutExpired:
                # Force kill if graceful termination failed
                proc.kill()
                proc.wait(timeout=5)  # Short wait for force kill
                self.unregister_process(pid)
                return True
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process already gone or access denied
            self.unregister_process(pid)
            return True
        except Exception as e:
            self.logger.error(f"Failed to terminate process {pid}: {e}")
            return False


class ProcessWorkspaceManager:
    """Manages isolated workspaces for processes."""
    
    def __init__(self, base_workspace_dir: str = "process_workspaces"):
        """Initialize workspace manager.
        
        Args:
            base_workspace_dir: Base directory for workspaces
        """
        self.base_workspace_dir = Path(base_workspace_dir)
        self.base_workspace_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Active workspaces
        self.active_workspaces: Dict[str, ProcessWorkspace] = {}
    
    def create_workspace(
        self,
        project_id: str,
        process_id: str,
        create_temp_dir: bool = True,
        create_log_files: bool = True
    ) -> ProcessWorkspace:
        """Create isolated workspace for a process.
        
        Args:
            project_id: Project identifier
            process_id: Process identifier
            create_temp_dir: Create temporary directory
            create_log_files: Create log files
            
        Returns:
            Process workspace configuration
        """
        # Create workspace directory
        workspace_path = self.base_workspace_dir / project_id / process_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create workspace configuration
        workspace = ProcessWorkspace(
            base_path=workspace_path,
            project_id=project_id,
            process_id=process_id
        )
        
        # Create temporary directory if requested
        if create_temp_dir:
            temp_dir = workspace_path / "temp"
            temp_dir.mkdir(exist_ok=True)
            workspace.temp_dir = temp_dir
        
        # Create log files if requested
        if create_log_files:
            workspace.log_file = workspace_path / "process.log"
            workspace.error_file = workspace_path / "error.log"
            workspace.input_file = workspace_path / "input.json"
            workspace.output_file = workspace_path / "output.json"
        
        # Track workspace
        workspace_key = f"{project_id}_{process_id}"
        self.active_workspaces[workspace_key] = workspace
        
        self.logger.debug(f"Created workspace for {workspace_key} at {workspace_path}")
        
        return workspace
    
    def get_workspace(self, project_id: str, process_id: str) -> Optional[ProcessWorkspace]:
        """Get existing workspace configuration.
        
        Args:
            project_id: Project identifier
            process_id: Process identifier
            
        Returns:
            Process workspace or None if not found
        """
        workspace_key = f"{project_id}_{process_id}"
        return self.active_workspaces.get(workspace_key)
    
    def cleanup_workspace(self, project_id: str, process_id: str) -> bool:
        """Cleanup workspace for a process.
        
        Args:
            project_id: Project identifier
            process_id: Process identifier
            
        Returns:
            True if cleaned up successfully
        """
        workspace_key = f"{project_id}_{process_id}"
        workspace = self.active_workspaces.get(workspace_key)
        
        if not workspace:
            return False
        
        try:
            # Remove workspace directory
            import shutil
            if workspace.base_path.exists():
                shutil.rmtree(workspace.base_path)
            
            # Remove from tracking
            del self.active_workspaces[workspace_key]
            
            self.logger.debug(f"Cleaned up workspace for {workspace_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup workspace {workspace_key}: {e}")
            return False
    
    def cleanup_project_workspaces(self, project_id: str) -> int:
        """Cleanup all workspaces for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of workspaces cleaned up
        """
        cleanup_count = 0
        
        # Find workspaces for project
        workspaces_to_cleanup = [
            key for key in self.active_workspaces.keys()
            if key.startswith(f"{project_id}_")
        ]
        
        for workspace_key in workspaces_to_cleanup:
            project_id_part, process_id = workspace_key.split("_", 1)
            if self.cleanup_workspace(project_id_part, process_id):
                cleanup_count += 1
        
        return cleanup_count
    
    def get_workspace_stats(self) -> Dict[str, Any]:
        """Get workspace statistics.
        
        Returns:
            Workspace statistics
        """
        total_size = 0
        project_counts = {}
        
        for workspace_key, workspace in self.active_workspaces.items():
            # Calculate workspace size
            try:
                size = sum(
                    f.stat().st_size
                    for f in workspace.base_path.rglob("*")
                    if f.is_file()
                )
                total_size += size
            except Exception:
                pass  # Ignore errors in size calculation
            
            # Count by project
            project_id = workspace.project_id
            project_counts[project_id] = project_counts.get(project_id, 0) + 1
        
        return {
            "total_workspaces": len(self.active_workspaces),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "projects": len(project_counts),
            "workspaces_by_project": project_counts,
            "base_workspace_dir": str(self.base_workspace_dir)
        }


class ProcessIsolationUtils:
    """Utilities for process isolation and management."""
    
    def __init__(
        self,
        cleanup_policy: Optional[ProcessCleanupPolicy] = None,
        workspace_dir: str = "process_workspaces",
        error_handler: Optional[ErrorHandler] = None
    ):
        """Initialize process isolation utilities.
        
        Args:
            cleanup_policy: Process cleanup policy
            workspace_dir: Base workspace directory
            error_handler: Error handler instance
        """
        self.cleanup_policy = cleanup_policy or ProcessCleanupPolicy()
        self.workspace_manager = ProcessWorkspaceManager(workspace_dir)
        self.process_monitor = ProcessMonitor(self.cleanup_policy)
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start process isolation utilities."""
        await self.process_monitor.start_monitoring()
        self.logger.info("Process isolation utilities started")
    
    async def stop(self):
        """Stop process isolation utilities."""
        await self.process_monitor.stop_monitoring()
        self.logger.info("Process isolation utilities stopped")
    
    def create_isolated_process_env(
        self,
        project_id: str,
        process_id: str,
        additional_env: Optional[Dict[str, str]] = None
    ) -> Tuple[ProcessWorkspace, Dict[str, str]]:
        """Create isolated environment for a process.
        
        Args:
            project_id: Project identifier
            process_id: Process identifier
            additional_env: Additional environment variables
            
        Returns:
            Tuple of (workspace, environment_variables)
        """
        # Create workspace
        workspace = self.workspace_manager.create_workspace(project_id, process_id)
        
        # Build environment variables
        env = os.environ.copy()
        env.update({
            "PROJECT_ID": project_id,
            "PROCESS_ID": process_id,
            "WORKSPACE_PATH": str(workspace.base_path),
            "TEMP_DIR": str(workspace.temp_dir) if workspace.temp_dir else "",
            "LOG_FILE": str(workspace.log_file) if workspace.log_file else "",
            "ERROR_FILE": str(workspace.error_file) if workspace.error_file else "",
            "INPUT_FILE": str(workspace.input_file) if workspace.input_file else "",
            "OUTPUT_FILE": str(workspace.output_file) if workspace.output_file else ""
        })
        
        if additional_env:
            env.update(additional_env)
        
        return workspace, env
    
    async def launch_isolated_process(
        self,
        command: str,
        project_id: str,
        process_id: str,
        additional_env: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None
    ) -> Tuple[subprocess.Popen, ProcessWorkspace]:
        """Launch process in isolated environment.
        
        Args:
            command: Command to execute
            project_id: Project identifier
            process_id: Process identifier
            additional_env: Additional environment variables
            timeout_seconds: Process timeout
            
        Returns:
            Tuple of (process, workspace)
        """
        # Create isolated environment
        workspace, env = self.create_isolated_process_env(
            project_id, process_id, additional_env
        )
        
        try:
            # Setup stdio redirection
            stdout_file = None
            stderr_file = None
            
            if workspace.log_file:
                stdout_file = open(workspace.log_file, 'w')
            
            if workspace.error_file:
                stderr_file = open(workspace.error_file, 'w')
            
            # Launch process
            process = subprocess.Popen(
                command,
                shell=True,
                env=env,
                cwd=workspace.base_path,
                stdout=stdout_file or subprocess.PIPE,
                stderr=stderr_file or subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Register with monitor
            self.process_monitor.register_process(process.pid, project_id)
            
            # Set timeout if specified
            if timeout_seconds:
                asyncio.create_task(self._timeout_process(process, timeout_seconds))
            
            self.logger.info(f"Launched isolated process {process.pid} for {project_id}")
            
            return process, workspace
            
        except Exception as e:
            # Cleanup on failure
            self.workspace_manager.cleanup_workspace(project_id, process_id)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    error=e,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.PROCESSING,
                    component="process_isolation",
                    operation="launch_process"
                )
            
            raise
    
    async def _timeout_process(self, process: subprocess.Popen, timeout_seconds: int):
        """Handle process timeout.
        
        Args:
            process: Process to monitor
            timeout_seconds: Timeout in seconds
        """
        await asyncio.sleep(timeout_seconds)
        
        try:
            if process.poll() is None:  # Process still running
                self.logger.warning(f"Process {process.pid} timed out, terminating")
                
                # Try graceful termination
                process.terminate()
                
                # Wait briefly for graceful termination
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill
                    process.kill()
                    process.wait(timeout=5)
                
                # Unregister from monitor
                self.process_monitor.unregister_process(process.pid)
                
        except Exception as e:
            self.logger.error(f"Error handling process timeout: {e}")
    
    async def cleanup_project(self, project_id: str) -> Dict[str, int]:
        """Cleanup all resources for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Cleanup statistics
        """
        stats = {
            "processes_cleaned": 0,
            "workspaces_cleaned": 0
        }
        
        # Cleanup processes
        stats["processes_cleaned"] = await self.process_monitor.cleanup_project_processes(project_id)
        
        # Cleanup workspaces
        stats["workspaces_cleaned"] = self.workspace_manager.cleanup_project_workspaces(project_id)
        
        self.logger.info(f"Project {project_id} cleanup completed: {stats}")
        
        return stats
    
    def get_isolation_stats(self) -> Dict[str, Any]:
        """Get comprehensive isolation statistics.
        
        Returns:
            Isolation statistics
        """
        return {
            "process_monitoring": self.process_monitor.get_monitoring_stats(),
            "workspace_management": self.workspace_manager.get_workspace_stats(),
            "cleanup_policy": self.cleanup_policy.dict()
        }


# Global process isolation utilities
process_utils = ProcessIsolationUtils()


async def initialize_process_isolation(
    cleanup_policy: Optional[ProcessCleanupPolicy] = None,
    workspace_dir: str = "process_workspaces"
) -> ProcessIsolationUtils:
    """Initialize global process isolation utilities.
    
    Args:
        cleanup_policy: Process cleanup policy
        workspace_dir: Base workspace directory
        
    Returns:
        Initialized process utilities
    """
    global process_utils
    process_utils = ProcessIsolationUtils(cleanup_policy, workspace_dir)
    await process_utils.start()
    
    return process_utils