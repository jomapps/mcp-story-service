"""Unit tests for narrative analysis algorithms with 75% threshold testing (T048)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services.narrative.analyzer import NarrativeAnalyzer
from src.models.story import StoryData, StoryArc
from src.models.analysis import AnalysisResult
from src.models.narrative_beat import NarrativeBeat


class TestNarrativeAnalyzer:
    """Unit tests for NarrativeAnalyzer algorithms."""
    
    @pytest.fixture
    def narrative_analyzer(self):
        """Create NarrativeAnalyzer instance for testing."""
        return NarrativeAnalyzer()
    
    @pytest.fixture
    def well_structured_story(self):
        """Sample well-structured story for testing."""
        return StoryData(
            content="""
            Detective Sarah Chen receives a call about a murdered corporate executive. 
            As she investigates, she discovers the victim was about to expose a massive corruption scheme.
            The deeper she digs, the more dangerous it becomes as powerful people try to stop her.
            When her own partner betrays her, Sarah realizes she's completely alone.
            In a final confrontation, she brings down the conspiracy but at great personal cost.
            """,
            metadata={
                "genre": "thriller",
                "project_id": "well-structured-test"
            }
        )
    
    @pytest.fixture
    def poorly_structured_story(self):
        """Sample poorly structured story for testing."""
        return StoryData(
            content="""
            Some things happen. A person does stuff. There might be conflict.
            Everything works out somehow. The end.
            """,
            metadata={
                "genre": "unknown",
                "project_id": "poorly-structured-test"
            }
        )
    
    @pytest.fixture
    def complex_story(self):
        """Sample complex multi-act story for testing."""
        return StoryData(
            content="""
            Act I: Young Luke Skywalker discovers his true heritage when droids arrive at his farm.
            His aunt and uncle are killed, forcing him to join Obi-Wan on a rescue mission.
            Act II: Luke learns about the Force while training. The group rescues Princess Leia.
            They discover the Death Star plans and the weakness in the space station.
            Act III: Luke joins the desperate attack on the Death Star. Using the Force,
            he destroys the ultimate weapon and deals a major blow to the Empire.
            """,
            metadata={
                "genre": "sci-fi",
                "project_id": "complex-story-test"
            }
        )
    
    @pytest.mark.asyncio
    async def test_analyze_story_structure_three_act_identification(
        self, narrative_analyzer, well_structured_story
    ):
        """Test three-act structure identification with confidence scoring."""
        result = await narrative_analyzer.analyze_story_structure(well_structured_story)
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "story_structure"
        assert "arc_analysis" in result.data
        
        arc_analysis = result.data["arc_analysis"]
        
        # Verify act structure identification
        assert "act_structure" in arc_analysis
        act_structure = arc_analysis["act_structure"]
        
        assert "act_one" in act_structure
        assert "act_two" in act_structure
        assert "act_three" in act_structure
        
        # Verify act boundaries
        act_one = act_structure["act_one"]
        act_two = act_structure["act_two"]
        act_three = act_structure["act_three"]
        
        assert act_one["start_position"] == 0.0
        assert act_one["end_position"] <= 0.3  # First act typically 25-30%
        assert act_three["start_position"] >= 0.7  # Third act typically 70-75%
        assert act_three["end_position"] == 1.0
        
        # Verify confidence scoring meets threshold
        assert "confidence_score" in act_structure
        confidence = act_structure["confidence_score"]
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.75  # Should meet 75% threshold for well-structured story
    
    @pytest.mark.asyncio
    async def test_analyze_story_structure_low_confidence_detection(
        self, narrative_analyzer, poorly_structured_story
    ):
        """Test detection of poor structure with appropriate low confidence."""
        result = await narrative_analyzer.analyze_story_structure(poorly_structured_story)
        
        assert isinstance(result, AnalysisResult)
        arc_analysis = result.data["arc_analysis"]
        act_structure = arc_analysis["act_structure"]
        
        # Should detect poor structure with low confidence
        confidence = act_structure["confidence_score"]
        assert confidence < 0.75  # Should NOT meet 75% threshold
        assert confidence >= 0.0  # But should still be valid
        
        # Should provide improvement suggestions
        if "recommendations" in arc_analysis:
            recommendations = arc_analysis["recommendations"]
            assert len(recommendations) > 0
            
            # Should suggest structural improvements
            rec_text = " ".join(recommendations).lower()
            structural_keywords = ["structure", "act", "conflict", "resolution", "character"]
            assert any(keyword in rec_text for keyword in structural_keywords)
    
    @pytest.mark.asyncio
    async def test_turning_points_identification_algorithm(
        self, narrative_analyzer, complex_story
    ):
        """Test turning points identification algorithm."""
        result = await narrative_analyzer.analyze_story_structure(complex_story)
        
        arc_analysis = result.data["arc_analysis"]
        
        # Should identify turning points
        assert "turning_points" in arc_analysis
        turning_points = arc_analysis["turning_points"]
        
        assert isinstance(turning_points, list)
        assert len(turning_points) >= 2  # At least plot point 1 and 2
        
        # Verify turning point structure
        for tp in turning_points:
            assert "position" in tp
            assert "type" in tp
            assert "description" in tp
            assert "confidence" in tp
            
            # Position should be valid
            assert 0.0 <= tp["position"] <= 1.0
            
            # Confidence should be valid
            assert 0.0 <= tp["confidence"] <= 1.0
        
        # Turning points should be ordered by position
        positions = [tp["position"] for tp in turning_points]
        assert positions == sorted(positions)
        
        # Should identify key turning point types
        tp_types = [tp["type"] for tp in turning_points]
        expected_types = ["plot_point_1", "midpoint", "plot_point_2", "climax"]
        identified_types = [t for t in expected_types if t in tp_types]
        assert len(identified_types) >= 2  # At least 2 key turning points
    
    @pytest.mark.asyncio
    async def test_genre_compliance_analysis(self, narrative_analyzer, well_structured_story):
        """Test genre-specific compliance analysis."""
        result = await narrative_analyzer.analyze_story_structure(well_structured_story)
        
        arc_analysis = result.data["arc_analysis"]
        
        # Should include genre compliance if genre specified
        if "genre_compliance" in arc_analysis:
            compliance = arc_analysis["genre_compliance"]
            
            assert "authenticity_score" in compliance
            assert "meets_threshold" in compliance
            assert "conventions_met" in compliance
            assert "conventions_missing" in compliance
            
            # Authenticity score should be valid
            auth_score = compliance["authenticity_score"]
            assert 0.0 <= auth_score <= 1.0
            
            # Threshold check should be boolean
            assert isinstance(compliance["meets_threshold"], bool)
            
            # Should have identified some conventions
            assert isinstance(compliance["conventions_met"], list)
            assert isinstance(compliance["conventions_missing"], list)
    
    @pytest.mark.asyncio
    async def test_pacing_analysis_algorithm(self, narrative_analyzer, complex_story):
        """Test story pacing analysis algorithm."""
        result = await narrative_analyzer.analyze_story_structure(complex_story)
        
        arc_analysis = result.data["arc_analysis"]
        
        # Should include pacing analysis
        if "pacing_analysis" in arc_analysis:
            pacing = arc_analysis["pacing_analysis"]
            
            assert "tension_curve" in pacing
            assert "pacing_issues" in pacing
            assert "suggested_improvements" in pacing
            assert "confidence_score" in pacing
            
            # Tension curve should be valid
            tension_curve = pacing["tension_curve"]
            assert isinstance(tension_curve, list)
            assert len(tension_curve) > 0
            
            # All tension values should be valid
            for tension_value in tension_curve:
                assert 0.0 <= tension_value <= 1.0
            
            # Pacing confidence should be valid
            pacing_confidence = pacing["confidence_score"]
            assert 0.0 <= pacing_confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_validation_algorithm(
        self, narrative_analyzer, well_structured_story, poorly_structured_story
    ):
        """Test confidence threshold validation algorithm."""
        # Test high-quality story
        good_result = await narrative_analyzer.analyze_story_structure(well_structured_story)
        good_confidence = good_result.confidence
        
        # Test poor-quality story
        poor_result = await narrative_analyzer.analyze_story_structure(poorly_structured_story)
        poor_confidence = poor_result.confidence
        
        # Well-structured story should have higher confidence
        assert good_confidence > poor_confidence
        
        # Well-structured story should meet threshold
        assert good_confidence >= 0.75
        
        # Poor story should not meet threshold
        assert poor_confidence < 0.75
        
        # Test threshold boundary cases
        threshold_cases = [
            {"threshold": 0.5, "expected_pass": True},
            {"threshold": 0.75, "expected_pass": True},
            {"threshold": 0.9, "expected_pass": False}  # Very high threshold
        ]
        
        for case in threshold_cases:
            meets_threshold = good_confidence >= case["threshold"]
            assert meets_threshold == case["expected_pass"]
    
    @pytest.mark.asyncio
    async def test_narrative_beat_extraction_algorithm(
        self, narrative_analyzer, complex_story
    ):
        """Test narrative beat extraction and analysis algorithm."""
        result = await narrative_analyzer.analyze_story_structure(complex_story)
        
        # Should extract narrative beats
        if hasattr(result, 'narrative_beats') or 'narrative_beats' in result.data:
            beats = result.data.get('narrative_beats', getattr(result, 'narrative_beats', []))
            
            assert isinstance(beats, list)
            
            for beat in beats:
                # Each beat should have required fields
                assert "position" in beat
                assert "type" in beat
                assert "emotional_impact" in beat
                assert "tension_level" in beat
                
                # Values should be in valid ranges
                assert 0.0 <= beat["position"] <= 1.0
                assert 0.0 <= beat["emotional_impact"] <= 1.0
                assert 0.0 <= beat["tension_level"] <= 1.0
                
                # Beat type should be valid
                valid_beat_types = [
                    "opening", "inciting_incident", "plot_point_1", "midpoint",
                    "plot_point_2", "climax", "resolution", "character_moment",
                    "action_sequence", "revelation", "setback"
                ]
                assert beat["type"] in valid_beat_types
    
    @pytest.mark.asyncio
    async def test_algorithm_error_handling(self, narrative_analyzer):
        """Test algorithm error handling for edge cases."""
        # Test with empty content
        empty_story = StoryData(
            content="",
            metadata={"project_id": "empty-test"}
        )
        
        result = await narrative_analyzer.analyze_story_structure(empty_story)
        
        # Should handle gracefully
        assert isinstance(result, AnalysisResult)
        assert result.confidence < 0.5  # Low confidence for empty content
        
        # Test with very short content
        short_story = StoryData(
            content="Short.",
            metadata={"project_id": "short-test"}
        )
        
        result = await narrative_analyzer.analyze_story_structure(short_story)
        assert isinstance(result, AnalysisResult)
        assert result.confidence < 0.75  # Should not meet threshold
        
        # Test with malformed content
        malformed_story = StoryData(
            content="@#$%^&*()_+ random symbols and 123456 numbers",
            metadata={"project_id": "malformed-test"}
        )
        
        result = await narrative_analyzer.analyze_story_structure(malformed_story)
        assert isinstance(result, AnalysisResult)
        assert 0.0 <= result.confidence <= 1.0  # Should still return valid confidence
    
    @pytest.mark.asyncio
    async def test_algorithm_performance_with_long_content(self, narrative_analyzer):
        """Test algorithm performance with long story content."""
        # Create long story content
        long_content = """
        This is a very long story with multiple acts and complex structure.
        """ * 1000  # Repeat to create long content
        
        long_story = StoryData(
            content=long_content,
            metadata={"project_id": "performance-test"}
        )
        
        import time
        start_time = time.time()
        
        result = await narrative_analyzer.analyze_story_structure(long_story)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time
        assert processing_time < 5.0  # Should complete within 5 seconds
        
        # Should still produce valid results
        assert isinstance(result, AnalysisResult)
        assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_algorithm_consistency_across_runs(self, narrative_analyzer, well_structured_story):
        """Test algorithm consistency across multiple runs."""
        results = []
        
        # Run analysis multiple times
        for _ in range(3):
            result = await narrative_analyzer.analyze_story_structure(well_structured_story)
            results.append(result)
        
        # Results should be consistent
        confidences = [r.confidence for r in results]
        
        # Confidence should not vary significantly
        max_confidence = max(confidences)
        min_confidence = min(confidences)
        confidence_variance = max_confidence - min_confidence
        
        assert confidence_variance < 0.1  # Should be consistent within 10%
        
        # All should meet or fail threshold consistently
        threshold_results = [c >= 0.75 for c in confidences]
        assert len(set(threshold_results)) == 1  # All same result
    
    @pytest.mark.asyncio
    async def test_algorithm_integration_with_external_services(self, narrative_analyzer):
        """Test algorithm integration with external validation services."""
        story = StoryData(
            content="Test story for external validation",
            metadata={"project_id": "external-validation-test"}
        )
        
        # Mock external service integration
        with patch('src.lib.integration_manager.IntegrationManager.get_external_validation') as mock_external:
            mock_external.return_value = {
                "validation_score": 0.85,
                "external_confidence": 0.9,
                "recommendations": ["Good structure", "Clear progression"]
            }
            
            result = await narrative_analyzer.analyze_story_structure(story)
            
            # Should incorporate external validation
            assert isinstance(result, AnalysisResult)
            
            # Confidence might be influenced by external validation
            assert 0.0 <= result.confidence <= 1.0
            
        # Test graceful handling of external service failure
        with patch('src.lib.integration_manager.IntegrationManager.get_external_validation') as mock_external:
            mock_external.side_effect = Exception("External service error")
            
            result = await narrative_analyzer.analyze_story_structure(story)
            
            # Should still complete successfully
            assert isinstance(result, AnalysisResult)
            assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_confidence_factor_decomposition(self, narrative_analyzer, well_structured_story):
        """Test decomposition of confidence factors for transparency."""
        result = await narrative_analyzer.analyze_story_structure(well_structured_story)
        
        # Should provide confidence factor breakdown
        if hasattr(result, 'metadata') and result.metadata:
            metadata = result.metadata
            
            if "confidence_factors" in metadata:
                factors = metadata["confidence_factors"]
                
                # Expected confidence factors
                expected_factors = [
                    "structure_clarity",
                    "character_development",
                    "pacing_consistency",
                    "genre_authenticity",
                    "narrative_coherence"
                ]
                
                for factor in expected_factors:
                    if factor in factors:
                        factor_score = factors[factor]
                        assert 0.0 <= factor_score <= 1.0
                
                # Overall confidence should relate to factor scores
                if len(factors) > 0:
                    avg_factor_score = sum(factors.values()) / len(factors)
                    confidence_diff = abs(result.confidence - avg_factor_score)
                    assert confidence_diff < 0.2  # Should be reasonably related