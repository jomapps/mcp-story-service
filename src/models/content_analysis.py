from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ContentWarning:
    warning_type: str
    description: str
    impact_on_analysis: str
    suggested_remediation: str
    confidence_penalty: float

@dataclass
class ContentAnalysisResult:
    content_id: str
    completeness_score: float
    missing_elements: List[str]
    warnings: List[ContentWarning]
    partial_analysis: Dict[str, Any]
    confidence_adjustments: Dict[str, float]
