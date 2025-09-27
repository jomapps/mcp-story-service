"""StorySession model with process isolation context.

This model manages story analysis sessions with process isolation
per Clarification C and D for concurrent project handling.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear session management without complexity  
- LLM Declaration (VI): Structured for session tracking workflows
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, validator, root_validator


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETING = "completing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"


class IsolationLevel(str, Enum):
    """Process isolation levels."""
    FULL_ISOLATION = "full_isolation"
    SHARED_RESOURCES = "shared_resources"
    CLUSTERED = "clustered"


class SessionData(BaseModel):
    """Core session data structure."""
    story_arcs: List[Dict[str, Any]] = Field(default_factory=list, description="Story arcs in session")
    plot_threads: List[Dict[str, Any]] = Field(default_factory=list, description="Plot threads being tracked")
    consistency_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Applied consistency rules")
    narrative_beats: List[Dict[str, Any]] = Field(default_factory=list, description="Identified narrative beats")
    genre_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Applied genre patterns")
    
    # Analysis state
    current_analysis: Optional[Dict[str, Any]] = Field(None, description="Current analysis state")
    analysis_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of analyses")
    
    # Session context
    target_genre: Optional[str] = Field(None, description="Target genre for analysis")
    content_length: int = Field(0, description="Total content length analyzed")
    analysis_count: int = Field(0, description="Number of analyses performed")


class ProcessIsolationContext(BaseModel):
    """Process isolation context for concurrent projects."""
    process_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique process identifier")
    isolation_level: IsolationLevel = Field(IsolationLevel.FULL_ISOLATION, description="Isolation level")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits for process")
    
    # Isolation metadata
    memory_limit_mb: int = Field(512, description="Memory limit in MB")
    execution_timeout_seconds: int = Field(300, description="Execution timeout in seconds")
    max_concurrent_operations: int = Field(5, description="Max concurrent operations")
    
    # Process tracking
    parent_process_id: Optional[str] = Field(None, description="Parent process if clustered")
    child_processes: List[str] = Field(default_factory=list, description="Child process IDs")
    shared_resources: Dict[str, str] = Field(default_factory=dict, description="Shared resource identifiers")


class SessionMetrics(BaseModel):
    """Session performance and usage metrics."""
    total_requests: int = Field(0, description="Total requests processed")
    successful_analyses: int = Field(0, description="Successful analyses")
    failed_analyses: int = Field(0, description="Failed analyses")
    
    # Performance metrics
    avg_response_time_ms: float = Field(0.0, description="Average response time in milliseconds")
    total_processing_time_ms: float = Field(0.0, description="Total processing time")
    peak_memory_usage_mb: float = Field(0.0, description="Peak memory usage")
    
    # Quality metrics
    avg_confidence_score: float = Field(0.0, description="Average confidence across analyses")
    threshold_compliance_rate: float = Field(0.0, description="Rate of meeting 75% threshold")
    
    # Timestamps
    first_request_at: Optional[datetime] = Field(None, description="First request timestamp")
    last_request_at: Optional[datetime] = Field(None, description="Last request timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionConfiguration(BaseModel):
    """Session configuration and preferences."""
    # Analysis preferences
    confidence_threshold: float = Field(0.75, ge=0.0, le=1.0, description="Confidence threshold per FR-001")
    enable_genre_analysis: bool = Field(True, description="Enable genre pattern analysis")
    enable_consistency_checking: bool = Field(True, description="Enable consistency validation")
    enable_pacing_analysis: bool = Field(True, description="Enable pacing analysis")
    
    # Session behavior
    session_timeout_minutes: int = Field(60, ge=5, le=1440, description="Session timeout in minutes")
    auto_save_interval_minutes: int = Field(5, ge=1, le=60, description="Auto-save interval")
    max_content_length: int = Field(1000000, ge=1000, description="Maximum content length")
    
    # Quality settings
    require_threshold_compliance: bool = Field(True, description="Require 75% threshold compliance")
    enable_malformed_content_handling: bool = Field(True, description="Handle malformed content gracefully")
    
    # Process isolation
    isolation_config: ProcessIsolationContext = Field(default_factory=ProcessIsolationContext, description="Isolation configuration")


class StorySession(BaseModel):
    """
    Story session model with process isolation context.
    
    Manages analysis sessions with complete isolation between concurrent
    projects per Clarification C and session persistence per Clarification D.
    """
    
    # Core identification
    session_id: str = Field(..., description="Unique session identifier")
    project_id: str = Field(..., description="Project identifier for grouping")
    user_context: Optional[str] = Field(None, description="User or client context")
    
    # Session state
    status: SessionStatus = Field(SessionStatus.ACTIVE, description="Current session status")
    session_data: SessionData = Field(default_factory=SessionData, description="Core session data")
    configuration: SessionConfiguration = Field(default_factory=SessionConfiguration, description="Session configuration")
    
    # Timestamps and lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")
    
    # Performance and monitoring
    metrics: SessionMetrics = Field(default_factory=SessionMetrics, description="Session metrics")
    
    # Error tracking
    error_count: int = Field(0, description="Number of errors encountered")
    last_error: Optional[str] = Field(None, description="Last error message")
    error_history: List[Dict[str, Any]] = Field(default_factory=list, description="Error history")
    
    # Metadata
    version: str = Field(default="1.0", description="Session model version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "project_id": "movie_project_alpha",
                "status": "active",
                "created_at": "2024-01-01T12:00:00Z",
                "configuration": {
                    "confidence_threshold": 0.75,
                    "session_timeout_minutes": 60
                }
            }
        }

    @validator('expires_at', always=True)
    def set_expiration(cls, v, values):
        """Set expiration time based on configuration."""
        if v is None and 'created_at' in values and 'configuration' in values:
            timeout_minutes = 60  # Default
            if values['configuration']:
                timeout_minutes = values['configuration'].session_timeout_minutes
            return values['created_at'] + timedelta(minutes=timeout_minutes)
        return v

    @root_validator
    def validate_session_consistency(cls, values):
        """Validate session state consistency."""
        status = values.get('status')
        completed_at = values.get('completed_at')
        
        if status == SessionStatus.COMPLETED and not completed_at:
            values['completed_at'] = datetime.utcnow()
        
        if completed_at and status not in [SessionStatus.COMPLETED, SessionStatus.ERROR]:
            raise ValueError("completed_at can only be set for completed or error sessions")
        
        return values

    def update_access_time(self) -> None:
        """Update last access time and extend expiration if needed."""
        self.last_accessed = datetime.utcnow()
        
        # Extend expiration for active sessions
        if self.status == SessionStatus.ACTIVE:
            timeout_minutes = self.configuration.session_timeout_minutes
            self.expires_at = self.last_accessed + timedelta(minutes=timeout_minutes)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        return (
            self.status == SessionStatus.ACTIVE and
            not self.is_expired()
        )

    def add_story_arc(self, story_arc_data: Dict[str, Any]) -> str:
        """Add story arc to session."""
        story_arc_id = story_arc_data.get('story_id', str(uuid4()))
        
        # Add timestamp
        story_arc_data['added_at'] = datetime.utcnow().isoformat()
        story_arc_data['session_id'] = self.session_id
        
        self.session_data.story_arcs.append(story_arc_data)
        self.update_access_time()
        
        return story_arc_id

    def add_plot_thread(self, plot_thread_data: Dict[str, Any]) -> str:
        """Add plot thread to session."""
        thread_id = plot_thread_data.get('thread_id', str(uuid4()))
        
        # Add session context
        plot_thread_data['session_id'] = self.session_id
        plot_thread_data['added_at'] = datetime.utcnow().isoformat()
        
        self.session_data.plot_threads.append(plot_thread_data)
        self.update_access_time()
        
        return thread_id

    def update_analysis_metrics(self, analysis_result: Dict[str, Any], 
                              processing_time_ms: float, success: bool = True) -> None:
        """Update session metrics with analysis results."""
        self.metrics.total_requests += 1
        self.metrics.total_processing_time_ms += processing_time_ms
        
        if success:
            self.metrics.successful_analyses += 1
            
            # Update confidence tracking
            confidence = analysis_result.get('confidence', 0.0)
            if self.metrics.avg_confidence_score == 0.0:
                self.metrics.avg_confidence_score = confidence
            else:
                # Running average
                total_successful = self.metrics.successful_analyses
                self.metrics.avg_confidence_score = (
                    (self.metrics.avg_confidence_score * (total_successful - 1) + confidence) /
                    total_successful
                )
            
            # Update threshold compliance
            if confidence >= self.configuration.confidence_threshold:
                compliant_count = self.metrics.threshold_compliance_rate * (total_successful - 1) + 1
                self.metrics.threshold_compliance_rate = compliant_count / total_successful
            else:
                compliant_count = self.metrics.threshold_compliance_rate * (total_successful - 1)
                self.metrics.threshold_compliance_rate = compliant_count / total_successful
        else:
            self.metrics.failed_analyses += 1
        
        # Update response time
        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time_ms = processing_time_ms
        else:
            self.metrics.avg_response_time_ms = (
                (self.metrics.avg_response_time_ms * (self.metrics.total_requests - 1) + processing_time_ms) /
                self.metrics.total_requests
            )
        
        # Update timestamps
        now = datetime.utcnow()
        if not self.metrics.first_request_at:
            self.metrics.first_request_at = now
        self.metrics.last_request_at = now
        
        self.update_access_time()

    def record_error(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Record an error in the session."""
        self.error_count += 1
        self.last_error = error_message
        
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_message,
            "details": error_details or {},
            "error_count": self.error_count
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 50 errors
        if len(self.error_history) > 50:
            self.error_history = self.error_history[-50:]
        
        # Check if session should be marked as error state
        recent_errors = [e for e in self.error_history 
                        if datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(minutes=5)]
        
        if len(recent_errors) >= 5:  # 5 errors in 5 minutes
            self.status = SessionStatus.ERROR

    def complete_session(self, completion_reason: str = "analysis_complete") -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.metadata["completion_reason"] = completion_reason

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        return {
            "session_info": {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "status": self.status.value,
                "created_at": self.created_at.isoformat(),
                "last_accessed": self.last_accessed.isoformat(),
                "is_active": self.is_active(),
                "is_expired": self.is_expired()
            },
            "content_summary": {
                "story_arcs": len(self.session_data.story_arcs),
                "plot_threads": len(self.session_data.plot_threads),
                "narrative_beats": len(self.session_data.narrative_beats),
                "analyses_performed": self.session_data.analysis_count,
                "target_genre": self.session_data.target_genre
            },
            "performance": {
                "total_requests": self.metrics.total_requests,
                "success_rate": f"{(self.metrics.successful_analyses / max(self.metrics.total_requests, 1)):.1%}",
                "avg_response_time": f"{self.metrics.avg_response_time_ms:.1f}ms",
                "avg_confidence": f"{self.metrics.avg_confidence_score:.1%}",
                "threshold_compliance": f"{self.metrics.threshold_compliance_rate:.1%}"
            },
            "isolation": {
                "process_id": self.configuration.isolation_config.process_id,
                "isolation_level": self.configuration.isolation_config.isolation_level.value,
                "memory_limit": f"{self.configuration.isolation_config.memory_limit_mb}MB",
                "concurrent_limit": self.configuration.isolation_config.max_concurrent_operations
            },
            "quality": {
                "error_count": self.error_count,
                "last_error": self.last_error,
                "meets_threshold": self.metrics.avg_confidence_score >= self.configuration.confidence_threshold
            }
        }

    def get_process_isolation_info(self) -> Dict[str, Any]:
        """Get process isolation information."""
        return {
            "process_id": self.configuration.isolation_config.process_id,
            "isolation_level": self.configuration.isolation_config.isolation_level.value,
            "resource_limits": {
                "memory_mb": self.configuration.isolation_config.memory_limit_mb,
                "timeout_seconds": self.configuration.isolation_config.execution_timeout_seconds,
                "max_concurrent": self.configuration.isolation_config.max_concurrent_operations
            },
            "process_hierarchy": {
                "parent_process": self.configuration.isolation_config.parent_process_id,
                "child_processes": self.configuration.isolation_config.child_processes,
                "shared_resources": self.configuration.isolation_config.shared_resources
            },
            "session_context": {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "created_at": self.created_at.isoformat(),
                "status": self.status.value
            }
        }

    def cleanup_old_data(self, max_age_hours: int = 24) -> int:
        """Clean up old session data beyond specified age."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        # Clean analysis history
        original_count = len(self.session_data.analysis_history)
        self.session_data.analysis_history = [
            analysis for analysis in self.session_data.analysis_history
            if datetime.fromisoformat(analysis.get("timestamp", "1970-01-01T00:00:00")) > cutoff_time
        ]
        cleaned_count += original_count - len(self.session_data.analysis_history)
        
        # Clean error history
        original_count = len(self.error_history)
        self.error_history = [
            error for error in self.error_history
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]
        cleaned_count += original_count - len(self.error_history)
        
        return cleaned_count

    def validate_isolation(self, other_session: "StorySession") -> bool:
        """Validate that this session is properly isolated from another."""
        # Different session IDs
        if self.session_id == other_session.session_id:
            return False
        
        # Different process IDs (if full isolation)
        if self.configuration.isolation_config.isolation_level == IsolationLevel.FULL_ISOLATION:
            return (self.configuration.isolation_config.process_id != 
                   other_session.configuration.isolation_config.process_id)
        
        # For shared resources, check project isolation
        if self.configuration.isolation_config.isolation_level == IsolationLevel.SHARED_RESOURCES:
            return self.project_id != other_session.project_id
        
        return True

    def to_mcp_response(self) -> Dict[str, Any]:
        """Convert to MCP tool response format."""
        return {
            "session_id": self.session_id,
            "session_data": {
                "story_arcs": self.session_data.story_arcs,
                "plot_threads": self.session_data.plot_threads,
                "consistency_rules": self.session_data.consistency_rules,
                "narrative_beats": self.session_data.narrative_beats,
                "current_analysis": self.session_data.current_analysis
            },
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_accessed.isoformat(),
            "metadata": {
                "status": self.status.value,
                "project_id": self.project_id,
                "analysis_count": self.session_data.analysis_count,
                "performance": {
                    "avg_confidence": self.metrics.avg_confidence_score,
                    "success_rate": self.metrics.successful_analyses / max(self.metrics.total_requests, 1),
                    "threshold_compliance": self.metrics.threshold_compliance_rate
                },
                "isolation": self.get_process_isolation_info()
            }
        }