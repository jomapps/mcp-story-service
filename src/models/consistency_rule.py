from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class RuleType(Enum):
    TIMELINE = "timeline"
    CHARACTER = "character"
    WORLD = "world"
    PLOT = "plot"
    CONTINUITY = "continuity"

class RuleSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"

class RuleScope(Enum):
    STORY_ARC = "story_arc"
    PLOT_THREAD = "plot_thread"
    NARRATIVE_BEAT = "narrative_beat"
    CHARACTER_JOURNEY = "character_journey"

@dataclass
class ValidationLogic:
    conditions: List[str]
    assertions: List[str]
    error_message: str
    confidence_penalty: float
    suggested_fix: Optional[str] = None

@dataclass
class ConsistencyRule:
    id: str
    name: str
    description: str
    rule_type: RuleType
    validation_logic: ValidationLogic
    severity: RuleSeverity
    scope: RuleScope
    confidence_impact: float
