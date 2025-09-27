"""StoryArc model with confidence scoring and project isolation.

This model represents a complete story arc with its structure, beats, and analysis.
Supports project isolation and confidence scoring per FR-001 and Clarification C.

Constitutional Compliance: 
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear data model with minimal complexity
- LLM Declaration (VI): Structured for LLM analysis workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class StructureType(str, Enum):
    """Supported narrative structure types."""
    THREE_ACT = "three_act"
    HEROS_JOURNEY = "heros_journey"
    FIVE_ACT = "five_act"
    FREYTAG_PYRAMID = "freytag_pyramid"
    SAVE_THE_CAT = "save_the_cat"
    CUSTOM = "custom"


class ActStructure(BaseModel):
    """Structure definition for a single act."""
    act_number: int = Field(..., ge=1, description="Act number in sequence")
    name: str = Field(..., description="Act name or description")
    start_position: float = Field(..., ge=0.0, le=1.0, description="Start position as percentage of story")
    end_position: float = Field(..., ge=0.0, le=1.0, description="End position as percentage of story")
    key_elements: List[str] = Field(default_factory=list, description="Key narrative elements in this act")
    beats: List[Dict[str, Any]] = Field(default_factory=list, description="Narrative beats within this act")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in act identification")

    @validator('end_position')
    def end_after_start(cls, v, values):
        if 'start_position' in values and v <= values['start_position']:
            raise ValueError('end_position must be greater than start_position')
        return v


class NarrativeBeatData(BaseModel):
    """Data structure for narrative beats within story arc."""
    beat_type: str = Field(..., description="Type of narrative beat")
    position: float = Field(..., ge=0.0, le=1.0, description="Position in story as percentage")
    content_snippet: str = Field(default="", description="Representative content snippet")
    emotional_impact: float = Field(0.5, ge=0.0, le=1.0, description="Emotional impact score")
    tension_level: float = Field(0.5, ge=0.0, le=1.0, description="Tension level at this beat")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in beat identification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional beat metadata")


class ProjectIsolationContext(BaseModel):
    """Context for project isolation per Clarification C."""
    project_id: str = Field(..., description="Unique project identifier")
    session_id: str = Field(..., description="Session identifier for process isolation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    process_context: Dict[str, Any] = Field(default_factory=dict, description="Process isolation metadata")


class ConfidenceMetrics(BaseModel):
    """Confidence scoring metrics per FR-001."""
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall story arc confidence")
    structure_confidence: float = Field(..., ge=0.0, le=1.0, description="Structure identification confidence")
    beat_confidence: float = Field(..., ge=0.0, le=1.0, description="Average beat identification confidence")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Story completeness score")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Internal consistency score")
    
    # Constitutional requirement: 75% minimum threshold
    meets_threshold: bool = Field(..., description="Whether confidence meets 75% threshold")
    threshold_details: Dict[str, float] = Field(default_factory=dict, description="Threshold analysis details")

    @validator('meets_threshold', always=True)
    def check_threshold(cls, v, values):
        """Validate against 75% confidence threshold per FR-001."""
        if 'overall_confidence' in values:
            return values['overall_confidence'] >= 0.75
        return False


class StoryArc(BaseModel):
    """
    Main story arc model with confidence scoring and project isolation.
    
    Represents a complete narrative arc with structure analysis, beats,
    and isolation context for concurrent project processing.
    """
    
    # Core identification
    story_id: str = Field(..., description="Unique story identifier")
    title: Optional[str] = Field(None, description="Story title if available")
    content: str = Field(..., min_length=1, description="Original story content")
    
    # Structure analysis
    structure_type: StructureType = Field(..., description="Identified narrative structure type")
    acts: List[ActStructure] = Field(default_factory=list, description="Act breakdown")
    narrative_beats: List[NarrativeBeatData] = Field(default_factory=list, description="Identified narrative beats")
    
    # Analysis metadata
    word_count: int = Field(..., ge=0, description="Total word count")
    estimated_reading_time: float = Field(..., ge=0.0, description="Estimated reading time in minutes")
    genre_hints: List[str] = Field(default_factory=list, description="Detected genre elements")
    
    # Confidence and quality metrics
    confidence_metrics: ConfidenceMetrics = Field(..., description="Confidence scoring per FR-001")
    
    # Project isolation context
    isolation_context: ProjectIsolationContext = Field(..., description="Project isolation per Clarification C")
    
    # Analysis timestamps
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    version: str = Field(default="1.0", description="Model version for compatibility")
    
    # Additional metadata
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis data")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "story_id": "story_123",
                "title": "The Hero's Quest",
                "content": "Once upon a time, a young hero...",
                "structure_type": "three_act",
                "word_count": 1500,
                "estimated_reading_time": 6.0,
                "confidence_metrics": {
                    "overall_confidence": 0.85,
                    "structure_confidence": 0.80,
                    "beat_confidence": 0.88,
                    "completeness_score": 0.90,
                    "consistency_score": 0.82,
                    "meets_threshold": True
                },
                "isolation_context": {
                    "project_id": "project_alpha",
                    "session_id": "session_123"
                }
            }
        }

    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        """Calculate word count from content if not provided."""
        if v == 0 and 'content' in values:
            return len(values['content'].split())
        return v

    @validator('estimated_reading_time', always=True)
    def calculate_reading_time(cls, v, values):
        """Calculate estimated reading time (250 WPM average)."""
        if v == 0.0 and 'word_count' in values:
            return values['word_count'] / 250.0
        return v

    @root_validator
    def validate_acts_structure(cls, values):
        """Validate act structure consistency."""
        acts = values.get('acts', [])
        structure_type = values.get('structure_type')
        
        if structure_type == StructureType.THREE_ACT and acts:
            if len(acts) != 3:
                raise ValueError(f"Three-act structure must have exactly 3 acts, got {len(acts)}")
        
        # Validate act positions don't overlap
        if len(acts) > 1:
            sorted_acts = sorted(acts, key=lambda x: x.start_position)
            for i in range(len(sorted_acts) - 1):
                if sorted_acts[i].end_position > sorted_acts[i + 1].start_position:
                    raise ValueError(f"Act {i + 1} overlaps with act {i + 2}")
        
        return values

    @root_validator
    def validate_narrative_beats(cls, values):
        """Validate narrative beats are in chronological order."""
        beats = values.get('narrative_beats', [])
        
        if len(beats) > 1:
            positions = [beat.position for beat in beats]
            if positions != sorted(positions):
                raise ValueError("Narrative beats must be in chronological order")
        
        return values

    def get_confidence_summary(self) -> Dict[str, Any]:
        """Get summarized confidence information."""
        return {
            "overall": self.confidence_metrics.overall_confidence,
            "meets_threshold": self.confidence_metrics.meets_threshold,
            "breakdown": {
                "structure": self.confidence_metrics.structure_confidence,
                "beats": self.confidence_metrics.beat_confidence,
                "completeness": self.confidence_metrics.completeness_score,
                "consistency": self.confidence_metrics.consistency_score
            },
            "analysis_quality": "high" if self.confidence_metrics.overall_confidence >= 0.85 else
                               "medium" if self.confidence_metrics.overall_confidence >= 0.75 else "low"
        }

    def get_structure_summary(self) -> Dict[str, Any]:
        """Get summarized structure information."""
        return {
            "type": self.structure_type.value,
            "act_count": len(self.acts),
            "beat_count": len(self.narrative_beats),
            "acts": [
                {
                    "act": act.act_number,
                    "name": act.name,
                    "coverage": f"{act.start_position:.1%} - {act.end_position:.1%}",
                    "confidence": act.confidence
                }
                for act in self.acts
            ],
            "key_beats": [
                {
                    "type": beat.beat_type,
                    "position": f"{beat.position:.1%}",
                    "confidence": beat.confidence
                }
                for beat in self.narrative_beats[:5]  # Top 5 beats
            ]
        }

    def update_isolation_context(self, access_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update isolation context for process tracking."""
        self.isolation_context.last_accessed = datetime.utcnow()
        if access_metadata:
            self.isolation_context.process_context.update(access_metadata)

    def is_complete_analysis(self) -> bool:
        """Check if analysis is complete based on structure and beats."""
        return (
            len(self.acts) > 0 and
            len(self.narrative_beats) >= 3 and  # Minimum viable beats
            self.confidence_metrics.completeness_score >= 0.75 and
            self.confidence_metrics.meets_threshold
        )

    def get_quality_assessment(self) -> Dict[str, Any]:
        """Get comprehensive quality assessment."""
        return {
            "is_complete": self.is_complete_analysis(),
            "confidence_summary": self.get_confidence_summary(),
            "structure_quality": {
                "type_identified": bool(self.structure_type != StructureType.CUSTOM),
                "acts_defined": len(self.acts) > 0,
                "beats_identified": len(self.narrative_beats) > 0,
                "genre_hints_found": len(self.genre_hints) > 0
            },
            "recommendations": self._generate_quality_recommendations()
        }

    def _generate_quality_recommendations(self) -> List[str]:
        """Generate recommendations for improving analysis quality."""
        recommendations = []
        
        if self.confidence_metrics.overall_confidence < 0.75:
            recommendations.append("Story structure is unclear. Consider adding more narrative elements.")
        
        if len(self.acts) == 0:
            recommendations.append("No clear act structure identified. Consider strengthening story progression.")
        
        if len(self.narrative_beats) < 5:
            recommendations.append("Few narrative beats identified. Consider adding more dramatic moments.")
        
        if self.confidence_metrics.consistency_score < 0.75:
            recommendations.append("Internal consistency issues detected. Review for contradictions.")
        
        if not self.genre_hints:
            recommendations.append("No clear genre elements identified. Consider strengthening genre conventions.")
        
        return recommendations

    def to_analysis_result(self) -> Dict[str, Any]:
        """Convert to analysis result format for MCP tool responses."""
        return {
            "story_id": self.story_id,
            "analysis": {
                "structure_type": self.structure_type.value,
                "acts": [act.dict() for act in self.acts],
                "beats": [beat.dict() for beat in self.narrative_beats],
                "quality_assessment": self.get_quality_assessment()
            },
            "confidence": self.confidence_metrics.overall_confidence,
            "metadata": {
                "word_count": self.word_count,
                "reading_time": self.estimated_reading_time,
                "analyzed_at": self.analyzed_at.isoformat(),
                "version": self.version,
                "isolation_context": self.isolation_context.dict()
            }
        }