"""NarrativeBeat model with emotional impact and tension scoring.

This model represents individual narrative beats with emotional and tension
analysis for pacing calculation per FR-006.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation  
- Simplicity (III): Clear beat representation without over-complexity
- LLM Declaration (VI): Structured for narrative analysis workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class BeatType(str, Enum):
    """Standard narrative beat types across different story structures."""
    # Universal beats
    OPENING_IMAGE = "opening_image"
    INCITING_INCIDENT = "inciting_incident"
    PLOT_POINT_1 = "plot_point_1"
    MIDPOINT = "midpoint"
    PLOT_POINT_2 = "plot_point_2"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    
    # Three-act specific
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    DENOUEMENT = "denouement"
    
    # Hero's journey specific
    CALL_TO_ADVENTURE = "call_to_adventure"
    REFUSAL_OF_CALL = "refusal_of_call"
    MEETING_MENTOR = "meeting_mentor"
    CROSSING_THRESHOLD = "crossing_threshold"
    TESTS_ALLIES_ENEMIES = "tests_allies_enemies"
    ORDEAL = "ordeal"
    REWARD = "reward"
    ROAD_BACK = "road_back"
    RESURRECTION = "resurrection"
    RETURN_ELIXIR = "return_elixir"
    
    # Genre-specific beats
    MEET_CUTE = "meet_cute"
    DARK_MOMENT = "dark_moment"
    FALSE_VICTORY = "false_victory"
    ALL_IS_LOST = "all_is_lost"
    REVELATION = "revelation"
    SACRIFICE = "sacrifice"
    
    # Custom/Other
    CHARACTER_MOMENT = "character_moment"
    EXPOSITION = "exposition"
    TRANSITION = "transition"
    CUSTOM = "custom"


class EmotionalTone(str, Enum):
    """Emotional tone classifications for beats."""
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    ANTICIPATION = "anticipation"
    TRUST = "trust"
    LOVE = "love"
    EXCITEMENT = "excitement"
    TENSION = "tension"
    RELIEF = "relief"
    HOPE = "hope"
    DESPAIR = "despair"
    NEUTRAL = "neutral"


class PacingType(str, Enum):
    """Pacing classifications for narrative beats."""
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    VERY_FAST = "very_fast"
    EXPLOSIVE = "explosive"


class EmotionalImpact(BaseModel):
    """Detailed emotional impact analysis for a beat."""
    primary_emotion: EmotionalTone = Field(..., description="Primary emotional tone")
    secondary_emotions: List[EmotionalTone] = Field(default_factory=list, description="Secondary emotional tones")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Emotional intensity (0=flat, 1=peak)")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Overall emotional impact on reader")
    character_emotions: Dict[str, EmotionalTone] = Field(default_factory=dict, description="Character-specific emotions")
    
    # Emotional arc tracking
    builds_from_previous: bool = Field(False, description="Whether emotion builds from previous beat")
    contrast_with_previous: bool = Field(False, description="Whether emotion contrasts with previous beat")
    emotional_turning_point: bool = Field(False, description="Whether this is an emotional turning point")


class TensionAnalysis(BaseModel):
    """Tension analysis for narrative beats."""
    tension_level: float = Field(..., ge=0.0, le=1.0, description="Current tension level (0=none, 1=maximum)")
    tension_type: str = Field(..., description="Type of tension (conflict, mystery, time pressure, etc.)")
    builds_tension: bool = Field(False, description="Whether beat builds tension")
    releases_tension: bool = Field(False, description="Whether beat releases tension")
    
    # Tension sources
    conflict_tension: float = Field(0.0, ge=0.0, le=1.0, description="Tension from conflict")
    mystery_tension: float = Field(0.0, ge=0.0, le=1.0, description="Tension from unanswered questions")
    time_pressure: float = Field(0.0, ge=0.0, le=1.0, description="Tension from time constraints")
    relationship_tension: float = Field(0.0, ge=0.0, le=1.0, description="Tension from relationships")
    
    # Tension dynamics
    tension_escalation: bool = Field(False, description="Whether tension escalates from previous beat")
    tension_plateau: bool = Field(False, description="Whether tension maintains from previous beat")
    tension_resolution: bool = Field(False, description="Whether tension resolves")


class PacingMetrics(BaseModel):
    """Pacing analysis for narrative beats."""
    pacing_type: PacingType = Field(..., description="Overall pacing classification")
    words_per_minute: float = Field(..., ge=0.0, description="Estimated reading speed for this beat")
    sentence_rhythm: str = Field(..., description="Sentence rhythm pattern (short, mixed, long, etc.)")
    
    # Pacing factors
    sentence_length_avg: float = Field(..., ge=0.0, description="Average sentence length in words")
    action_density: float = Field(..., ge=0.0, le=1.0, description="Density of action elements")
    dialogue_percentage: float = Field(..., ge=0.0, le=1.0, description="Percentage of beat that is dialogue")
    description_percentage: float = Field(..., ge=0.0, le=1.0, description="Percentage that is description")
    
    # Rhythm patterns
    has_short_sentences: bool = Field(False, description="Contains short, punchy sentences")
    has_long_sentences: bool = Field(False, description="Contains long, flowing sentences")
    rhythm_variety: float = Field(..., ge=0.0, le=1.0, description="Variety in sentence rhythm")


class BeatContext(BaseModel):
    """Contextual information about beat placement and function."""
    act_number: Optional[int] = Field(None, description="Which act this beat occurs in")
    scene_function: str = Field(..., description="Function within the scene (setup, conflict, resolution)")
    story_function: str = Field(..., description="Function within overall story")
    
    # Structural relationships
    setup_for_later: bool = Field(False, description="Whether beat sets up later events")
    payoff_for_earlier: bool = Field(False, description="Whether beat pays off earlier setup")
    turning_point: bool = Field(False, description="Whether beat is a major turning point")
    
    # Character impact
    character_development: bool = Field(False, description="Whether beat develops character")
    relationship_development: bool = Field(False, description="Whether beat develops relationships")
    plot_advancement: bool = Field(False, description="Whether beat advances main plot")


class NarrativeBeat(BaseModel):
    """
    Narrative beat model with emotional impact and tension scoring.
    
    Represents a single narrative moment with comprehensive analysis
    of emotional impact, tension dynamics, and pacing contribution.
    """
    
    # Core identification
    beat_id: str = Field(..., description="Unique beat identifier")
    beat_type: BeatType = Field(..., description="Type/classification of narrative beat")
    position: float = Field(..., ge=0.0, le=1.0, description="Position in story (0=start, 1=end)")
    
    # Content and description
    title: str = Field(..., description="Brief title/description of beat")
    content_snippet: str = Field(..., description="Representative content excerpt")
    summary: str = Field(..., description="Summary of what happens in this beat")
    
    # Story context
    context: BeatContext = Field(..., description="Contextual information about beat placement")
    characters_present: List[str] = Field(default_factory=list, description="Characters involved in beat")
    
    # Emotional analysis
    emotional_impact: EmotionalImpact = Field(..., description="Emotional impact analysis")
    
    # Tension analysis  
    tension_analysis: TensionAnalysis = Field(..., description="Tension dynamics analysis")
    
    # Pacing analysis
    pacing_metrics: PacingMetrics = Field(..., description="Pacing and rhythm analysis")
    
    # Quality and confidence
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in beat identification")
    clarity_score: float = Field(..., ge=0.0, le=1.0, description="Clarity of beat execution")
    effectiveness_score: float = Field(..., ge=0.0, le=1.0, description="Effectiveness at achieving purpose")
    
    # Timing analysis
    timing_score: float = Field(..., ge=0.0, le=1.0, description="Quality of beat timing/placement")
    duration_words: int = Field(..., ge=0, description="Length of beat in words")
    estimated_reading_time: float = Field(..., ge=0.0, description="Estimated reading time in seconds")
    
    # Relationships to other beats
    precedes: Optional[str] = Field(None, description="ID of beat that follows this one")
    follows: Optional[str] = Field(None, description="ID of beat that precedes this one")
    echoes: List[str] = Field(default_factory=list, description="Beat IDs that this beat echoes/parallels")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    analysis_version: str = Field(default="1.0", description="Analysis version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional beat metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "beat_id": "beat_123",
                "beat_type": "inciting_incident",
                "position": 0.12,
                "title": "Hero Discovers Call to Adventure",
                "summary": "Protagonist learns of quest that will change everything",
                "confidence": 0.85,
                "emotional_impact": {
                    "primary_emotion": "anticipation",
                    "intensity": 0.75,
                    "impact_score": 0.80
                },
                "tension_analysis": {
                    "tension_level": 0.60,
                    "tension_type": "anticipation",
                    "builds_tension": True
                }
            }
        }

    @validator('estimated_reading_time', always=True)
    def calculate_reading_time(cls, v, values):
        """Calculate reading time based on word count and pacing."""
        if v == 0.0 and 'duration_words' in values and 'pacing_metrics' in values:
            words = values['duration_words']
            wpm = values['pacing_metrics'].words_per_minute if values['pacing_metrics'] else 250
            return (words / wpm) * 60  # Convert to seconds
        return v

    @root_validator
    def validate_tension_consistency(cls, values):
        """Ensure tension analysis is internally consistent."""
        tension = values.get('tension_analysis')
        if tension:
            # Can't both build and release tension
            if tension.builds_tension and tension.releases_tension:
                raise ValueError("Beat cannot both build and release tension")
            
            # Escalation implies building
            if tension.tension_escalation and not tension.builds_tension:
                raise ValueError("Tension escalation requires builds_tension=True")
        
        return values

    def get_emotional_summary(self) -> Dict[str, Any]:
        """Get summary of emotional analysis."""
        return {
            "primary_emotion": self.emotional_impact.primary_emotion.value,
            "intensity": self.emotional_impact.intensity,
            "impact_score": self.emotional_impact.impact_score,
            "emotional_complexity": len(self.emotional_impact.secondary_emotions),
            "is_turning_point": self.emotional_impact.emotional_turning_point,
            "character_emotions": {
                char: emotion.value 
                for char, emotion in self.emotional_impact.character_emotions.items()
            }
        }

    def get_tension_summary(self) -> Dict[str, Any]:
        """Get summary of tension analysis."""
        return {
            "current_level": self.tension_analysis.tension_level,
            "tension_type": self.tension_analysis.tension_type,
            "tension_dynamics": {
                "builds": self.tension_analysis.builds_tension,
                "releases": self.tension_analysis.releases_tension,
                "escalates": self.tension_analysis.tension_escalation,
                "resolves": self.tension_analysis.tension_resolution
            },
            "tension_sources": {
                "conflict": self.tension_analysis.conflict_tension,
                "mystery": self.tension_analysis.mystery_tension,
                "time_pressure": self.tension_analysis.time_pressure,
                "relationship": self.tension_analysis.relationship_tension
            }
        }

    def get_pacing_summary(self) -> Dict[str, Any]:
        """Get summary of pacing analysis."""
        return {
            "pacing_type": self.pacing_metrics.pacing_type.value,
            "reading_speed": f"{self.pacing_metrics.words_per_minute:.0f} WPM",
            "rhythm": self.pacing_metrics.sentence_rhythm,
            "composition": {
                "action_density": self.pacing_metrics.action_density,
                "dialogue_percent": f"{self.pacing_metrics.dialogue_percentage:.1%}",
                "description_percent": f"{self.pacing_metrics.description_percentage:.1%}"
            },
            "rhythm_analysis": {
                "avg_sentence_length": self.pacing_metrics.sentence_length_avg,
                "has_variety": self.pacing_metrics.rhythm_variety > 0.5,
                "short_sentences": self.pacing_metrics.has_short_sentences,
                "long_sentences": self.pacing_metrics.has_long_sentences
            }
        }

    def get_structural_analysis(self) -> Dict[str, Any]:
        """Get structural analysis of beat function."""
        return {
            "beat_type": self.beat_type.value,
            "position": f"{self.position:.1%}",
            "story_function": self.context.story_function,
            "scene_function": self.context.scene_function,
            "structural_role": {
                "is_turning_point": self.context.turning_point,
                "sets_up_later": self.context.setup_for_later,
                "pays_off_earlier": self.context.payoff_for_earlier
            },
            "development_impact": {
                "character_development": self.context.character_development,
                "relationship_development": self.context.relationship_development,
                "plot_advancement": self.context.plot_advancement
            }
        }

    def get_quality_assessment(self) -> Dict[str, Any]:
        """Assess overall beat quality and effectiveness."""
        return {
            "overall_quality": {
                "confidence": self.confidence,
                "clarity": self.clarity_score,
                "effectiveness": self.effectiveness_score,
                "timing": self.timing_score
            },
            "strengths": self._identify_strengths(),
            "weaknesses": self._identify_weaknesses(),
            "recommendations": self._generate_recommendations()
        }

    def _identify_strengths(self) -> List[str]:
        """Identify beat strengths."""
        strengths = []
        
        if self.emotional_impact.impact_score >= 0.8:
            strengths.append("Strong emotional impact")
        
        if self.tension_analysis.tension_level >= 0.7:
            strengths.append("High tension level")
        
        if self.timing_score >= 0.8:
            strengths.append("Well-timed placement")
        
        if self.effectiveness_score >= 0.8:
            strengths.append("Effective execution")
        
        if self.context.turning_point:
            strengths.append("Significant turning point")
        
        if self.pacing_metrics.rhythm_variety >= 0.7:
            strengths.append("Good rhythm variety")
        
        return strengths

    def _identify_weaknesses(self) -> List[str]:
        """Identify beat weaknesses."""
        weaknesses = []
        
        if self.confidence < 0.75:
            weaknesses.append("Low identification confidence")
        
        if self.clarity_score < 0.6:
            weaknesses.append("Unclear execution")
        
        if self.effectiveness_score < 0.6:
            weaknesses.append("Low effectiveness")
        
        if self.emotional_impact.impact_score < 0.4:
            weaknesses.append("Weak emotional impact")
        
        if self.timing_score < 0.6:
            weaknesses.append("Poor timing/placement")
        
        if self.pacing_metrics.rhythm_variety < 0.3:
            weaknesses.append("Monotonous rhythm")
        
        return weaknesses

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for beat improvement."""
        recommendations = []
        
        if self.emotional_impact.impact_score < 0.6:
            recommendations.append("Strengthen emotional impact through more vivid description or character reaction")
        
        if self.tension_analysis.tension_level < 0.4 and self.beat_type in [BeatType.CLIMAX, BeatType.PLOT_POINT_2]:
            recommendations.append("Increase tension for this critical story moment")
        
        if self.clarity_score < 0.7:
            recommendations.append("Clarify what happens and why it matters to the story")
        
        if self.pacing_metrics.rhythm_variety < 0.5:
            recommendations.append("Vary sentence length and structure for better rhythm")
        
        if not self.context.plot_advancement and self.beat_type not in [BeatType.CHARACTER_MOMENT, BeatType.EXPOSITION]:
            recommendations.append("Ensure beat advances plot or character development")
        
        if self.timing_score < 0.6:
            recommendations.append("Consider repositioning beat for better story flow")
        
        return recommendations

    def calculate_pacing_contribution(self) -> float:
        """Calculate this beat's contribution to overall story pacing."""
        # Weight factors for pacing contribution
        tension_weight = 0.3
        emotion_weight = 0.25
        rhythm_weight = 0.25
        effectiveness_weight = 0.2
        
        return (
            self.tension_analysis.tension_level * tension_weight +
            self.emotional_impact.impact_score * emotion_weight +
            self.pacing_metrics.rhythm_variety * rhythm_weight +
            self.effectiveness_score * effectiveness_weight
        )

    def to_analysis_result(self) -> Dict[str, Any]:
        """Convert to analysis result format for MCP tool responses."""
        return {
            "beat_id": self.beat_id,
            "type": self.beat_type.value,
            "position": self.position,
            "title": self.title,
            "summary": self.summary,
            "analysis": {
                "emotional": self.get_emotional_summary(),
                "tension": self.get_tension_summary(),
                "pacing": self.get_pacing_summary(),
                "structural": self.get_structural_analysis()
            },
            "quality": self.get_quality_assessment(),
            "confidence": self.confidence,
            "metadata": {
                "characters": self.characters_present,
                "duration": f"{self.estimated_reading_time:.1f}s",
                "word_count": self.duration_words,
                "created_at": self.created_at.isoformat()
            }
        }