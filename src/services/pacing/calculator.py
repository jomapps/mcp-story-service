"""PacingCalculator service with tension curve analysis.

This service analyzes narrative pacing and calculates tension curves
for story rhythm evaluation per FR-006.

Constitutional Compliance:
- Library-First (I): Focused pacing analysis service
- Test-First (II): Tests written before implementation
- Simplicity (III): Clear pacing algorithms without complexity
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ...models.narrative_beat import NarrativeBeat, BeatType, PacingType, PacingMetrics, TensionAnalysis, EmotionalImpact


@dataclass
class PacingSegment:
    """Represents a segment of story with pacing characteristics."""
    start_position: float
    end_position: float
    pacing_type: PacingType
    tension_level: float
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    action_density: float
    dialogue_percentage: float


class PacingCalculator:
    """
    Service for calculating narrative pacing and analyzing tension curves.
    
    Provides story rhythm analysis, pacing variation detection,
    and tension curve calculation for narrative flow assessment.
    """
    
    def __init__(self):
        self.default_reading_speed = 250  # words per minute
        
    async def calculate_pacing(self, story_content: str, genre_context: str = None) -> Dict[str, Any]:
        """
        Calculate narrative pacing and analyze tension curves.
        
        Args:
            story_content: Story content to analyze
            genre_context: Optional genre context for pacing expectations
            
        Returns:
            Pacing analysis results with scores and recommendations
        """
        try:
            # Preprocess content
            processed_content = self._preprocess_content(story_content)
            
            if not processed_content.strip():
                return self._create_empty_content_result()
            
            # Analyze pacing segments
            segments = await self._analyze_pacing_segments(processed_content)
            
            # Calculate overall pacing metrics
            pacing_metrics = self._calculate_overall_pacing(segments, processed_content)
            
            # Analyze tension curve
            tension_curve = self._analyze_tension_curve(segments)
            
            # Identify rhythm patterns
            rhythm_patterns = self._identify_rhythm_patterns(processed_content, segments)
            
            # Detect pacing issues
            pacing_issues = self._detect_pacing_issues(segments, rhythm_patterns)
            
            # Calculate pacing score
            pacing_score = self._calculate_pacing_score(segments, rhythm_patterns, pacing_issues)
            
            # Generate recommendations
            recommendations = self._generate_pacing_recommendations(
                segments, pacing_issues, genre_context
            )
            
            # Analyze beat timing if applicable
            beat_timing = await self._analyze_beat_timing(processed_content)
            
            return {
                "pacing_analysis": {
                    "overall_pacing": pacing_metrics,
                    "tension_curve": tension_curve,
                    "pacing_segments": [self._segment_to_dict(seg) for seg in segments],
                    "beat_timing": beat_timing,
                    "pacing_issues": [self._issue_to_dict(issue) for issue in pacing_issues],
                    "word_count": len(processed_content.split()),
                    "sentence_count": len(self._split_sentences(processed_content)),
                    "estimated_reading_time": len(processed_content.split()) / self.default_reading_speed
                },
                "pacing_score": pacing_score,
                "rhythm_patterns": rhythm_patterns,
                "recommendations": recommendations,
                "metadata": {
                    "genre_context": genre_context,
                    "analysis_timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
                    "segments_analyzed": len(segments)
                }
            }
            
        except Exception as e:
            return self._create_error_result(str(e))

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for pacing analysis."""
        if not content:
            return ""
        
        # Clean up formatting while preserving sentence structure
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        content = content.strip()
        
        return content

    async def _analyze_pacing_segments(self, content: str) -> List[PacingSegment]:
        """Analyze content and divide into pacing segments."""
        segments = []
        
        # Split content into paragraphs for segment analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            # If no paragraph breaks, split by length
            paragraphs = self._split_by_length(content, 500)  # ~500 char segments
        
        total_length = len(content)
        current_position = 0.0
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph:
                continue
                
            # Calculate segment boundaries
            start_pos = current_position
            end_pos = start_pos + (len(paragraph) / total_length)
            
            # Analyze this segment
            segment = await self._analyze_segment(paragraph, start_pos, end_pos)
            segments.append(segment)
            
            current_position = end_pos
        
        return segments

    def _split_by_length(self, content: str, max_length: int) -> List[str]:
        """Split content by length while preserving sentence boundaries."""
        segments = []
        sentences = self._split_sentences(content)
        
        current_segment = ""
        for sentence in sentences:
            if len(current_segment + sentence) > max_length and current_segment:
                segments.append(current_segment.strip())
                current_segment = sentence
            else:
                current_segment += " " + sentence
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments

    async def _analyze_segment(self, segment_content: str, start_pos: float, end_pos: float) -> PacingSegment:
        """Analyze pacing characteristics of a content segment."""
        # Basic metrics
        words = segment_content.split()
        word_count = len(words)
        sentences = self._split_sentences(segment_content)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Analyze pacing characteristics
        action_density = self._calculate_action_density(segment_content)
        dialogue_percentage = self._calculate_dialogue_percentage(segment_content)
        tension_level = self._calculate_tension_level(segment_content)
        
        # Determine pacing type
        pacing_type = self._determine_pacing_type(
            avg_sentence_length, action_density, dialogue_percentage
        )
        
        return PacingSegment(
            start_position=start_pos,
            end_position=end_pos,
            pacing_type=pacing_type,
            tension_level=tension_level,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            action_density=action_density,
            dialogue_percentage=dialogue_percentage
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (could be improved with NLP)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_action_density(self, content: str) -> float:
        """Calculate density of action elements in content."""
        action_words = [
            'ran', 'jumped', 'fought', 'attacked', 'chased', 'crashed', 'exploded',
            'shot', 'fired', 'hit', 'struck', 'grabbed', 'pushed', 'pulled',
            'ducked', 'dodged', 'rushed', 'sprinted', 'leaped', 'slammed'
        ]
        
        content_lower = content.lower()
        words = content_lower.split()
        
        action_count = sum(1 for word in words if any(action in word for action in action_words))
        
        return min(action_count / max(len(words), 1), 1.0)

    def _calculate_dialogue_percentage(self, content: str) -> float:
        """Calculate percentage of content that is dialogue."""
        # Look for dialogue markers
        dialogue_patterns = [
            r'"[^"]*"',  # Quoted dialogue
            r"'[^']*'",  # Single-quoted dialogue
            r'\b\w+\s+said\b',  # "said" tags
            r'\b\w+\s+asked\b',  # "asked" tags
            r'\b\w+\s+replied\b',  # "replied" tags
        ]
        
        dialogue_chars = 0
        for pattern in dialogue_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                dialogue_chars += len(match.group(0))
        
        return min(dialogue_chars / max(len(content), 1), 1.0)

    def _calculate_tension_level(self, content: str) -> float:
        """Calculate tension level in content segment."""
        tension_indicators = {
            'high': ['danger', 'threat', 'fear', 'panic', 'terror', 'urgent', 'desperate', 'crisis'],
            'medium': ['worried', 'concerned', 'anxious', 'nervous', 'tense', 'pressure'],
            'low': ['calm', 'peaceful', 'relaxed', 'comfortable', 'safe', 'serene']
        }
        
        content_lower = content.lower()
        words = content_lower.split()
        
        high_count = sum(1 for word in words if any(indicator in word for indicator in tension_indicators['high']))
        medium_count = sum(1 for word in words if any(indicator in word for indicator in tension_indicators['medium']))
        low_count = sum(1 for word in words if any(indicator in word for indicator in tension_indicators['low']))
        
        total_indicators = high_count + medium_count + low_count
        if total_indicators == 0:
            return 0.5  # neutral
        
        # Weight the indicators
        tension_score = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.2) / total_indicators
        
        return min(tension_score, 1.0)

    def _determine_pacing_type(self, avg_sentence_length: float, action_density: float, 
                             dialogue_percentage: float) -> PacingType:
        """Determine pacing type based on content characteristics."""
        # Calculate pacing score
        pacing_score = 0.0
        
        # Short sentences increase pace
        if avg_sentence_length < 10:
            pacing_score += 0.4
        elif avg_sentence_length < 15:
            pacing_score += 0.2
        elif avg_sentence_length > 25:
            pacing_score -= 0.2
        
        # High action density increases pace
        pacing_score += action_density * 0.3
        
        # Dialogue can increase pace
        pacing_score += dialogue_percentage * 0.3
        
        # Determine pacing type
        if pacing_score >= 0.8:
            return PacingType.VERY_FAST
        elif pacing_score >= 0.6:
            return PacingType.FAST
        elif pacing_score >= 0.4:
            return PacingType.MODERATE
        elif pacing_score >= 0.2:
            return PacingType.SLOW
        else:
            return PacingType.VERY_SLOW

    def _calculate_overall_pacing(self, segments: List[PacingSegment], content: str) -> Dict[str, Any]:
        """Calculate overall pacing metrics from segments."""
        if not segments:
            return {"error": "No segments to analyze"}
        
        # Calculate averages
        avg_tension = sum(seg.tension_level for seg in segments) / len(segments)
        avg_sentence_length = sum(seg.avg_sentence_length for seg in segments) / len(segments)
        avg_action_density = sum(seg.action_density for seg in segments) / len(segments)
        avg_dialogue_percentage = sum(seg.dialogue_percentage for seg in segments) / len(segments)
        
        # Calculate pacing variation
        tension_values = [seg.tension_level for seg in segments]
        pacing_variation = max(tension_values) - min(tension_values) if tension_values else 0
        
        # Determine dominant pacing type
        pacing_types = [seg.pacing_type for seg in segments]
        dominant_type = max(set(pacing_types), key=pacing_types.count)
        
        return {
            "dominant_pacing_type": dominant_type.value,
            "average_tension": avg_tension,
            "pacing_variation": pacing_variation,
            "average_sentence_length": avg_sentence_length,
            "average_action_density": avg_action_density,
            "average_dialogue_percentage": avg_dialogue_percentage,
            "total_segments": len(segments),
            "pacing_consistency": self._calculate_pacing_consistency(segments)
        }

    def _calculate_pacing_consistency(self, segments: List[PacingSegment]) -> float:
        """Calculate how consistent the pacing is throughout the story."""
        if len(segments) < 2:
            return 1.0
        
        # Calculate variance in tension levels
        tension_levels = [seg.tension_level for seg in segments]
        mean_tension = sum(tension_levels) / len(tension_levels)
        variance = sum((t - mean_tension) ** 2 for t in tension_levels) / len(tension_levels)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency = max(0, 1 - (variance * 2))  # Scale appropriately
        
        return consistency

    def _analyze_tension_curve(self, segments: List[PacingSegment]) -> Dict[str, Any]:
        """Analyze the tension curve throughout the story."""
        tension_points = []
        
        for segment in segments:
            tension_points.append({
                "position": (segment.start_position + segment.end_position) / 2,
                "tension": segment.tension_level,
                "pacing_type": segment.pacing_type.value
            })
        
        # Analyze curve characteristics
        curve_analysis = self._analyze_curve_characteristics(tension_points)
        
        return {
            "tension_points": tension_points,
            "curve_analysis": curve_analysis,
            "peak_tension": max(point["tension"] for point in tension_points) if tension_points else 0,
            "minimum_tension": min(point["tension"] for point in tension_points) if tension_points else 0,
            "tension_range": (max(point["tension"] for point in tension_points) - 
                            min(point["tension"] for point in tension_points)) if tension_points else 0
        }

    def _analyze_curve_characteristics(self, tension_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze characteristics of the tension curve."""
        if len(tension_points) < 3:
            return {"insufficient_data": True}
        
        # Find peaks and valleys
        peaks = []
        valleys = []
        
        for i in range(1, len(tension_points) - 1):
            prev_tension = tension_points[i-1]["tension"]
            curr_tension = tension_points[i]["tension"]
            next_tension = tension_points[i+1]["tension"]
            
            if curr_tension > prev_tension and curr_tension > next_tension:
                peaks.append(tension_points[i])
            elif curr_tension < prev_tension and curr_tension < next_tension:
                valleys.append(tension_points[i])
        
        # Analyze curve shape
        overall_trend = self._calculate_overall_trend(tension_points)
        
        return {
            "peaks": len(peaks),
            "valleys": len(valleys),
            "peak_positions": [p["position"] for p in peaks],
            "valley_positions": [v["position"] for v in valleys],
            "overall_trend": overall_trend,
            "curve_smoothness": self._calculate_curve_smoothness(tension_points)
        }

    def _calculate_overall_trend(self, tension_points: List[Dict[str, Any]]) -> str:
        """Calculate overall trend of tension curve."""
        if len(tension_points) < 2:
            return "unknown"
        
        start_tension = tension_points[0]["tension"]
        end_tension = tension_points[-1]["tension"]
        
        if end_tension > start_tension + 0.2:
            return "rising"
        elif end_tension < start_tension - 0.2:
            return "falling"
        else:
            return "stable"

    def _calculate_curve_smoothness(self, tension_points: List[Dict[str, Any]]) -> float:
        """Calculate how smooth the tension curve is."""
        if len(tension_points) < 3:
            return 1.0
        
        # Calculate average change between adjacent points
        total_change = 0
        for i in range(1, len(tension_points)):
            change = abs(tension_points[i]["tension"] - tension_points[i-1]["tension"])
            total_change += change
        
        avg_change = total_change / (len(tension_points) - 1)
        
        # Convert to smoothness score (lower change = smoother)
        smoothness = max(0, 1 - (avg_change * 2))
        
        return smoothness

    def _identify_rhythm_patterns(self, content: str, segments: List[PacingSegment]) -> Dict[str, Any]:
        """Identify rhythm patterns in the narrative."""
        patterns = {}
        
        # Analyze sentence length patterns
        sentences = self._split_sentences(content)
        sentence_lengths = [len(s.split()) for s in sentences]
        
        patterns["short_sentences"] = {
            "count": sum(1 for length in sentence_lengths if length < 8),
            "percentage": sum(1 for length in sentence_lengths if length < 8) / max(len(sentence_lengths), 1)
        }
        
        patterns["long_sentences"] = {
            "count": sum(1 for length in sentence_lengths if length > 20),
            "percentage": sum(1 for length in sentence_lengths if length > 20) / max(len(sentence_lengths), 1)
        }
        
        # Analyze rhythm variety
        patterns["rhythm_variety"] = self._calculate_rhythm_variety(sentence_lengths)
        
        # Analyze pacing transitions
        patterns["pacing_transitions"] = self._analyze_pacing_transitions(segments)
        
        # Check for alternating patterns
        patterns["alternating_rhythm"] = self._detect_alternating_rhythm(segments)
        
        return patterns

    def _calculate_rhythm_variety(self, sentence_lengths: List[int]) -> float:
        """Calculate variety in sentence rhythm."""
        if len(sentence_lengths) < 2:
            return 0.0
        
        # Calculate standard deviation as measure of variety
        mean_length = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((length - mean_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
        std_dev = variance ** 0.5
        
        # Normalize to 0-1 scale (assuming reasonable sentence length range)
        variety = min(std_dev / 10, 1.0)
        
        return variety

    def _analyze_pacing_transitions(self, segments: List[PacingSegment]) -> Dict[str, Any]:
        """Analyze transitions between different pacing types."""
        transitions = []
        
        for i in range(1, len(segments)):
            prev_type = segments[i-1].pacing_type
            curr_type = segments[i].pacing_type
            
            if prev_type != curr_type:
                transitions.append({
                    "from": prev_type.value,
                    "to": curr_type.value,
                    "position": segments[i].start_position
                })
        
        return {
            "total_transitions": len(transitions),
            "transitions": transitions,
            "transition_frequency": len(transitions) / max(len(segments), 1)
        }

    def _detect_alternating_rhythm(self, segments: List[PacingSegment]) -> Dict[str, Any]:
        """Detect alternating rhythm patterns."""
        if len(segments) < 4:
            return {"detected": False, "reason": "insufficient_segments"}
        
        # Check for alternating fast/slow pattern
        alternating_pattern = True
        pattern_type = None
        
        for i in range(2, len(segments)):
            prev_prev = segments[i-2].pacing_type
            current = segments[i].pacing_type
            
            if i == 2:  # First comparison
                pattern_type = "fast_slow" if prev_prev in [PacingType.FAST, PacingType.VERY_FAST] else "slow_fast"
            
            # Check if pattern continues
            if pattern_type == "fast_slow":
                expected = PacingType.FAST if i % 2 == 0 else PacingType.SLOW
            else:
                expected = PacingType.SLOW if i % 2 == 0 else PacingType.FAST
            
            if not self._pacing_types_match(current, expected):
                alternating_pattern = False
                break
        
        return {
            "detected": alternating_pattern,
            "pattern_type": pattern_type if alternating_pattern else None,
            "consistency": self._calculate_pattern_consistency(segments) if alternating_pattern else 0
        }

    def _pacing_types_match(self, actual: PacingType, expected: PacingType) -> bool:
        """Check if pacing types match allowing for some flexibility."""
        fast_types = [PacingType.FAST, PacingType.VERY_FAST]
        slow_types = [PacingType.SLOW, PacingType.VERY_SLOW]
        
        if expected in fast_types:
            return actual in fast_types or actual == PacingType.MODERATE
        elif expected in slow_types:
            return actual in slow_types or actual == PacingType.MODERATE
        else:
            return actual == expected

    def _calculate_pattern_consistency(self, segments: List[PacingSegment]) -> float:
        """Calculate consistency of detected patterns."""
        # Simplified consistency calculation
        return 0.75  # Placeholder

    def _detect_pacing_issues(self, segments: List[PacingSegment], 
                            rhythm_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect pacing issues that need attention."""
        issues = []
        
        # Check for monotonous pacing
        if len(set(seg.pacing_type for seg in segments)) == 1:
            issues.append({
                "type": "monotonous_pacing",
                "description": "Story maintains same pacing throughout without variation",
                "severity": "medium",
                "position": 0.5,
                "suggestion": "Add pacing variation with alternating fast and slow sections"
            })
        
        # Check for low rhythm variety
        if rhythm_patterns.get("rhythm_variety", 0) < 0.3:
            issues.append({
                "type": "low_rhythm_variety",
                "description": "Sentence rhythm lacks variety",
                "severity": "low", 
                "position": 0.5,
                "suggestion": "Vary sentence length and structure for better rhythm"
            })
        
        # Check for tension curve issues
        tension_levels = [seg.tension_level for seg in segments]
        if max(tension_levels) - min(tension_levels) < 0.2:
            issues.append({
                "type": "flat_tension_curve",
                "description": "Tension curve lacks dramatic variation",
                "severity": "medium",
                "position": 0.5,
                "suggestion": "Create more dramatic tension peaks and valleys"
            })
        
        # Check for abrupt pacing changes
        for i in range(1, len(segments)):
            tension_change = abs(segments[i].tension_level - segments[i-1].tension_level)
            if tension_change > 0.7:
                issues.append({
                    "type": "abrupt_pacing_change",
                    "description": f"Abrupt tension change between segments",
                    "severity": "low",
                    "position": segments[i].start_position,
                    "suggestion": "Smooth transition between pacing changes"
                })
        
        return issues

    def _calculate_pacing_score(self, segments: List[PacingSegment], 
                              rhythm_patterns: Dict[str, Any], 
                              issues: List[Dict[str, Any]]) -> float:
        """Calculate overall pacing quality score."""
        score = 1.0
        
        # Deduct for pacing issues
        for issue in issues:
            if issue["severity"] == "critical":
                score -= 0.3
            elif issue["severity"] == "medium":
                score -= 0.2
            elif issue["severity"] == "low":
                score -= 0.1
        
        # Reward good rhythm variety
        rhythm_variety = rhythm_patterns.get("rhythm_variety", 0)
        if rhythm_variety > 0.7:
            score += 0.1
        elif rhythm_variety < 0.3:
            score -= 0.1
        
        # Reward good pacing variation
        if len(segments) > 1:
            pacing_types = set(seg.pacing_type for seg in segments)
            if len(pacing_types) >= 3:
                score += 0.1
            elif len(pacing_types) == 1:
                score -= 0.2
        
        return max(0.0, min(score, 1.0))

    def _generate_pacing_recommendations(self, segments: List[PacingSegment], 
                                       issues: List[Dict[str, Any]], 
                                       genre_context: str = None) -> List[Dict[str, Any]]:
        """Generate recommendations for improving pacing."""
        recommendations = []
        
        # Issue-based recommendations
        for issue in issues:
            recommendations.append({
                "priority": issue["severity"],
                "description": issue["suggestion"],
                "type": "issue_fix",
                "related_issue": issue["type"]
            })
        
        # Genre-specific recommendations
        if genre_context:
            if genre_context.lower() == "thriller":
                recommendations.append({
                    "priority": "medium",
                    "description": "Increase tension buildup in middle sections for thriller pacing",
                    "type": "genre_specific"
                })
            elif genre_context.lower() == "romance":
                recommendations.append({
                    "priority": "low",
                    "description": "Allow for slower, emotional moments between action",
                    "type": "genre_specific"
                })
        
        # General recommendations
        if len(segments) > 0:
            avg_tension = sum(seg.tension_level for seg in segments) / len(segments)
            if avg_tension < 0.4:
                recommendations.append({
                    "priority": "medium",
                    "description": "Overall tension level is low. Consider adding more conflict or stakes",
                    "type": "general_improvement"
                })
        
        return recommendations

    async def _analyze_beat_timing(self, content: str) -> Dict[str, Any]:
        """Analyze timing of narrative beats for pacing assessment."""
        # Simplified beat detection for timing analysis
        beat_positions = []
        content_lower = content.lower()
        content_length = len(content)
        
        # Look for common beat indicators
        beat_indicators = {
            "inciting_incident": ["suddenly", "unexpected", "changed"],
            "midpoint": ["realized", "discovered", "revelation"],
            "climax": ["final", "confrontation", "decisive"],
            "resolution": ["ended", "resolved", "finally"]
        }
        
        for beat_type, keywords in beat_indicators.items():
            for keyword in keywords:
                pos = content_lower.find(keyword)
                if pos != -1:
                    beat_positions.append({
                        "beat_type": beat_type,
                        "position": pos / content_length,
                        "keyword": keyword
                    })
                    break  # Only find first occurrence of each beat type
        
        # Analyze beat intervals
        intervals = []
        if len(beat_positions) > 1:
            sorted_beats = sorted(beat_positions, key=lambda x: x["position"])
            for i in range(1, len(sorted_beats)):
                interval = sorted_beats[i]["position"] - sorted_beats[i-1]["position"]
                intervals.append(interval)
        
        return {
            "beats_identified": len(beat_positions),
            "beat_positions": beat_positions,
            "beat_intervals": intervals,
            "timing_consistency": self._calculate_timing_consistency(intervals),
            "average_interval": sum(intervals) / len(intervals) if intervals else 0
        }

    def _calculate_timing_consistency(self, intervals: List[float]) -> float:
        """Calculate consistency of beat timing."""
        if len(intervals) < 2:
            return 1.0
        
        # Calculate variance in intervals
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((interval - mean_interval) ** 2 for interval in intervals) / len(intervals)
        
        # Convert to consistency score
        consistency = max(0, 1 - (variance * 4))  # Scale appropriately
        
        return consistency

    def _segment_to_dict(self, segment: PacingSegment) -> Dict[str, Any]:
        """Convert PacingSegment to dictionary."""
        return {
            "start_position": segment.start_position,
            "end_position": segment.end_position,
            "pacing_type": segment.pacing_type.value,
            "tension_level": segment.tension_level,
            "word_count": segment.word_count,
            "sentence_count": segment.sentence_count,
            "avg_sentence_length": segment.avg_sentence_length,
            "action_density": segment.action_density,
            "dialogue_percentage": segment.dialogue_percentage
        }

    def _issue_to_dict(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Convert pacing issue to dictionary."""
        return issue  # Already in dict format

    def _create_empty_content_result(self) -> Dict[str, Any]:
        """Create result for empty content."""
        return {
            "pacing_analysis": {
                "error": "Empty content provided",
                "word_count": 0,
                "sentence_count": 0
            },
            "pacing_score": 0.0,
            "rhythm_patterns": {},
            "recommendations": [
                {
                    "priority": "error",
                    "description": "No content provided for pacing analysis",
                    "type": "input_error"
                }
            ]
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create result for analysis errors."""
        return {
            "pacing_analysis": {
                "error": error_message
            },
            "pacing_score": 0.0,
            "rhythm_patterns": {},
            "recommendations": [
                {
                    "priority": "error",
                    "description": f"Pacing analysis error: {error_message}",
                    "type": "processing_error"
                }
            ]
        }