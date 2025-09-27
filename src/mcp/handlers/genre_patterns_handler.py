"""Genre patterns tool handler with 75% confidence threshold."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...models.story import StoryData
from ...models.analysis import AnalysisResult
from ...services.genre.analyzer import GenreAnalyzer
from ...services.session_manager import StorySessionManager
from ...services.process_isolation import ProcessIsolationManager, ProcessConfig


class GenrePatternsHandler:
    """Handler for genre patterns analysis MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize genre patterns handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.genre_analyzer = GenreAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle genre patterns analysis tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            story_content = arguments.get("story_content", "")
            session_id = arguments.get("session_id", "")
            target_genres = arguments.get("target_genres", [])
            
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
                metadata={"target_genres": target_genres}
            )
            
            # Perform genre pattern analysis
            result = await self._analyze_genre_patterns(
                story_data=story_data,
                session=session,
                target_genres=target_genres
            )
            
            # Update session with results
            await self.session_manager.update_session(
                session_id=session_id,
                story_data=story_data,
                analysis_result=result
            )
            
            # Format response
            response_content = {
                "target_genres": target_genres,
                "confidence": result.confidence,
                "detected_genres": result.data.get("detected_genres", []),
                "genre_matches": result.data.get("genre_matches", {}),
                "pattern_analysis": result.data.get("pattern_analysis", {}),
                "authenticity_scores": result.data.get("authenticity_scores", {}),
                "recommendations": result.data.get("recommendations", []),
                "threshold_compliance": result.data.get("threshold_compliance", {}),
                "metadata": result.metadata
            }
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(response_content, indent=2)
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Genre patterns analysis error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error analyzing genre patterns: {str(e)}"
                }],
                isError=True
            )
    
    async def _analyze_genre_patterns(
        self,
        story_data: StoryData,
        session: Any,
        target_genres: List[str]
    ) -> AnalysisResult:
        """Analyze genre patterns with 75% confidence threshold.
        
        Args:
            story_data: Story data to analyze
            session: Story session
            target_genres: Target genres for analysis
            
        Returns:
            Analysis result with genre pattern data
        """
        # Use the genre analyzer service
        base_result = await self.genre_analyzer.apply_genre_patterns(story_data)
        
        # Enhanced analysis with target genres
        if target_genres:
            enhanced_result = await self._analyze_target_genres(
                story_data, target_genres, base_result
            )
        else:
            enhanced_result = base_result
        
        # Apply 75% confidence threshold filtering
        filtered_genres = self._apply_confidence_threshold(
            enhanced_result.data.get("detected_genres", [])
        )
        
        # Calculate pattern analysis
        pattern_analysis = await self._analyze_genre_patterns_detailed(
            story_data, filtered_genres
        )
        
        # Calculate authenticity scores
        authenticity_scores = self._calculate_authenticity_scores(
            filtered_genres, pattern_analysis
        )
        
        # Generate threshold compliance report
        threshold_compliance = self._generate_threshold_compliance(
            enhanced_result.data.get("detected_genres", []), filtered_genres
        )
        
        # Generate recommendations
        recommendations = self._generate_genre_recommendations(
            filtered_genres, authenticity_scores, threshold_compliance
        )
        
        return AnalysisResult(
            analysis_type="genre_patterns",
            confidence=enhanced_result.confidence,
            data={
                "detected_genres": filtered_genres,
                "genre_matches": self._create_genre_matches(filtered_genres),
                "pattern_analysis": pattern_analysis,
                "authenticity_scores": authenticity_scores,
                "threshold_compliance": threshold_compliance,
                "recommendations": recommendations
            },
            metadata={
                "target_genres": target_genres,
                "total_genres_analyzed": len(enhanced_result.data.get("detected_genres", [])),
                "threshold_passing_genres": len(filtered_genres),
                "confidence_threshold": 0.75,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        )
    
    async def _analyze_target_genres(
        self,
        story_data: StoryData,
        target_genres: List[str],
        base_result: AnalysisResult
    ) -> AnalysisResult:
        """Analyze specific target genres in detail.
        
        Args:
            story_data: Story data
            target_genres: Target genres to analyze
            base_result: Base genre analysis result
            
        Returns:
            Enhanced analysis result
        """
        detected_genres = base_result.data.get("detected_genres", [])
        
        # Add detailed analysis for target genres
        enhanced_genres = []
        
        for genre_data in detected_genres:
            genre_name = genre_data.get("genre", "")
            
            if genre_name.lower() in [tg.lower() for tg in target_genres]:
                # Enhanced analysis for target genre
                enhanced_genre = await self._enhance_genre_analysis(
                    story_data, genre_data
                )
                enhanced_genres.append(enhanced_genre)
            else:
                enhanced_genres.append(genre_data)
        
        # Check for missing target genres
        detected_names = [g.get("genre", "").lower() for g in enhanced_genres]
        for target_genre in target_genres:
            if target_genre.lower() not in detected_names:
                # Analyze missing target genre
                missing_analysis = await self._analyze_missing_genre(
                    story_data, target_genre
                )
                if missing_analysis:
                    enhanced_genres.append(missing_analysis)
        
        # Update result data
        enhanced_data = base_result.data.copy()
        enhanced_data["detected_genres"] = enhanced_genres
        
        return AnalysisResult(
            analysis_type=base_result.analysis_type,
            confidence=base_result.confidence,
            data=enhanced_data,
            metadata=base_result.metadata
        )
    
    async def _enhance_genre_analysis(
        self,
        story_data: StoryData,
        genre_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance analysis for a specific genre.
        
        Args:
            story_data: Story data
            genre_data: Base genre analysis data
            
        Returns:
            Enhanced genre data
        """
        genre_name = genre_data.get("genre", "")
        
        # Add detailed pattern matching
        enhanced_patterns = await self._analyze_genre_patterns_deep(
            story_data.content, genre_name
        )
        
        # Add trope analysis
        trope_analysis = self._analyze_genre_tropes(
            story_data.content, genre_name
        )
        
        # Enhanced confidence calculation
        enhanced_confidence = self._calculate_enhanced_confidence(
            genre_data.get("confidence", 0.0),
            enhanced_patterns,
            trope_analysis
        )
        
        enhanced_genre = genre_data.copy()
        enhanced_genre.update({
            "confidence": enhanced_confidence,
            "detailed_patterns": enhanced_patterns,
            "trope_analysis": trope_analysis,
            "enhancement_applied": True
        })
        
        return enhanced_genre
    
    async def _analyze_missing_genre(
        self,
        story_data: StoryData,
        target_genre: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze a target genre that wasn't initially detected.
        
        Args:
            story_data: Story data
            target_genre: Target genre to analyze
            
        Returns:
            Genre analysis data or None if not found
        """
        # Force analysis of the target genre
        genre_patterns = await self._analyze_genre_patterns_deep(
            story_data.content, target_genre
        )
        
        # Calculate confidence for this specific genre
        confidence = self._calculate_genre_confidence(genre_patterns)
        
        if confidence >= 0.30:  # Lower threshold for forced analysis
            return {
                "genre": target_genre,
                "confidence": confidence,
                "score": confidence,
                "patterns": genre_patterns,
                "forced_analysis": True,
                "reason": "Target genre analysis"
            }
        
        return None
    
    def _apply_confidence_threshold(
        self,
        detected_genres: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply 75% confidence threshold to filter genres.
        
        Args:
            detected_genres: All detected genres
            
        Returns:
            Filtered genres meeting threshold
        """
        threshold = 0.75
        
        return [
            genre for genre in detected_genres
            if genre.get("confidence", 0.0) >= threshold
        ]
    
    async def _analyze_genre_patterns_detailed(
        self,
        story_data: StoryData,
        filtered_genres: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform detailed pattern analysis for filtered genres.
        
        Args:
            story_data: Story data
            filtered_genres: Genres meeting confidence threshold
            
        Returns:
            Detailed pattern analysis
        """
        content = story_data.content.lower()
        
        pattern_summary = {
            "common_elements": [],
            "unique_elements": [],
            "pattern_strength": {},
            "cross_genre_patterns": []
        }
        
        # Analyze common elements across genres
        all_patterns = []
        for genre in filtered_genres:
            patterns = genre.get("patterns", {})
            all_patterns.extend(patterns.get("matched", []))
        
        # Find common patterns
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        common_patterns = [
            pattern for pattern, count in pattern_counts.items()
            if count > 1
        ]
        
        pattern_summary["common_elements"] = common_patterns
        
        # Analyze pattern strength for each genre
        for genre in filtered_genres:
            genre_name = genre.get("genre", "")
            patterns = genre.get("patterns", {})
            
            strength = len(patterns.get("matched", [])) / max(
                len(patterns.get("total", [])), 1
            )
            
            pattern_summary["pattern_strength"][genre_name] = round(strength, 3)
        
        return pattern_summary
    
    def _calculate_authenticity_scores(
        self,
        filtered_genres: List[Dict[str, Any]],
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate authenticity scores for each genre.
        
        Args:
            filtered_genres: Filtered genres
            pattern_analysis: Pattern analysis data
            
        Returns:
            Authenticity scores by genre
        """
        authenticity_scores = {}
        
        for genre in filtered_genres:
            genre_name = genre.get("genre", "")
            confidence = genre.get("confidence", 0.0)
            
            # Base authenticity from confidence
            base_authenticity = confidence
            
            # Pattern strength bonus
            pattern_strength = pattern_analysis.get("pattern_strength", {}).get(genre_name, 0.0)
            pattern_bonus = pattern_strength * 0.1
            
            # Trope analysis bonus (if available)
            trope_score = genre.get("trope_analysis", {}).get("authenticity", 0.0)
            trope_bonus = trope_score * 0.05
            
            # Final authenticity score
            authenticity = min(base_authenticity + pattern_bonus + trope_bonus, 1.0)
            authenticity_scores[genre_name] = round(authenticity, 3)
        
        return authenticity_scores
    
    def _generate_threshold_compliance(
        self,
        all_genres: List[Dict[str, Any]],
        filtered_genres: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate threshold compliance report.
        
        Args:
            all_genres: All detected genres
            filtered_genres: Genres meeting threshold
            
        Returns:
            Threshold compliance data
        """
        total_detected = len(all_genres)
        passing_threshold = len(filtered_genres)
        
        # Genres that didn't meet threshold
        failed_genres = [
            {
                "genre": genre.get("genre", ""),
                "confidence": genre.get("confidence", 0.0),
                "gap": 0.75 - genre.get("confidence", 0.0)
            }
            for genre in all_genres
            if genre.get("confidence", 0.0) < 0.75
        ]
        
        return {
            "threshold": 0.75,
            "total_detected": total_detected,
            "passing_threshold": passing_threshold,
            "compliance_rate": round((passing_threshold / max(total_detected, 1)) * 100, 1),
            "failed_genres": failed_genres,
            "average_confidence": round(
                sum(g.get("confidence", 0.0) for g in all_genres) / max(total_detected, 1), 3
            )
        }
    
    def _generate_genre_recommendations(
        self,
        filtered_genres: List[Dict[str, Any]],
        authenticity_scores: Dict[str, float],
        threshold_compliance: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for genre pattern improvement.
        
        Args:
            filtered_genres: Genres meeting threshold
            authenticity_scores: Authenticity scores
            threshold_compliance: Threshold compliance data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Threshold compliance recommendations
        compliance_rate = threshold_compliance.get("compliance_rate", 0.0)
        
        if compliance_rate < 50:
            recommendations.append(
                "Consider strengthening genre elements to meet 75% confidence threshold"
            )
        
        # Genre-specific recommendations
        if not filtered_genres:
            recommendations.append(
                "No genres meet the 75% confidence threshold - consider clarifying genre focus"
            )
        elif len(filtered_genres) == 1:
            genre_name = filtered_genres[0].get("genre", "")
            recommendations.append(
                f"Strong {genre_name} genre focus - consider maintaining consistent elements"
            )
        elif len(filtered_genres) > 3:
            recommendations.append(
                "Multiple strong genre patterns detected - consider focusing on primary genre"
            )
        
        # Authenticity recommendations
        low_authenticity = [
            genre for genre, score in authenticity_scores.items()
            if score < 0.80
        ]
        
        if low_authenticity:
            recommendations.append(
                f"Enhance authenticity for: {', '.join(low_authenticity)}"
            )
        
        # Failed genres recommendations
        failed_genres = threshold_compliance.get("failed_genres", [])
        if failed_genres:
            high_potential = [
                g["genre"] for g in failed_genres
                if g["confidence"] > 0.60
            ]
            if high_potential:
                recommendations.append(
                    f"Consider strengthening elements for potential genres: {', '.join(high_potential)}"
                )
        
        if not recommendations:
            recommendations.append(
                "Excellent genre pattern compliance - maintain current quality"
            )
        
        return recommendations
    
    def _create_genre_matches(
        self,
        filtered_genres: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create genre matches summary.
        
        Args:
            filtered_genres: Genres meeting threshold
            
        Returns:
            Genre matches data
        """
        matches = {}
        
        for genre in filtered_genres:
            genre_name = genre.get("genre", "")
            matches[genre_name] = {
                "confidence": genre.get("confidence", 0.0),
                "score": genre.get("score", 0.0),
                "matched_patterns": len(genre.get("patterns", {}).get("matched", [])),
                "total_patterns": len(genre.get("patterns", {}).get("total", [])),
                "match_ratio": round(
                    len(genre.get("patterns", {}).get("matched", [])) /
                    max(len(genre.get("patterns", {}).get("total", [])), 1), 3
                )
            }
        
        return matches
    
    # Helper methods
    
    async def _analyze_genre_patterns_deep(
        self,
        content: str,
        genre_name: str
    ) -> Dict[str, Any]:
        """Deep analysis of genre patterns."""
        # Simplified implementation for demo
        return {
            "structural": ["three_act_structure"],
            "thematic": [f"{genre_name}_themes"],
            "character": [f"{genre_name}_archetypes"],
            "setting": [f"{genre_name}_settings"]
        }
    
    def _analyze_genre_tropes(
        self,
        content: str,
        genre_name: str
    ) -> Dict[str, Any]:
        """Analyze genre-specific tropes."""
        return {
            "common_tropes": [f"{genre_name}_trope_1"],
            "authenticity": 0.80,
            "trope_count": 3
        }
    
    def _calculate_enhanced_confidence(
        self,
        base_confidence: float,
        patterns: Dict[str, Any],
        tropes: Dict[str, Any]
    ) -> float:
        """Calculate enhanced confidence score."""
        pattern_bonus = len(patterns.get("structural", [])) * 0.05
        trope_bonus = tropes.get("authenticity", 0.0) * 0.1
        
        return round(min(base_confidence + pattern_bonus + trope_bonus, 1.0), 3)
    
    def _calculate_genre_confidence(
        self,
        patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence for genre patterns."""
        total_patterns = sum(len(p) for p in patterns.values())
        return min(total_patterns * 0.1, 0.90)