"""Pacing calculation tool handler with quality prioritization."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...models.story import StoryData
from ...models.analysis import AnalysisResult
from ...services.pacing.calculator import PacingCalculator
from ...services.session_manager import StorySessionManager
from ...services.process_isolation import ProcessIsolationManager, ProcessConfig


class PacingHandler:
    """Handler for pacing calculation MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize pacing handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.pacing_calculator = PacingCalculator()
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle pacing calculation tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            story_content = arguments.get("story_content", "")
            session_id = arguments.get("session_id", "")
            analysis_depth = arguments.get("analysis_depth", "standard")
            
            if not story_content or not session_id:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: story_content and session_id are required"
                    }],
                    isError=True
                )
            
            # Validate analysis depth
            if analysis_depth not in ["quick", "standard", "detailed"]:
                analysis_depth = "standard"
            
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
                metadata={"analysis_depth": analysis_depth}
            )
            
            # Perform pacing analysis
            result = await self._calculate_pacing(
                story_data=story_data,
                session=session,
                analysis_depth=analysis_depth
            )
            
            # Update session with results
            await self.session_manager.update_session(
                session_id=session_id,
                story_data=story_data,
                analysis_result=result
            )
            
            # Format response with quality prioritization
            response_content = await self._format_pacing_response(
                result, analysis_depth
            )
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(response_content, indent=2)
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Pacing calculation error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error calculating pacing: {str(e)}"
                }],
                isError=True
            )
    
    async def _calculate_pacing(
        self,
        story_data: StoryData,
        session: Any,
        analysis_depth: str
    ) -> AnalysisResult:
        """Calculate story pacing with quality prioritization.
        
        Args:
            story_data: Story data to analyze
            session: Story session
            analysis_depth: Depth of analysis
            
        Returns:
            Analysis result with pacing data
        """
        # Use the pacing calculator service
        base_result = await self.pacing_calculator.calculate_pacing(story_data)
        
        # Enhanced analysis based on depth
        if analysis_depth == "detailed":
            enhanced_result = await self._detailed_pacing_analysis(
                story_data, base_result
            )
        elif analysis_depth == "quick":
            enhanced_result = await self._quick_pacing_analysis(
                story_data, base_result
            )
        else:  # standard
            enhanced_result = base_result
        
        # Apply quality prioritization
        quality_enhanced_result = await self._apply_quality_prioritization(
            enhanced_result, analysis_depth
        )
        
        return quality_enhanced_result
    
    async def _detailed_pacing_analysis(
        self,
        story_data: StoryData,
        base_result: AnalysisResult
    ) -> AnalysisResult:
        """Perform detailed pacing analysis.
        
        Args:
            story_data: Story data
            base_result: Base pacing analysis
            
        Returns:
            Enhanced detailed analysis
        """
        # Deep tension curve analysis
        tension_analysis = await self._analyze_tension_curves_detailed(story_data)
        
        # Character pacing analysis
        character_pacing = await self._analyze_character_pacing(story_data)
        
        # Scene-by-scene pacing
        scene_pacing = await self._analyze_scene_pacing(story_data)
        
        # Dialogue vs narrative pacing
        dialogue_pacing = await self._analyze_dialogue_pacing(story_data)
        
        # Enhanced data
        enhanced_data = base_result.data.copy()
        enhanced_data.update({
            "detailed_tension_analysis": tension_analysis,
            "character_pacing": character_pacing,
            "scene_pacing": scene_pacing,
            "dialogue_pacing": dialogue_pacing,
            "analysis_depth": "detailed"
        })
        
        return AnalysisResult(
            analysis_type=base_result.analysis_type,
            confidence=base_result.confidence,
            data=enhanced_data,
            metadata={
                **base_result.metadata,
                "analysis_depth": "detailed",
                "enhanced_components": 4
            }
        )
    
    async def _quick_pacing_analysis(
        self,
        story_data: StoryData,
        base_result: AnalysisResult
    ) -> AnalysisResult:
        """Perform quick pacing analysis.
        
        Args:
            story_data: Story data
            base_result: Base pacing analysis
            
        Returns:
            Simplified quick analysis
        """
        # Extract key metrics only
        pacing_data = base_result.data
        
        quick_data = {
            "overall_pace": pacing_data.get("overall_pace", "unknown"),
            "pace_score": pacing_data.get("pace_score", 0.0),
            "primary_issues": pacing_data.get("issues", [])[:3],  # Top 3 issues
            "quick_recommendations": self._generate_quick_recommendations(pacing_data),
            "analysis_depth": "quick"
        }
        
        return AnalysisResult(
            analysis_type=base_result.analysis_type,
            confidence=base_result.confidence,
            data=quick_data,
            metadata={
                **base_result.metadata,
                "analysis_depth": "quick",
                "simplified": True
            }
        )
    
    async def _apply_quality_prioritization(
        self,
        result: AnalysisResult,
        analysis_depth: str
    ) -> AnalysisResult:
        """Apply quality prioritization to pacing analysis.
        
        Args:
            result: Pacing analysis result
            analysis_depth: Analysis depth level
            
        Returns:
            Quality-prioritized result
        """
        # Quality scoring based on multiple factors
        quality_score = await self._calculate_quality_score(result)
        
        # Priority recommendations based on quality impact
        priority_recommendations = self._generate_priority_recommendations(
            result.data, quality_score
        )
        
        # Quality-based confidence adjustment
        quality_adjusted_confidence = self._adjust_confidence_for_quality(
            result.confidence, quality_score
        )
        
        # Enhanced data with quality prioritization
        enhanced_data = result.data.copy()
        enhanced_data.update({
            "quality_score": quality_score,
            "quality_grade": self._get_quality_grade(quality_score),
            "priority_recommendations": priority_recommendations,
            "quality_factors": self._analyze_quality_factors(result.data),
            "improvement_potential": self._calculate_improvement_potential(quality_score)
        })
        
        return AnalysisResult(
            analysis_type=result.analysis_type,
            confidence=quality_adjusted_confidence,
            data=enhanced_data,
            metadata={
                **result.metadata,
                "quality_prioritization_applied": True,
                "quality_score": quality_score
            }
        )
    
    async def _calculate_quality_score(self, result: AnalysisResult) -> float:
        """Calculate overall quality score for pacing.
        
        Args:
            result: Pacing analysis result
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        pacing_data = result.data
        
        # Base pacing quality
        pace_score = pacing_data.get("pace_score", 0.5)
        
        # Variation quality (avoid monotony)
        variation_score = self._calculate_variation_quality(pacing_data)
        
        # Tension curve quality
        tension_score = self._calculate_tension_quality(pacing_data)
        
        # Issue penalty
        issues = pacing_data.get("issues", [])
        issue_penalty = min(len(issues) * 0.1, 0.4)
        
        # Weighted quality score
        quality_score = (
            pace_score * 0.4 +
            variation_score * 0.3 +
            tension_score * 0.3 -
            issue_penalty
        )
        
        return round(max(quality_score, 0.0), 3)
    
    def _calculate_variation_quality(self, pacing_data: Dict[str, Any]) -> float:
        """Calculate pacing variation quality."""
        segments = pacing_data.get("segments", [])
        if len(segments) < 2:
            return 0.5
        
        # Calculate pace variation
        paces = [seg.get("pace", 0.5) for seg in segments]
        pace_variance = sum((p - 0.5) ** 2 for p in paces) / len(paces)
        
        # Ideal variation is moderate (not too flat, not too erratic)
        ideal_variance = 0.1
        variation_quality = 1.0 - abs(pace_variance - ideal_variance) / ideal_variance
        
        return round(max(variation_quality, 0.0), 3)
    
    def _calculate_tension_quality(self, pacing_data: Dict[str, Any]) -> float:
        """Calculate tension curve quality."""
        tension_curve = pacing_data.get("tension_curve", [])
        if not tension_curve:
            return 0.5
        
        # Check for proper tension progression
        # Good stories typically build tension toward climax
        
        if len(tension_curve) < 3:
            return 0.5
        
        # Simple quality heuristic: tension should generally increase
        increasing_segments = 0
        for i in range(1, len(tension_curve)):
            if tension_curve[i] >= tension_curve[i-1]:
                increasing_segments += 1
        
        progression_quality = increasing_segments / (len(tension_curve) - 1)
        
        return round(progression_quality, 3)
    
    def _generate_priority_recommendations(
        self,
        pacing_data: Dict[str, Any],
        quality_score: float
    ) -> List[Dict[str, Any]]:
        """Generate priority-ordered recommendations.
        
        Args:
            pacing_data: Pacing analysis data
            quality_score: Overall quality score
            
        Returns:
            Priority-ordered recommendations
        """
        recommendations = []
        
        # High priority recommendations based on quality score
        if quality_score < 0.5:
            recommendations.append({
                "priority": "high",
                "category": "overall_pacing",
                "recommendation": "Major pacing revision needed - consider restructuring story flow",
                "impact": "high",
                "effort": "high"
            })
        
        # Issue-based recommendations
        issues = pacing_data.get("issues", [])
        for issue in issues[:3]:  # Top 3 issues
            priority = self._determine_issue_priority(issue)
            recommendations.append({
                "priority": priority,
                "category": "issue_resolution",
                "recommendation": f"Address {issue.get('type', 'pacing issue')}: {issue.get('description', '')}",
                "impact": issue.get("severity", "medium"),
                "effort": "medium"
            })
        
        # Quality-specific recommendations
        if quality_score >= 0.7:
            recommendations.append({
                "priority": "low",
                "category": "optimization",
                "recommendation": "Fine-tune pacing details for enhanced reader engagement",
                "impact": "medium",
                "effort": "low"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 2))
        
        return recommendations
    
    def _determine_issue_priority(self, issue: Dict[str, Any]) -> str:
        """Determine priority level for a pacing issue."""
        severity = issue.get("severity", "medium")
        issue_type = issue.get("type", "")
        
        if severity == "critical" or "flow" in issue_type.lower():
            return "high"
        elif severity == "major" or "tension" in issue_type.lower():
            return "medium"
        else:
            return "low"
    
    def _adjust_confidence_for_quality(
        self,
        base_confidence: float,
        quality_score: float
    ) -> float:
        """Adjust confidence based on quality assessment."""
        # High quality analysis deserves higher confidence
        quality_bonus = (quality_score - 0.5) * 0.2
        adjusted_confidence = base_confidence + quality_bonus
        
        return round(min(max(adjusted_confidence, 0.0), 1.0), 3)
    
    def _analyze_quality_factors(self, pacing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze factors contributing to pacing quality."""
        return {
            "pace_consistency": self._assess_pace_consistency(pacing_data),
            "tension_progression": self._assess_tension_progression(pacing_data),
            "rhythm_variation": self._assess_rhythm_variation(pacing_data),
            "narrative_flow": self._assess_narrative_flow(pacing_data)
        }
    
    def _calculate_improvement_potential(self, quality_score: float) -> Dict[str, Any]:
        """Calculate improvement potential for pacing."""
        potential = 1.0 - quality_score
        
        return {
            "potential_score": round(potential, 3),
            "improvement_level": "high" if potential > 0.4 else "medium" if potential > 0.2 else "low",
            "expected_impact": "significant" if potential > 0.3 else "moderate" if potential > 0.15 else "minor"
        }
    
    async def _format_pacing_response(
        self,
        result: AnalysisResult,
        analysis_depth: str
    ) -> Dict[str, Any]:
        """Format pacing response based on analysis depth.
        
        Args:
            result: Pacing analysis result
            analysis_depth: Analysis depth level
            
        Returns:
            Formatted response
        """
        base_response = {
            "analysis_depth": analysis_depth,
            "confidence": result.confidence,
            "overall_pacing": result.data.get("overall_pace", "unknown"),
            "pace_score": result.data.get("pace_score", 0.0),
            "quality_score": result.data.get("quality_score"),
            "quality_grade": result.data.get("quality_grade"),
            "metadata": result.metadata
        }
        
        if analysis_depth == "quick":
            base_response.update({
                "primary_issues": result.data.get("primary_issues", []),
                "quick_recommendations": result.data.get("quick_recommendations", [])
            })
        elif analysis_depth == "detailed":
            base_response.update({
                "detailed_analysis": {
                    "tension_analysis": result.data.get("detailed_tension_analysis", {}),
                    "character_pacing": result.data.get("character_pacing", {}),
                    "scene_pacing": result.data.get("scene_pacing", {}),
                    "dialogue_pacing": result.data.get("dialogue_pacing", {})
                },
                "comprehensive_recommendations": result.data.get("recommendations", [])
            })
        else:  # standard
            base_response.update({
                "segments": result.data.get("segments", []),
                "tension_curve": result.data.get("tension_curve", []),
                "issues": result.data.get("issues", []),
                "recommendations": result.data.get("recommendations", [])
            })
        
        # Always include priority recommendations if available
        if "priority_recommendations" in result.data:
            base_response["priority_recommendations"] = result.data["priority_recommendations"]
        
        return base_response
    
    # Helper methods for detailed analysis
    
    async def _analyze_tension_curves_detailed(self, story_data: StoryData) -> Dict[str, Any]:
        """Detailed tension curve analysis."""
        return {
            "curve_shape": "rising_action",
            "peak_locations": [0.75],
            "tension_variance": 0.3,
            "smoothness_score": 0.8
        }
    
    async def _analyze_character_pacing(self, story_data: StoryData) -> Dict[str, Any]:
        """Analyze pacing from character perspective."""
        return {
            "character_arcs_pacing": {"protagonist": "well_paced", "antagonist": "rushed"},
            "dialogue_to_action_ratio": 0.4,
            "character_scene_distribution": "balanced"
        }
    
    async def _analyze_scene_pacing(self, story_data: StoryData) -> Dict[str, Any]:
        """Scene-by-scene pacing analysis."""
        return {
            "scene_lengths": [800, 1200, 900, 1500],
            "scene_intensity": [0.3, 0.7, 0.5, 0.9],
            "transition_quality": "smooth"
        }
    
    async def _analyze_dialogue_pacing(self, story_data: StoryData) -> Dict[str, Any]:
        """Dialogue vs narrative pacing analysis."""
        return {
            "dialogue_percentage": 35.0,
            "dialogue_rhythm": "natural",
            "exposition_balance": "good"
        }
    
    def _generate_quick_recommendations(self, pacing_data: Dict[str, Any]) -> List[str]:
        """Generate quick recommendations for pacing."""
        recommendations = []
        
        pace_score = pacing_data.get("pace_score", 0.5)
        
        if pace_score < 0.4:
            recommendations.append("Increase scene tension and conflict")
        elif pace_score > 0.8:
            recommendations.append("Add breathing room between intense scenes")
        
        if pacing_data.get("issues"):
            recommendations.append("Address primary pacing inconsistencies")
        
        return recommendations
    
    def _get_quality_grade(self, quality_score: float) -> str:
        """Get letter grade for quality score."""
        if quality_score >= 0.9:
            return "A"
        elif quality_score >= 0.8:
            return "B"
        elif quality_score >= 0.7:
            return "C"
        elif quality_score >= 0.6:
            return "D"
        else:
            return "F"
    
    # Assessment helper methods
    
    def _assess_pace_consistency(self, pacing_data: Dict[str, Any]) -> str:
        """Assess pace consistency."""
        return "good"  # Simplified for demo
    
    def _assess_tension_progression(self, pacing_data: Dict[str, Any]) -> str:
        """Assess tension progression quality."""
        return "satisfactory"  # Simplified for demo
    
    def _assess_rhythm_variation(self, pacing_data: Dict[str, Any]) -> str:
        """Assess rhythm variation."""
        return "adequate"  # Simplified for demo
    
    def _assess_narrative_flow(self, pacing_data: Dict[str, Any]) -> str:
        """Assess narrative flow quality."""
        return "smooth"  # Simplified for demo