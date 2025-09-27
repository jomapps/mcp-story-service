"""GenreTemplate model with conventions and authenticity rules.

This model represents genre templates with their conventions, patterns,
and authenticity validation rules per FR-005.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear genre representation with standard patterns
- LLM Declaration (VI): Structured for genre analysis workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class GenreCategory(str, Enum):
    """Primary genre categories."""
    ACTION = "action"
    ADVENTURE = "adventure"
    ANIMATION = "animation"
    BIOGRAPHICAL = "biographical"
    COMEDY = "comedy"
    CRIME = "crime"
    DOCUMENTARY = "documentary"
    DRAMA = "drama"
    FAMILY = "family"
    FANTASY = "fantasy"
    HISTORICAL = "historical"
    HORROR = "horror"
    MUSICAL = "musical"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    SCI_FI = "sci-fi"
    SUPERHERO = "superhero"
    THRILLER = "thriller"
    WAR = "war"
    WESTERN = "western"


class ConventionType(str, Enum):
    """Types of genre conventions."""
    PACING = "pacing"
    STRUCTURE = "structure" 
    CHARACTER_ARCHETYPES = "character_archetypes"
    COMMON_ELEMENTS = "common_elements"
    THEMES = "themes"
    TONE = "tone"
    SETTING = "setting"
    PLOT_DEVICES = "plot_devices"


class AuthenticityLevel(str, Enum):
    """Authenticity requirement levels."""
    REQUIRED = "required"
    EXPECTED = "expected"
    OPTIONAL = "optional"
    DISCOURAGED = "discouraged"
    FORBIDDEN = "forbidden"


class GenreConvention(BaseModel):
    """Individual genre convention with validation rules."""
    name: str = Field(..., description="Convention name")
    description: str = Field(..., description="Detailed description of convention")
    convention_type: ConventionType = Field(..., description="Type of convention")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance weight (0=optional, 1=critical)")
    
    # Pattern matching
    keywords: List[str] = Field(default_factory=list, description="Keywords that indicate this convention")
    patterns: List[str] = Field(default_factory=list, description="Regex patterns for detection")
    examples: List[str] = Field(default_factory=list, description="Example implementations")
    
    # Validation rules
    authenticity_level: AuthenticityLevel = Field(..., description="Required authenticity level")
    validation_rules: List[str] = Field(default_factory=list, description="Specific validation rules")
    
    # Confidence factors
    confidence_boost: float = Field(0.0, ge=-0.5, le=0.5, description="Confidence adjustment when present")
    confidence_penalty: float = Field(0.0, ge=-0.5, le=0.5, description="Confidence penalty when missing")


class StructuralPattern(BaseModel):
    """Structural patterns specific to genre."""
    pattern_name: str = Field(..., description="Name of structural pattern")
    act_structure: Dict[str, Any] = Field(..., description="Expected act structure")
    beat_sequence: List[str] = Field(default_factory=list, description="Expected beat sequence")
    pacing_profile: Dict[str, float] = Field(default_factory=dict, description="Expected pacing profile")
    
    # Validation
    required_beats: List[str] = Field(default_factory=list, description="Beats required for authenticity")
    optional_beats: List[str] = Field(default_factory=list, description="Beats that enhance authenticity")
    forbidden_beats: List[str] = Field(default_factory=list, description="Beats that break authenticity")


class CharacterArchetype(BaseModel):
    """Character archetype for genre."""
    archetype_name: str = Field(..., description="Name of character archetype")
    description: str = Field(..., description="Description of archetype role")
    importance: AuthenticityLevel = Field(..., description="Importance level for genre")
    
    # Characteristics
    typical_traits: List[str] = Field(default_factory=list, description="Typical character traits")
    typical_roles: List[str] = Field(default_factory=list, description="Typical story roles")
    relationship_patterns: List[str] = Field(default_factory=list, description="Common relationship patterns")
    
    # Validation
    required_for_authenticity: bool = Field(False, description="Whether required for authentic genre")
    examples: List[str] = Field(default_factory=list, description="Example characters from genre")


class ThematicElement(BaseModel):
    """Thematic elements associated with genre."""
    theme_name: str = Field(..., description="Name of thematic element")
    description: str = Field(..., description="Description of thematic content")
    prevalence: float = Field(..., ge=0.0, le=1.0, description="How common this theme is in genre")
    
    # Detection
    keywords: List[str] = Field(default_factory=list, description="Keywords indicating theme")
    situations: List[str] = Field(default_factory=list, description="Situations that express theme")
    conflicts: List[str] = Field(default_factory=list, description="Conflicts that explore theme")


class AuthenticityRule(BaseModel):
    """Rules for determining genre authenticity."""
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="What this rule validates")
    
    # Rule logic
    rule_type: str = Field(..., description="Type of rule (presence, absence, pattern, etc.)")
    conditions: Dict[str, Any] = Field(..., description="Conditions that must be met")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in overall authenticity score")
    
    # Scoring
    pass_score: float = Field(1.0, ge=0.0, le=1.0, description="Score when rule passes")
    fail_score: float = Field(0.0, ge=0.0, le=1.0, description="Score when rule fails")
    partial_scoring: bool = Field(False, description="Whether rule allows partial scores")


class ConfidenceThresholds(BaseModel):
    """Confidence thresholds for genre validation."""
    minimum: float = Field(0.75, ge=0.0, le=1.0, description="Minimum threshold per FR-001")
    excellent: float = Field(0.90, ge=0.0, le=1.0, description="Excellent threshold")
    
    # Component thresholds
    structure_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Structure component threshold")
    character_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Character component threshold")
    theme_threshold: float = Field(0.60, ge=0.0, le=1.0, description="Theme component threshold")
    element_threshold: float = Field(0.65, ge=0.0, le=1.0, description="Element component threshold")

    @validator('excellent')
    def excellent_above_minimum(cls, v, values):
        if 'minimum' in values and v <= values['minimum']:
            raise ValueError('excellent threshold must be higher than minimum')
        return v


class GenreTemplate(BaseModel):
    """
    Genre template model with conventions and authenticity rules.
    
    Defines comprehensive genre patterns, conventions, and validation
    rules for determining story adherence to genre expectations.
    """
    
    # Core identification
    genre_id: str = Field(..., description="Unique genre identifier")
    name: str = Field(..., description="Genre name")
    category: GenreCategory = Field(..., description="Primary genre category")
    description: str = Field(..., description="Detailed genre description")
    
    # Alternative names and aliases
    aliases: List[str] = Field(default_factory=list, description="Alternative names for genre")
    subgenres: List[str] = Field(default_factory=list, description="Related subgenres")
    parent_genres: List[str] = Field(default_factory=list, description="Parent/broader genres")
    
    # Core conventions
    conventions: List[GenreConvention] = Field(default_factory=list, description="Genre conventions")
    structural_patterns: List[StructuralPattern] = Field(default_factory=list, description="Structural patterns")
    character_archetypes: List[CharacterArchetype] = Field(default_factory=list, description="Character archetypes")
    thematic_elements: List[ThematicElement] = Field(default_factory=list, description="Thematic elements")
    
    # Authenticity validation
    authenticity_rules: List[AuthenticityRule] = Field(default_factory=list, description="Authenticity rules")
    confidence_thresholds: ConfidenceThresholds = Field(default_factory=ConfidenceThresholds, description="Confidence thresholds")
    
    # Usage metadata
    popularity_score: float = Field(0.5, ge=0.0, le=1.0, description="Genre popularity/commonness")
    complexity_score: float = Field(0.5, ge=0.0, le=1.0, description="Genre complexity for analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation time")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    version: str = Field(default="1.0", description="Template version")
    
    # Metadata
    examples: List[str] = Field(default_factory=list, description="Example works in this genre")
    sources: List[str] = Field(default_factory=list, description="Sources for genre definition")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "genre_id": "thriller",
                "name": "Thriller",
                "category": "thriller",
                "description": "Stories designed to keep audience on edge with suspense and excitement",
                "confidence_thresholds": {
                    "minimum": 0.75,
                    "excellent": 0.90
                },
                "conventions": [
                    {
                        "name": "Building Tension",
                        "description": "Gradually escalating tension throughout story",
                        "convention_type": "pacing",
                        "importance": 0.9,
                        "authenticity_level": "required"
                    }
                ]
            }
        }

    @validator('confidence_thresholds', always=True)
    def ensure_thresholds(cls, v):
        """Ensure confidence thresholds are properly set."""
        if not v:
            v = ConfidenceThresholds()
        # Ensure minimum threshold meets constitutional requirement
        if v.minimum < 0.75:
            v.minimum = 0.75
        return v

    @root_validator
    def validate_authenticity_rules(cls, values):
        """Validate authenticity rules are consistent."""
        rules = values.get('authenticity_rules', [])
        
        # Check for duplicate rule IDs
        rule_ids = [rule.rule_id for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Authenticity rules must have unique IDs")
        
        # Validate total weight doesn't exceed reasonable bounds
        total_weight = sum(rule.weight for rule in rules)
        if total_weight > 2.0:  # Allow some flexibility
            raise ValueError(f"Total authenticity rule weight ({total_weight}) exceeds reasonable bounds")
        
        return values

    def get_conventions_by_type(self, convention_type: ConventionType) -> List[GenreConvention]:
        """Get conventions of a specific type."""
        return [conv for conv in self.conventions if conv.convention_type == convention_type]

    def get_required_conventions(self) -> List[GenreConvention]:
        """Get all required conventions for authenticity."""
        return [conv for conv in self.conventions 
                if conv.authenticity_level == AuthenticityLevel.REQUIRED]

    def get_critical_authenticity_rules(self) -> List[AuthenticityRule]:
        """Get authenticity rules with high weight."""
        return [rule for rule in self.authenticity_rules if rule.weight >= 0.7]

    def calculate_pattern_confidence(self, story_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for different pattern categories."""
        scores = {
            "structure": 0.0,
            "characters": 0.0,
            "themes": 0.0,
            "elements": 0.0,
            "overall": 0.0
        }
        
        # Structure scoring
        structure_matches = 0
        structure_total = len(self.structural_patterns)
        if structure_total > 0:
            # This would be implemented with actual pattern matching logic
            scores["structure"] = structure_matches / structure_total
        
        # Character scoring
        character_matches = 0
        character_total = len(self.character_archetypes)
        if character_total > 0:
            scores["characters"] = character_matches / character_total
        
        # Theme scoring
        theme_matches = 0
        theme_total = len(self.thematic_elements)
        if theme_total > 0:
            scores["themes"] = theme_matches / theme_total
        
        # Convention scoring
        element_matches = 0
        element_total = len(self.conventions)
        if element_total > 0:
            scores["elements"] = element_matches / element_total
        
        # Overall scoring with weights
        scores["overall"] = (
            scores["structure"] * 0.3 +
            scores["characters"] * 0.25 +
            scores["elements"] * 0.25 +
            scores["themes"] * 0.2
        )
        
        return scores

    def validate_authenticity(self, story_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate story authenticity against genre rules."""
        results = {
            "passes_minimum": False,
            "authenticity_score": 0.0,
            "rule_results": [],
            "violations": [],
            "recommendations": []
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for rule in self.authenticity_rules:
            # This would contain actual rule evaluation logic
            rule_passed = True  # Placeholder
            rule_score = rule.pass_score if rule_passed else rule.fail_score
            
            total_score += rule_score * rule.weight
            total_weight += rule.weight
            
            rule_result = {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "passed": rule_passed,
                "score": rule_score,
                "weight": rule.weight
            }
            results["rule_results"].append(rule_result)
            
            if not rule_passed and rule.weight >= 0.5:  # Important rule
                results["violations"].append({
                    "rule": rule.rule_name,
                    "description": rule.description,
                    "severity": "high" if rule.weight >= 0.7 else "medium"
                })
        
        # Calculate final authenticity score
        if total_weight > 0:
            results["authenticity_score"] = total_score / total_weight
        
        results["passes_minimum"] = results["authenticity_score"] >= self.confidence_thresholds.minimum
        
        # Generate recommendations
        if not results["passes_minimum"]:
            results["recommendations"] = self._generate_authenticity_recommendations(results)
        
        return results

    def _generate_authenticity_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving genre authenticity."""
        recommendations = []
        
        violations = validation_results.get("violations", [])
        high_severity = [v for v in violations if v.get("severity") == "high"]
        
        if high_severity:
            recommendations.append(f"Address {len(high_severity)} critical genre violations")
        
        # Check required conventions
        required_convs = self.get_required_conventions()
        if required_convs:
            recommendations.append(f"Ensure story includes required {self.name.lower()} conventions")
        
        # Check structural patterns
        if self.structural_patterns:
            recommendations.append(f"Follow {self.name.lower()} structural patterns for better authenticity")
        
        # Check character archetypes
        required_chars = [arch for arch in self.character_archetypes 
                         if arch.required_for_authenticity]
        if required_chars:
            recommendations.append(f"Include key {self.name.lower()} character archetypes")
        
        return recommendations

    def get_pattern_keywords(self) -> Set[str]:
        """Get all keywords associated with this genre."""
        keywords = set()
        
        # Convention keywords
        for conv in self.conventions:
            keywords.update(conv.keywords)
        
        # Theme keywords
        for theme in self.thematic_elements:
            keywords.update(theme.keywords)
        
        # Add genre aliases
        keywords.update(self.aliases)
        keywords.add(self.name.lower())
        
        return keywords

    def get_genre_summary(self) -> Dict[str, Any]:
        """Get comprehensive genre template summary."""
        return {
            "genre": {
                "id": self.genre_id,
                "name": self.name,
                "category": self.category.value,
                "description": self.description
            },
            "conventions": {
                "total": len(self.conventions),
                "required": len(self.get_required_conventions()),
                "by_type": {
                    conv_type.value: len(self.get_conventions_by_type(conv_type))
                    for conv_type in ConventionType
                }
            },
            "patterns": {
                "structural": len(self.structural_patterns),
                "characters": len(self.character_archetypes),
                "themes": len(self.thematic_elements),
                "rules": len(self.authenticity_rules)
            },
            "thresholds": {
                "minimum": self.confidence_thresholds.minimum,
                "excellent": self.confidence_thresholds.excellent
            },
            "metadata": {
                "complexity": self.complexity_score,
                "popularity": self.popularity_score,
                "version": self.version,
                "last_updated": self.last_updated.isoformat()
            }
        }

    def to_analysis_template(self) -> Dict[str, Any]:
        """Convert to format suitable for genre analysis."""
        return {
            "genre_id": self.genre_id,
            "name": self.name,
            "description": self.description,
            "conventions": [conv.dict() for conv in self.conventions],
            "structural_patterns": [pattern.dict() for pattern in self.structural_patterns],
            "character_archetypes": [arch.dict() for arch in self.character_archetypes],
            "thematic_elements": [theme.dict() for theme in self.thematic_elements],
            "authenticity_rules": [rule.dict() for rule in self.authenticity_rules],
            "confidence_thresholds": self.confidence_thresholds.dict(),
            "keywords": list(self.get_pattern_keywords()),
            "metadata": {
                "category": self.category.value,
                "complexity": self.complexity_score,
                "version": self.version
            }
        }

    @classmethod
    def load_from_yaml_config(cls, yaml_config: Dict[str, Any]) -> "GenreTemplate":
        """Load genre template from YAML configuration."""
        # Convert YAML structure to model format
        processed_config = yaml_config.copy()
        
        # Process conventions
        if "conventions" in processed_config:
            conventions_data = processed_config["conventions"]
            processed_conventions = []
            
            for conv_type, conv_items in conventions_data.items():
                if isinstance(conv_items, list):
                    for item in conv_items:
                        conv = GenreConvention(
                            name=item,
                            description=item,
                            convention_type=ConventionType(conv_type.lower()),
                            importance=0.7,  # Default importance
                            authenticity_level=AuthenticityLevel.EXPECTED
                        )
                        processed_conventions.append(conv)
            
            processed_config["conventions"] = processed_conventions
        
        # Set defaults
        processed_config.setdefault("genre_id", processed_config["name"].lower().replace("-", "_"))
        processed_config.setdefault("category", processed_config["name"].lower().replace("-", "_"))
        
        return cls(**processed_config)