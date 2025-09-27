"""Contract tests for apply_genre_patterns MCP tool.

These tests define the expected behavior of the apply_genre_patterns tool
according to the MCP protocol contract. They MUST FAIL until implementation is complete.

Constitutional Compliance: Test-First Development (II)
"""

import pytest
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List

# These imports will fail until implementation exists - that's expected for TDD
try:
    from src.mcp.handlers.genre_patterns import apply_genre_patterns
    from src.models.genre_template import GenreTemplate
    from src.models.story_arc import StoryArc
except ImportError:
    # Expected during TDD phase - tests must fail first
    apply_genre_patterns = None
    GenreTemplate = None
    StoryArc = None


class TestApplyGenrePatternsTools:
    """Test MCP tool contract for genre pattern application."""
    
    @pytest.mark.asyncio
    async def test_tool_signature_compliance(self):
        """Test that tool follows MCP protocol signature requirements."""
        # Tool must exist and be callable
        assert apply_genre_patterns is not None, "apply_genre_patterns tool not implemented"
        assert callable(apply_genre_patterns), "Tool must be callable"
        
        # Tool must accept required parameters per specification
        # FR-005: Apply genre-specific patterns and validate adherence
        story_content = "Detective investigates murder in dark city setting."
        target_genre = "thriller"
        
        result = await apply_genre_patterns(
            story_content=story_content,
            target_genre=target_genre
        )
        
        # Must return dict with required fields
        assert isinstance(result, dict), "Tool must return dict response"
        assert "genre_analysis" in result, "Must include genre_analysis field"
        assert "pattern_matches" in result, "Must include pattern_matches field"
        assert "recommendations" in result, "Must include recommendations field"
        assert "adherence_score" in result, "Must include adherence_score per FR-005"
    
    @pytest.mark.asyncio
    async def test_thriller_genre_pattern_detection(self):
        """Test detection and application of thriller genre patterns."""
        # FR-005: Apply thriller-specific patterns from genre templates
        thriller_story = """
        The phone rang at 3 AM. Detective Sarah picked up to hear heavy breathing.
        "I know what you did last summer," whispered the voice before the line went dead.
        
        Sarah checked her locks, drew the curtains. Someone was watching her house.
        Every shadow seemed to move. The killer was getting closer.
        
        The final confrontation came in the abandoned warehouse. Sarah faced her
        tormentor in a deadly game of cat and mouse.
        """
        
        result = await apply_genre_patterns(
            story_content=thriller_story,
            target_genre="thriller"
        )
        
        pattern_matches = result["pattern_matches"]
        assert isinstance(pattern_matches, list), "Pattern matches must be a list"
        
        # Should identify thriller conventions
        thriller_patterns = [pattern["name"] for pattern in pattern_matches]
        expected_patterns = ["building_tension", "stalking", "final_confrontation", "cat_and_mouse"]
        
        found_patterns = [p for p in expected_patterns if any(exp in pattern.lower() for pattern in thriller_patterns)]
        assert len(found_patterns) > 0, "Should identify thriller-specific patterns"
        
        # Should score well for thriller adherence
        assert result["adherence_score"] >= 0.75, "Thriller story should score high for thriller genre"
    
    @pytest.mark.asyncio
    async def test_romance_genre_pattern_detection(self):
        """Test detection and application of romance genre patterns."""
        # FR-005: Apply romance-specific patterns from genre templates
        romance_story = """
        Emma bumped into Jake at the coffee shop, spilling her latte on his shirt.
        "I'm so sorry!" she gasped, their eyes meeting for the first time.
        
        Despite their initial awkwardness, they began meeting regularly.
        The chemistry was undeniable, but Emma's past made her hesitant to trust.
        
        A misunderstanding nearly tore them apart, but Jake's grand gesture
        at the airport proved his love was real. They embraced as the sun set.
        """
        
        result = await apply_genre_patterns(
            story_content=romance_story,
            target_genre="romance"
        )
        
        pattern_matches = result["pattern_matches"]
        
        # Should identify romance conventions
        romance_patterns = [pattern["name"] for pattern in pattern_matches]
        expected_patterns = ["meet_cute", "chemistry", "misunderstanding", "grand_gesture", "happy_ending"]
        
        found_patterns = [p for p in expected_patterns if any(exp in pattern.lower() for pattern in romance_patterns)]
        assert len(found_patterns) >= 2, "Should identify multiple romance patterns"
        
        # Should score well for romance adherence
        assert result["adherence_score"] >= 0.75, "Romance story should score high for romance genre"
    
    @pytest.mark.asyncio
    async def test_horror_genre_pattern_detection(self):
        """Test detection and application of horror genre patterns."""
        # FR-005: Apply horror-specific patterns from genre templates
        horror_story = """
        The old house stood empty for decades. No one dared enter after the murders.
        
        But teenagers always think they're invincible. Sarah and her friends
        decided to explore the abandoned mansion on Halloween night.
        
        The doors slammed shut behind them. Strange sounds echoed from upstairs.
        One by one, her friends disappeared into the darkness.
        
        Sarah found herself alone, facing an unspeakable evil that had waited
        so long for fresh victims.
        """
        
        result = await apply_genre_patterns(
            story_content=horror_story,
            target_genre="horror"
        )
        
        pattern_matches = result["pattern_matches"]
        
        # Should identify horror conventions
        horror_patterns = [pattern["name"] for pattern in pattern_matches]
        expected_patterns = ["isolation", "dread", "supernatural", "victims", "final_girl"]
        
        found_patterns = [p for p in expected_patterns if any(exp in pattern.lower() for pattern in horror_patterns)]
        assert len(found_patterns) > 0, "Should identify horror-specific patterns"
        
        # Should score well for horror adherence
        assert result["adherence_score"] >= 0.70, "Horror story should score reasonably for horror genre"
    
    @pytest.mark.asyncio
    async def test_genre_mismatch_detection(self):
        """Test detection when story doesn't match target genre."""
        # Should identify when story doesn't fit specified genre
        romantic_story = """
        Jane and Bob met at a wedding and fell in love instantly.
        They had a beautiful courtship filled with flowers and poetry.
        Their wedding was perfect and they lived happily ever after.
        """
        
        result = await apply_genre_patterns(
            story_content=romantic_story,
            target_genre="horror"  # Mismatch: romance story vs horror genre
        )
        
        # Should score low for horror adherence
        assert result["adherence_score"] < 0.5, "Romance story should score low for horror genre"
        
        # Analysis should identify the mismatch
        genre_analysis = result["genre_analysis"]
        assert "mismatch" in genre_analysis or "incompatible" in str(genre_analysis).lower(), \
            "Should identify genre mismatch"
        
        # Recommendations should suggest genre change
        recommendations = result["recommendations"]
        assert len(recommendations) > 0, "Should provide recommendations for mismatch"
        
        recommendation_text = " ".join([rec.get("description", "") for rec in recommendations])
        assert "romance" in recommendation_text.lower() or "genre" in recommendation_text.lower(), \
            "Should recommend considering different genre"
    
    @pytest.mark.asyncio
    async def test_multiple_genre_detection(self):
        """Test detection of multiple genre influences."""
        # FR-005: Handle stories with multiple genre elements
        mixed_genre_story = """
        Detective Sarah investigated the mysterious murders (thriller)
        while falling for her partner Jake (romance).
        
        The killer used supernatural methods to dispatch victims (horror),
        leading to explosive confrontations (action).
        
        Sarah's witty banter with Jake lightened the dark investigation (comedy).
        """
        
        result = await apply_genre_patterns(
            story_content=mixed_genre_story,
            target_genre="thriller"
        )
        
        genre_analysis = result["genre_analysis"]
        
        # Should identify multiple genre influences
        assert "multiple_genres" in genre_analysis or "mixed" in str(genre_analysis).lower(), \
            "Should identify multiple genre influences"
        
        # Should still provide analysis for target genre
        assert result["adherence_score"] > 0, "Should still score for target genre"
        
        # Recommendations should address genre mixing
        recommendations = result["recommendations"]
        mixed_recommendations = [rec for rec in recommendations if 
                               "multiple" in rec.get("description", "").lower() or
                               "mixed" in rec.get("description", "").lower()]
        assert len(mixed_recommendations) > 0, "Should provide recommendations for genre mixing"
    
    @pytest.mark.asyncio
    async def test_genre_template_integration(self):
        """Test integration with genre template system."""
        # FR-005: Use genre templates for pattern matching
        story_content = "Sci-fi story with space travel and technology..."
        
        result = await apply_genre_patterns(
            story_content=story_content,
            target_genre="sci-fi"
        )
        
        # Should reference genre template elements
        genre_analysis = result["genre_analysis"]
        assert "template" in genre_analysis or "conventions" in genre_analysis, \
            "Should reference genre template system"
        
        # Pattern matches should align with genre template structure
        pattern_matches = result["pattern_matches"]
        for pattern in pattern_matches:
            assert "name" in pattern, "Each pattern must have a name"
            assert "confidence" in pattern, "Each pattern must have confidence score"
            assert "description" in pattern, "Each pattern must have description"
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_compliance(self):
        """Test compliance with confidence thresholds."""
        # FR-001: 75% minimum confidence threshold
        # Should respect genre-specific confidence thresholds
        
        clear_thriller = """
        Tension builds as the detective realizes the killer is closer than ever.
        Every shadow hides danger. The phone rings with another threat.
        Time is running out for the final confrontation.
        """
        
        result = await apply_genre_patterns(
            story_content=clear_thriller,
            target_genre="thriller"
        )
        
        # Strong genre adherence should meet threshold
        assert result["adherence_score"] >= 0.75, "Clear genre adherence must meet threshold"
        
        # Individual pattern confidences should be available
        pattern_matches = result["pattern_matches"]
        for pattern in pattern_matches:
            confidence = pattern.get("confidence", 0)
            assert isinstance(confidence, (int, float)), "Pattern confidence must be numeric"
            assert 0 <= confidence <= 1, "Pattern confidence must be normalized"
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self):
        """Test generation of genre-specific recommendations."""
        # FR-005: Provide recommendations for better genre adherence
        weak_thriller = """
        Mary went to the store. She bought some groceries.
        The weather was nice. She went home and made dinner.
        """
        
        result = await apply_genre_patterns(
            story_content=weak_thriller,
            target_genre="thriller"
        )
        
        # Should score low for thriller
        assert result["adherence_score"] < 0.5, "Non-thriller content should score low"
        
        # Should provide specific recommendations
        recommendations = result["recommendations"]
        assert len(recommendations) > 0, "Should provide recommendations for improvement"
        
        # Recommendations should be actionable and specific
        for rec in recommendations:
            assert "description" in rec, "Each recommendation must have description"
            assert "priority" in rec, "Each recommendation must have priority"
            assert len(rec["description"]) > 10, "Recommendations should be detailed"
    
    @pytest.mark.asyncio
    async def test_malformed_content_handling(self):
        """Test handling of malformed or invalid content."""
        # Clarification B: Partial analysis for malformed content
        malformed_inputs = [
            ("", "thriller"),
            ("   ", "romance"),
            ("Single word", "horror"),
            ("A" * 10000, "comedy"),  # Very long content
        ]
        
        for content, genre in malformed_inputs:
            result = await apply_genre_patterns(
                story_content=content,
                target_genre=genre
            )
            
            # Must handle gracefully
            assert isinstance(result, dict), "Must return dict for malformed input"
            assert "adherence_score" in result, "Must include adherence_score"
            assert result["adherence_score"] <= 0.25, "Malformed content should score very low"
    
    @pytest.mark.asyncio
    async def test_unsupported_genre_handling(self):
        """Test handling of unsupported or invalid genres."""
        story_content = "A story about adventures and mystery..."
        
        # Test with invalid genre
        result = await apply_genre_patterns(
            story_content=story_content,
            target_genre="invalid_genre_xyz"
        )
        
        # Should handle gracefully
        assert isinstance(result, dict), "Must return dict for invalid genre"
        
        # Should indicate unsupported genre
        genre_analysis = result["genre_analysis"]
        assert "unsupported" in str(genre_analysis).lower() or "unknown" in str(genre_analysis).lower(), \
            "Should indicate unsupported genre"
    
    @pytest.mark.asyncio
    async def test_integration_with_genre_template_model(self):
        """Test integration with GenreTemplate data model."""
        # FR-002: Store and use genre templates
        # Constitutional: Integration Testing (IV)
        
        story_content = "Fantasy story with magic and dragons..."
        result = await apply_genre_patterns(
            story_content=story_content,
            target_genre="fantasy"
        )
        
        # Should be compatible with GenreTemplate model
        if GenreTemplate:
            # This will fail until GenreTemplate model is implemented
            template_data = {
                "name": "fantasy",
                "conventions": result["genre_analysis"].get("conventions", {}),
                "confidence_threshold": 0.75
            }
            genre_template = GenreTemplate(**template_data)
            assert genre_template.name == "fantasy"
    
    @pytest.mark.asyncio
    async def test_observability_requirements(self):
        """Test observability and monitoring compliance."""
        # Constitutional: Observability (V) - structured logging and metrics
        
        story_content = "Sample story for observability testing..."
        result = await apply_genre_patterns(
            story_content=story_content,
            target_genre="drama"
        )
        
        # Must provide observable execution metadata
        assert "metadata" in result or "execution_time" in result, \
            "Must provide execution metadata for observability"
        
        # Should include metrics for monitoring
        genre_analysis = result["genre_analysis"]
        assert "pattern_count" in genre_analysis, "Must provide pattern count metric"
        assert "processing_time" in genre_analysis or "execution_time" in result, \
            "Must provide timing metrics"


@pytest.mark.integration
class TestGenrePatternsToolIntegration:
    """Integration tests for genre patterns application tool."""
    
    @pytest.mark.asyncio
    async def test_cross_genre_analysis_workflow(self):
        """Test analysis workflow across multiple genres."""
        story_content = """
        In a dystopian future, detective Sarah investigates cyber-crimes
        while navigating a dangerous romance with a rebel hacker.
        
        High-tech gadgets and AI assist her investigation, but ancient
        magic still influences the digital world in unexpected ways.
        """
        
        # Test against multiple genres
        genres_to_test = ["sci-fi", "thriller", "romance", "fantasy"]
        results = {}
        
        for genre in genres_to_test:
            result = await apply_genre_patterns(
                story_content=story_content,
                target_genre=genre
            )
            results[genre] = result["adherence_score"]
        
        # Should score differently for different genres
        assert len(set(results.values())) > 1, "Should score differently for different genres"
        
        # Sci-fi should likely score highest due to futuristic setting
        assert results["sci-fi"] >= results["fantasy"], "Sci-fi elements should score higher than fantasy"