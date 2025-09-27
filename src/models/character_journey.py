from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class CharacterArcType(Enum):
    HERO_JOURNEY = "hero_journey"
    CORRUPTION = "corruption"
    REDEMPTION = "redemption"
    COMING_OF_AGE = "coming_of_age"
    FALL_FROM_GRACE = "fall_from_grace"
    RISE_TO_POWER = "rise_to_power"
    STATIC = "static"

@dataclass
class CharacterState:
    position: float
    emotional_state: str
    capabilities: List[str]
    relationships: Dict[str, str]
    goals: List[str]
    knowledge: List[str]

@dataclass
class CharacterJourney:
    id: str
    story_arc_id: str
    project_id: str
    character_name: str
    arc_type: CharacterArcType
    starting_state: CharacterState
    ending_state: CharacterState
    key_moments: List[str]
    motivation: str
    conflict: str
    growth_trajectory: List[CharacterState]
    confidence_score: float
