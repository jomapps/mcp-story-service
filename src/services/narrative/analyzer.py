import re
import logging
import yaml
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from src.models.story_arc import (
    StoryArc,
    ActStructure,
    Act,
    TurningPoint,
    PacingProfile,
    ArcStatus,
)
from src.lib.genre_loader import GenreLoader
from src.lib.error_handler import AnalysisError


class NarrativeAnalyzer:
    def __init__(self, genre_loader: GenreLoader):
        self.genre_loader = genre_loader
        self.logger = logging.getLogger(__name__)
        self.structure_patterns = self._load_structure_patterns()

    def _load_structure_patterns(self) -> Dict:
        """Load story structure patterns from config files."""
        try:
            patterns_path = Path("config/patterns/three_act_structure.yaml")
            if patterns_path.exists():
                with open(patterns_path, "r") as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning("Structure patterns file not found, using defaults")
                return self._get_default_patterns()
        except Exception as e:
            self.logger.error(f"Error loading structure patterns: {e}")
            return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict:
        """Return default three-act structure patterns."""
        return {
            "acts": {
                "act_one": {
                    "percentage": 25,
                    "key_elements": ["Inciting incident", "Character introduction"],
                },
                "act_two": {
                    "percentage": 50,
                    "key_elements": ["Rising action", "Midpoint reversal"],
                },
                "act_three": {
                    "percentage": 25,
                    "key_elements": ["Climax", "Resolution"],
                },
            },
            "beats": [
                {"name": "inciting_incident", "position": 0.12},
                {"name": "plot_point_1", "position": 0.25},
                {"name": "midpoint", "position": 0.50},
                {"name": "plot_point_2", "position": 0.75},
                {"name": "climax", "position": 0.90},
            ],
        }

    def analyze_story_structure(self, story_content: str, genre: str) -> StoryArc:
        """
        Analyzes the story structure using pattern matching and text analysis.
        """
        if not story_content or not story_content.strip():
            raise AnalysisError("Story content cannot be empty")

        # Validate genre
        if not self.genre_loader.get_genre(genre):
            raise AnalysisError(f"Invalid genre: {genre}")

        try:
            self.logger.info(f"Analyzing story structure for genre: {genre}")

            # Analyze story content
            story_segments = self._segment_story(story_content)
            story_beats = self._identify_story_beats(story_content, story_segments)
            act_analysis = self._analyze_three_act_structure(
                story_segments, story_beats
            )
            turning_points = self._identify_turning_points(story_beats)
            pacing_analysis = self._analyze_pacing(story_segments, story_beats)

            # Calculate confidence based on analysis quality
            confidence_score = self._calculate_structure_confidence(
                act_analysis, story_beats, turning_points
            )

            # Create story arc
            story_arc = StoryArc(
                id=f"arc_{hash(story_content[:100]) % 10000}",
                project_id="analyzed",
                title=self._extract_title(story_content),
                genre=genre,
                act_structure=act_analysis,
                pacing_profile=pacing_analysis,
                confidence_score=confidence_score,
                status=ArcStatus.ANALYZED,
            )

            self.logger.info(
                f"Story structure analysis complete. Confidence: {confidence_score:.2f}"
            )
            return story_arc

        except Exception as e:
            self.logger.error(f"Error analyzing story structure: {e}")
            raise AnalysisError(f"Story structure analysis failed: {str(e)}")

    def _segment_story(self, story_content: str) -> List[str]:
        """Segment story into logical parts based on paragraphs and scene breaks."""
        # Split by double newlines (paragraph breaks) and filter empty segments
        segments = [
            seg.strip() for seg in re.split(r"\n\s*\n", story_content) if seg.strip()
        ]

        if len(segments) < 3:
            # If too few segments, split by sentences for better analysis
            sentences = re.split(r"[.!?]+", story_content)
            segments = [s.strip() for s in sentences if s.strip()]

        return segments

    def _identify_story_beats(
        self, story_content: str, segments: List[str]
    ) -> Dict[str, Dict]:
        """Identify key story beats using pattern matching."""
        beats = {}
        content_lower = story_content.lower()

        # Define beat detection patterns
        beat_patterns = {
            "inciting_incident": [
                r"\b(suddenly|then|when|after)\b.*\b(discover|find|realize|learn|see)\b",
                r"\b(call|message|news|letter|phone)\b",
                r"\b(attack|threat|danger|crisis|problem)\b",
            ],
            "midpoint": [
                r"\b(reveal|discover|realize|truth|secret)\b",
                r"\b(betrayal|twist|surprise|shock)\b",
                r"\b(halfway|middle|center)\b",
            ],
            "climax": [
                r"\b(final|last|ultimate|decisive)\b.*\b(battle|fight|confrontation|showdown)\b",
                r"\b(climax|peak|culmination)\b",
                r"\b(face|confront|defeat|overcome)\b.*\b(enemy|villain|antagonist)\b",
            ],
        }

        # Analyze each segment for beat patterns
        for i, segment in enumerate(segments):
            segment_lower = segment.lower()
            position = i / len(segments) if len(segments) > 1 else 0.5

            for beat_name, patterns in beat_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, segment_lower):
                        if beat_name not in beats or abs(
                            position - self._get_expected_position(beat_name)
                        ) < abs(
                            beats[beat_name]["position"]
                            - self._get_expected_position(beat_name)
                        ):
                            beats[beat_name] = {
                                "position": position,
                                "segment_index": i,
                                "content": segment[:200] + "..."
                                if len(segment) > 200
                                else segment,
                                "confidence": self._calculate_beat_confidence(
                                    beat_name, position, segment
                                ),
                            }

        return beats

    def _get_expected_position(self, beat_name: str) -> float:
        """Get expected position for a story beat."""
        expected_positions = {
            "inciting_incident": 0.12,
            "plot_point_1": 0.25,
            "midpoint": 0.50,
            "plot_point_2": 0.75,
            "climax": 0.90,
        }
        return expected_positions.get(beat_name, 0.5)

    def _calculate_beat_confidence(
        self, beat_name: str, position: float, content: str
    ) -> float:
        """Calculate confidence score for a detected beat."""
        expected_pos = self._get_expected_position(beat_name)
        position_penalty = (
            abs(position - expected_pos) * 2
        )  # Penalty for wrong position

        # Content quality indicators
        content_lower = content.lower()
        quality_indicators = {
            "inciting_incident": ["character", "protagonist", "hero", "main"],
            "midpoint": ["reveal", "discovery", "truth", "change"],
            "climax": ["final", "ultimate", "decisive", "resolution"],
        }

        quality_score = 0.5  # Base score
        if beat_name in quality_indicators:
            for indicator in quality_indicators[beat_name]:
                if indicator in content_lower:
                    quality_score += 0.1

        confidence = max(0.1, min(0.95, quality_score - position_penalty))
        return confidence

    def _analyze_three_act_structure(
        self, segments: List[str], beats: Dict
    ) -> ActStructure:
        """Analyze the three-act structure of the story."""
        total_segments = len(segments)

        # Determine act boundaries based on detected beats or default positions
        act1_end = 0.25
        act2_end = 0.75

        if "plot_point_1" in beats:
            act1_end = beats["plot_point_1"]["position"]
        if "plot_point_2" in beats:
            act2_end = beats["plot_point_2"]["position"]

        # Create acts with detected events
        act_one = Act(
            start_position=0.0,
            end_position=act1_end,
            purpose="Setup and Introduction",
            key_events=self._extract_act_events(
                segments, 0, int(act1_end * total_segments), beats
            ),
            character_arcs=[],
        )

        act_two = Act(
            start_position=act1_end,
            end_position=act2_end,
            purpose="Development and Confrontation",
            key_events=self._extract_act_events(
                segments,
                int(act1_end * total_segments),
                int(act2_end * total_segments),
                beats,
            ),
            character_arcs=[],
        )

        act_three = Act(
            start_position=act2_end,
            end_position=1.0,
            purpose="Climax and Resolution",
            key_events=self._extract_act_events(
                segments, int(act2_end * total_segments), total_segments, beats
            ),
            character_arcs=[],
        )

        # Calculate structure confidence
        structure_confidence = self._calculate_act_confidence(
            act_one, act_two, act_three, beats
        )

        return ActStructure(
            act_one=act_one,
            act_two=act_two,
            act_three=act_three,
            turning_points=self._identify_turning_points(beats),
            confidence_score=structure_confidence,
        )

    def _extract_act_events(
        self, segments: List[str], start_idx: int, end_idx: int, beats: Dict
    ) -> List[str]:
        """Extract key events from segments within an act."""
        events = []

        # Add detected beats that fall within this act
        for beat_name, beat_data in beats.items():
            segment_idx = beat_data["segment_index"]
            if start_idx <= segment_idx < end_idx:
                events.append(
                    f"{beat_name.replace('_', ' ').title()}: {beat_data['content'][:100]}..."
                )

        # If no beats found, extract significant sentences
        if not events and end_idx > start_idx:
            for i in range(start_idx, min(end_idx, len(segments))):
                segment = segments[i]
                # Look for action words or significant events
                if re.search(
                    r"\b(discover|find|realize|decide|fight|escape|meet|arrive|leave)\b",
                    segment.lower(),
                ):
                    events.append(
                        segment[:100] + "..." if len(segment) > 100 else segment
                    )
                    if len(events) >= 3:  # Limit events per act
                        break

        return events if events else ["Story development continues"]

    def _identify_turning_points(self, beats: Dict) -> List[TurningPoint]:
        """Identify major turning points in the story."""
        turning_points = []

        # Map beats to turning points
        turning_point_beats = {
            "plot_point_1": "First turning point - commitment to the journey",
            "midpoint": "Midpoint reversal - major revelation or setback",
            "plot_point_2": "Second turning point - point of no return",
            "climax": "Climax - final confrontation",
        }

        for beat_name, description in turning_point_beats.items():
            if beat_name in beats:
                turning_points.append(
                    TurningPoint(
                        position=beats[beat_name]["position"],
                        description=f"{description}: {beats[beat_name]['content'][:100]}...",
                    )
                )

        # If no beats detected, add default turning points
        if not turning_points:
            turning_points = [
                TurningPoint(
                    position=0.25, description="First turning point (estimated)"
                ),
                TurningPoint(
                    position=0.75, description="Second turning point (estimated)"
                ),
            ]

        return sorted(turning_points, key=lambda tp: tp.position)

    def _analyze_pacing(self, segments: List[str], beats: Dict) -> PacingProfile:
        """Analyze story pacing and create tension curve."""
        tension_curve = []
        pacing_issues = []
        improvements = []

        # Calculate tension for each segment
        for i, segment in enumerate(segments):
            position = i / len(segments) if len(segments) > 1 else 0.5
            tension = self._calculate_segment_tension(segment, position, beats)
            tension_curve.append(tension)

        # Smooth the curve if too many segments
        if len(tension_curve) > 10:
            tension_curve = self._smooth_tension_curve(tension_curve, 10)

        # Analyze pacing issues
        pacing_issues, improvements = self._analyze_pacing_issues(tension_curve)

        # Calculate pacing confidence
        confidence = self._calculate_pacing_confidence(tension_curve, pacing_issues)

        return PacingProfile(
            tension_curve=tension_curve,
            pacing_issues=pacing_issues,
            suggested_improvements=improvements,
            confidence_score=confidence,
        )

    def _calculate_segment_tension(
        self, segment: str, position: float, beats: Dict
    ) -> float:
        """Calculate tension level for a story segment."""
        base_tension = 0.3  # Baseline tension

        # Increase tension based on content
        content_lower = segment.lower()
        tension_words = {
            "high": [
                "fight",
                "battle",
                "danger",
                "threat",
                "crisis",
                "attack",
                "death",
                "kill",
            ],
            "medium": [
                "conflict",
                "argue",
                "problem",
                "worry",
                "fear",
                "concern",
                "chase",
            ],
            "low": ["calm", "peaceful", "rest", "sleep", "quiet", "gentle"],
        }

        for word in tension_words["high"]:
            if word in content_lower:
                base_tension += 0.2
        for word in tension_words["medium"]:
            if word in content_lower:
                base_tension += 0.1
        for word in tension_words["low"]:
            if word in content_lower:
                base_tension -= 0.1

        # Adjust based on story position (typical tension curve)
        if position < 0.25:  # Act 1
            base_tension *= 0.8
        elif position > 0.75:  # Act 3
            base_tension *= 1.3
        else:  # Act 2
            base_tension *= 1.1

        # Boost tension near detected beats
        for beat_data in beats.values():
            if abs(position - beat_data["position"]) < 0.1:
                base_tension += 0.2

        return max(0.1, min(1.0, base_tension))

    def _smooth_tension_curve(
        self, curve: List[float], target_length: int
    ) -> List[float]:
        """Smooth and reduce tension curve to target length."""
        if len(curve) <= target_length:
            return curve

        chunk_size = len(curve) / target_length
        smoothed = []

        for i in range(target_length):
            start_idx = int(i * chunk_size)
            end_idx = int((i + 1) * chunk_size)
            chunk_avg = sum(curve[start_idx:end_idx]) / (end_idx - start_idx)
            smoothed.append(chunk_avg)

        return smoothed

    def _analyze_pacing_issues(
        self, tension_curve: List[float]
    ) -> Tuple[List[str], List[str]]:
        """Analyze pacing issues and suggest improvements."""
        issues = []
        improvements = []

        if not tension_curve:
            return issues, improvements

        # Check for flat pacing
        if max(tension_curve) - min(tension_curve) < 0.3:
            issues.append("Flat pacing - insufficient tension variation")
            improvements.append("Add more dramatic peaks and valleys")

        # Check for proper climax
        max_tension_pos = tension_curve.index(max(tension_curve)) / len(tension_curve)
        if max_tension_pos < 0.6:
            issues.append("Early climax - peak tension occurs too early")
            improvements.append("Build tension more gradually toward the end")

        # Check for resolution
        if len(tension_curve) > 2 and tension_curve[-1] > tension_curve[-2]:
            issues.append("Unresolved ending - tension increases at the end")
            improvements.append("Provide proper resolution after climax")

        return issues, improvements

    def _calculate_pacing_confidence(
        self, tension_curve: List[float], issues: List[str]
    ) -> float:
        """Calculate confidence score for pacing analysis."""
        base_confidence = 0.7

        # Reduce confidence for each issue
        confidence_penalty = len(issues) * 0.1

        # Bonus for good tension curve shape
        if tension_curve and len(tension_curve) > 3:
            # Check for proper arc (low -> high -> low)
            start_avg = sum(tension_curve[: len(tension_curve) // 3]) / (
                len(tension_curve) // 3
            )
            middle_avg = sum(
                tension_curve[len(tension_curve) // 3 : 2 * len(tension_curve) // 3]
            ) / (len(tension_curve) // 3)
            end_avg = sum(tension_curve[2 * len(tension_curve) // 3 :]) / (
                len(tension_curve) - 2 * len(tension_curve) // 3
            )

            if middle_avg > start_avg and end_avg < middle_avg:
                base_confidence += 0.1

        return max(0.1, min(0.95, base_confidence - confidence_penalty))

    def _calculate_act_confidence(
        self, act1: Act, act2: Act, act3: Act, beats: Dict
    ) -> float:
        """Calculate confidence score for act structure."""
        base_confidence = 0.6

        # Bonus for detected beats
        beat_bonus = len(beats) * 0.05

        # Bonus for proper act proportions
        act1_length = act1.end_position - act1.start_position
        act2_length = act2.end_position - act2.start_position
        act3_length = act3.end_position - act3.start_position

        # Ideal proportions: 25%, 50%, 25%
        if (
            0.2 <= act1_length <= 0.3
            and 0.4 <= act2_length <= 0.6
            and 0.2 <= act3_length <= 0.3
        ):
            base_confidence += 0.1

        # Bonus for events in each act
        if act1.key_events and act2.key_events and act3.key_events:
            base_confidence += 0.1

        return max(0.1, min(0.95, base_confidence + beat_bonus))

    def _calculate_structure_confidence(
        self,
        act_structure: ActStructure,
        beats: Dict,
        turning_points: List[TurningPoint],
    ) -> float:
        """Calculate overall confidence score for story structure analysis."""
        # Combine different confidence scores
        act_confidence = act_structure.confidence_score
        beat_confidence = (
            sum(beat["confidence"] for beat in beats.values()) / len(beats)
            if beats
            else 0.5
        )
        turning_point_confidence = 0.8 if len(turning_points) >= 2 else 0.5

        # Weighted average
        overall_confidence = (
            act_confidence * 0.5
            + beat_confidence * 0.3
            + turning_point_confidence * 0.2
        )

        return max(0.1, min(0.95, overall_confidence))

    def _extract_title(self, story_content: str) -> str:
        """Extract or generate a title for the story."""
        lines = story_content.strip().split("\n")

        # Check if first line looks like a title (short, no punctuation at end)
        if lines and len(lines[0]) < 100 and not lines[0].endswith("."):
            return lines[0].strip()

        # Generate title from first sentence
        first_sentence = re.split(r"[.!?]", story_content)[0].strip()
        if len(first_sentence) < 100:
            return f"Story: {first_sentence[:50]}..."

        return "Untitled Story"
