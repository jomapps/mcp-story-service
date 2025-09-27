import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from statistics import mean, stdev
from src.lib.error_handler import AnalysisError


class PacingCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tension_indicators = self._initialize_tension_indicators()
        self.pacing_indicators = self._initialize_pacing_indicators()

    def _initialize_tension_indicators(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize tension level indicators."""
        return {
            "high": {
                "action": [
                    "fight",
                    "battle",
                    "chase",
                    "escape",
                    "attack",
                    "explosion",
                    "crash",
                    "run",
                ],
                "emotion": [
                    "scream",
                    "panic",
                    "terror",
                    "rage",
                    "fury",
                    "desperate",
                    "frantic",
                ],
                "stakes": [
                    "death",
                    "kill",
                    "destroy",
                    "save",
                    "rescue",
                    "urgent",
                    "critical",
                    "final",
                ],
            },
            "medium": {
                "action": [
                    "argue",
                    "confront",
                    "search",
                    "investigate",
                    "pursue",
                    "challenge",
                ],
                "emotion": [
                    "worry",
                    "fear",
                    "anger",
                    "concern",
                    "tension",
                    "stress",
                    "conflict",
                ],
                "stakes": [
                    "important",
                    "serious",
                    "problem",
                    "trouble",
                    "danger",
                    "risk",
                ],
            },
            "low": {
                "action": [
                    "talk",
                    "discuss",
                    "walk",
                    "sit",
                    "think",
                    "remember",
                    "reflect",
                ],
                "emotion": [
                    "calm",
                    "peaceful",
                    "quiet",
                    "gentle",
                    "soft",
                    "relaxed",
                    "content",
                ],
                "stakes": [
                    "normal",
                    "routine",
                    "everyday",
                    "simple",
                    "easy",
                    "comfortable",
                ],
            },
        }

    def _initialize_pacing_indicators(self) -> Dict[str, List[str]]:
        """Initialize pacing speed indicators."""
        return {
            "fast": [
                "quickly",
                "rapidly",
                "suddenly",
                "immediately",
                "instantly",
                "rushed",
                "hurried",
                "swift",
            ],
            "slow": [
                "slowly",
                "gradually",
                "carefully",
                "thoughtfully",
                "deliberately",
                "gently",
                "quietly",
            ],
            "medium": ["steadily", "normally", "regularly", "evenly", "consistently"],
        }

    def calculate_pacing(self, narrative_beats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates comprehensive pacing analysis including tension curve, rhythm, and recommendations.
        """
        if not narrative_beats:
            raise AnalysisError("Narrative beats cannot be empty")

        try:
            self.logger.info(
                f"Analyzing pacing for {len(narrative_beats)} narrative beats"
            )

            # Calculate tension levels for each beat
            tension_curve = self._calculate_tension_curve(narrative_beats)

            # Analyze rhythm patterns
            rhythm_analysis = self._analyze_rhythm(narrative_beats, tension_curve)

            # Calculate overall pacing score
            pacing_score = self._calculate_pacing_score(tension_curve, rhythm_analysis)

            # Generate recommendations
            recommendations = self._generate_pacing_recommendations(
                tension_curve, rhythm_analysis, narrative_beats
            )

            # Assess genre compliance
            genre_compliance = self._assess_genre_compliance(
                tension_curve, rhythm_analysis
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence(
                narrative_beats, tension_curve
            )

            self.logger.info(
                f"Pacing analysis complete. Score: {pacing_score:.2f}, Confidence: {confidence_score:.2f}"
            )

            return {
                "tension_curve": tension_curve,
                "pacing_score": round(pacing_score, 2),
                "confidence_score": round(confidence_score, 2),
                "rhythm_analysis": rhythm_analysis,
                "recommendations": recommendations,
                "genre_compliance": round(genre_compliance, 2),
            }

        except Exception as e:
            self.logger.error(f"Error calculating pacing: {e}")
            raise AnalysisError(f"Pacing calculation failed: {str(e)}")

    def _calculate_tension_curve(
        self, narrative_beats: List[Dict[str, Any]]
    ) -> List[float]:
        """Calculate tension level for each narrative beat."""
        tension_curve = []

        for i, beat in enumerate(narrative_beats):
            # Start with existing tension level if provided
            base_tension = beat.get("tension_level", 0.5)

            # Analyze beat content for tension indicators
            description = beat.get("description", "").lower()
            beat_type = beat.get("type", "").lower()
            content = f"{description} {beat_type}"

            # Calculate content-based tension
            content_tension = self._analyze_content_tension(content)

            # Calculate positional tension (story arc)
            position = i / len(narrative_beats) if len(narrative_beats) > 1 else 0.5
            positional_tension = self._calculate_positional_tension(position)

            # Combine tensions with weights
            final_tension = (
                base_tension * 0.3 + content_tension * 0.5 + positional_tension * 0.2
            )

            # Ensure tension is within bounds
            final_tension = max(0.0, min(1.0, final_tension))
            tension_curve.append(round(final_tension, 2))

        return tension_curve

    def _analyze_content_tension(self, content: str) -> float:
        """Analyze content for tension indicators."""
        tension_score = 0.5  # Base tension

        # Check for high tension indicators
        for category, words in self.tension_indicators["high"].items():
            matches = sum(1 for word in words if word in content)
            tension_score += matches * 0.15

        # Check for medium tension indicators
        for category, words in self.tension_indicators["medium"].items():
            matches = sum(1 for word in words if word in content)
            tension_score += matches * 0.05  # Reduced from 0.08 to 0.05

        # Check for low tension indicators (reduce tension)
        for category, words in self.tension_indicators["low"].items():
            matches = sum(1 for word in words if word in content)
            tension_score -= matches * 0.05

        return round(max(0.1, min(1.0, tension_score)), 2)

    def _calculate_positional_tension(self, position: float) -> float:
        """Calculate tension based on position in story (typical story arc)."""
        # Classic three-act structure tension curve
        if position <= 0.25:  # Act 1
            return 0.3 + (position * 0.8)  # Rising from 0.3 to 0.5
        elif position <= 0.75:  # Act 2
            # Peak around midpoint, then rise to climax
            if position <= 0.5:
                return 0.5 + ((position - 0.25) * 1.2)  # Rise to 0.8
            else:
                return 0.8 + ((position - 0.5) * 0.8)  # Rise to 1.0
        else:  # Act 3
            return 1.0 - ((position - 0.75) * 1.6)  # Fall from 1.0 to 0.6

    def _analyze_rhythm(
        self, narrative_beats: List[Dict[str, Any]], tension_curve: List[float]
    ) -> Dict[str, Any]:
        """Analyze rhythm patterns in the story."""
        if len(tension_curve) < 3:
            return {
                "fast_sections": [],
                "slow_sections": [],
                "balanced_sections": [],
                "rhythm_score": 0.5,
                "variation_score": 0.5,
            }

        # Identify sections by pacing
        fast_sections = []
        slow_sections = []
        balanced_sections = []

        # Analyze pacing indicators in beat descriptions
        for i, beat in enumerate(narrative_beats):
            description = beat.get("description", "").lower()

            # Count pacing indicators
            fast_count = sum(
                1 for word in self.pacing_indicators["fast"] if word in description
            )
            slow_count = sum(
                1 for word in self.pacing_indicators["slow"] if word in description
            )

            # Determine section type
            if fast_count > slow_count and fast_count > 0:
                fast_sections.append(
                    {
                        "start": i,
                        "end": i + 1,
                        "tension_level": tension_curve[i],
                        "description": beat.get("description", "")[:100] + "...",
                    }
                )
            elif slow_count > fast_count and slow_count > 0:
                slow_sections.append(
                    {
                        "start": i,
                        "end": i + 1,
                        "tension_level": tension_curve[i],
                        "description": beat.get("description", "")[:100] + "...",
                    }
                )
            else:
                balanced_sections.append(
                    {
                        "start": i,
                        "end": i + 1,
                        "tension_level": tension_curve[i],
                        "description": beat.get("description", "")[:100] + "...",
                    }
                )

        # Calculate rhythm scores
        rhythm_score = self._calculate_rhythm_score(
            fast_sections, slow_sections, balanced_sections, len(narrative_beats)
        )
        variation_score = self._calculate_variation_score(tension_curve)

        return {
            "fast_sections": fast_sections,
            "slow_sections": slow_sections,
            "balanced_sections": balanced_sections,
            "rhythm_score": round(rhythm_score, 2),
            "variation_score": round(variation_score, 2),
        }

    def _calculate_rhythm_score(
        self,
        fast_sections: List,
        slow_sections: List,
        balanced_sections: List,
        total_beats: int,
    ) -> float:
        """Calculate rhythm quality score."""
        if total_beats == 0:
            return 0.5

        # Good rhythm has a mix of all pacing types
        fast_ratio = len(fast_sections) / total_beats
        slow_ratio = len(slow_sections) / total_beats
        balanced_ratio = len(balanced_sections) / total_beats

        # Ideal ratios: 30% fast, 30% slow, 40% balanced
        ideal_fast = 0.3
        ideal_slow = 0.3
        ideal_balanced = 0.4

        # Calculate deviation from ideal
        fast_deviation = abs(fast_ratio - ideal_fast)
        slow_deviation = abs(slow_ratio - ideal_slow)
        balanced_deviation = abs(balanced_ratio - ideal_balanced)

        # Score based on how close to ideal
        rhythm_score = 1.0 - (fast_deviation + slow_deviation + balanced_deviation) / 3

        return max(0.1, min(1.0, rhythm_score))

    def _calculate_variation_score(self, tension_curve: List[float]) -> float:
        """Calculate tension variation score."""
        if len(tension_curve) < 2:
            return 0.5

        # Good variation has appropriate range and changes
        tension_range = max(tension_curve) - min(tension_curve)

        # Calculate standard deviation for variation measure
        try:
            tension_std = stdev(tension_curve)
        except:
            tension_std = 0.1

        # Ideal range is 0.4-0.8, ideal std is 0.15-0.25
        range_score = 1.0 - abs(tension_range - 0.6) / 0.6
        std_score = 1.0 - abs(tension_std - 0.2) / 0.2

        variation_score = (range_score + std_score) / 2

        return max(0.1, min(1.0, variation_score))

    def _calculate_pacing_score(
        self, tension_curve: List[float], rhythm_analysis: Dict
    ) -> float:
        """Calculate overall pacing quality score."""
        if not tension_curve:
            return 0.5

        # Components of pacing score
        rhythm_score = rhythm_analysis.get("rhythm_score", 0.5)
        variation_score = rhythm_analysis.get("variation_score", 0.5)

        # Check for proper story arc
        arc_score = self._evaluate_story_arc(tension_curve)

        # Weighted combination
        pacing_score = rhythm_score * 0.4 + variation_score * 0.3 + arc_score * 0.3

        return max(0.1, min(1.0, pacing_score))

    def _evaluate_story_arc(self, tension_curve: List[float]) -> float:
        """Evaluate how well the tension curve follows a good story arc."""
        if len(tension_curve) < 5:
            return 0.5

        # Check for rising action, climax, and falling action
        first_quarter = tension_curve[: len(tension_curve) // 4]
        middle_half = tension_curve[
            len(tension_curve) // 4 : 3 * len(tension_curve) // 4
        ]
        last_quarter = tension_curve[3 * len(tension_curve) // 4 :]

        # Calculate averages
        first_avg = mean(first_quarter) if first_quarter else 0.5
        middle_avg = mean(middle_half) if middle_half else 0.5
        last_avg = mean(last_quarter) if last_quarter else 0.5

        # Good arc: rising to middle, then falling
        arc_score = 0.5

        if middle_avg > first_avg:  # Rising action
            arc_score += 0.25
        if last_avg < middle_avg:  # Falling action
            arc_score += 0.25

        return arc_score

    def _generate_pacing_recommendations(
        self,
        tension_curve: List[float],
        rhythm_analysis: Dict,
        narrative_beats: List[Dict],
    ) -> List[str]:
        """Generate pacing improvement recommendations."""
        recommendations = []

        # Check tension curve issues
        if not tension_curve:
            return ["Add more narrative beats to analyze pacing"]

        tension_range = max(tension_curve) - min(tension_curve)
        if tension_range < 0.3:
            recommendations.append(
                "Increase tension variation - add more dramatic peaks and valleys"
            )

        # Check for proper climax
        max_tension_pos = tension_curve.index(max(tension_curve)) / len(tension_curve)
        if max_tension_pos < 0.6:
            recommendations.append("Move climax later in the story for better pacing")
        elif max_tension_pos > 0.9:
            recommendations.append("Allow more space for resolution after climax")

        # Check rhythm balance
        fast_count = len(rhythm_analysis.get("fast_sections", []))
        slow_count = len(rhythm_analysis.get("slow_sections", []))
        total_beats = len(narrative_beats)

        if fast_count / total_beats > 0.5:
            recommendations.append(
                "Add more slow, reflective moments to balance pacing"
            )
        elif slow_count / total_beats > 0.5:
            recommendations.append("Add more action and urgency to increase engagement")

        # Check for flat sections
        flat_sections = self._identify_flat_sections(tension_curve)
        if flat_sections:
            recommendations.append(
                f"Address {len(flat_sections)} flat pacing sections with more tension variation"
            )

        # Variation score recommendations
        variation_score = rhythm_analysis.get("variation_score", 0.5)
        if variation_score < 0.4:
            recommendations.append(
                "Improve pacing variation with alternating high and low tension scenes"
            )

        return recommendations[:5]  # Limit to top 5

    def _identify_flat_sections(self, tension_curve: List[float]) -> List[Dict]:
        """Identify sections with flat tension."""
        flat_sections = []

        if len(tension_curve) < 3:
            return flat_sections

        # Look for consecutive beats with similar tension
        for i in range(len(tension_curve) - 2):
            section = tension_curve[i : i + 3]
            if max(section) - min(section) < 0.1:  # Very flat
                flat_sections.append(
                    {"start": i, "end": i + 3, "avg_tension": mean(section)}
                )

        return flat_sections

    def _assess_genre_compliance(
        self, tension_curve: List[float], rhythm_analysis: Dict
    ) -> float:
        """Assess how well pacing fits typical genre expectations."""
        # This is a simplified assessment - in practice, you'd compare against genre templates
        base_compliance = 0.7

        # Good variation generally fits most genres
        variation_score = rhythm_analysis.get("variation_score", 0.5)
        if variation_score > 0.6:
            base_compliance += 0.1

        # Good rhythm fits most genres
        rhythm_score = rhythm_analysis.get("rhythm_score", 0.5)
        if rhythm_score > 0.6:
            base_compliance += 0.1

        # Proper story arc fits most genres
        if tension_curve:
            arc_score = self._evaluate_story_arc(tension_curve)
            if arc_score > 0.6:
                base_compliance += 0.1

        return max(0.1, min(1.0, base_compliance))

    def _calculate_confidence(
        self, narrative_beats: List[Dict], tension_curve: List[float]
    ) -> float:
        """Calculate confidence in pacing analysis."""
        base_confidence = 0.7

        # More beats = higher confidence
        if len(narrative_beats) >= 10:
            base_confidence += 0.1
        elif len(narrative_beats) >= 5:
            base_confidence += 0.05
        elif len(narrative_beats) < 3:
            base_confidence -= 0.2

        # Rich descriptions = higher confidence
        rich_descriptions = sum(
            1 for beat in narrative_beats if len(beat.get("description", "")) > 50
        )
        if rich_descriptions / len(narrative_beats) > 0.7:
            base_confidence += 0.1

        # Consistent tension data = higher confidence
        if tension_curve and len(set(tension_curve)) > len(tension_curve) * 0.5:
            base_confidence += 0.05

        return max(0.1, min(0.95, base_confidence))
