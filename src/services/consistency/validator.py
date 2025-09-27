import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime, timedelta
from src.models.consistency_rule import (
    ConsistencyRule,
    RuleSeverity,
    RuleType,
    RuleScope,
    ValidationLogic,
)
from src.lib.error_handler import AnalysisError


class ConsistencyValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: List[ConsistencyRule] = self._initialize_rules()

    def _initialize_rules(self) -> List[ConsistencyRule]:
        """Initialize built-in consistency rules."""
        rules = []

        # Timeline consistency rules
        rules.append(
            ConsistencyRule(
                id="timeline_order",
                name="Timeline Order Validation",
                description="Events must occur in chronological order",
                rule_type=RuleType.TIMELINE,
                validation_logic=ValidationLogic(
                    conditions=["events", "timestamp"],
                    assertions=["timestamp_order"],
                    error_message="Events are not in chronological order",
                    suggested_fix="Reorder events or correct timestamps",
                    confidence_penalty=0.2,
                ),
                severity=RuleSeverity.CRITICAL,
                scope=RuleScope.STORY_ARC,
                confidence_impact=0.2,
            )
        )

        # Character consistency rules
        rules.append(
            ConsistencyRule(
                id="character_attributes",
                name="Character Attribute Consistency",
                description="Character attributes must remain consistent",
                rule_type=RuleType.CHARACTER,
                validation_logic=ValidationLogic(
                    conditions=["characters", "attributes"],
                    assertions=["attribute_consistency"],
                    error_message="Character attributes are inconsistent",
                    suggested_fix="Review character descriptions for consistency",
                    confidence_penalty=0.15,
                ),
                severity=RuleSeverity.WARNING,
                scope=RuleScope.CHARACTER_JOURNEY,
                confidence_impact=0.15,
            )
        )

        # World consistency rules
        rules.append(
            ConsistencyRule(
                id="world_rules",
                name="World Rules Consistency",
                description="World rules and physics must be consistent",
                rule_type=RuleType.WORLD,
                validation_logic=ValidationLogic(
                    conditions=["world_details", "consistency_rule"],
                    assertions=["rule_adherence"],
                    error_message="World rules are violated",
                    suggested_fix="Ensure all events follow established world rules",
                    confidence_penalty=0.1,
                ),
                severity=RuleSeverity.WARNING,
                scope=RuleScope.STORY_ARC,
                confidence_impact=0.1,
            )
        )

        return rules

    def validate(self, story_elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the consistency of the story elements and returns a comprehensive report.
        """
        if not story_elements:
            raise AnalysisError("Story elements cannot be empty")

        try:
            self.logger.info("Starting comprehensive consistency validation")

            issues = []
            strengths = []
            recommendations = []

            # Validate timeline consistency
            timeline_issues, timeline_strengths = self._validate_timeline(
                story_elements.get("events", [])
            )
            issues.extend(timeline_issues)
            strengths.extend(timeline_strengths)

            # Validate character consistency
            character_issues, character_strengths = self._validate_characters(
                story_elements.get("characters", [])
            )
            issues.extend(character_issues)
            strengths.extend(character_strengths)

            # Validate world consistency
            world_issues, world_strengths = self._validate_world_rules(
                story_elements.get("world_details", []),
                story_elements.get("events", []),
            )
            issues.extend(world_issues)
            strengths.extend(world_strengths)

            # Validate plot consistency
            plot_issues, plot_strengths = self._validate_plot_consistency(
                story_elements
            )
            issues.extend(plot_issues)
            strengths.extend(plot_strengths)

            # Generate recommendations
            recommendations = self._generate_recommendations(issues, story_elements)

            # Calculate scores
            overall_score = self._calculate_overall_score(issues)
            confidence_score = self._calculate_confidence_score(issues, story_elements)

            self.logger.info(
                f"Consistency validation complete. Score: {overall_score:.2f}, Confidence: {confidence_score:.2f}"
            )

            return {
                "overall_score": overall_score,
                "confidence_score": confidence_score,
                "issues": issues,
                "strengths": strengths,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Error during consistency validation: {e}")
            raise AnalysisError(f"Consistency validation failed: {str(e)}")

    def _validate_timeline(
        self, events: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[str]]:
        """Validate timeline consistency of events."""
        issues = []
        strengths = []

        if not events:
            return issues, strengths

        # Check chronological order
        for i in range(len(events) - 1):
            event1 = events[i]
            event2 = events[i + 1]

            # Compare timestamps if available
            if "timestamp" in event1 and "timestamp" in event2:
                if (
                    self._compare_timestamps(event1["timestamp"], event2["timestamp"])
                    > 0
                ):
                    issues.append(
                        {
                            "type": "timeline",
                            "severity": "critical",
                            "description": f"Event '{event2.get('description', 'Unknown')}' occurs before '{event1.get('description', 'Unknown')}' but has a later timestamp",
                            "location": f"Events {i + 1} and {i + 2}",
                            "suggested_fix": "Reorder events or correct timestamps",
                            "confidence_impact": 0.2,
                        }
                    )

            # Check for logical sequence
            if "episode" in event1 and "episode" in event2:
                if event1["episode"] > event2["episode"]:
                    issues.append(
                        {
                            "type": "timeline",
                            "severity": "warning",
                            "description": f"Event sequence may be incorrect between episodes {event1['episode']} and {event2['episode']}",
                            "location": f"Events {i + 1} and {i + 2}",
                            "suggested_fix": "Review episode order",
                            "confidence_impact": 0.1,
                        }
                    )

        # Check for timeline gaps
        timeline_gaps = self._detect_timeline_gaps(events)
        for gap in timeline_gaps:
            issues.append(
                {
                    "type": "timeline",
                    "severity": "suggestion",
                    "description": f"Potential timeline gap detected: {gap['description']}",
                    "location": gap["location"],
                    "suggested_fix": "Consider adding transitional events or clarifying time passage",
                    "confidence_impact": 0.05,
                }
            )

        # Identify strengths
        if len(events) > 1 and not any(
            issue["severity"] == "critical" for issue in issues
        ):
            strengths.append("Timeline maintains chronological consistency")

        if len(events) >= 5:
            strengths.append("Rich event timeline provides good story structure")

        return issues, strengths

    def _validate_characters(
        self, characters: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[str]]:
        """Validate character consistency."""
        issues = []
        strengths = []

        if not characters:
            return issues, strengths

        # Track character attributes across appearances
        character_tracker = {}

        for char in characters:
            name = char.get("name", "Unknown")
            attributes = char.get("attributes", {})

            if name in character_tracker:
                # Check for attribute consistency
                previous_attrs = character_tracker[name]
                for attr, value in attributes.items():
                    if attr in previous_attrs and previous_attrs[attr] != value:
                        issues.append(
                            {
                                "type": "character",
                                "severity": "warning",
                                "description": f"Character '{name}' has inconsistent {attr}: '{previous_attrs[attr]}' vs '{value}'",
                                "location": f"Character definition for {name}",
                                "suggested_fix": f"Standardize {attr} for character {name}",
                                "confidence_impact": 0.15,
                            }
                        )
            else:
                character_tracker[name] = attributes

        # Check for character development consistency
        for char in characters:
            name = char.get("name", "Unknown")
            role = char.get("role", "")

            # Validate protagonist consistency
            if role == "protagonist":
                if not char.get("attributes", {}).get("age"):
                    issues.append(
                        {
                            "type": "character",
                            "severity": "suggestion",
                            "description": f"Protagonist '{name}' lacks age specification",
                            "location": f"Character definition for {name}",
                            "suggested_fix": "Add age to protagonist character profile",
                            "confidence_impact": 0.05,
                        }
                    )

        # Identify strengths
        if len(characters) > 0:
            strengths.append(f"Story includes {len(characters)} defined characters")

        protagonist_count = sum(
            1 for char in characters if char.get("role") == "protagonist"
        )
        if protagonist_count == 1:
            strengths.append("Clear single protagonist structure")
        elif protagonist_count > 1:
            strengths.append("Multi-protagonist narrative structure")

        return issues, strengths

    def _validate_world_rules(
        self, world_details: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[str]]:
        """Validate world building consistency."""
        issues = []
        strengths = []

        if not world_details:
            return issues, strengths

        # Extract world rules
        world_rules = {}
        for detail in world_details:
            aspect = detail.get("aspect", "")
            rule = detail.get("consistency_rule", "")
            if aspect and rule:
                world_rules[aspect] = rule

        # Validate events against world rules
        for i, event in enumerate(events):
            location = event.get("location", "")
            description = event.get("description", "").lower()

            # Check location-based rules
            if "jurisdiction" in world_rules and location:
                jurisdiction_rule = world_rules["jurisdiction"].lower()
                if (
                    "outside_jurisdiction" in location.lower()
                    and "arrest" in description
                ):
                    issues.append(
                        {
                            "type": "world",
                            "severity": "warning",
                            "description": f"Event violates jurisdiction rule: {jurisdiction_rule}",
                            "location": f"Event {i + 1}: {event.get('description', 'Unknown')}",
                            "suggested_fix": "Modify event location or add explanation for jurisdiction exception",
                            "confidence_impact": 0.1,
                        }
                    )

            # Check physics/magic rules
            if "physics" in world_rules:
                physics_rule = world_rules["physics"].lower()
                if "magic" in physics_rule and "impossible" in description:
                    issues.append(
                        {
                            "type": "world",
                            "severity": "suggestion",
                            "description": "Event may violate established physics rules",
                            "location": f"Event {i + 1}",
                            "suggested_fix": "Ensure event follows established world physics",
                            "confidence_impact": 0.05,
                        }
                    )

        # Identify strengths
        if world_rules:
            strengths.append(
                f"World building includes {len(world_rules)} consistency rules"
            )

        if len(world_details) >= 3:
            strengths.append("Rich world building with multiple defined aspects")

        return issues, strengths

    def _validate_plot_consistency(
        self, story_elements: Dict[str, Any]
    ) -> Tuple[List[Dict], List[str]]:
        """Validate plot consistency and logical flow."""
        issues = []
        strengths = []

        events = story_elements.get("events", [])
        characters = story_elements.get("characters", [])

        # Check for plot holes - events that reference unknown characters
        character_names = {char.get("name", "").lower() for char in characters}

        for i, event in enumerate(events):
            event_chars = event.get("characters", [])
            description = event.get("description", "").lower()

            # Check if event references undefined characters
            for char_name in event_chars:
                if char_name.lower() not in character_names:
                    issues.append(
                        {
                            "type": "plot",
                            "severity": "warning",
                            "description": f"Event references undefined character: '{char_name}'",
                            "location": f"Event {i + 1}",
                            "suggested_fix": f"Define character '{char_name}' or remove reference",
                            "confidence_impact": 0.1,
                        }
                    )

            # Check for logical inconsistencies in descriptions
            if "dead" in description and "speak" in description:
                issues.append(
                    {
                        "type": "plot",
                        "severity": "critical",
                        "description": "Logical inconsistency: dead character speaking",
                        "location": f"Event {i + 1}",
                        "suggested_fix": "Resolve character death/speaking contradiction",
                        "confidence_impact": 0.2,
                    }
                )

        # Check for cause and effect consistency
        cause_effect_issues = self._analyze_cause_effect(events)
        issues.extend(cause_effect_issues)

        # Identify strengths
        if events and characters:
            strengths.append("Story includes both events and character definitions")

        if len(events) >= 3:
            strengths.append("Plot has sufficient event complexity")

        return issues, strengths

    def _analyze_cause_effect(self, events: List[Dict[str, Any]]) -> List[Dict]:
        """Analyze cause and effect relationships between events."""
        issues = []

        # Look for events that should have consequences
        consequence_keywords = {
            "kill": ["death", "funeral", "grief"],
            "marry": ["wedding", "spouse", "husband", "wife"],
            "arrest": ["jail", "prison", "trial", "court"],
            "fire": ["unemployed", "job search", "new job"],
        }

        for i, event in enumerate(events):
            description = event.get("description", "").lower()

            for trigger, expected_consequences in consequence_keywords.items():
                if trigger in description:
                    # Look for consequences in subsequent events
                    found_consequence = False
                    for j in range(
                        i + 1, min(i + 5, len(events))
                    ):  # Check next 4 events
                        next_event = events[j].get("description", "").lower()
                        if any(
                            consequence in next_event
                            for consequence in expected_consequences
                        ):
                            found_consequence = True
                            break

                    if not found_consequence:
                        issues.append(
                            {
                                "type": "plot",
                                "severity": "suggestion",
                                "description": f"Event '{trigger}' may lack appropriate consequences",
                                "location": f"Event {i + 1}",
                                "suggested_fix": f"Consider adding consequences related to {trigger}",
                                "confidence_impact": 0.05,
                            }
                        )

        return issues

    def _compare_timestamps(self, timestamp1: Any, timestamp2: Any) -> int:
        """Compare two timestamps. Returns -1, 0, or 1."""
        try:
            # Handle different timestamp formats
            if isinstance(timestamp1, str) and isinstance(timestamp2, str):
                # Try to parse as day_time format
                if "_" in timestamp1 and "_" in timestamp2:
                    # Extract day number and time separately
                    day1_match = re.search(r"day_(\d+)", timestamp1)
                    day2_match = re.search(r"day_(\d+)", timestamp2)

                    time1_match = re.search(r"day_\d+_(.+)", timestamp1)
                    time2_match = re.search(r"day_\d+_(.+)", timestamp2)

                    if day1_match and day2_match and time1_match and time2_match:
                        day1_num = int(day1_match.group(1))
                        day2_num = int(day2_match.group(1))
                        time1 = time1_match.group(1)
                        time2 = time2_match.group(1)
                    else:
                        # Fallback to original logic if pattern doesn't match
                        day1, time1 = timestamp1.split("_", 1)
                        day2, time2 = timestamp2.split("_", 1)
                        day1_num = (
                            int(re.search(r"\d+", day1).group())
                            if re.search(r"\d+", day1)
                            else 0
                        )
                        day2_num = (
                            int(re.search(r"\d+", day2).group())
                            if re.search(r"\d+", day2)
                            else 0
                        )

                    if day1_num != day2_num:
                        return -1 if day1_num < day2_num else 1

                    # Compare times within the same day
                    time_order = {
                        "morning": 1,
                        "afternoon": 2,
                        "evening": 3,
                        "night": 4,
                    }
                    time1_val = time_order.get(time1.lower(), 2)
                    time2_val = time_order.get(time2.lower(), 2)

                    return (
                        -1
                        if time1_val < time2_val
                        else (1 if time1_val > time2_val else 0)
                    )

            # Handle numeric timestamps
            if isinstance(timestamp1, (int, float)) and isinstance(
                timestamp2, (int, float)
            ):
                return (
                    -1
                    if timestamp1 < timestamp2
                    else (1 if timestamp1 > timestamp2 else 0)
                )

            # Default string comparison
            return (
                -1
                if str(timestamp1) < str(timestamp2)
                else (1 if str(timestamp1) > str(timestamp2) else 0)
            )

        except Exception:
            return 0  # Unable to compare

    def _detect_timeline_gaps(self, events: List[Dict[str, Any]]) -> List[Dict]:
        """Detect potential gaps in the timeline."""
        gaps = []

        for i in range(len(events) - 1):
            event1 = events[i]
            event2 = events[i + 1]

            # Check for large time jumps
            if "timestamp" in event1 and "timestamp" in event2:
                timestamp1 = event1["timestamp"]
                timestamp2 = event2["timestamp"]

                # Simple gap detection for day-based timestamps
                if isinstance(timestamp1, str) and isinstance(timestamp2, str):
                    if "_" in timestamp1 and "_" in timestamp2:
                        day1_match = re.search(r"day_(\d+)", timestamp1.lower())
                        day2_match = re.search(r"day_(\d+)", timestamp2.lower())

                        if day1_match and day2_match:
                            day1 = int(day1_match.group(1))
                            day2 = int(day2_match.group(1))

                            if day2 - day1 > 3:  # Gap of more than 3 days
                                gaps.append(
                                    {
                                        "description": f"Large time gap between day {day1} and day {day2}",
                                        "location": f"Between events {i + 1} and {i + 2}",
                                    }
                                )

        return gaps

    def _generate_recommendations(
        self, issues: List[Dict], story_elements: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on identified issues."""
        recommendations = []

        # Count issues by type
        issue_counts = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Generate type-specific recommendations
        if issue_counts.get("timeline", 0) > 0:
            recommendations.append(
                "Review timeline consistency - ensure events occur in logical chronological order"
            )

        if issue_counts.get("character", 0) > 0:
            recommendations.append(
                "Standardize character attributes and ensure consistency across all appearances"
            )

        if issue_counts.get("world", 0) > 0:
            recommendations.append(
                "Review world-building rules and ensure all events adhere to established constraints"
            )

        if issue_counts.get("plot", 0) > 0:
            recommendations.append(
                "Address plot inconsistencies and ensure cause-and-effect relationships are clear"
            )

        # General recommendations based on story structure
        events = story_elements.get("events", [])
        characters = story_elements.get("characters", [])

        if len(events) < 3:
            recommendations.append(
                "Consider adding more events to develop the plot structure"
            )

        if len(characters) < 2:
            recommendations.append(
                "Consider adding more characters to create richer interactions"
            )

        # Critical issue recommendations
        critical_issues = [
            issue for issue in issues if issue.get("severity") == "critical"
        ]
        if critical_issues:
            recommendations.insert(
                0,
                f"Address {len(critical_issues)} critical consistency issues immediately",
            )

        return recommendations

    def _calculate_overall_score(self, issues: List[Dict]) -> float:
        """Calculate overall consistency score."""
        if not issues:
            return 1.0

        # Weight issues by severity
        severity_weights = {"critical": 0.3, "warning": 0.15, "suggestion": 0.05}

        total_penalty = 0.0
        for issue in issues:
            severity = issue.get("severity", "suggestion")
            penalty = severity_weights.get(severity, 0.05)
            total_penalty += penalty

        # Calculate score with diminishing returns for many issues
        raw_score = 1.0 - total_penalty
        adjusted_score = max(0.0, min(1.0, raw_score))

        return round(adjusted_score, 2)

    def _calculate_confidence_score(
        self, issues: List[Dict], story_elements: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the consistency analysis."""
        base_confidence = 0.8

        # Reduce confidence based on analysis limitations
        events = story_elements.get("events", [])
        characters = story_elements.get("characters", [])
        world_details = story_elements.get("world_details", [])

        # Penalty for insufficient data
        if len(events) < 2:
            base_confidence -= 0.2
        if len(characters) < 1:
            base_confidence -= 0.1
        if len(world_details) < 1:
            base_confidence -= 0.1

        # Penalty for unresolved critical issues
        critical_issues = [
            issue for issue in issues if issue.get("severity") == "critical"
        ]
        base_confidence -= len(critical_issues) * 0.05

        # Bonus for comprehensive data
        if len(events) >= 5 and len(characters) >= 3:
            base_confidence += 0.1

        return max(0.1, min(0.95, base_confidence))
