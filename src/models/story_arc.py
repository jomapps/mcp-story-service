from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ArcStatus(Enum):
    DRAFT = "draft"
    ANALYZED = "analyzed"
    VALIDATED = "validated"
    COMPLETE = "complete"

@dataclass
class Act:
    start_position: float
    end_position: float
    purpose: str
    key_events: List[str]
    character_arcs: List[str]

@dataclass
class TurningPoint:
    position: float
    description: str

@dataclass
class ActStructure:
    act_one: Act
    act_two: Act
    act_three: Act
    turning_points: List[TurningPoint]
    confidence_score: float

@dataclass
class PacingProfile:
    tension_curve: List[float]
    pacing_issues: List[str]
    suggested_improvements: List[str]
    confidence_score: float

@dataclass
class StoryArc:
    id: str
    project_id: str
    title: str
    genre: str
    act_structure: ActStructure
    pacing_profile: PacingProfile
    confidence_score: float
    status: ArcStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
