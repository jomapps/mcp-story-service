from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class BeatType(Enum):
    INCITING_INCIDENT = "inciting_incident"
    PLOT_POINT_1 = "plot_point_1"
    MIDPOINT = "midpoint"
    PLOT_POINT_2 = "plot_point_2"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    REVELATION = "revelation"
    SETBACK = "setback"
    VICTORY = "victory"
    TWIST = "twist"

@dataclass
class NarrativeBeat:
    id: str
    story_arc_id: str
    project_id: str
    position: float
    type: BeatType
    emotional_impact: float
    tension_level: float
    description: str
    episode_number: Optional[int]
    character_focus: List[str]
    plot_threads: List[str]
    confidence_score: float
