from dataclasses import dataclass
from typing import List
from enum import Enum
from src.models.narrative_beat import BeatType

class ConventionImportance(Enum):
    ESSENTIAL = "essential"
    TYPICAL = "typical"
    OPTIONAL = "optional"

@dataclass
class Convention:
    name: str
    description: str
    importance: ConventionImportance
    examples: List[str]
    violations_allowed: bool
    confidence_weight: float

@dataclass
class GenrePacing:
    name: str
    curve: List[float]

@dataclass
class CharacterArchetype:
    name: str
    description: str

@dataclass
class AuthenticityRule:
    name: str
    description: str
    validation_logic: str

@dataclass
class GenreTemplate:
    id: str
    name: str
    description: str
    conventions: List[Convention]
    pacing_profile: GenrePacing
    character_archetypes: List[CharacterArchetype]
    common_beats: List[BeatType]
    authenticity_rules: List[AuthenticityRule]
    subgenres: List[str]
