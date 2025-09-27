"""Consistency validation tool handler with severity ratings."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...models.story import StoryData
from ...models.analysis import AnalysisResult
from ...services.consistency.validator import ConsistencyValidator
from ...services.session_manager import StorySessionManager
from ...services.process_isolation import ProcessIsolationManager, ProcessConfig


class ConsistencyHandler:
    """Handler for consistency validation MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize consistency handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.consistency_validator = ConsistencyValidator()
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle consistency validation tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            story_content = arguments.get("story_content", "")
            session_id = arguments.get("session_id", "")
            validation_scope = arguments.get("validation_scope", "all")
            
            if not story_content or not session_id:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: story_content and session_id are required"
                    }],
                    isError=True
                )
            
            # Get session
            session = await self.session_manager.get_session(session_id)
            if not session:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Error: Session {session_id} not found"
                    }],
                    isError=True
                )
            
            # Create story data
            story_data = StoryData(
                content=story_content,
                metadata={"validation_scope": validation_scope}
            )
            
            # Perform consistency validation
            result = await self._validate_consistency(
                story_data=story_data,
                session=session,
                validation_scope=validation_scope
            )
            
            # Update session with results
            await self.session_manager.update_session(
                session_id=session_id,
                story_data=story_data,
                analysis_result=result
            )
            
            # Format response
            response_content = {
                "validation_scope": validation_scope,
                "confidence": result.confidence,
                "overall_consistency": result.data.get("overall_consistency", {}),
                "violations": result.data.get("violations", []),
                "severity_breakdown": result.data.get("severity_breakdown", {}),
                "validation_summary": result.data.get("validation_summary", {}),
                "recommendations": result.data.get("recommendations", []),
                "metadata": result.metadata
            }
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(response_content, indent=2)
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Consistency validation error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error validating consistency: {str(e)}"
                }],
                isError=True
            )
    
    async def _validate_consistency(
        self,
        story_data: StoryData,
        session: Any,
        validation_scope: str
    ) -> AnalysisResult:
        """Validate story consistency with severity ratings.
        
        Args:
            story_data: Story data to validate
            session: Story session
            validation_scope: Scope of validation
            
        Returns:
            Analysis result with consistency validation
        """
        # Use the consistency validator service
        base_result = await self.consistency_validator.validate_consistency(story_data)
        
        # Filter results based on validation scope
        filtered_violations = self._filter_violations_by_scope(
            base_result.data.get("violations", []),
            validation_scope
        )
        
        # Calculate severity breakdown
        severity_breakdown = self._calculate_severity_breakdown(filtered_violations)
        
        # Generate validation summary
        validation_summary = self._generate_validation_summary(
            filtered_violations, severity_breakdown
        )
        
        # Calculate scope-specific confidence
        scope_confidence = self._calculate_scope_confidence(
            base_result.confidence, validation_scope, severity_breakdown
        )
        
        # Generate scope-specific recommendations
        recommendations = self._generate_scope_recommendations(
            filtered_violations, validation_scope, scope_confidence
        )
        
        return AnalysisResult(
            analysis_type="consistency_validation",
            confidence=scope_confidence,
            data={
                "overall_consistency": {
                    "score": scope_confidence,
                    "grade": self._get_consistency_grade(scope_confidence),
                    "total_violations": len(filtered_violations),
                    "critical_violations": len([v for v in filtered_violations if v.get("severity") == "critical"])
                },
                "violations": filtered_violations,
                "severity_breakdown": severity_breakdown,
                "validation_summary": validation_summary,
                "recommendations": recommendations
            },
            metadata={
                "validation_scope": validation_scope,
                "total_checks_performed": self._count_checks_by_scope(validation_scope),
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "validator_version": "1.0.0"
            }
        )
    
    def _filter_violations_by_scope(
        self,
        violations: List[Dict[str, Any]],
        scope: str
    ) -> List[Dict[str, Any]]:
        """Filter violations by validation scope.
        
        Args:
            violations: All violations found
            scope: Validation scope filter
            
        Returns:
            Filtered violations list
        """
        if scope == "all":
            return violations
        
        scope_mapping = {
            "character": ["character_attribute", "character_behavior", "character_development"],
            "timeline": ["timeline_consistency", "chronological_order", "temporal_logic"],
            "plot": ["plot_logic", "causality", "narrative_flow", "plot_holes"]
        }
        
        relevant_types = scope_mapping.get(scope, [])
        
        return [
            violation for violation in violations
            if violation.get("type", "") in relevant_types or scope == "all"
        ]
    
    def _calculate_severity_breakdown(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate breakdown of violations by severity.
        
        Args:
            violations: List of violations
            
        Returns:
            Severity breakdown statistics
        """
        severity_counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        
        for violation in violations:
            severity = violation.get("severity", "minor")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        total_violations = len(violations)
        severity_percentages = {}
        
        if total_violations > 0:
            for severity, count in severity_counts.items():
                severity_percentages[f"{severity}_percentage"] = round(
                    (count / total_violations) * 100, 1
                )
        
        return {
            "counts": severity_counts,
            "percentages": severity_percentages,
            "total": total_violations,
            "severity_score": self._calculate_severity_score(severity_counts)
        }
    
    def _calculate_severity_score(self, severity_counts: Dict[str, int]) -> float:
        """Calculate weighted severity score.
        
        Args:
            severity_counts: Count of violations by severity
            
        Returns:
            Weighted severity score (0.0 to 1.0, higher is worse)
        """
        weights = {"critical": 1.0, "major": 0.7, "minor": 0.3, "info": 0.1}
        
        weighted_sum = sum(
            severity_counts.get(severity, 0) * weight
            for severity, weight in weights.items()
        )
        
        total_violations = sum(severity_counts.values())
        
        if total_violations == 0:
            return 0.0
        
        # Normalize by total violations and apply logarithmic scaling
        severity_score = min(weighted_sum / (total_violations * 2), 1.0)
        
        return round(severity_score, 3)
    
    def _generate_validation_summary(
        self,
        violations: List[Dict[str, Any]],
        severity_breakdown: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of validation results.
        
        Args:
            violations: List of violations
            severity_breakdown: Severity breakdown data
            
        Returns:
            Validation summary
        """
        # Group violations by type
        violation_types = {}
        for violation in violations:
            v_type = violation.get("type", "unknown")
            if v_type not in violation_types:
                violation_types[v_type] = []
            violation_types[v_type].append(violation)
        
        # Identify most problematic areas
        problem_areas = sorted(
            violation_types.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:3]
        
        return {
            "total_violations": len(violations),
            "unique_violation_types": len(violation_types),
            "most_problematic_areas": [
                {
                    "type": area[0],
                    "count": len(area[1]),
                    "percentage": round((len(area[1]) / max(len(violations), 1)) * 100, 1)
                }
                for area in problem_areas
            ],
            "consistency_level": self._determine_consistency_level(severity_breakdown),
            "requires_attention": severity_breakdown["counts"]["critical"] > 0 or 
                                  severity_breakdown["counts"]["major"] > 3
        }
    
    def _calculate_scope_confidence(
        self,
        base_confidence: float,
        scope: str,
        severity_breakdown: Dict[str, Any]
    ) -> float:
        """Calculate confidence adjusted for validation scope.
        
        Args:
            base_confidence: Base confidence from validator
            scope: Validation scope
            severity_breakdown: Severity breakdown data
            
        Returns:
            Scope-adjusted confidence score
        """
        # Adjust confidence based on severity of violations
        severity_penalty = severity_breakdown["severity_score"] * 0.3
        adjusted_confidence = max(base_confidence - severity_penalty, 0.0)
        
        # Scope-specific adjustments
        scope_multipliers = {
            "character": 1.0,    # No adjustment for character scope
            "timeline": 0.95,    # Slightly lower confidence for timeline (harder to validate)
            "plot": 0.90,        # Lower confidence for plot logic (most complex)
            "all": 0.85          # Lower confidence for comprehensive validation
        }
        
        scope_multiplier = scope_multipliers.get(scope, 1.0)
        final_confidence = adjusted_confidence * scope_multiplier
        
        return round(min(final_confidence, 1.0), 3)
    
    def _generate_scope_recommendations(
        self,
        violations: List[Dict[str, Any]],
        scope: str,
        confidence: float
    ) -> List[str]:
        """Generate recommendations specific to validation scope.
        
        Args:
            violations: List of violations
            scope: Validation scope
            confidence: Confidence score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if confidence < 0.75:
            scope_advice = {
                "character": "Review character descriptions and behavior patterns for consistency",
                "timeline": "Verify chronological order and temporal references",
                "plot": "Check logical flow and causality between events",
                "all": "Address consistency issues across all story elements"
            }
            recommendations.append(scope_advice.get(scope, "Address identified consistency issues"))
        
        # Critical violation recommendations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            recommendations.append(
                f"Immediately address {len(critical_violations)} critical consistency issue(s)"
            )
        
        # Type-specific recommendations
        violation_types = set(v.get("type", "") for v in violations)
        
        if "character_attribute" in violation_types:
            recommendations.append("Maintain consistent character attributes throughout the story")
        
        if "timeline_consistency" in violation_types:
            recommendations.append("Create a timeline to track chronological events")
        
        if "plot_logic" in violation_types:
            recommendations.append("Ensure logical cause-and-effect relationships between events")
        
        if not recommendations:
            recommendations.append("Story consistency is good - maintain current quality standards")
        
        return recommendations
    
    def _get_consistency_grade(self, confidence: float) -> str:
        """Get letter grade for consistency score.
        
        Args:
            confidence: Confidence/consistency score
            
        Returns:
            Letter grade
        """
        if confidence >= 0.90:
            return "A"
        elif confidence >= 0.80:
            return "B"
        elif confidence >= 0.70:
            return "C"
        elif confidence >= 0.60:
            return "D"
        else:
            return "F"
    
    def _determine_consistency_level(self, severity_breakdown: Dict[str, Any]) -> str:
        """Determine overall consistency level.
        
        Args:
            severity_breakdown: Severity breakdown data
            
        Returns:
            Consistency level description
        """
        critical_count = severity_breakdown["counts"]["critical"]
        major_count = severity_breakdown["counts"]["major"]
        total_count = severity_breakdown["total"]
        
        if critical_count > 0:
            return "Poor"
        elif major_count > 5 or total_count > 15:
            return "Fair"
        elif major_count > 2 or total_count > 8:
            return "Good"
        elif total_count > 3:
            return "Very Good"
        else:
            return "Excellent"
    
    def _count_checks_by_scope(self, scope: str) -> int:
        """Count number of checks performed by scope.
        
        Args:
            scope: Validation scope
            
        Returns:
            Number of checks performed
        """
        check_counts = {
            "character": 8,   # Character-specific checks
            "timeline": 6,    # Timeline-specific checks
            "plot": 10,       # Plot logic checks
            "all": 24         # All checks combined
        }
        
        return check_counts.get(scope, 24)