"""NarrativeAnalyzer service with three-act structure identification.

This service provides story structure analysis with confidence scoring
and pattern recognition per FR-001.

Constitutional Compliance:
- Library-First (I): Focused single-responsibility service
- Test-First (II): Tests written before implementation
- Simplicity (III): Clear analysis algorithms without complexity
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ...models.story_arc import StoryArc, StructureType, ActStructure, NarrativeBeatData, ConfidenceMetrics, ProjectIsolationContext
from ...models.narrative_beat import NarrativeBeat, BeatType, EmotionalImpact, TensionAnalysis, PacingMetrics, BeatContext
from ...models.content_analysis import ContentAnalysisResult, ContentQuality, ProcessingStatus


class StructurePattern:
    """Pattern definition for story structure detection."""
    
    def __init__(self, name: str, beats: List[str], act_boundaries: List[float]):
        self.name = name
        self.beats = beats
        self.act_boundaries = act_boundaries
        self.confidence_threshold = 0.75


class NarrativeAnalyzer:
    """
    Service for analyzing story structure and identifying narrative patterns.
    
    Provides three-act structure identification, beat detection, and 
    confidence scoring with 75% threshold compliance per FR-001.
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.confidence_threshold = 0.75
        
    def _initialize_patterns(self) -> Dict[str, StructurePattern]:
        """Initialize story structure patterns."""
        return {
            "three_act": StructurePattern(
                name="three_act",
                beats=["setup", "inciting_incident", "plot_point_1", "midpoint", "plot_point_2", "climax", "resolution"],
                act_boundaries=[0.25, 0.75, 1.0]
            ),
            "heros_journey": StructurePattern(
                name="heros_journey", 
                beats=["ordinary_world", "call_to_adventure", "crossing_threshold", "tests", "ordeal", "reward", "return"],
                act_boundaries=[0.2, 0.8, 1.0]
            ),
            "five_act": StructurePattern(
                name="five_act",
                beats=["exposition", "rising_action", "climax", "falling_action", "denouement"],
                act_boundaries=[0.2, 0.4, 0.6, 0.8, 1.0]
            )
        }

    async def analyze_story_structure(self, story_content: str, session_id: str = None) -> Dict[str, Any]:
        """
        Analyze story structure and identify narrative patterns.
        
        Args:
            story_content: Raw story content to analyze
            session_id: Optional session ID for isolation context
            
        Returns:
            Analysis results with confidence scoring per FR-001
        """
        try:
            # Preprocess content
            processed_content = self._preprocess_content(story_content)
            
            if not processed_content.strip():
                return self._create_empty_content_result(story_content, session_id)
            
            # Detect structure type
            structure_type, structure_confidence = await self._detect_structure_type(processed_content)
            
            # Analyze acts
            acts = await self._analyze_acts(processed_content, structure_type)
            
            # Identify narrative beats
            beats = await self._identify_narrative_beats(processed_content, structure_type)
            
            # Calculate overall confidence
            confidence_metrics = self._calculate_confidence_metrics(
                structure_confidence, acts, beats, processed_content
            )
            
            # Create story arc
            story_arc = self._create_story_arc(
                processed_content, structure_type, acts, beats, 
                confidence_metrics, session_id
            )
            
            return story_arc.to_analysis_result()
            
        except Exception as e:
            return self._create_error_result(str(e), story_content, session_id)

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for analysis."""
        if not content:
            return ""
        
        # Clean up common formatting issues
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)  # Remove control chars
        content = content.strip()
        
        return content

    async def _detect_structure_type(self, content: str) -> Tuple[StructureType, float]:
        """Detect the most likely story structure type."""
        scores = {}
        
        # Three-act structure detection
        three_act_score = self._score_three_act_structure(content)
        scores[StructureType.THREE_ACT] = three_act_score
        
        # Hero's journey detection
        heros_journey_score = self._score_heros_journey_structure(content)
        scores[StructureType.HEROS_JOURNEY] = heros_journey_score
        
        # Five-act structure detection
        five_act_score = self._score_five_act_structure(content)
        scores[StructureType.FIVE_ACT] = five_act_score
        
        # Find best match
        best_structure = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_structure]
        
        # If no structure has good confidence, default to three-act
        if best_score < 0.3:
            return StructureType.THREE_ACT, 0.3
        
        return best_structure, best_score

    def _score_three_act_structure(self, content: str) -> float:
        """Score content for three-act structure adherence."""
        score = 0.0
        content_lower = content.lower()
        
        # Look for act markers
        act_markers = ['act i', 'act 1', 'chapter 1', 'beginning']
        if any(marker in content_lower for marker in act_markers):
            score += 0.2
        
        # Look for setup elements
        setup_keywords = ['introduce', 'establish', 'normal', 'ordinary', 'routine']
        setup_score = sum(1 for keyword in setup_keywords if keyword in content_lower)
        score += min(setup_score * 0.1, 0.3)
        
        # Look for inciting incident
        incident_keywords = ['suddenly', 'unexpected', 'changed', 'discovered', 'crisis']
        incident_score = sum(1 for keyword in incident_keywords if keyword in content_lower)
        score += min(incident_score * 0.15, 0.4)
        
        # Look for resolution
        resolution_keywords = ['finally', 'ended', 'resolved', 'conclusion', 'victory']
        resolution_score = sum(1 for keyword in resolution_keywords if keyword in content_lower)
        score += min(resolution_score * 0.1, 0.3)
        
        return min(score, 1.0)

    def _score_heros_journey_structure(self, content: str) -> float:
        """Score content for hero's journey structure adherence."""
        score = 0.0
        content_lower = content.lower()
        
        # Look for hero's journey elements
        journey_keywords = ['hero', 'quest', 'journey', 'adventure', 'call', 'destiny']
        journey_score = sum(1 for keyword in journey_keywords if keyword in content_lower)
        score += min(journey_score * 0.15, 0.4)
        
        # Look for mentor elements
        mentor_keywords = ['mentor', 'guide', 'teacher', 'wise', 'advisor']
        mentor_score = sum(1 for keyword in mentor_keywords if keyword in content_lower)
        score += min(mentor_score * 0.2, 0.3)
        
        # Look for transformation
        transform_keywords = ['transform', 'change', 'grow', 'learn', 'become']
        transform_score = sum(1 for keyword in transform_keywords if keyword in content_lower)
        score += min(transform_score * 0.1, 0.3)
        
        return min(score, 1.0)

    def _score_five_act_structure(self, content: str) -> float:
        """Score content for five-act structure adherence."""
        score = 0.0
        content_lower = content.lower()
        
        # Look for classical structure elements
        classical_keywords = ['exposition', 'rising', 'climax', 'falling', 'denouement']
        classical_score = sum(1 for keyword in classical_keywords if keyword in content_lower)
        score += min(classical_score * 0.2, 0.6)
        
        # Five-act is less common in modern stories
        if 'shakespeare' in content_lower or 'classical' in content_lower:
            score += 0.3
        
        return min(score, 1.0)

    async def _analyze_acts(self, content: str, structure_type: StructureType) -> List[ActStructure]:
        """Analyze and identify acts within the story."""
        acts = []
        
        if structure_type == StructureType.THREE_ACT:
            acts = self._analyze_three_acts(content)
        elif structure_type == StructureType.HEROS_JOURNEY:
            acts = self._analyze_hero_journey_acts(content)
        elif structure_type == StructureType.FIVE_ACT:
            acts = self._analyze_five_acts(content)
        else:
            # Default to three-act
            acts = self._analyze_three_acts(content)
        
        return acts

    def _analyze_three_acts(self, content: str) -> List[ActStructure]:
        """Analyze three-act structure."""
        acts = []
        content_length = len(content)
        
        # Act I: Setup (0-25%)
        act_one = ActStructure(
            act_number=1,
            name="Setup",
            start_position=0.0,
            end_position=0.25,
            key_elements=self._identify_act_elements(content[:int(content_length * 0.25)], "setup"),
            beats=[],
            confidence=self._calculate_act_confidence(content[:int(content_length * 0.25)], "setup")
        )
        acts.append(act_one)
        
        # Act II: Confrontation (25-75%)
        act_two_content = content[int(content_length * 0.25):int(content_length * 0.75)]
        act_two = ActStructure(
            act_number=2,
            name="Confrontation",
            start_position=0.25,
            end_position=0.75,
            key_elements=self._identify_act_elements(act_two_content, "confrontation"),
            beats=[],
            confidence=self._calculate_act_confidence(act_two_content, "confrontation")
        )
        acts.append(act_two)
        
        # Act III: Resolution (75-100%)
        act_three_content = content[int(content_length * 0.75):]
        act_three = ActStructure(
            act_number=3,
            name="Resolution",
            start_position=0.75,
            end_position=1.0,
            key_elements=self._identify_act_elements(act_three_content, "resolution"),
            beats=[],
            confidence=self._calculate_act_confidence(act_three_content, "resolution")
        )
        acts.append(act_three)
        
        return acts

    def _analyze_hero_journey_acts(self, content: str) -> List[ActStructure]:
        """Analyze hero's journey structure."""
        # Simplified to three main phases
        acts = []
        content_length = len(content)
        
        # Departure (0-20%)
        departure = ActStructure(
            act_number=1,
            name="Departure",
            start_position=0.0,
            end_position=0.2,
            key_elements=["ordinary_world", "call_to_adventure", "refusal", "mentor"],
            beats=[],
            confidence=0.7
        )
        acts.append(departure)
        
        # Initiation (20-80%)
        initiation = ActStructure(
            act_number=2,
            name="Initiation", 
            start_position=0.2,
            end_position=0.8,
            key_elements=["crossing_threshold", "tests", "allies", "enemies", "ordeal"],
            beats=[],
            confidence=0.7
        )
        acts.append(initiation)
        
        # Return (80-100%)
        return_act = ActStructure(
            act_number=3,
            name="Return",
            start_position=0.8,
            end_position=1.0,
            key_elements=["reward", "road_back", "resurrection", "return_elixir"],
            beats=[],
            confidence=0.7
        )
        acts.append(return_act)
        
        return acts

    def _analyze_five_acts(self, content: str) -> List[ActStructure]:
        """Analyze five-act structure."""
        acts = []
        boundaries = [0.2, 0.4, 0.6, 0.8, 1.0]
        act_names = ["Exposition", "Rising Action", "Climax", "Falling Action", "Denouement"]
        
        start_pos = 0.0
        for i, (end_pos, name) in enumerate(zip(boundaries, act_names)):
            act = ActStructure(
                act_number=i + 1,
                name=name,
                start_position=start_pos,
                end_position=end_pos,
                key_elements=[name.lower().replace(" ", "_")],
                beats=[],
                confidence=0.6  # Lower confidence for five-act detection
            )
            acts.append(act)
            start_pos = end_pos
        
        return acts

    def _identify_act_elements(self, act_content: str, act_type: str) -> List[str]:
        """Identify key elements within an act."""
        elements = []
        content_lower = act_content.lower()
        
        if act_type == "setup":
            if any(word in content_lower for word in ['introduce', 'meet', 'establish']):
                elements.append("character_introduction")
            if any(word in content_lower for word in ['world', 'setting', 'place']):
                elements.append("world_establishment")
            if any(word in content_lower for word in ['conflict', 'problem', 'challenge']):
                elements.append("conflict_introduction")
        
        elif act_type == "confrontation":
            if any(word in content_lower for word in ['struggle', 'fight', 'battle']):
                elements.append("rising_action")
            if any(word in content_lower for word in ['reveal', 'discover', 'realize']):
                elements.append("revelation")
            if any(word in content_lower for word in ['obstacle', 'setback', 'failure']):
                elements.append("obstacles")
        
        elif act_type == "resolution":
            if any(word in content_lower for word in ['resolve', 'solve', 'overcome']):
                elements.append("conflict_resolution")
            if any(word in content_lower for word in ['end', 'conclusion', 'finally']):
                elements.append("denouement")
        
        return elements

    def _calculate_act_confidence(self, act_content: str, act_type: str) -> float:
        """Calculate confidence score for act identification."""
        if not act_content.strip():
            return 0.0
        
        elements = self._identify_act_elements(act_content, act_type)
        base_confidence = len(elements) * 0.2
        
        # Adjust for content length
        length_factor = min(len(act_content) / 100, 1.0)  # Normalize around 100 chars
        
        return min(base_confidence * length_factor, 1.0)

    async def _identify_narrative_beats(self, content: str, structure_type: StructureType) -> List[NarrativeBeatData]:
        """Identify narrative beats within the story."""
        beats = []
        
        # Look for common narrative beats
        if structure_type == StructureType.THREE_ACT:
            beats = self._identify_three_act_beats(content)
        elif structure_type == StructureType.HEROS_JOURNEY:
            beats = self._identify_hero_journey_beats(content)
        else:
            beats = self._identify_three_act_beats(content)  # Default
        
        return beats

    def _identify_three_act_beats(self, content: str) -> List[NarrativeBeatData]:
        """Identify beats in three-act structure."""
        beats = []
        content_lower = content.lower()
        content_length = len(content)
        
        # Inciting incident (around 12%)
        if any(word in content_lower for word in ['suddenly', 'unexpected', 'changed']):
            beats.append(NarrativeBeatData(
                beat_type="inciting_incident",
                position=0.12,
                content_snippet=content[:200] + "...",
                emotional_impact=0.7,
                tension_level=0.6,
                confidence=0.8
            ))
        
        # Plot point 1 (around 25%)
        beats.append(NarrativeBeatData(
            beat_type="plot_point_1",
            position=0.25,
            content_snippet=content[int(content_length * 0.2):int(content_length * 0.3)][:200] + "...",
            emotional_impact=0.6,
            tension_level=0.7,
            confidence=0.7
        ))
        
        # Midpoint (around 50%)
        beats.append(NarrativeBeatData(
            beat_type="midpoint",
            position=0.50,
            content_snippet=content[int(content_length * 0.45):int(content_length * 0.55)][:200] + "...",
            emotional_impact=0.8,
            tension_level=0.8,
            confidence=0.75
        ))
        
        # Plot point 2 (around 75%)
        beats.append(NarrativeBeatData(
            beat_type="plot_point_2",
            position=0.75,
            content_snippet=content[int(content_length * 0.7):int(content_length * 0.8)][:200] + "...",
            emotional_impact=0.9,
            tension_level=0.9,
            confidence=0.8
        ))
        
        # Climax (around 90%)
        if any(word in content_lower for word in ['climax', 'final', 'confrontation']):
            beats.append(NarrativeBeatData(
                beat_type="climax",
                position=0.90,
                content_snippet=content[int(content_length * 0.85):][:200] + "...",
                emotional_impact=1.0,
                tension_level=1.0,
                confidence=0.85
            ))
        
        return beats

    def _identify_hero_journey_beats(self, content: str) -> List[NarrativeBeatData]:
        """Identify beats in hero's journey structure."""
        beats = []
        
        # Call to adventure
        beats.append(NarrativeBeatData(
            beat_type="call_to_adventure",
            position=0.10,
            content_snippet="Hero receives call to adventure...",
            emotional_impact=0.6,
            tension_level=0.5,
            confidence=0.7
        ))
        
        # Crossing threshold
        beats.append(NarrativeBeatData(
            beat_type="crossing_threshold",
            position=0.25,
            content_snippet="Hero commits to journey...",
            emotional_impact=0.7,
            tension_level=0.6,
            confidence=0.7
        ))
        
        # Ordeal
        beats.append(NarrativeBeatData(
            beat_type="ordeal",
            position=0.75,
            content_snippet="Hero faces greatest challenge...",
            emotional_impact=0.9,
            tension_level=0.9,
            confidence=0.8
        ))
        
        return beats

    def _calculate_confidence_metrics(self, structure_confidence: float, acts: List[ActStructure], 
                                   beats: List[NarrativeBeatData], content: str) -> ConfidenceMetrics:
        """Calculate overall confidence metrics."""
        # Beat confidence
        beat_confidence = sum(beat.confidence for beat in beats) / max(len(beats), 1)
        
        # Completeness score
        completeness_score = min(len(beats) / 5, 1.0)  # Assume 5 beats for complete story
        
        # Consistency score (simplified)
        consistency_score = min(structure_confidence + 0.1, 1.0)
        
        # Overall confidence
        overall_confidence = (
            structure_confidence * 0.4 +
            beat_confidence * 0.3 +
            completeness_score * 0.2 +
            consistency_score * 0.1
        )
        
        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            structure_confidence=structure_confidence,
            beat_confidence=beat_confidence,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            meets_threshold=overall_confidence >= self.confidence_threshold,
            threshold_details={
                "required_threshold": self.confidence_threshold,
                "achieved_score": overall_confidence,
                "components": {
                    "structure": structure_confidence,
                    "beats": beat_confidence,
                    "completeness": completeness_score,
                    "consistency": consistency_score
                }
            }
        )

    def _create_story_arc(self, content: str, structure_type: StructureType, acts: List[ActStructure],
                         beats: List[NarrativeBeatData], confidence_metrics: ConfidenceMetrics,
                         session_id: str = None) -> StoryArc:
        """Create StoryArc model from analysis results."""
        from uuid import uuid4
        
        story_id = str(uuid4())
        
        # Create isolation context
        isolation_context = ProjectIsolationContext(
            project_id=session_id or "default_project",
            session_id=session_id or story_id
        )
        
        return StoryArc(
            story_id=story_id,
            content=content,
            structure_type=structure_type,
            acts=acts,
            narrative_beats=beats,
            word_count=len(content.split()),
            estimated_reading_time=len(content.split()) / 250.0,  # 250 WPM
            confidence_metrics=confidence_metrics,
            isolation_context=isolation_context
        )

    def _create_empty_content_result(self, content: str, session_id: str = None) -> Dict[str, Any]:
        """Create result for empty content."""
        return {
            "analysis": {
                "structure_type": "unknown",
                "acts": [],
                "beats": [],
                "issues": ["Content is empty or contains only whitespace"]
            },
            "confidence": 0.0,
            "metadata": {
                "word_count": 0,
                "reading_time": 0.0,
                "session_id": session_id,
                "error": "Empty content provided"
            }
        }

    def _create_error_result(self, error_message: str, content: str, session_id: str = None) -> Dict[str, Any]:
        """Create result for analysis errors."""
        return {
            "analysis": {
                "structure_type": "unknown",
                "acts": [],
                "beats": [],
                "issues": [f"Analysis error: {error_message}"]
            },
            "confidence": 0.0,
            "metadata": {
                "word_count": len(content.split()) if content else 0,
                "reading_time": 0.0,
                "session_id": session_id,
                "error": error_message
            }
        }