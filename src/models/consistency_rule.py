"""ConsistencyRule model with validation logic and severity levels.

This model represents consistency validation rules with logic and severity
classification per FR-004.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear rule structure without over-complexity
- LLM Declaration (VI): Structured for consistency validation workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class RuleType(str, Enum):
    """Types of consistency rules."""
    CHARACTER_ATTRIBUTE = "character_attribute"
    TIMELINE = "timeline"
    PLOT_LOGIC = "plot_logic"
    WORLD_BUILDING = "world_building"
    CHARACTER_BEHAVIOR = "character_behavior"
    RELATIONSHIP = "relationship"
    SETTING = "setting"
    OBJECT_TRACKING = "object_tracking"
    CAUSE_EFFECT = "cause_effect"
    CONTINUITY = "continuity"


class SeverityLevel(str, Enum):
    """Severity levels for consistency violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINOR = "minor"


class ValidationLogic(str, Enum):
    """Types of validation logic."""
    EXACT_MATCH = "exact_match"
    PATTERN_MATCH = "pattern_match"
    RANGE_CHECK = "range_check"
    PRESENCE_CHECK = "presence_check"
    ABSENCE_CHECK = "absence_check"
    SEQUENCE_CHECK = "sequence_check"
    RELATIONSHIP_CHECK = "relationship_check"
    CUSTOM_LOGIC = "custom_logic"


class RuleCondition(BaseModel):
    """Individual condition within a consistency rule."""
    condition_id: str = Field(..., description="Unique condition identifier")
    description: str = Field(..., description="Human-readable condition description")
    validation_logic: ValidationLogic = Field(..., description="Type of validation logic")
    
    # Condition parameters
    target_attribute: str = Field(..., description="Attribute or element to validate")
    expected_value: Optional[Any] = Field(None, description="Expected value for validation")
    pattern: Optional[str] = Field(None, description="Regex pattern for pattern matching")
    range_min: Optional[float] = Field(None, description="Minimum value for range checks")
    range_max: Optional[float] = Field(None, description="Maximum value for range checks")
    
    # Context and scope
    scope: str = Field("global", description="Scope of validation (global, scene, chapter, etc.)")
    context_requirements: List[str] = Field(default_factory=list, description="Required context for validation")
    
    # Tolerance and flexibility
    tolerance: float = Field(0.0, ge=0.0, le=1.0, description="Tolerance for fuzzy matching")
    case_sensitive: bool = Field(True, description="Whether validation is case sensitive")
    whitespace_sensitive: bool = Field(False, description="Whether whitespace matters")


class ViolationEvidence(BaseModel):
    """Evidence of a consistency violation."""
    position: float = Field(..., ge=0.0, le=1.0, description="Position in story where violation occurs")
    content_snippet: str = Field(..., description="Content that violates the rule")
    conflicting_with: Optional[str] = Field(None, description="What this content conflicts with")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in violation detection")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional violation context")


class ConsistencyRule(BaseModel):
    """
    Consistency rule model with validation logic and severity levels.
    
    Defines rules for validating narrative consistency with configurable
    logic, severity assessment, and violation tracking.
    """
    
    # Core identification
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    rule_type: RuleType = Field(..., description="Category of consistency rule")
    
    # Rule definition
    description: str = Field(..., description="Detailed description of what rule validates")
    conditions: List[RuleCondition] = Field(..., min_items=1, description="Validation conditions")
    
    # Severity and impact
    severity_level: SeverityLevel = Field(..., description="Severity of violations")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact on story quality (0=none, 1=critical)")
    confidence_penalty: float = Field(..., ge=0.0, le=1.0, description="Confidence penalty for violations")
    
    # Rule behavior
    is_active: bool = Field(True, description="Whether rule is currently active")
    applies_to_genres: List[str] = Field(default_factory=list, description="Genres this rule applies to")
    exclusion_patterns: List[str] = Field(default_factory=list, description="Patterns that exclude rule application")
    
    # Validation configuration
    require_all_conditions: bool = Field(True, description="Whether all conditions must pass")
    allow_exceptions: bool = Field(False, description="Whether exceptions are allowed")
    exception_patterns: List[str] = Field(default_factory=list, description="Patterns that allow exceptions")
    
    # Performance and optimization
    max_violations: int = Field(100, ge=1, description="Maximum violations to track")
    early_termination: bool = Field(False, description="Whether to stop after first violation")
    cache_results: bool = Field(True, description="Whether to cache validation results")
    
    # Metadata and tracking
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Rule creation time")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last rule update")
    usage_count: int = Field(0, description="Number of times rule has been applied")
    violation_count: int = Field(0, description="Total violations found by this rule")
    
    # Rule metadata
    author: Optional[str] = Field(None, description="Rule author/creator")
    source: Optional[str] = Field(None, description="Source or reference for rule")
    examples: List[str] = Field(default_factory=list, description="Example violations")
    version: str = Field(default="1.0", description="Rule version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional rule metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "rule_id": "char_eye_color_consistency",
                "rule_name": "Character Eye Color Consistency",
                "rule_type": "character_attribute",
                "description": "Character eye color must remain consistent throughout story",
                "severity_level": "medium",
                "impact_score": 0.6,
                "conditions": [
                    {
                        "condition_id": "eye_color_check",
                        "description": "Check eye color mentions for consistency",
                        "validation_logic": "exact_match",
                        "target_attribute": "character.eye_color"
                    }
                ]
            }
        }

    @validator('conditions')
    def validate_conditions(cls, v):
        """Validate that conditions have unique IDs."""
        condition_ids = [condition.condition_id for condition in v]
        if len(condition_ids) != len(set(condition_ids)):
            raise ValueError("Condition IDs must be unique within a rule")
        return v

    @root_validator
    def validate_rule_consistency(cls, values):
        """Validate rule internal consistency."""
        severity = values.get('severity_level')
        impact = values.get('impact_score', 0.0)
        
        # High severity should have high impact
        if severity == SeverityLevel.CRITICAL and impact < 0.7:
            raise ValueError("Critical severity should have impact score >= 0.7")
        
        if severity == SeverityLevel.HIGH and impact < 0.5:
            raise ValueError("High severity should have impact score >= 0.5")
        
        return values

    def validate_content(self, story_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate content against this consistency rule."""
        if not self.is_active:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.rule_name,
                "passed": True,
                "skipped": True,
                "reason": "Rule is inactive"
            }
        
        context = context or {}
        violations = []
        passed_conditions = 0
        total_conditions = len(self.conditions)
        
        for condition in self.conditions:
            condition_result = self._validate_condition(condition, story_content, context)
            
            if condition_result["passed"]:
                passed_conditions += 1
            else:
                violations.extend(condition_result.get("violations", []))
                
                # Early termination if configured
                if self.early_termination:
                    break
        
        # Determine overall pass/fail
        if self.require_all_conditions:
            passed = passed_conditions == total_conditions
        else:
            passed = passed_conditions > 0
        
        # Update usage statistics
        self.usage_count += 1
        if not passed:
            self.violation_count += len(violations)
        
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type.value,
            "passed": passed,
            "severity": self.severity_level.value if not passed else None,
            "impact_score": self.impact_score if not passed else 0.0,
            "confidence_penalty": self.confidence_penalty if not passed else 0.0,
            "conditions_passed": passed_conditions,
            "total_conditions": total_conditions,
            "violations": violations,
            "metadata": {
                "usage_count": self.usage_count,
                "total_violations": self.violation_count
            }
        }

    def _validate_condition(self, condition: RuleCondition, content: str, 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single condition."""
        violations = []
        
        try:
            if condition.validation_logic == ValidationLogic.EXACT_MATCH:
                violations = self._validate_exact_match(condition, content, context)
            elif condition.validation_logic == ValidationLogic.PATTERN_MATCH:
                violations = self._validate_pattern_match(condition, content, context)
            elif condition.validation_logic == ValidationLogic.PRESENCE_CHECK:
                violations = self._validate_presence_check(condition, content, context)
            elif condition.validation_logic == ValidationLogic.SEQUENCE_CHECK:
                violations = self._validate_sequence_check(condition, content, context)
            else:
                # Placeholder for other validation types
                violations = []
            
            passed = len(violations) == 0
            
        except Exception as e:
            # Handle validation errors gracefully
            violations = [{
                "type": "validation_error",
                "description": f"Error validating condition: {str(e)}",
                "position": 0.0,
                "confidence": 0.5
            }]
            passed = False
        
        return {
            "condition_id": condition.condition_id,
            "passed": passed,
            "violations": violations
        }

    def _validate_exact_match(self, condition: RuleCondition, content: str, 
                            context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate exact match condition."""
        violations = []
        
        # This is a simplified implementation
        # Real implementation would extract and compare character attributes
        target_attr = condition.target_attribute
        expected_value = condition.expected_value
        
        if "character" in target_attr and "eye_color" in target_attr:
            # Example: Look for eye color mentions
            import re
            eye_color_pattern = r'(\w+)\s+eyes?'
            matches = re.finditer(eye_color_pattern, content, re.IGNORECASE)
            
            found_colors = []
            for match in matches:
                color = match.group(1).lower()
                position = match.start() / len(content)
                found_colors.append((color, position))
            
            # Check for inconsistencies
            unique_colors = set(color for color, _ in found_colors)
            if len(unique_colors) > 1:
                for color, position in found_colors[1:]:  # Skip first occurrence
                    if color != found_colors[0][0]:
                        violations.append({
                            "type": "attribute_inconsistency",
                            "description": f"Eye color changed from '{found_colors[0][0]}' to '{color}'",
                            "position": position,
                            "content_snippet": content[max(0, int(position * len(content)) - 50):
                                                     int(position * len(content)) + 50],
                            "confidence": 0.8
                        })
        
        return violations

    def _validate_pattern_match(self, condition: RuleCondition, content: str,
                              context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate pattern match condition."""
        violations = []
        
        if condition.pattern:
            import re
            try:
                pattern = re.compile(condition.pattern, re.IGNORECASE if not condition.case_sensitive else 0)
                matches = list(pattern.finditer(content))
                
                # For demonstration, assume any match is a violation
                # Real logic would depend on the specific rule
                for match in matches:
                    position = match.start() / len(content)
                    violations.append({
                        "type": "pattern_violation",
                        "description": f"Pattern '{condition.pattern}' found",
                        "position": position,
                        "content_snippet": match.group(0),
                        "confidence": 0.9
                    })
            except re.error:
                # Invalid pattern
                pass
        
        return violations

    def _validate_presence_check(self, condition: RuleCondition, content: str,
                               context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate presence check condition."""
        violations = []
        
        target_attr = condition.target_attribute
        if target_attr.lower() not in content.lower():
            violations.append({
                "type": "missing_element",
                "description": f"Required element '{target_attr}' not found",
                "position": 0.0,
                "content_snippet": content[:100] + "..." if len(content) > 100 else content,
                "confidence": 0.7
            })
        
        return violations

    def _validate_sequence_check(self, condition: RuleCondition, content: str,
                               context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate sequence check condition."""
        violations = []
        
        # Simplified timeline validation
        # Real implementation would parse and validate event sequences
        
        return violations

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get comprehensive rule summary."""
        return {
            "rule_info": {
                "id": self.rule_id,
                "name": self.rule_name,
                "type": self.rule_type.value,
                "description": self.description
            },
            "severity": {
                "level": self.severity_level.value,
                "impact_score": self.impact_score,
                "confidence_penalty": self.confidence_penalty
            },
            "configuration": {
                "is_active": self.is_active,
                "require_all_conditions": self.require_all_conditions,
                "allow_exceptions": self.allow_exceptions,
                "early_termination": self.early_termination
            },
            "conditions": [
                {
                    "id": cond.condition_id,
                    "description": cond.description,
                    "logic": cond.validation_logic.value,
                    "target": cond.target_attribute
                }
                for cond in self.conditions
            ],
            "statistics": {
                "usage_count": self.usage_count,
                "violation_count": self.violation_count,
                "violation_rate": self.violation_count / max(self.usage_count, 1)
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat(),
                "version": self.version,
                "author": self.author
            }
        }

    def applies_to_genre(self, genre: str) -> bool:
        """Check if rule applies to specified genre."""
        if not self.applies_to_genres:
            return True  # Applies to all genres if none specified
        
        return genre.lower() in [g.lower() for g in self.applies_to_genres]

    def is_excluded_by_pattern(self, content: str) -> bool:
        """Check if content matches exclusion patterns."""
        import re
        
        for pattern in self.exclusion_patterns:
            try:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            except re.error:
                continue  # Skip invalid patterns
        
        return False

    def update_statistics(self, violations_found: int) -> None:
        """Update rule usage statistics."""
        self.usage_count += 1
        self.violation_count += violations_found
        self.last_updated = datetime.utcnow()

    def clone_with_modifications(self, modifications: Dict[str, Any]) -> "ConsistencyRule":
        """Create a copy of rule with modifications."""
        rule_data = self.dict()
        rule_data.update(modifications)
        
        # Generate new ID for cloned rule
        if 'rule_id' not in modifications:
            rule_data['rule_id'] = f"{self.rule_id}_clone_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return ConsistencyRule(**rule_data)

    def to_validation_config(self) -> Dict[str, Any]:
        """Convert to validation configuration format."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type.value,
            "severity": self.severity_level.value,
            "active": self.is_active,
            "conditions": [
                {
                    "id": cond.condition_id,
                    "logic": cond.validation_logic.value,
                    "target": cond.target_attribute,
                    "expected": cond.expected_value,
                    "pattern": cond.pattern,
                    "scope": cond.scope,
                    "tolerance": cond.tolerance
                }
                for cond in self.conditions
            ],
            "configuration": {
                "require_all": self.require_all_conditions,
                "allow_exceptions": self.allow_exceptions,
                "early_termination": self.early_termination,
                "max_violations": self.max_violations
            },
            "impact": {
                "score": self.impact_score,
                "penalty": self.confidence_penalty
            }
        }