from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ThreadStage(Enum):
    INTRODUCED = "introduced"
    DEVELOPING = "developing"
    READY_FOR_RESOLUTION = "ready_for_resolution"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"

class ThreadType(Enum):
    MAIN = "main"
    SUBPLOT = "subplot"
    CHARACTER_ARC = "character_arc"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    CONFLICT = "conflict"

@dataclass
class PlotThread:
    id: str
    story_arc_id: str
    project_id: str
    name: str
    type: ThreadType
    lifecycle_stage: ThreadStage
    introduction_point: float
    resolution_point: Optional[float]
    episodes: List[int]
    dependencies: List[str]
    importance_score: float
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
