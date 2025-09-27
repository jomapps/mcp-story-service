"""ConsistencyValidator service with plot hole detection and confidence scoring.

This service validates narrative consistency and detects plot holes
with confidence impact assessment per FR-004.

Constitutional Compliance:
- Library-First (I): Focused validation service
- Test-First (II): Tests written before implementation
- Simplicity (III): Clear validation logic without complexity
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ...models.consistency_rule import ConsistencyRule, RuleType, SeverityLevel, ViolationEvidence
from ...models.character_journey import CharacterJourney
from ...models.content_analysis import ContentAnalysisResult, ContentQuality, ProcessingStatus


class ConsistencyViolation:
    """Individual consistency violation found during validation."""
    
    def __init__(self, rule_id: str, description: str, severity: SeverityLevel,
                 position: float, evidence: str, confidence: float):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity
        self.position = position
        self.evidence = evidence
        self.confidence = confidence
        self.confidence_penalty = self._calculate_penalty()
    
    def _calculate_penalty(self) -> float:
        """Calculate confidence penalty based on severity."""
        penalty_map = {
            SeverityLevel.CRITICAL: 0.4,
            SeverityLevel.HIGH: 0.3,
            SeverityLevel.MEDIUM: 0.2,
            SeverityLevel.LOW: 0.1,
            SeverityLevel.MINOR: 0.05
        }
        return penalty_map.get(self.severity, 0.2)


class ConsistencyValidator:
    """
    Service for validating narrative consistency and detecting plot holes.
    
    Analyzes story content for character consistency, timeline issues,
    plot logic problems, and world-building contradictions.
    """
    
    def __init__(self):
        self.built_in_rules = self._initialize_built_in_rules()
        self.confidence_threshold = 0.75
        
    def _initialize_built_in_rules(self) -> List[ConsistencyRule]:
        """Initialize built-in consistency rules."""
        rules = []
        
        # Character attribute consistency
        char_attr_rule = ConsistencyRule(
            rule_id="character_attribute_consistency",
            rule_name="Character Attribute Consistency",
            rule_type=RuleType.CHARACTER_ATTRIBUTE,
            description="Character physical attributes must remain consistent",
            conditions=[],  # Simplified for this implementation
            severity_level=SeverityLevel.MEDIUM,
            impact_score=0.6,
            confidence_penalty=0.2
        )
        rules.append(char_attr_rule)
        
        # Timeline consistency
        timeline_rule = ConsistencyRule(
            rule_id="timeline_consistency",
            rule_name="Timeline Consistency",
            rule_type=RuleType.TIMELINE,
            description="Events must follow logical chronological order",
            conditions=[],
            severity_level=SeverityLevel.HIGH,
            impact_score=0.8,
            confidence_penalty=0.3
        )
        rules.append(timeline_rule)
        
        # Plot logic consistency
        plot_logic_rule = ConsistencyRule(
            rule_id="plot_logic_consistency",
            rule_name="Plot Logic Consistency",
            rule_type=RuleType.PLOT_LOGIC,
            description="Plot events must follow logical cause and effect",
            conditions=[],
            severity_level=SeverityLevel.HIGH,
            impact_score=0.7,
            confidence_penalty=0.25
        )
        rules.append(plot_logic_rule)
        
        # Character behavior consistency
        behavior_rule = ConsistencyRule(
            rule_id="character_behavior_consistency",
            rule_name="Character Behavior Consistency",
            rule_type=RuleType.CHARACTER_BEHAVIOR,
            description="Characters must act consistently with established personality",
            conditions=[],
            severity_level=SeverityLevel.MEDIUM,
            impact_score=0.6,
            confidence_penalty=0.15
        )
        rules.append(behavior_rule)
        
        return rules

    async def validate_consistency(self, story_content: str, custom_rules: List[Dict[str, Any]] = None,
                                 character_journeys: List[CharacterJourney] = None) -> Dict[str, Any]:
        """
        Validate story consistency and detect plot holes.
        
        Args:
            story_content: Story content to validate
            custom_rules: Optional custom consistency rules
            character_journeys: Optional character journey data for validation
            
        Returns:
            Validation results with violations and confidence impact
        """
        try:
            # Preprocess content
            processed_content = self._preprocess_content(story_content)
            
            if not processed_content.strip():
                return self._create_empty_content_result()
            
            # Get all rules to apply
            all_rules = self.built_in_rules.copy()
            if custom_rules:
                all_rules.extend(self._convert_custom_rules(custom_rules))
            
            # Run validation
            violations = []
            for rule in all_rules:
                rule_violations = await self._validate_rule(rule, processed_content, character_journeys)
                violations.extend(rule_violations)
            
            # Calculate overall scores
            overall_score = self._calculate_overall_score(violations, processed_content)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations)
            
            return {
                "consistency_report": {
                    "total_violations": len(violations),
                    "violations_by_severity": self._group_violations_by_severity(violations),
                    "applied_rules": [rule.rule_id for rule in all_rules],
                    "analysis_summary": self._create_analysis_summary(violations, processed_content)
                },
                "violations": [self._violation_to_dict(v) for v in violations],
                "overall_score": overall_score,
                "recommendations": recommendations,
                "metadata": {
                    "rules_applied": len(all_rules),
                    "content_length": len(processed_content),
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return self._create_error_result(str(e))

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for consistency validation."""
        if not content:
            return ""
        
        # Clean up formatting
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        content = content.strip()
        
        return content

    async def _validate_rule(self, rule: ConsistencyRule, content: str,
                           character_journeys: List[CharacterJourney] = None) -> List[ConsistencyViolation]:
        """Validate a single consistency rule against content."""
        violations = []
        
        if rule.rule_type == RuleType.CHARACTER_ATTRIBUTE:
            violations.extend(await self._validate_character_attributes(content))
        elif rule.rule_type == RuleType.TIMELINE:
            violations.extend(await self._validate_timeline(content))
        elif rule.rule_type == RuleType.PLOT_LOGIC:
            violations.extend(await self._validate_plot_logic(content))
        elif rule.rule_type == RuleType.CHARACTER_BEHAVIOR:
            violations.extend(await self._validate_character_behavior(content, character_journeys))
        
        return violations

    async def _validate_character_attributes(self, content: str) -> List[ConsistencyViolation]:
        """Validate character attribute consistency."""
        violations = []
        
        # Extract character attribute mentions
        attributes = self._extract_character_attributes(content)
        
        # Check for inconsistencies
        for character, char_attributes in attributes.items():
            for attr_type, mentions in char_attributes.items():
                if len(set(mentions)) > 1:  # Multiple different values
                    violation = ConsistencyViolation(
                        rule_id="character_attribute_consistency",
                        description=f"Character '{character}' has inconsistent {attr_type}: {mentions}",
                        severity=SeverityLevel.MEDIUM,
                        position=0.5,  # Simplified position
                        evidence=f"Found conflicting {attr_type} descriptions: {', '.join(set(mentions))}",
                        confidence=0.8
                    )
                    violations.append(violation)
        
        return violations

    def _extract_character_attributes(self, content: str) -> Dict[str, Dict[str, List[str]]]:
        """Extract character attribute mentions from content."""
        attributes = {}
        
        # Simple patterns for common attributes
        eye_color_pattern = r'(\w+)(?:\'s)?\s+([a-z]+)\s+eyes?'
        hair_pattern = r'(\w+)(?:\'s)?\s+([a-z]+)\s+hair'
        height_pattern = r'(\w+)(?:\s+was|\s+is)?\s+(tall|short|average|medium)'
        
        patterns = {
            'eye_color': eye_color_pattern,
            'hair_color': hair_pattern,
            'height': height_pattern
        }
        
        for attr_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                character = match.group(1).lower()
                attribute_value = match.group(2).lower()
                
                if character not in attributes:
                    attributes[character] = {}
                if attr_type not in attributes[character]:
                    attributes[character][attr_type] = []
                
                attributes[character][attr_type].append(attribute_value)
        
        return attributes

    async def _validate_timeline(self, content: str) -> List[ConsistencyViolation]:
        """Validate timeline consistency."""
        violations = []
        
        # Extract temporal references
        time_events = self._extract_temporal_events(content)
        
        # Check for timeline inconsistencies
        for i, event1 in enumerate(time_events):
            for event2 in time_events[i+1:]:
                if self._has_timeline_conflict(event1, event2):
                    violation = ConsistencyViolation(
                        rule_id="timeline_consistency",
                        description=f"Timeline conflict between '{event1['text']}' and '{event2['text']}'",
                        severity=SeverityLevel.HIGH,
                        position=max(event1['position'], event2['position']),
                        evidence=f"Conflicting temporal references: {event1['text']} vs {event2['text']}",
                        confidence=0.7
                    )
                    violations.append(violation)
        
        return violations

    def _extract_temporal_events(self, content: str) -> List[Dict[str, Any]]:
        """Extract temporal events and references from content."""
        events = []
        
        # Simple temporal patterns
        temporal_patterns = [
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(yesterday|today|tomorrow)',
            r'(morning|afternoon|evening|night)',
            r'(\d{1,2}:\d{2})',  # Times
            r'(before|after|during|while)\s+([^.]+)',
        ]
        
        for pattern in temporal_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                position = match.start() / len(content)
                events.append({
                    'text': match.group(0),
                    'position': position,
                    'type': 'temporal_reference'
                })
        
        return events

    def _has_timeline_conflict(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> bool:
        """Check if two events have timeline conflicts."""
        # Simplified timeline conflict detection
        text1 = event1['text'].lower()
        text2 = event2['text'].lower()
        
        # Check for obvious conflicts
        if 'before' in text1 and 'after' in text2:
            return True
        if 'yesterday' in text1 and 'tomorrow' in text2:
            return True
        
        return False

    async def _validate_plot_logic(self, content: str) -> List[ConsistencyViolation]:
        """Validate plot logic consistency."""
        violations = []
        
        # Look for logical inconsistencies
        logic_issues = self._detect_plot_logic_issues(content)
        
        for issue in logic_issues:
            violation = ConsistencyViolation(
                rule_id="plot_logic_consistency",
                description=issue['description'],
                severity=SeverityLevel.HIGH,
                position=issue['position'],
                evidence=issue['evidence'],
                confidence=issue['confidence']
            )
            violations.append(violation)
        
        return violations

    def _detect_plot_logic_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect plot logic issues in content."""
        issues = []
        
        # Look for contradictory statements
        content_lower = content.lower()
        
        # Dead character speaking
        if 'died' in content_lower and 'said' in content_lower:
            # Simple check - could be false positive
            died_pos = content_lower.find('died')
            said_pos = content_lower.rfind('said')  # Last occurrence
            
            if died_pos < said_pos and abs(died_pos - said_pos) > 100:
                issues.append({
                    'description': 'Character appears to speak after being described as dead',
                    'position': said_pos / len(content),
                    'evidence': content[max(0, said_pos-50):said_pos+50],
                    'confidence': 0.6
                })
        
        # Impossible physical actions
        impossible_patterns = [
            r'flew\s+without\s+wings',
            r'breathed\s+underwater\s+without',
            r'saw\s+through\s+solid'
        ]
        
        for pattern in impossible_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'description': f'Potentially impossible action: {match.group(0)}',
                    'position': match.start() / len(content),
                    'evidence': match.group(0),
                    'confidence': 0.5
                })
        
        return issues

    async def _validate_character_behavior(self, content: str, 
                                         character_journeys: List[CharacterJourney] = None) -> List[ConsistencyViolation]:
        """Validate character behavior consistency."""
        violations = []
        
        if not character_journeys:
            return violations
        
        # Check character behavior against established journeys
        for journey in character_journeys:
            behavior_violations = self._check_character_behavior_consistency(content, journey)
            violations.extend(behavior_violations)
        
        return violations

    def _check_character_behavior_consistency(self, content: str, 
                                            journey: CharacterJourney) -> List[ConsistencyViolation]:
        """Check behavior consistency for a specific character."""
        violations = []
        
        character_name = journey.character_name.lower()
        content_lower = content.lower()
        
        # Look for character mentions and actions
        character_actions = self._extract_character_actions(content, character_name)
        
        # Check against character traits
        for action in character_actions:
            if self._action_conflicts_with_traits(action, journey.current_traits):
                violation = ConsistencyViolation(
                    rule_id="character_behavior_consistency",
                    description=f"Character '{journey.character_name}' acts inconsistently with established traits",
                    severity=SeverityLevel.MEDIUM,
                    position=action['position'],
                    evidence=action['text'],
                    confidence=0.6
                )
                violations.append(violation)
        
        return violations

    def _extract_character_actions(self, content: str, character_name: str) -> List[Dict[str, Any]]:
        """Extract actions performed by a specific character."""
        actions = []
        
        # Simple pattern to find character actions
        action_pattern = rf'{character_name}\s+(walked|ran|said|shouted|whispered|fought|helped|hurt)'
        
        matches = re.finditer(action_pattern, content, re.IGNORECASE)
        for match in matches:
            actions.append({
                'text': match.group(0),
                'action': match.group(1),
                'position': match.start() / len(content)
            })
        
        return actions

    def _action_conflicts_with_traits(self, action: Dict[str, Any], traits: List[Any]) -> bool:
        """Check if an action conflicts with character traits."""
        # Simplified trait checking
        action_verb = action['action'].lower()
        
        for trait in traits:
            trait_name = trait.trait_name.lower()
            
            # Simple conflict detection
            if 'peaceful' in trait_name and action_verb == 'fought':
                return True
            if 'quiet' in trait_name and action_verb in ['shouted', 'yelled']:
                return True
            if 'coward' in trait_name and action_verb == 'fought':
                return True
        
        return False

    def _convert_custom_rules(self, custom_rules: List[Dict[str, Any]]) -> List[ConsistencyRule]:
        """Convert custom rule dictionaries to ConsistencyRule objects."""
        rules = []
        
        for rule_data in custom_rules:
            try:
                rule = ConsistencyRule(
                    rule_id=rule_data.get('rule_id', f'custom_{len(rules)}'),
                    rule_name=rule_data.get('rule_name', 'Custom Rule'),
                    rule_type=RuleType(rule_data.get('rule_type', 'custom')),
                    description=rule_data.get('description', ''),
                    conditions=[],  # Simplified
                    severity_level=SeverityLevel(rule_data.get('severity', 'medium')),
                    impact_score=rule_data.get('impact_score', 0.5),
                    confidence_penalty=rule_data.get('confidence_penalty', 0.1)
                )
                rules.append(rule)
            except Exception:
                continue  # Skip invalid rules
        
        return rules

    def _calculate_overall_score(self, violations: List[ConsistencyViolation], content: str) -> float:
        """Calculate overall consistency score."""
        if not violations:
            return 1.0
        
        # Start with perfect score
        score = 1.0
        
        # Apply penalties for violations
        for violation in violations:
            score -= violation.confidence_penalty * violation.confidence
        
        # Ensure score doesn't go below 0
        return max(score, 0.0)

    def _group_violations_by_severity(self, violations: List[ConsistencyViolation]) -> Dict[str, int]:
        """Group violations by severity level."""
        groups = {severity.value: 0 for severity in SeverityLevel}
        
        for violation in violations:
            groups[violation.severity.value] += 1
        
        return groups

    def _create_analysis_summary(self, violations: List[ConsistencyViolation], content: str) -> Dict[str, Any]:
        """Create analysis summary."""
        return {
            "content_length": len(content),
            "total_violations": len(violations),
            "critical_issues": len([v for v in violations if v.severity == SeverityLevel.CRITICAL]),
            "high_issues": len([v for v in violations if v.severity == SeverityLevel.HIGH]),
            "consistency_quality": "poor" if len(violations) > 5 else "acceptable" if len(violations) > 2 else "good",
            "most_common_issue": self._get_most_common_issue_type(violations),
            "confidence_impact": sum(v.confidence_penalty for v in violations)
        }

    def _get_most_common_issue_type(self, violations: List[ConsistencyViolation]) -> str:
        """Get the most common type of violation."""
        if not violations:
            return "none"
        
        rule_counts = {}
        for violation in violations:
            rule_id = violation.rule_id
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        
        return max(rule_counts.keys(), key=lambda k: rule_counts[k])

    def _generate_recommendations(self, violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
        """Generate recommendations for fixing violations."""
        recommendations = []
        
        if not violations:
            recommendations.append({
                "priority": "info",
                "description": "No consistency violations detected. Story maintains good internal consistency."
            })
            return recommendations
        
        # Group violations by type
        violation_types = {}
        for violation in violations:
            rule_id = violation.rule_id
            if rule_id not in violation_types:
                violation_types[rule_id] = []
            violation_types[rule_id].append(violation)
        
        # Generate type-specific recommendations
        for rule_id, rule_violations in violation_types.items():
            if rule_id == "character_attribute_consistency":
                recommendations.append({
                    "priority": "high",
                    "description": f"Review character descriptions for consistency. Found {len(rule_violations)} attribute conflicts."
                })
            elif rule_id == "timeline_consistency":
                recommendations.append({
                    "priority": "critical",
                    "description": f"Fix timeline issues. Found {len(rule_violations)} temporal conflicts that affect story logic."
                })
            elif rule_id == "plot_logic_consistency":
                recommendations.append({
                    "priority": "critical",
                    "description": f"Address plot logic problems. Found {len(rule_violations)} logical inconsistencies."
                })
            elif rule_id == "character_behavior_consistency":
                recommendations.append({
                    "priority": "medium",
                    "description": f"Review character behavior consistency. Found {len(rule_violations)} behavioral conflicts."
                })
        
        # Overall recommendations
        total_violations = len(violations)
        if total_violations > 10:
            recommendations.append({
                "priority": "critical",
                "description": "Story has numerous consistency issues. Consider major revision for coherence."
            })
        elif total_violations > 5:
            recommendations.append({
                "priority": "high",
                "description": "Story has several consistency issues that should be addressed."
            })
        
        return recommendations

    def _violation_to_dict(self, violation: ConsistencyViolation) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            "rule_id": violation.rule_id,
            "description": violation.description,
            "severity": violation.severity.value,
            "position": violation.position,
            "evidence": violation.evidence,
            "confidence": violation.confidence,
            "confidence_penalty": violation.confidence_penalty
        }

    def _create_empty_content_result(self) -> Dict[str, Any]:
        """Create result for empty content."""
        return {
            "consistency_report": {
                "total_violations": 0,
                "violations_by_severity": {severity.value: 0 for severity in SeverityLevel},
                "applied_rules": [],
                "analysis_summary": {
                    "content_length": 0,
                    "consistency_quality": "unknown",
                    "error": "Empty content provided"
                }
            },
            "violations": [],
            "overall_score": 0.0,
            "recommendations": [
                {
                    "priority": "error",
                    "description": "No content provided for consistency validation."
                }
            ]
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create result for validation errors."""
        return {
            "consistency_report": {
                "total_violations": 0,
                "violations_by_severity": {severity.value: 0 for severity in SeverityLevel},
                "applied_rules": [],
                "analysis_summary": {
                    "error": error_message,
                    "consistency_quality": "error"
                }
            },
            "violations": [],
            "overall_score": 0.0,
            "recommendations": [
                {
                    "priority": "error",
                    "description": f"Validation error: {error_message}"
                }
            ]
        }