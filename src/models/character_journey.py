"""CharacterJourney model with arc types and state progression.

This model represents character development arcs with state tracking
and progression analysis for consistency validation.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear character arc representation
- LLM Declaration (VI): Structured for character analysis workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class ArcType(str, Enum):
    """Types of character development arcs."""
    POSITIVE_CHANGE = "positive_change"
    FLAT_ARC = "flat_arc"
    NEGATIVE_ARC = "negative_arc"
    CORRUPTION_ARC = "corruption_arc"
    REDEMPTION_ARC = "redemption_arc"
    DISILLUSIONMENT_ARC = "disillusionment_arc"
    COMING_OF_AGE = "coming_of_age"
    HERO_JOURNEY = "hero_journey"
    ANTIHERO_ARC = "antihero_arc"
    TRANSFORMATION = "transformation"


class CharacterState(str, Enum):
    """Character states during journey progression."""
    INTRODUCED = "introduced"
    ESTABLISHING = "establishing"
    DEVELOPING = "developing"
    CHALLENGING = "challenging"
    TRANSFORMING = "transforming"
    REALIZING = "realizing"
    COMPLETING = "completing"
    RESOLVED = "resolved"


class EmotionalState(BaseModel):
    """Character's emotional state at a point in time."""
    primary_emotion: str = Field(..., description="Primary emotional state")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Emotional intensity")
    secondary_emotions: List[str] = Field(default_factory=list, description="Secondary emotional states")
    stability: float = Field(..., ge=0.0, le=1.0, description="Emotional stability")
    context: str = Field(..., description="Context that triggered this emotional state")


class CharacterTrait(BaseModel):
    """Individual character trait with tracking."""
    trait_name: str = Field(..., description="Name of the trait")
    description: str = Field(..., description="Description of the trait")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of trait (0=absent, 1=dominant)")
    consistency: float = Field(..., ge=0.0, le=1.0, description="How consistently trait is displayed")
    
    # Development tracking
    initial_strength: float = Field(..., ge=0.0, le=1.0, description="Initial trait strength")
    development_direction: str = Field("stable", description="Direction of trait development")
    change_evidence: List[str] = Field(default_factory=list, description="Evidence of trait changes")


class RelationshipDynamic(BaseModel):
    """Character's relationship with another character."""
    other_character: str = Field(..., description="Name of other character")
    relationship_type: str = Field(..., description="Type of relationship")
    closeness: float = Field(..., ge=0.0, le=1.0, description="Closeness of relationship")
    trust_level: float = Field(..., ge=0.0, le=1.0, description="Level of trust")
    conflict_level: float = Field(..., ge=0.0, le=1.0, description="Level of conflict")
    
    # Development tracking
    relationship_arc: str = Field("stable", description="How relationship develops")
    key_moments: List[str] = Field(default_factory=list, description="Key relationship moments")
    current_status: str = Field("active", description="Current relationship status")


class CharacterGoal(BaseModel):
    """Character goal with tracking."""
    goal_id: str = Field(..., description="Unique goal identifier")
    description: str = Field(..., description="Goal description")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance to character")
    motivation: str = Field(..., description="What motivates this goal")
    
    # Progress tracking
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress toward goal")
    obstacles: List[str] = Field(default_factory=list, description="Obstacles encountered")
    status: str = Field("active", description="Goal status (active, achieved, abandoned, etc.)")
    
    # Story integration
    introduced_at: float = Field(..., ge=0.0, le=1.0, description="When goal was introduced")
    resolved_at: Optional[float] = Field(None, ge=0.0, le=1.0, description="When goal was resolved")


class JourneyMilestone(BaseModel):
    """Significant milestone in character journey."""
    milestone_id: str = Field(..., description="Unique milestone identifier")
    name: str = Field(..., description="Milestone name")
    description: str = Field(..., description="What happens at this milestone")
    position: float = Field(..., ge=0.0, le=1.0, description="Position in story")
    
    # Milestone significance
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance to character arc")
    emotional_impact: float = Field(..., ge=0.0, le=1.0, description="Emotional impact on character")
    character_state: CharacterState = Field(..., description="Character state at milestone")
    
    # Changes and growth
    traits_affected: List[str] = Field(default_factory=list, description="Traits affected by milestone")
    relationships_affected: List[str] = Field(default_factory=list, description="Relationships affected")
    beliefs_changed: List[str] = Field(default_factory=list, description="Beliefs or worldview changes")
    
    # Evidence and context
    content_evidence: str = Field(..., description="Content evidence for milestone")
    emotional_state: EmotionalState = Field(..., description="Character's emotional state")


class CharacterJourney(BaseModel):
    """
    Character journey model with arc types and state progression.
    
    Tracks complete character development through story with detailed
    state progression, relationship dynamics, and consistency validation.
    """
    
    # Core identification
    journey_id: str = Field(..., description="Unique journey identifier")
    character_name: str = Field(..., description="Character name")
    arc_type: ArcType = Field(..., description="Type of character arc")
    
    # Journey overview
    journey_description: str = Field(..., description="Overall journey description")
    central_conflict: str = Field(..., description="Central conflict driving character")
    transformation_theme: str = Field(..., description="Theme of character transformation")
    
    # Character foundation
    initial_traits: List[CharacterTrait] = Field(default_factory=list, description="Starting character traits")
    current_traits: List[CharacterTrait] = Field(default_factory=list, description="Current character traits")
    core_beliefs: List[str] = Field(default_factory=list, description="Character's core beliefs")
    fears_and_desires: Dict[str, str] = Field(default_factory=dict, description="Character fears and desires")
    
    # Journey progression
    current_state: CharacterState = Field(..., description="Current character state")
    milestones: List[JourneyMilestone] = Field(default_factory=list, description="Journey milestones")
    goals: List[CharacterGoal] = Field(default_factory=list, description="Character goals")
    
    # Relationships
    relationships: List[RelationshipDynamic] = Field(default_factory=list, description="Character relationships")
    
    # Journey quality metrics
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Character consistency score")
    development_quality: float = Field(..., ge=0.0, le=1.0, description="Quality of character development")
    believability_score: float = Field(..., ge=0.0, le=1.0, description="Character believability")
    
    # Arc completion
    is_complete: bool = Field(False, description="Whether character arc is complete")
    completion_quality: float = Field(0.0, ge=0.0, le=1.0, description="Quality of arc completion")
    resolution_satisfaction: float = Field(0.0, ge=0.0, le=1.0, description="Satisfaction of character resolution")
    
    # Session and metadata
    session_id: str = Field(..., description="Session context")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Journey tracking start")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    analysis_version: str = Field(default="1.0", description="Analysis version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "journey_id": "journey_123",
                "character_name": "Sarah Miller",
                "arc_type": "positive_change",
                "journey_description": "Librarian discovers magical powers and grows into confident hero",
                "central_conflict": "Self-doubt vs. accepting magical destiny",
                "current_state": "developing",
                "consistency_score": 0.85,
                "session_id": "session_456"
            }
        }

    @validator('milestones')
    def validate_milestone_order(cls, v):
        """Ensure milestones are in chronological order."""
        if len(v) > 1:
            positions = [milestone.position for milestone in v]
            if positions != sorted(positions):
                raise ValueError("Milestones must be in chronological order")
        return v

    @root_validator
    def validate_journey_consistency(cls, values):
        """Validate internal consistency of character journey."""
        arc_type = values.get('arc_type')
        current_state = values.get('current_state')
        is_complete = values.get('is_complete', False)
        
        # Complete journeys should be in resolved state
        if is_complete and current_state != CharacterState.RESOLVED:
            raise ValueError("Complete journeys must be in resolved state")
        
        # Validate arc type consistency with milestones
        milestones = values.get('milestones', [])
        if arc_type == ArcType.FLAT_ARC and len(milestones) > 3:
            # Flat arcs should have fewer transformation milestones
            pass  # Could add specific validation
        
        return values

    def add_milestone(self, name: str, description: str, position: float,
                     importance: float, emotional_impact: float,
                     character_state: CharacterState, content_evidence: str,
                     emotional_state: EmotionalState) -> str:
        """Add a new milestone to the character journey."""
        from uuid import uuid4
        
        milestone_id = str(uuid4())
        milestone = JourneyMilestone(
            milestone_id=milestone_id,
            name=name,
            description=description,
            position=position,
            importance=importance,
            emotional_impact=emotional_impact,
            character_state=character_state,
            content_evidence=content_evidence,
            emotional_state=emotional_state
        )
        
        # Insert in chronological order
        inserted = False
        for i, existing_milestone in enumerate(self.milestones):
            if position < existing_milestone.position:
                self.milestones.insert(i, milestone)
                inserted = True
                break
        
        if not inserted:
            self.milestones.append(milestone)
        
        self.current_state = character_state
        self.last_updated = datetime.utcnow()
        
        return milestone_id

    def update_trait(self, trait_name: str, new_strength: float, evidence: str) -> None:
        """Update a character trait with new strength and evidence."""
        for trait in self.current_traits:
            if trait.trait_name.lower() == trait_name.lower():
                # Calculate development direction
                if new_strength > trait.strength:
                    trait.development_direction = "strengthening"
                elif new_strength < trait.strength:
                    trait.development_direction = "weakening"
                else:
                    trait.development_direction = "stable"
                
                trait.strength = new_strength
                trait.change_evidence.append(evidence)
                self.last_updated = datetime.utcnow()
                return
        
        # If trait not found, this might be a new trait discovery
        new_trait = CharacterTrait(
            trait_name=trait_name,
            description=f"Newly discovered trait: {trait_name}",
            strength=new_strength,
            consistency=0.5,  # Default for new traits
            initial_strength=new_strength,
            development_direction="emerging",
            change_evidence=[evidence]
        )
        self.current_traits.append(new_trait)

    def add_relationship(self, other_character: str, relationship_type: str,
                        closeness: float, trust_level: float, conflict_level: float) -> None:
        """Add or update a character relationship."""
        for relationship in self.relationships:
            if relationship.other_character.lower() == other_character.lower():
                # Update existing relationship
                relationship.closeness = closeness
                relationship.trust_level = trust_level
                relationship.conflict_level = conflict_level
                self.last_updated = datetime.utcnow()
                return
        
        # Add new relationship
        new_relationship = RelationshipDynamic(
            other_character=other_character,
            relationship_type=relationship_type,
            closeness=closeness,
            trust_level=trust_level,
            conflict_level=conflict_level
        )
        self.relationships.append(new_relationship)

    def add_goal(self, description: str, importance: float, motivation: str,
                introduced_at: float) -> str:
        """Add a new character goal."""
        from uuid import uuid4
        
        goal_id = str(uuid4())
        goal = CharacterGoal(
            goal_id=goal_id,
            description=description,
            importance=importance,
            motivation=motivation,
            introduced_at=introduced_at
        )
        
        self.goals.append(goal)
        self.last_updated = datetime.utcnow()
        
        return goal_id

    def update_goal_progress(self, goal_id: str, progress: float, obstacles: List[str] = None) -> None:
        """Update progress on a character goal."""
        for goal in self.goals:
            if goal.goal_id == goal_id:
                goal.progress = progress
                if obstacles:
                    goal.obstacles.extend(obstacles)
                
                # Auto-update status based on progress
                if progress >= 1.0:
                    goal.status = "achieved"
                elif progress <= 0.0 and goal.status == "active":
                    goal.status = "stalled"
                
                self.last_updated = datetime.utcnow()
                return

    def get_character_development_summary(self) -> Dict[str, Any]:
        """Get summary of character development."""
        trait_changes = []
        for current_trait in self.current_traits:
            for initial_trait in self.initial_traits:
                if current_trait.trait_name == initial_trait.trait_name:
                    change = current_trait.strength - initial_trait.strength
                    if abs(change) > 0.1:  # Significant change
                        trait_changes.append({
                            "trait": current_trait.trait_name,
                            "change": change,
                            "direction": current_trait.development_direction
                        })
                    break
        
        return {
            "character": self.character_name,
            "arc_type": self.arc_type.value,
            "current_state": self.current_state.value,
            "progression": {
                "milestones_reached": len(self.milestones),
                "major_milestones": len([m for m in self.milestones if m.importance >= 0.7]),
                "current_progress": self._calculate_arc_progress()
            },
            "development": {
                "traits_changed": len(trait_changes),
                "trait_changes": trait_changes,
                "relationships": len(self.relationships),
                "active_goals": len([g for g in self.goals if g.status == "active"])
            },
            "quality": {
                "consistency": self.consistency_score,
                "development_quality": self.development_quality,
                "believability": self.believability_score
            }
        }

    def get_consistency_analysis(self) -> Dict[str, Any]:
        """Analyze character consistency throughout journey."""
        consistency_issues = []
        
        # Check trait consistency
        for trait in self.current_traits:
            if trait.consistency < 0.7:
                consistency_issues.append({
                    "type": "trait_inconsistency",
                    "description": f"Inconsistent portrayal of {trait.trait_name}",
                    "severity": "medium" if trait.consistency < 0.5 else "low"
                })
        
        # Check milestone emotional consistency
        emotional_jumps = []
        for i in range(1, len(self.milestones)):
            prev_milestone = self.milestones[i-1]
            curr_milestone = self.milestones[i]
            
            intensity_jump = abs(curr_milestone.emotional_impact - prev_milestone.emotional_impact)
            if intensity_jump > 0.7:
                emotional_jumps.append({
                    "from_milestone": prev_milestone.name,
                    "to_milestone": curr_milestone.name,
                    "intensity_jump": intensity_jump
                })
        
        return {
            "overall_consistency": self.consistency_score,
            "issues_found": len(consistency_issues),
            "consistency_issues": consistency_issues,
            "emotional_analysis": {
                "emotional_jumps": len(emotional_jumps),
                "jump_details": emotional_jumps
            },
            "recommendations": self._generate_consistency_recommendations(consistency_issues)
        }

    def _calculate_arc_progress(self) -> float:
        """Calculate overall arc progress based on state and milestones."""
        state_progress = {
            CharacterState.INTRODUCED: 0.1,
            CharacterState.ESTABLISHING: 0.2,
            CharacterState.DEVELOPING: 0.4,
            CharacterState.CHALLENGING: 0.6,
            CharacterState.TRANSFORMING: 0.8,
            CharacterState.REALIZING: 0.9,
            CharacterState.COMPLETING: 0.95,
            CharacterState.RESOLVED: 1.0
        }
        
        base_progress = state_progress.get(self.current_state, 0.5)
        
        # Adjust based on milestones
        if self.milestones:
            milestone_progress = len(self.milestones) / max(5, len(self.milestones))  # Assume ~5 major milestones
            return min(1.0, (base_progress + milestone_progress) / 2)
        
        return base_progress

    def _generate_consistency_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving character consistency."""
        recommendations = []
        
        if len(issues) > 3:
            recommendations.append("Character has multiple consistency issues. Review characterization throughout story.")
        
        trait_issues = [i for i in issues if i["type"] == "trait_inconsistency"]
        if trait_issues:
            recommendations.append("Review character trait portrayals for consistency.")
        
        if self.consistency_score < 0.7:
            recommendations.append("Character consistency is below acceptable threshold. Strengthen character voice and behavior patterns.")
        
        if len(self.milestones) < 3:
            recommendations.append("Character arc needs more development milestones for proper progression.")
        
        unresolved_goals = [g for g in self.goals if g.status == "active" and g.progress < 0.5]
        if len(unresolved_goals) > 2:
            recommendations.append("Character has many unresolved goals. Consider resolving or removing some.")
        
        return recommendations

    def complete_journey(self, completion_quality: float, resolution_satisfaction: float) -> None:
        """Mark character journey as complete."""
        self.is_complete = True
        self.current_state = CharacterState.RESOLVED
        self.completion_quality = completion_quality
        self.resolution_satisfaction = resolution_satisfaction
        self.last_updated = datetime.utcnow()

    def to_analysis_result(self) -> Dict[str, Any]:
        """Convert to analysis result format for MCP tool responses."""
        return {
            "journey_id": self.journey_id,
            "character_name": self.character_name,
            "arc_analysis": {
                "arc_type": self.arc_type.value,
                "current_state": self.current_state.value,
                "progression": self._calculate_arc_progress(),
                "is_complete": self.is_complete
            },
            "development_summary": self.get_character_development_summary(),
            "consistency_analysis": self.get_consistency_analysis(),
            "quality_metrics": {
                "consistency": self.consistency_score,
                "development": self.development_quality,
                "believability": self.believability_score,
                "completion": self.completion_quality if self.is_complete else None
            },
            "metadata": {
                "session_id": self.session_id,
                "milestones_count": len(self.milestones),
                "relationships_count": len(self.relationships),
                "goals_count": len(self.goals),
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat()
            }
        }