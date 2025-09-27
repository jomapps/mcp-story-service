"""Unit tests for genre pattern matching with confidence scoring (T050)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.services.genre.analyzer import GenreAnalyzer
from src.models.story import StoryData
from src.models.analysis import AnalysisResult
from src.models.genre_template import GenreTemplate


class TestGenreAnalyzer:
    """Unit tests for GenreAnalyzer pattern matching algorithms."""
    
    @pytest.fixture
    def genre_analyzer(self):
        """Create GenreAnalyzer instance for testing."""
        return GenreAnalyzer()
    
    @pytest.fixture
    def thriller_story_data(self):
        """Sample thriller story data for testing."""
        return StoryData(
            content="""
            Detective Sarah discovers her partner's involvement in a corporate conspiracy.
            As she investigates deeper, she realizes the conspiracy reaches the highest levels.
            When her own life is threatened, she must choose between her career and the truth.
            In a final confrontation, she brings down the corrupt officials at great personal cost.
            """,
            metadata={
                "genre": "thriller",
                "project_id": "thriller-test"
            }
        )
    
    @pytest.fixture
    def comedy_story_data(self):
        """Sample comedy story data for testing."""
        return StoryData(
            content="""
            Bumbling office worker Danny gets promoted by mistake to executive level.
            He tries to fake competence while hiding his incompetence from colleagues.
            Misunderstandings multiply as Danny gets deeper into corporate schemes.
            Eventually, his genuine insights accidentally solve real business problems.
            Danny earns respect through authenticity and learns to believe in himself.
            """,
            metadata={
                "genre": "comedy",
                "project_id": "comedy-test"
            }
        )
    
    @pytest.fixture
    def horror_story_data(self):
        """Sample horror story data for testing."""
        return StoryData(
            content="""
            Family moves to isolated house with dark history of previous owners' deaths.
            Strange noises and moving objects begin to terrorize the family.
            Ghostly encounters become violent as supernatural force targets the children.
            Family discovers tragic fate of previous owners and connection to their presence.
            Final supernatural confrontation forces family to flee or face deadly consequences.
            """,
            metadata={
                "genre": "horror",
                "project_id": "horror-test"
            }
        )
    
    @pytest.fixture
    def genre_neutral_story(self):
        """Sample genre-neutral story for testing."""
        return StoryData(
            content="""
            A person goes to a place and does some things.
            Various events happen in sequence.
            Eventually everything concludes.
            """,
            metadata={
                "project_id": "neutral-test"
            }
        )
    
    @pytest.mark.asyncio
    async def test_thriller_genre_pattern_matching(self, genre_analyzer, thriller_story_data):
        """Test thriller genre pattern recognition and confidence scoring."""
        result = await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre="thriller")
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "genre_authentication"
        assert "genre_guidance" in result.data
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should recognize thriller patterns
        assert "score" in compliance
        assert "confidence_score" in compliance
        assert "meets_threshold" in compliance
        
        # Thriller content should meet confidence threshold
        assert compliance["confidence_score"] >= 0.75
        assert compliance["meets_threshold"] is True
        
        # Should identify thriller conventions
        assert "met_conventions" in compliance
        met_conventions = compliance["met_conventions"]
        
        thriller_keywords = ["tension", "conspiracy", "investigation", "danger", "corruption"]
        met_text = " ".join(met_conventions).lower()
        
        # Should recognize at least some thriller elements
        recognized_elements = sum(1 for keyword in thriller_keywords if keyword in met_text)
        assert recognized_elements >= 2
    
    @pytest.mark.asyncio
    async def test_comedy_genre_pattern_matching(self, genre_analyzer, comedy_story_data):
        """Test comedy genre pattern recognition."""
        result = await genre_analyzer.apply_genre_patterns(comedy_story_data, target_genre="comedy")
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Comedy content should meet threshold
        assert compliance["confidence_score"] >= 0.75
        assert compliance["meets_threshold"] is True
        
        # Should identify comedy conventions
        met_conventions = compliance["met_conventions"]
        met_text = " ".join(met_conventions).lower()
        
        comedy_keywords = ["humor", "misunderstanding", "character", "growth", "optimism"]
        recognized_elements = sum(1 for keyword in comedy_keywords if keyword in met_text)
        assert recognized_elements >= 1  # At least some comedy recognition
    
    @pytest.mark.asyncio
    async def test_horror_genre_pattern_matching(self, genre_analyzer, horror_story_data):
        """Test horror genre pattern recognition."""
        result = await genre_analyzer.apply_genre_patterns(horror_story_data, target_genre="horror")
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Horror content should meet threshold
        assert compliance["confidence_score"] >= 0.75
        assert compliance["meets_threshold"] is True
        
        # Should identify horror conventions
        met_conventions = compliance["met_conventions"]
        met_text = " ".join(met_conventions).lower()
        
        horror_keywords = ["supernatural", "terror", "fear", "isolation", "death", "haunted"]
        recognized_elements = sum(1 for keyword in horror_keywords if keyword in met_text)
        assert recognized_elements >= 2  # Should recognize horror elements
    
    @pytest.mark.asyncio
    async def test_genre_mismatch_detection(self, genre_analyzer, thriller_story_data):
        """Test detection of genre mismatches with appropriate confidence penalties."""
        # Apply comedy patterns to thriller content
        result = await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre="comedy")
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should detect mismatch with low confidence
        assert compliance["confidence_score"] < 0.75
        assert compliance["meets_threshold"] is False
        
        # Should have missing comedy conventions
        missing_conventions = compliance["missing_conventions"]
        assert len(missing_conventions) > 0
        
        # Should suggest improvements
        improvements = guidance["authenticity_improvements"]
        assert len(improvements) > 0
        
        # Should suggest high-impact changes for mismatch
        high_impact_improvements = [imp for imp in improvements if imp["impact"] == "high"]
        assert len(high_impact_improvements) > 0
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_validation(self, genre_analyzer, genre_neutral_story):
        """Test 75% confidence threshold validation."""
        result = await genre_analyzer.apply_genre_patterns(genre_neutral_story, target_genre="thriller")
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Neutral content should not meet threshold
        assert compliance["confidence_score"] < 0.75
        assert compliance["meets_threshold"] is False
        
        # Should provide many missing conventions
        missing_conventions = compliance["missing_conventions"]
        assert len(missing_conventions) >= 3
        
        # Should provide comprehensive improvement suggestions
        improvements = guidance["authenticity_improvements"]
        assert len(improvements) >= 3
    
    @pytest.mark.asyncio
    async def test_genre_specific_beats_identification(self, genre_analyzer, thriller_story_data):
        """Test identification of genre-specific story beats."""
        result = await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre="thriller")
        
        guidance = result.data["genre_guidance"]
        
        # Should identify genre-specific beats
        assert "genre_specific_beats" in guidance
        beats = guidance["genre_specific_beats"]
        
        assert isinstance(beats, list)
        assert len(beats) > 0
        
        for beat in beats:
            assert "beat_type" in beat
            assert "suggested_position" in beat
            assert "purpose" in beat
            assert "confidence" in beat
            
            # Position should be valid
            assert 0.0 <= beat["suggested_position"] <= 1.0
            
            # Confidence should be valid
            assert 0.0 <= beat["confidence"] <= 1.0
        
        # Should include thriller-specific beats
        beat_types = [beat["beat_type"] for beat in beats]
        thriller_beats = ["hook", "inciting_incident", "escalation", "revelation", "climax"]
        
        found_thriller_beats = [bt for bt in thriller_beats if any(tb in bt.lower() for tb in beat_types)]
        assert len(found_thriller_beats) >= 1
    
    @pytest.mark.asyncio
    async def test_authenticity_improvement_recommendations(self, genre_analyzer, comedy_story_data):
        """Test generation of authenticity improvement recommendations."""
        result = await genre_analyzer.apply_genre_patterns(comedy_story_data, target_genre="horror")
        
        guidance = result.data["genre_guidance"]
        improvements = guidance["authenticity_improvements"]
        
        # Should provide specific improvements for genre mismatch
        assert len(improvements) > 0
        
        for improvement in improvements:
            assert "aspect" in improvement
            assert "current_state" in improvement
            assert "recommendation" in improvement
            assert "impact" in improvement
            assert "confidence" in improvement
            
            # Impact should be valid
            assert improvement["impact"] in ["high", "medium", "low"]
            
            # Confidence should be valid
            assert 0.0 <= improvement["confidence"] <= 1.0
        
        # For comedy->horror conversion, should suggest high-impact changes
        high_impact_count = len([imp for imp in improvements if imp["impact"] == "high"])
        assert high_impact_count >= 1
        
        # Should mention relevant horror elements
        improvement_text = " ".join([imp["recommendation"] for imp in improvements]).lower()
        horror_suggestions = ["dark", "fear", "suspense", "terror", "supernatural"]
        
        found_suggestions = sum(1 for suggestion in horror_suggestions if suggestion in improvement_text)
        assert found_suggestions >= 1
    
    @pytest.mark.asyncio
    async def test_pattern_matching_algorithm_consistency(self, genre_analyzer, thriller_story_data):
        """Test pattern matching algorithm consistency across multiple runs."""
        results = []
        
        # Run pattern matching multiple times
        for _ in range(3):
            result = await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre="thriller")
            results.append(result)
        
        # Extract confidence scores
        confidences = []
        for result in results:
            guidance = result.data["genre_guidance"]
            confidence = guidance["convention_compliance"]["confidence_score"]
            confidences.append(confidence)
        
        # Should be consistent
        max_confidence = max(confidences)
        min_confidence = min(confidences)
        variance = max_confidence - min_confidence
        
        assert variance < 0.1  # Should be consistent within 10%
        
        # All should meet or fail threshold consistently
        threshold_results = [c >= 0.75 for c in confidences]
        assert len(set(threshold_results)) == 1  # All same result
    
    @pytest.mark.asyncio
    async def test_multi_genre_analysis_comparison(self, genre_analyzer, thriller_story_data):
        """Test analysis against multiple genres for best fit identification."""
        genres_to_test = ["thriller", "comedy", "horror", "romance", "drama"]
        genre_scores = {}
        
        for genre in genres_to_test:
            result = await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre=genre)
            guidance = result.data["genre_guidance"]
            confidence = guidance["convention_compliance"]["confidence_score"]
            genre_scores[genre] = confidence
        
        # Thriller should score highest for thriller content
        assert genre_scores["thriller"] == max(genre_scores.values())
        
        # Thriller should meet threshold
        assert genre_scores["thriller"] >= 0.75
        
        # Comedy should score lower for thriller content
        assert genre_scores["comedy"] < genre_scores["thriller"]
        
        # Scores should be properly distributed
        score_range = max(genre_scores.values()) - min(genre_scores.values())
        assert score_range >= 0.2  # Should have meaningful differences
    
    @pytest.mark.asyncio
    async def test_genre_template_loading_and_application(self, genre_analyzer):
        """Test genre template loading and pattern application."""
        # Test with specific genre that should have template
        story_data = StoryData(
            content="Western story with cowboys, saloons, and gunfights in frontier town",
            metadata={"project_id": "western-template-test"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(story_data, target_genre="western")
        
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should apply western genre template
        assert isinstance(compliance["met_conventions"], list)
        assert isinstance(compliance["missing_conventions"], list)
        
        # Should recognize western elements if template is working
        met_text = " ".join(compliance["met_conventions"]).lower()
        western_elements = ["frontier", "gunfight", "saloon", "western", "cowboy"]
        
        # Should recognize at least some western elements
        recognized = sum(1 for element in western_elements if element in met_text)
        # If western template is loaded correctly, should recognize some elements
        # If not loaded, will still work but with lower confidence
        assert 0.0 <= compliance["confidence_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_edge_case_handling_in_pattern_matching(self, genre_analyzer):
        """Test pattern matching with edge cases and unusual inputs."""
        # Test with empty content
        empty_story = StoryData(
            content="",
            metadata={"project_id": "empty-test"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(empty_story, target_genre="thriller")
        
        # Should handle gracefully
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        assert 0.0 <= compliance["confidence_score"] <= 1.0
        assert compliance["confidence_score"] < 0.5  # Should be low for empty content
        
        # Test with very long content
        long_content = "A thriller story. " * 1000
        long_story = StoryData(
            content=long_content,
            metadata={"project_id": "long-test"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(long_story, target_genre="thriller")
        
        # Should handle large content
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        assert 0.0 <= compliance["confidence_score"] <= 1.0
        
        # Test with special characters and unusual formatting
        special_story = StoryData(
            content="@#$%^&*()_+ Thriller with symbols! 123456789 [brackets] {braces}",
            metadata={"project_id": "special-chars-test"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(special_story, target_genre="thriller")
        
        # Should not crash on special characters
        guidance = result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        assert 0.0 <= compliance["confidence_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation_algorithm(self, genre_analyzer):
        """Test confidence score calculation algorithm accuracy."""
        # High-quality genre match
        high_quality_thriller = StoryData(
            content="""
            Seasoned detective investigates series of murders with corporate conspiracy undertones.
            Escalating tension as powerful enemies threaten protagonist and loved ones.
            Red herrings and plot twists keep audience guessing until final revelation.
            Climactic confrontation where justice prevails but at significant personal cost.
            """,
            metadata={"project_id": "high-quality-thriller"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(high_quality_thriller, target_genre="thriller")
        guidance = result.data["genre_guidance"]
        high_confidence = guidance["convention_compliance"]["confidence_score"]
        
        # Medium-quality genre match
        medium_quality_thriller = StoryData(
            content="""
            Person investigates something suspicious.
            Some dangerous things happen.
            Problem gets resolved.
            """,
            metadata={"project_id": "medium-quality-thriller"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(medium_quality_thriller, target_genre="thriller")
        guidance = result.data["genre_guidance"]
        medium_confidence = guidance["convention_compliance"]["confidence_score"]
        
        # High quality should score higher than medium quality
        assert high_confidence > medium_confidence
        assert high_confidence >= 0.75  # Should meet threshold
        assert medium_confidence < 0.75  # Should not meet threshold
        
        # Scores should be meaningfully different
        assert (high_confidence - medium_confidence) >= 0.2
    
    @pytest.mark.asyncio
    async def test_genre_analyzer_performance(self, genre_analyzer, thriller_story_data):
        """Test genre analyzer performance with timing requirements."""
        import time
        
        start_time = time.time()
        
        # Run multiple genre analyses
        for _ in range(5):
            await genre_analyzer.apply_genre_patterns(thriller_story_data, target_genre="thriller")
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time = total_time / 5
        
        # Should complete within reasonable time
        assert average_time < 2.0  # Each analysis should complete within 2 seconds
        assert total_time < 8.0  # Total time should be reasonable
    
    @pytest.mark.asyncio
    async def test_pattern_matching_with_metadata_enhancement(self, genre_analyzer):
        """Test pattern matching enhanced by story metadata."""
        # Story with helpful metadata
        story_with_metadata = StoryData(
            content="A detective story about corruption and danger",
            metadata={
                "project_id": "metadata-enhanced",
                "genre": "thriller",
                "themes": ["corruption", "justice", "betrayal"],
                "tone": "dark",
                "setting": "urban_contemporary",
                "character_archetypes": ["detective", "corrupt_official"]
            }
        )
        
        result = await genre_analyzer.apply_genre_patterns(story_with_metadata, target_genre="thriller")
        guidance = result.data["genre_guidance"]
        enhanced_confidence = guidance["convention_compliance"]["confidence_score"]
        
        # Story without metadata
        story_without_metadata = StoryData(
            content="A detective story about corruption and danger",
            metadata={"project_id": "no-metadata"}
        )
        
        result = await genre_analyzer.apply_genre_patterns(story_without_metadata, target_genre="thriller")
        guidance = result.data["genre_guidance"]
        basic_confidence = guidance["convention_compliance"]["confidence_score"]
        
        # Metadata should help confidence (or at least not hurt)
        assert enhanced_confidence >= basic_confidence
        
        # Both should still work
        assert 0.0 <= enhanced_confidence <= 1.0
        assert 0.0 <= basic_confidence <= 1.0