"""Redis connection and session state management with project isolation."""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as redis
from pydantic import BaseModel

from ..models.session import SessionData
from ..models.story import StoryData
from ..models.analysis import AnalysisResult


class RedisConfig(BaseModel):
    """Redis configuration settings."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    max_connections: int = 20


class ProjectIsolationManager:
    """Manages project-based key isolation in Redis."""
    
    def __init__(self, base_prefix: str = "story_service"):
        """Initialize project isolation manager.
        
        Args:
            base_prefix: Base prefix for all Redis keys
        """
        self.base_prefix = base_prefix
        self.project_separator = ":"
        self.logger = logging.getLogger(__name__)
    
    def get_project_key(self, project_id: str, key_type: str, key_id: str) -> str:
        """Generate isolated key for project.
        
        Args:
            project_id: Project identifier
            key_type: Type of data (session, analysis, etc.)
            key_id: Specific key identifier
            
        Returns:
            Fully qualified Redis key
        """
        # Sanitize project_id
        safe_project_id = self._sanitize_project_id(project_id)
        
        return f"{self.base_prefix}{self.project_separator}{safe_project_id}{self.project_separator}{key_type}{self.project_separator}{key_id}"
    
    def parse_project_key(self, redis_key: str) -> Optional[Dict[str, str]]:
        """Parse project key components.
        
        Args:
            redis_key: Redis key to parse
            
        Returns:
            Key components or None if invalid
        """
        try:
            parts = redis_key.split(self.project_separator)
            
            if len(parts) >= 4 and parts[0] == self.base_prefix:
                return {
                    "project_id": parts[1],
                    "key_type": parts[2],
                    "key_id": self.project_separator.join(parts[3:])
                }
        except Exception as e:
            self.logger.error(f"Error parsing Redis key {redis_key}: {e}")
        
        return None
    
    def get_project_pattern(self, project_id: str, key_type: Optional[str] = None) -> str:
        """Generate pattern for project keys.
        
        Args:
            project_id: Project identifier
            key_type: Optional key type filter
            
        Returns:
            Redis key pattern
        """
        safe_project_id = self._sanitize_project_id(project_id)
        
        if key_type:
            return f"{self.base_prefix}{self.project_separator}{safe_project_id}{self.project_separator}{key_type}{self.project_separator}*"
        else:
            return f"{self.base_prefix}{self.project_separator}{safe_project_id}{self.project_separator}*"
    
    def _sanitize_project_id(self, project_id: str) -> str:
        """Sanitize project ID for Redis key safety.
        
        Args:
            project_id: Raw project identifier
            
        Returns:
            Sanitized project identifier
        """
        # Remove unsafe characters and limit length
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        sanitized = "".join(c for c in project_id if c in safe_chars)
        
        return sanitized[:50]  # Limit length


class RedisSessionManager:
    """Redis-based session state management with project isolation."""
    
    def __init__(self, redis_client: redis.Redis, config: Optional[RedisConfig] = None):
        """Initialize Redis session manager.
        
        Args:
            redis_client: Redis client instance
            config: Redis configuration
        """
        self.redis = redis_client
        self.config = config or RedisConfig()
        self.isolation_manager = ProjectIsolationManager()
        self.logger = logging.getLogger(__name__)
        
        # Session expiration settings
        self.session_ttl = 86400  # 24 hours
        self.analysis_ttl = 604800  # 7 days
        self.temp_data_ttl = 3600  # 1 hour
    
    async def store_session(
        self,
        session_data: SessionData,
        project_id: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Store session data with project isolation.
        
        Args:
            session_data: Session data to store
            project_id: Project identifier for isolation
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if stored successfully
        """
        try:
            session_key = self.isolation_manager.get_project_key(
                project_id=project_id,
                key_type="session",
                key_id=session_data.session_id
            )
            
            # Serialize session data
            session_json = json.dumps(session_data.dict(), default=str)
            
            # Store with TTL
            expiration = ttl or self.session_ttl
            await self.redis.setex(session_key, expiration, session_json)
            
            # Add to project session index
            await self._add_to_project_index(project_id, "sessions", session_data.session_id)
            
            self.logger.info(f"Stored session {session_data.session_id} for project {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing session: {e}")
            return False
    
    async def retrieve_session(
        self,
        session_id: str,
        project_id: str
    ) -> Optional[SessionData]:
        """Retrieve session data with project isolation.
        
        Args:
            session_id: Session identifier
            project_id: Project identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            session_key = self.isolation_manager.get_project_key(
                project_id=project_id,
                key_type="session",
                key_id=session_id
            )
            
            session_json = await self.redis.get(session_key)
            
            if session_json:
                session_dict = json.loads(session_json)
                
                # Parse datetime fields
                if "created_at" in session_dict:
                    session_dict["created_at"] = datetime.fromisoformat(session_dict["created_at"])
                if "last_accessed" in session_dict:
                    session_dict["last_accessed"] = datetime.fromisoformat(session_dict["last_accessed"])
                
                return SessionData(**session_dict)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    async def store_analysis_result(
        self,
        analysis_result: AnalysisResult,
        session_id: str,
        project_id: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Store analysis result with project isolation.
        
        Args:
            analysis_result: Analysis result to store
            session_id: Associated session ID
            project_id: Project identifier
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if stored successfully
        """
        try:
            # Generate unique analysis ID
            analysis_id = f"{session_id}_{analysis_result.analysis_type}_{int(datetime.now().timestamp())}"
            
            analysis_key = self.isolation_manager.get_project_key(
                project_id=project_id,
                key_type="analysis",
                key_id=analysis_id
            )
            
            # Serialize analysis data
            analysis_json = json.dumps(analysis_result.dict(), default=str)
            
            # Store with TTL
            expiration = ttl or self.analysis_ttl
            await self.redis.setex(analysis_key, expiration, analysis_json)
            
            # Add to session analysis index
            await self._add_to_session_analysis_index(project_id, session_id, analysis_id)
            
            self.logger.info(f"Stored analysis {analysis_id} for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing analysis result: {e}")
            return False
    
    async def retrieve_session_analyses(
        self,
        session_id: str,
        project_id: str
    ) -> List[AnalysisResult]:
        """Retrieve all analysis results for a session.
        
        Args:
            session_id: Session identifier
            project_id: Project identifier
            
        Returns:
            List of analysis results
        """
        try:
            # Get analysis IDs from session index
            index_key = self.isolation_manager.get_project_key(
                project_id=project_id,
                key_type="session_analyses",
                key_id=session_id
            )
            
            analysis_ids = await self.redis.smembers(index_key)
            analyses = []
            
            for analysis_id in analysis_ids:
                analysis_key = self.isolation_manager.get_project_key(
                    project_id=project_id,
                    key_type="analysis",
                    key_id=analysis_id.decode() if isinstance(analysis_id, bytes) else analysis_id
                )
                
                analysis_json = await self.redis.get(analysis_key)
                if analysis_json:
                    analysis_dict = json.loads(analysis_json)
                    analyses.append(AnalysisResult(**analysis_dict))
            
            return analyses
            
        except Exception as e:
            self.logger.error(f"Error retrieving session analyses: {e}")
            return []
    
    async def list_project_sessions(self, project_id: str) -> List[str]:
        """List all sessions for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of session IDs
        """
        try:
            index_key = self.isolation_manager.get_project_key(
                project_id=project_id,
                key_type="project_index",
                key_id="sessions"
            )
            
            session_ids = await self.redis.smembers(index_key)
            return [sid.decode() if isinstance(sid, bytes) else sid for sid in session_ids]
            
        except Exception as e:
            self.logger.error(f"Error listing project sessions: {e}")
            return []
    
    async def cleanup_project_data(self, project_id: str) -> int:
        """Cleanup all data for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of keys deleted
        """
        try:
            pattern = self.isolation_manager.get_project_pattern(project_id)
            keys = await self.redis.keys(pattern)
            
            if keys:
                deleted_count = await self.redis.delete(*keys)
                self.logger.info(f"Cleaned up {deleted_count} keys for project {project_id}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error cleaning up project data: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions across all projects.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            # This is a simplified cleanup - in production you'd want more sophisticated logic
            cleanup_count = 0
            
            # Get all session keys
            pattern = f"{self.isolation_manager.base_prefix}:*:session:*"
            session_keys = await self.redis.keys(pattern)
            
            for key in session_keys:
                ttl = await self.redis.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set default expiration
                    await self.redis.expire(key, self.session_ttl)
                elif ttl == -2:  # Key doesn't exist (expired)
                    cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project statistics
        """
        try:
            stats = {
                "project_id": project_id,
                "total_sessions": 0,
                "total_analyses": 0,
                "active_sessions": 0,
                "storage_usage": 0
            }
            
            # Count sessions
            sessions = await self.list_project_sessions(project_id)
            stats["total_sessions"] = len(sessions)
            
            # Count analyses and check active sessions
            for session_id in sessions:
                analyses = await self.retrieve_session_analyses(session_id, project_id)
                stats["total_analyses"] += len(analyses)
                
                # Check if session is active (has recent activity)
                session = await self.retrieve_session(session_id, project_id)
                if session and session.status == "active":
                    stats["active_sessions"] += 1
            
            # Estimate storage usage
            pattern = self.isolation_manager.get_project_pattern(project_id)
            keys = await self.redis.keys(pattern)
            
            for key in keys:
                try:
                    size = await self.redis.memory_usage(key)
                    if size:
                        stats["storage_usage"] += size
                except:
                    pass  # memory_usage not available in all Redis versions
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting project stats: {e}")
            return {"project_id": project_id, "error": str(e)}
    
    # Private helper methods
    
    async def _add_to_project_index(
        self,
        project_id: str,
        index_type: str,
        item_id: str
    ):
        """Add item to project index."""
        index_key = self.isolation_manager.get_project_key(
            project_id=project_id,
            key_type="project_index",
            key_id=index_type
        )
        
        await self.redis.sadd(index_key, item_id)
        await self.redis.expire(index_key, self.session_ttl * 2)  # Longer TTL for indices
    
    async def _add_to_session_analysis_index(
        self,
        project_id: str,
        session_id: str,
        analysis_id: str
    ):
        """Add analysis to session analysis index."""
        index_key = self.isolation_manager.get_project_key(
            project_id=project_id,
            key_type="session_analyses",
            key_id=session_id
        )
        
        await self.redis.sadd(index_key, analysis_id)
        await self.redis.expire(index_key, self.analysis_ttl)


class RedisConnectionManager:
    """Manages Redis connections with health checking and reconnection."""
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis connection manager.
        
        Args:
            config: Redis configuration
        """
        self.config = config or RedisConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.session_manager: Optional[RedisSessionManager] = None
        self.logger = logging.getLogger(__name__)
        self._health_check_task: Optional[asyncio.Task] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis server.
        
        Returns:
            True if connected successfully
        """
        try:
            # Create Redis client
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                ssl=self.config.ssl,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                max_connections=self.config.max_connections,
                decode_responses=False  # Handle bytes manually for better control
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize session manager
            self.session_manager = RedisSessionManager(self.redis_client, self.config)
            
            self._connected = True
            
            # Start health check
            self._health_check_task = asyncio.create_task(self._health_check_worker())
            
            self.logger.info("Connected to Redis successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis server."""
        try:
            self._connected = False
            
            # Stop health check
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("Disconnected from Redis")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Redis: {e}")
    
    async def is_healthy(self) -> bool:
        """Check if Redis connection is healthy.
        
        Returns:
            True if connection is healthy
        """
        try:
            if not self.redis_client or not self._connected:
                return False
            
            await self.redis_client.ping()
            return True
            
        except Exception:
            return False
    
    async def _health_check_worker(self):
        """Background health check worker."""
        while self._connected:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                if not await self.is_healthy():
                    self.logger.warning("Redis health check failed, attempting reconnection")
                    await self._reconnect()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
    
    async def _reconnect(self):
        """Attempt to reconnect to Redis."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            # Recreate connection
            await self.connect()
            
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")


# Global Redis connection manager
redis_manager = RedisConnectionManager()


async def get_redis_session_manager() -> Optional[RedisSessionManager]:
    """Get Redis session manager instance.
    
    Returns:
        Redis session manager or None if not connected
    """
    if redis_manager.session_manager:
        return redis_manager.session_manager
    
    # Try to connect if not already connected
    if await redis_manager.connect():
        return redis_manager.session_manager
    
    return None


async def initialize_redis_from_env() -> bool:
    """Initialize Redis connection from environment variables.
    
    Returns:
        True if initialized successfully
    """
    config = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        db=int(os.getenv("REDIS_DB", "0")),
        ssl=os.getenv("REDIS_SSL", "false").lower() == "true"
    )
    
    global redis_manager
    redis_manager = RedisConnectionManager(config)
    
    return await redis_manager.connect()