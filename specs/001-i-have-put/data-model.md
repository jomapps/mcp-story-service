# Data Model: MCP Story Service

**Generated**: 2025-09-26  
**Purpose**: Entity definitions and relationships for narrative intelligence system

## Core Story Entities

### Story Arc
**Purpose**: Represents complete narrative structure from beginning to resolution  
**Source**: Feature requirements FR-001, FR-005 (structure analysis, pacing)

```python
@dataclass
class StoryArc:
    id: str                          # Unique identifier
    project_id: str                  # Associated project for isolation
    title: str                       # Story title/description
    genre: str                       # Primary genre classification
    act_structure: ActStructure      # Three-act progression details
    pacing_profile: PacingProfile    # Tension curve and rhythm data
    confidence_score: float          # Analysis confidence (0.0-1.0)
    created_at: datetime
    updated_at: datetime
    status: ArcStatus               # draft, analyzed, validated, complete

@dataclass 
class ActStructure:
    act_one: Act                    # Setup and introduction
    act_two: Act                    # Confrontation and development  
    act_three: Act                  # Resolution and conclusion
    turning_points: List[TurningPoint]  # Major plot pivots
    confidence_score: float         # Structure analysis confidence

@dataclass
class Act:
    start_position: float           # Percentage of total story (0.0-1.0)
    end_position: float            # Percentage of total story
    purpose: str                   # Act's narrative function
    key_events: List[str]          # Major events in this act
    character_arcs: List[str]      # Character development in this act
```

**Validation Rules**:
- `confidence_score` must be >= 0.75 for recommendations per clarification
- `act_structure.act_one.end_position` typically ≤ 0.25 
- `act_structure.act_two.end_position` typically ≤ 0.75
- Total act coverage must span 0.0 to 1.0
- `genre` must exist in genre template library (15+ supported)

### Plot Thread  
**Purpose**: Individual story elements tracked across episodes  
**Source**: Feature requirements FR-002 (plot thread management)

```python
@dataclass
class PlotThread:
    id: str                          # Unique identifier
    story_arc_id: str               # Parent story arc
    project_id: str                 # Project isolation key
    name: str                       # Thread description
    type: ThreadType                # main, subplot, character_arc, mystery
    lifecycle_stage: ThreadStage    # introduced, developing, ready_for_resolution, resolved
    introduction_point: float       # Position where thread starts (0.0-1.0)
    resolution_point: Optional[float]  # Position where resolved (None if unresolved)
    episodes: List[int]             # Episode numbers where thread appears
    dependencies: List[str]         # Other thread IDs this depends on
    importance_score: float         # 0.0-1.0, thread significance to overall story
    confidence_score: float         # Tracking confidence (0.0-1.0)
    created_at: datetime
    updated_at: datetime

@enum
class ThreadStage:
    INTRODUCED = "introduced"       # Just been established
    DEVELOPING = "developing"       # Active development
    READY_FOR_RESOLUTION = "ready_for_resolution"  # Peak moment/revelation opportunity
    RESOLVED = "resolved"          # Satisfactorily concluded
    ABANDONED = "abandoned"        # Dropped without resolution

@enum  
class ThreadType:
    MAIN = "main"                  # Central story line
    SUBPLOT = "subplot"            # Supporting story line
    CHARACTER_ARC = "character_arc"  # Character development thread
    MYSTERY = "mystery"            # Mystery/reveal thread
    ROMANCE = "romance"            # Romantic development
    CONFLICT = "conflict"          # Ongoing conflict thread
```

**State Transitions**:
- `INTRODUCED` → `DEVELOPING` (automatic after 2+ episodes)
- `DEVELOPING` → `READY_FOR_RESOLUTION` (analysis detection or manual)  
- `READY_FOR_RESOLUTION` → `RESOLVED` (manual confirmation)
- Any stage → `ABANDONED` (explicit decision)

### Narrative Beat
**Purpose**: Specific story moments with emotional/structural impact  
**Source**: Feature requirements FR-005 (pacing analysis)

```python
@dataclass
class NarrativeBeat:
    id: str                          # Unique identifier  
    story_arc_id: str               # Parent story arc
    project_id: str                 # Project isolation key
    position: float                 # Story position (0.0-1.0)
    type: BeatType                  # Specific beat classification
    emotional_impact: float         # -1.0 to 1.0 (negative/positive)
    tension_level: float           # 0.0-1.0 story tension at this point
    description: str               # Beat description
    episode_number: Optional[int]   # Episode if multi-episode story
    character_focus: List[str]     # Characters central to this beat
    plot_threads: List[str]        # Thread IDs affected by this beat
    confidence_score: float        # Beat analysis confidence

@enum
class BeatType:
    INCITING_INCIDENT = "inciting_incident"    # Story catalyst
    PLOT_POINT_1 = "plot_point_1"             # End of Act 1
    MIDPOINT = "midpoint"                      # Act 2 center
    PLOT_POINT_2 = "plot_point_2"             # End of Act 2  
    CLIMAX = "climax"                          # Story peak
    RESOLUTION = "resolution"                   # Story conclusion
    REVELATION = "revelation"                   # Major information reveal
    SETBACK = "setback"                        # Obstacle/complication
    VICTORY = "victory"                        # Success/achievement
    TWIST = "twist"                            # Unexpected turn
```

### Character Journey
**Purpose**: Character development aligned with plot progression  
**Source**: Feature requirements FR-003 (consistency validation)

```python
@dataclass  
class CharacterJourney:
    id: str                          # Unique identifier
    story_arc_id: str               # Parent story arc  
    project_id: str                 # Project isolation key
    character_name: str             # Character identifier
    arc_type: CharacterArcType      # Development pattern
    starting_state: CharacterState  # Initial character condition
    ending_state: CharacterState    # Final character condition  
    key_moments: List[str]          # Major character development points
    motivation: str                 # Core character drive
    conflict: str                   # Primary character obstacle
    growth_trajectory: List[CharacterState]  # State progression over time
    confidence_score: float         # Character analysis confidence

@dataclass
class CharacterState:
    position: float                 # Story position (0.0-1.0)
    emotional_state: str           # Character's emotional condition
    capabilities: List[str]        # Skills/powers at this point  
    relationships: Dict[str, str]  # Character connections and quality
    goals: List[str]              # Active character objectives
    knowledge: List[str]          # Information character possesses

@enum
class CharacterArcType:
    HERO_JOURNEY = "hero_journey"          # Classic hero transformation
    CORRUPTION = "corruption"              # Good to bad transition
    REDEMPTION = "redemption"              # Bad to good transition  
    COMING_OF_AGE = "coming_of_age"       # Maturation arc
    FALL_FROM_GRACE = "fall_from_grace"   # High to low status
    RISE_TO_POWER = "rise_to_power"       # Low to high status
    STATIC = "static"                      # Character remains unchanged
```

## Genre and Pattern Entities

### Genre Template
**Purpose**: Reusable storytelling patterns for different movie genres  
**Source**: Feature requirements FR-004 (15+ genre-specific guidance)

```python
@dataclass
class GenreTemplate:
    id: str                          # Unique genre identifier
    name: str                       # Genre display name  
    description: str                # Genre characteristics
    conventions: List[Convention]   # Expected story patterns
    pacing_profile: GenrePacing    # Typical tension curve
    character_archetypes: List[CharacterArchetype]  # Common character types
    common_beats: List[BeatType]   # Typical story beats for genre
    authenticity_rules: List[AuthenticityRule]  # Validation criteria (75% threshold)
    subgenres: List[str]           # Related genre variations

@dataclass
class Convention:
    name: str                       # Convention identifier
    description: str               # What this convention entails
    importance: ConventionImportance  # How critical this convention is
    examples: List[str]            # Example implementations
    violations_allowed: bool        # Can this convention be broken
    confidence_weight: float       # Impact on 75% threshold calculation
    
@enum
class ConventionImportance:
    ESSENTIAL = "essential"         # Genre-defining, must have
    TYPICAL = "typical"            # Common but not required  
    OPTIONAL = "optional"          # Nice to have, adds authenticity
```

### Consistency Rule
**Purpose**: Validation logic for detecting narrative contradictions  
**Source**: Feature requirements FR-003 (consistency validation)

```python
@dataclass
class ConsistencyRule:
    id: str                          # Unique rule identifier
    name: str                       # Rule display name
    description: str               # What this rule validates
    rule_type: RuleType           # Category of consistency check
    validation_logic: ValidationLogic  # How to apply this rule
    severity: RuleSeverity        # Impact level of violations
    scope: RuleScope              # What story elements this applies to
    confidence_impact: float       # Effect on confidence scores

@enum
class RuleType:
    TIMELINE = "timeline"              # Chronological consistency
    CHARACTER = "character"            # Character behavior consistency  
    WORLD = "world"                   # World-building consistency
    PLOT = "plot"                     # Plot logic consistency
    CONTINUITY = "continuity"         # Detail continuity
    
@enum  
class RuleSeverity:
    CRITICAL = "critical"             # Major plot hole
    WARNING = "warning"               # Potential issue
    SUGGESTION = "suggestion"         # Minor improvement
    
@dataclass
class ValidationLogic:
    conditions: List[str]             # What triggers this rule
    assertions: List[str]            # What must be true
    error_message: str               # Message when rule fails
    suggested_fix: Optional[str]     # Recommended solution
    confidence_penalty: float       # Impact on analysis confidence
```

## Session and State Entities

### Story Session  
**Purpose**: Maintain story state across multiple analysis requests  
**Source**: Feature requirements FR-008 (session continuity until project completion)

```python
@dataclass
class StorySession:
    session_id: str                  # Unique session identifier
    project_id: str                 # Associated project (isolation key)
    active_story_arcs: List[str]    # Arc IDs being analyzed
    analysis_cache: Dict[str, Any]  # Cached analysis results with confidence scores
    last_activity: datetime         # Most recent session use
    session_data: SessionData       # Persistent session information
    persistence_policy: PersistencePolicy  # Until completion or manual deletion
    process_isolation_context: ProcessContext  # Separate process state

@dataclass  
class SessionData:
    user_preferences: Dict[str, Any]   # Analysis preferences
    active_operations: List[str]       # Ongoing analysis operations
    temporary_modifications: List[Any]  # Session-specific changes
    analysis_history: List[AnalysisRequest]  # Recent analysis requests
    confidence_thresholds: Dict[str, float]  # Customized confidence levels

@dataclass
class ProcessContext:
    process_id: str                    # Separate process identifier
    isolation_boundary: str           # Project isolation enforcement
    resource_limits: Dict[str, Any]   # Process resource constraints
    cleanup_policy: str               # Process termination rules
```

## Malformed Content Handling

### Content Analysis Result
**Purpose**: Handle incomplete/malformed content with partial analysis  
**Source**: Clarification session - partial analysis with confidence scores and warnings

```python
@dataclass
class ContentAnalysisResult:
    content_id: str                    # Content identifier
    completeness_score: float         # 0.0-1.0 content quality
    missing_elements: List[str]        # Identified gaps in content
    warnings: List[ContentWarning]    # Missing data warnings
    partial_analysis: Dict[str, Any]  # Analysis results where possible
    confidence_adjustments: Dict[str, float]  # Confidence impact of missing data

@dataclass
class ContentWarning:
    warning_type: str                  # Type of missing/malformed element
    description: str                   # Specific issue description
    impact_on_analysis: str           # How this affects results
    suggested_remediation: str        # How to improve content
    confidence_penalty: float         # Impact on analysis confidence
```

## Entity Relationships

```
StoryArc (1) ←→ (N) PlotThread
StoryArc (1) ←→ (N) NarrativeBeat  
StoryArc (1) ←→ (N) CharacterJourney
StoryArc (N) ←→ (1) GenreTemplate
PlotThread (N) ←→ (N) NarrativeBeat
CharacterJourney (N) ←→ (N) NarrativeBeat
StorySession (1) ←→ (N) StoryArc
ConsistencyRule (N) ←→ (N) StoryArc [validation]
ProcessContext (1) ←→ (1) StorySession [isolation]

Project Isolation Enforcement:
- All entities include project_id for process separation
- ProcessContext enforces isolation boundaries
- Session cleanup on project completion or manual deletion
```

**Validation Dependencies**:
- All Plot Threads must belong to a Story Arc with matching project_id
- Narrative Beats must reference valid Plot Threads within same project
- Character Journeys must align with Story Arc timeline in same project
- Genre Template must exist before Story Arc validation (15+ templates)
- Consistency Rules applied based on Story Arc genre and structure
- Confidence scores must meet 75% threshold for recommendations
- Malformed content handling provides partial analysis with warnings

---

**Data Model Complete**: All entities defined with validation rules, confidence scoring, state transitions, project isolation, and clarification requirements integrated.