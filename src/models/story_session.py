from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum

class PersistencePolicy(Enum):
    UNTIL_COMPLETION = "until_completion"
    MANUAL_DELETION = "manual_deletion"

@dataclass
class AnalysisRequest:
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime

@dataclass
class SessionData:
    user_preferences: Dict[str, Any]
    active_operations: List[str]
    temporary_modifications: List[Any]
    analysis_history: List[AnalysisRequest]
    confidence_thresholds: Dict[str, float]

@dataclass
class ProcessContext:
    process_id: str
    isolation_boundary: str
    resource_limits: Dict[str, Any]
    cleanup_policy: str

@dataclass
class StorySession:
    session_id: str
    project_id: str
    active_story_arcs: List[str]
    analysis_cache: Dict[str, Any]
    last_activity: datetime
    session_data: SessionData
    persistence_policy: PersistencePolicy
    process_isolation_context: ProcessContext
