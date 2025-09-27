"""PlotThread model with lifecycle stages and confidence tracking.

This model represents individual plot threads within a story, tracking their
lifecycle stages, resolution status, and importance scoring per FR-003.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear lifecycle tracking without complexity
- LLM Declaration (VI): Structured for thread analysis workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from uuid import uuid4, UUID

from pydantic import BaseModel, Field, validator, root_validator


class ThreadStatus(str, Enum):
    """Plot thread lifecycle status."""
    INTRODUCED = "introduced"
    DEVELOPING = "developing"
    COMPLICATING = "complicating"
    CLIMAXING = "climaxing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"
    UNRESOLVED = "unresolved"


class ThreadImportance(str, Enum):
    """Thread importance classification."""
    MAIN_PLOT = "main_plot"
    MAJOR_SUBPLOT = "major_subplot" 
    MINOR_SUBPLOT = "minor_subplot"
    CHARACTER_ARC = "character_arc"
    BACKSTORY = "backstory"
    WORLDBUILDING = "worldbuilding"


class ThreadType(str, Enum):
    """Types of plot threads."""
    CONFLICT = "conflict"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    CHARACTER_DEVELOPMENT = "character_development"
    QUEST = "quest"
    RELATIONSHIP = "relationship"
    MYSTERY_REVELATION = "mystery_revelation"
    INTERNAL_STRUGGLE = "internal_struggle"
    EXTERNAL_OBSTACLE = "external_obstacle"


class ThreadLifecycleStage(BaseModel):
    """Individual lifecycle stage within a plot thread."""
    stage: ThreadStatus = Field(..., description="Current lifecycle stage")
    position: float = Field(..., ge=0.0, le=1.0, description="Position in story where stage occurs")
    content_evidence: str = Field(..., description="Text evidence supporting this stage")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in stage identification")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When stage was identified")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreadConnection(BaseModel):
    """Connection to other plot threads."""
    connected_thread_id: str = Field(..., description="ID of connected thread")
    connection_type: str = Field(..., description="Type of connection (supports, conflicts, resolves, etc.)")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of connection")
    description: str = Field(..., description="Description of how threads connect")


class ThreadResolution(BaseModel):
    """Resolution details for completed threads."""
    resolution_type: str = Field(..., description="Type of resolution (satisfying, abrupt, open, etc.)")
    position: float = Field(..., ge=0.0, le=1.0, description="Where in story thread resolves")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality of resolution")
    content_evidence: str = Field(..., description="Text evidence of resolution")
    satisfying: bool = Field(..., description="Whether resolution is satisfying")
    foreshadowed: bool = Field(False, description="Whether resolution was properly foreshadowed")


class PlotThread(BaseModel):
    """
    Plot thread model with lifecycle tracking and confidence scoring.
    
    Tracks individual narrative threads through their complete lifecycle
    from introduction to resolution, with confidence metrics and connections.
    """
    
    # Core identification
    thread_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique thread identifier")
    session_id: str = Field(..., description="Session context for process isolation")
    thread_type: ThreadType = Field(..., description="Type of plot thread")
    
    # Thread content and description
    title: str = Field(..., description="Brief title/summary of thread")
    description: str = Field(..., description="Detailed description of thread")
    characters_involved: List[str] = Field(default_factory=list, description="Characters involved in thread")
    
    # Lifecycle tracking
    current_status: ThreadStatus = Field(..., description="Current lifecycle status")
    lifecycle_stages: List[ThreadLifecycleStage] = Field(default_factory=list, description="Complete lifecycle history")
    
    # Importance and priority
    importance: ThreadImportance = Field(..., description="Thread importance classification")
    importance_score: float = Field(..., ge=0.0, le=1.0, description="Numeric importance score")
    priority_rank: Optional[int] = Field(None, ge=1, description="Priority ranking within story")
    
    # Position and coverage
    first_introduced: float = Field(..., ge=0.0, le=1.0, description="Position where thread first appears")
    last_mentioned: float = Field(..., ge=0.0, le=1.0, description="Position where thread last appears")
    coverage_percentage: float = Field(..., ge=0.0, le=1.0, description="Percentage of story covering this thread")
    
    # Resolution tracking
    is_resolved: bool = Field(False, description="Whether thread is resolved")
    resolution: Optional[ThreadResolution] = Field(None, description="Resolution details if resolved")
    
    # Relationships and connections
    connections: List[ThreadConnection] = Field(default_factory=list, description="Connections to other threads")
    supports_main_plot: bool = Field(True, description="Whether thread supports main plot")
    
    # Quality and confidence metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in thread identification")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Internal coherence of thread")
    development_quality: float = Field(..., ge=0.0, le=1.0, description="Quality of thread development")
    
    # Timestamps and metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thread creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    analysis_version: str = Field(default="1.0", description="Analysis version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional thread metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "thread_id": "thread_123",
                "session_id": "session_456",
                "thread_type": "quest",
                "title": "Hero's Search for Magic Sword",
                "description": "Main character seeks ancient weapon to defeat dark lord",
                "current_status": "developing", 
                "importance": "main_plot",
                "importance_score": 0.95,
                "first_introduced": 0.15,
                "last_mentioned": 0.85,
                "confidence": 0.88
            }
        }

    @validator('last_mentioned')
    def last_after_first(cls, v, values):
        """Ensure last_mentioned comes after first_introduced."""
        if 'first_introduced' in values and v < values['first_introduced']:
            raise ValueError('last_mentioned must be >= first_introduced')
        return v

    @validator('coverage_percentage', always=True)
    def calculate_coverage(cls, v, values):
        """Calculate coverage percentage from positions."""
        if 'first_introduced' in values and 'last_mentioned' in values:
            return values['last_mentioned'] - values['first_introduced']
        return v

    @root_validator
    def validate_resolution_consistency(cls, values):
        """Ensure resolution status is consistent with resolution details."""
        is_resolved = values.get('is_resolved', False)
        resolution = values.get('resolution')
        current_status = values.get('current_status')
        
        if is_resolved and not resolution:
            raise ValueError('is_resolved=True requires resolution details')
        
        if resolution and not is_resolved:
            raise ValueError('Resolution details provided but is_resolved=False')
        
        if is_resolved and current_status not in [ThreadStatus.RESOLVED, ThreadStatus.ABANDONED]:
            raise ValueError('Resolved threads must have RESOLVED or ABANDONED status')
        
        return values

    def add_lifecycle_stage(self, stage: ThreadStatus, position: float, 
                           content_evidence: str, confidence: float) -> None:
        """Add a new lifecycle stage to the thread."""
        new_stage = ThreadLifecycleStage(
            stage=stage,
            position=position,
            content_evidence=content_evidence,
            confidence=confidence
        )
        
        self.lifecycle_stages.append(new_stage)
        self.current_status = stage
        self.last_updated = datetime.utcnow()
        
        # Update last_mentioned if this stage is later in the story
        if position > self.last_mentioned:
            self.last_mentioned = position
            self.coverage_percentage = self.last_mentioned - self.first_introduced

    def mark_resolved(self, resolution_type: str, position: float, 
                     quality_score: float, content_evidence: str,
                     satisfying: bool = True, foreshadowed: bool = False) -> None:
        """Mark thread as resolved with resolution details."""
        self.resolution = ThreadResolution(
            resolution_type=resolution_type,
            position=position,
            quality_score=quality_score,
            content_evidence=content_evidence,
            satisfying=satisfying,
            foreshadowed=foreshadowed
        )
        
        self.is_resolved = True
        self.current_status = ThreadStatus.RESOLVED
        self.last_updated = datetime.utcnow()
        
        # Add resolved stage to lifecycle
        self.add_lifecycle_stage(
            ThreadStatus.RESOLVED, 
            position, 
            content_evidence, 
            quality_score
        )

    def add_connection(self, other_thread_id: str, connection_type: str, 
                      strength: float, description: str) -> None:
        """Add connection to another plot thread."""
        connection = ThreadConnection(
            connected_thread_id=other_thread_id,
            connection_type=connection_type,
            strength=strength,
            description=description
        )
        
        self.connections.append(connection)
        self.last_updated = datetime.utcnow()

    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get summary of thread lifecycle progression."""
        return {
            "current_status": self.current_status.value,
            "stages_completed": len(self.lifecycle_stages),
            "stage_history": [
                {
                    "stage": stage.stage.value,
                    "position": f"{stage.position:.1%}",
                    "confidence": stage.confidence
                }
                for stage in self.lifecycle_stages
            ],
            "development_span": {
                "start": f"{self.first_introduced:.1%}",
                "end": f"{self.last_mentioned:.1%}",
                "coverage": f"{self.coverage_percentage:.1%}"
            },
            "is_complete": self.is_resolved
        }

    def get_quality_assessment(self) -> Dict[str, Any]:
        """Assess thread quality and development."""
        return {
            "overall_quality": {
                "confidence": self.confidence,
                "coherence": self.coherence_score,
                "development": self.development_quality
            },
            "structural_quality": {
                "well_introduced": self.first_introduced <= 0.3,  # Introduced early
                "adequate_development": self.coverage_percentage >= 0.1,  # Covers 10%+ of story
                "proper_resolution": self.is_resolved if self.importance in [ThreadImportance.MAIN_PLOT, ThreadImportance.MAJOR_SUBPLOT] else True
            },
            "resolution_quality": {
                "is_resolved": self.is_resolved,
                "satisfying": self.resolution.satisfying if self.resolution else None,
                "foreshadowed": self.resolution.foreshadowed if self.resolution else None,
                "quality_score": self.resolution.quality_score if self.resolution else None
            },
            "importance_match": {
                "importance": self.importance.value,
                "importance_score": self.importance_score,
                "priority_rank": self.priority_rank,
                "supports_main": self.supports_main_plot
            }
        }

    def get_connection_summary(self) -> Dict[str, Any]:
        """Get summary of thread connections."""
        return {
            "connection_count": len(self.connections),
            "connections": [
                {
                    "to_thread": conn.connected_thread_id,
                    "type": conn.connection_type,
                    "strength": conn.strength,
                    "description": conn.description
                }
                for conn in self.connections
            ],
            "supports_main_plot": self.supports_main_plot,
            "integration_score": sum(conn.strength for conn in self.connections) / max(len(self.connections), 1)
        }

    def is_thread_healthy(self) -> bool:
        """Check if thread is well-developed and healthy."""
        return (
            self.confidence >= 0.75 and
            self.coherence_score >= 0.70 and
            self.development_quality >= 0.70 and
            (self.is_resolved or self.current_status in [ThreadStatus.DEVELOPING, ThreadStatus.COMPLICATING]) and
            self.coverage_percentage >= 0.05  # At least 5% coverage
        )

    def get_recommendations(self) -> List[str]:
        """Generate recommendations for improving thread development."""
        recommendations = []
        
        if self.confidence < 0.75:
            recommendations.append(f"Thread confidence ({self.confidence:.1%}) is below threshold. Clarify thread purpose and development.")
        
        if self.coherence_score < 0.70:
            recommendations.append("Thread lacks coherence. Ensure consistent development throughout story.")
        
        if not self.is_resolved and self.importance in [ThreadImportance.MAIN_PLOT, ThreadImportance.MAJOR_SUBPLOT]:
            recommendations.append("Important thread is unresolved. Consider adding resolution.")
        
        if self.coverage_percentage < 0.05:
            recommendations.append("Thread has minimal story coverage. Expand development or consider removing.")
        
        if len(self.lifecycle_stages) < 3:
            recommendations.append("Thread has few development stages. Add more progression points.")
        
        if not self.connections and self.importance != ThreadImportance.MAIN_PLOT:
            recommendations.append("Thread is isolated. Consider connecting to other plot elements.")
        
        if self.resolution and not self.resolution.satisfying:
            recommendations.append("Thread resolution is unsatisfying. Improve resolution quality.")
        
        return recommendations

    def to_tracking_result(self) -> Dict[str, Any]:
        """Convert to tracking result format for MCP tool responses."""
        return {
            "thread_id": self.thread_id,
            "description": self.description,
            "status": self.current_status.value,
            "importance": self.importance_score,
            "lifecycle": self.get_lifecycle_summary(),
            "quality": self.get_quality_assessment(),
            "connections": self.get_connection_summary(),
            "recommendations": self.get_recommendations(),
            "metadata": {
                "type": self.thread_type.value,
                "characters": self.characters_involved,
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat()
            }
        }

    def update_from_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """Update thread from new analysis data."""
        if 'status' in analysis_data:
            new_status = ThreadStatus(analysis_data['status'])
            if new_status != self.current_status:
                self.add_lifecycle_stage(
                    new_status,
                    analysis_data.get('position', self.last_mentioned),
                    analysis_data.get('evidence', ''),
                    analysis_data.get('confidence', self.confidence)
                )
        
        if 'importance_score' in analysis_data:
            self.importance_score = analysis_data['importance_score']
        
        if 'characters' in analysis_data:
            new_characters = set(analysis_data['characters']) - set(self.characters_involved)
            self.characters_involved.extend(list(new_characters))
        
        self.last_updated = datetime.utcnow()