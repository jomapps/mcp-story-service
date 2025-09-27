"""Integration test for malformed content handling scenario.

This test simulates various malformed content scenarios as described in 
Clarification B: Partial analysis for malformed content.

Constitutional Compliance: Test-First Development (II), Integration Testing (IV)
"""

import pytest
from typing import Dict, Any, List

# These imports will fail until implementation exists - that's expected for TDD
try:
    from src.mcp.handlers.story_structure import analyze_story_structure
    from src.mcp.handlers.plot_threads import track_plot_threads
    from src.mcp.handlers.consistency import validate_consistency
    from src.mcp.handlers.genre_patterns import apply_genre_patterns
    from src.mcp.handlers.pacing import calculate_pacing
    from src.services.content_analyzer import ContentAnalyzer
except ImportError:
    # Expected during TDD phase - tests must fail first
    analyze_story_structure = None
    track_plot_threads = None
    validate_consistency = None
    apply_genre_patterns = None
    calculate_pacing = None
    ContentAnalyzer = None


@pytest.mark.integration
class TestMalformedContentHandlingScenario:
    """Integration test for handling various malformed content scenarios."""
    
    @pytest.mark.asyncio
    async def test_empty_content_across_all_tools(self):
        """Test handling of empty content across all MCP tools."""
        # Clarification B: Tools should provide partial analysis for malformed content
        
        empty_content = ""
        session_id = "empty_content_test"
        
        # Test story structure analysis with empty content
        structure_result = await analyze_story_structure(story_content=empty_content)
        assert isinstance(structure_result, dict), "Structure analysis must return dict"
        assert "confidence" in structure_result, "Must include confidence score"
        assert structure_result["confidence"] == 0.0, "Empty content should score 0 confidence"
        assert "analysis" in structure_result, "Must include analysis explaining issue"
        
        # Test plot thread tracking with empty content
        threads_result = await track_plot_threads(
            story_content=empty_content, 
            session_id=session_id
        )
        assert isinstance(threads_result, dict), "Thread tracking must return dict"
        assert "plot_threads" in threads_result, "Must include plot_threads field"
        assert len(threads_result["plot_threads"]) == 0, "Empty content should have no threads"
        
        # Test consistency validation with empty content
        consistency_result = await validate_consistency(story_content=empty_content)
        assert isinstance(consistency_result, dict), "Consistency check must return dict"
        assert "overall_score" in consistency_result, "Must include overall score"
        assert consistency_result["overall_score"] == 0.0, "Empty content should score 0"
        
        # Test genre pattern application with empty content
        genre_result = await apply_genre_patterns(
            story_content=empty_content,
            target_genre="thriller"
        )
        assert isinstance(genre_result, dict), "Genre analysis must return dict"
        assert "adherence_score" in genre_result, "Must include adherence score"
        assert genre_result["adherence_score"] <= 0.1, "Empty content should score very low"
        
        # Test pacing calculation with empty content
        pacing_result = await calculate_pacing(story_content=empty_content)
        assert isinstance(pacing_result, dict), "Pacing analysis must return dict"
        assert "pacing_score" in pacing_result, "Must include pacing score"
        assert pacing_result["pacing_score"] == 0.0, "Empty content should score 0"
    
    @pytest.mark.asyncio
    async def test_whitespace_only_content(self):
        """Test handling of whitespace-only content."""
        whitespace_variations = [
            "   ",  # Spaces only
            "\t\t\t",  # Tabs only
            "\n\n\n",  # Newlines only
            " \t \n \r ",  # Mixed whitespace
        ]
        
        for i, whitespace_content in enumerate(whitespace_variations):
            session_id = f"whitespace_test_{i}"
            
            # Test across multiple tools
            structure_result = await analyze_story_structure(story_content=whitespace_content)
            assert structure_result["confidence"] <= 0.1, \
                f"Whitespace content should score very low: {repr(whitespace_content)}"
            
            threads_result = await track_plot_threads(
                story_content=whitespace_content,
                session_id=session_id
            )
            assert len(threads_result["plot_threads"]) == 0, \
                "Whitespace should not produce plot threads"
            
            # All tools should handle whitespace gracefully without crashing
            consistency_result = await validate_consistency(story_content=whitespace_content)
            assert isinstance(consistency_result, dict), "Must handle whitespace gracefully"
    
    @pytest.mark.asyncio
    async def test_extremely_short_content(self):
        """Test handling of extremely short content."""
        short_content_examples = [
            "A",  # Single character
            "Hi.",  # Single word with punctuation
            "The cat.",  # Three words
            "Once upon a time.",  # Classic opening but incomplete
        ]
        
        for short_content in short_content_examples:
            session_id = f"short_content_{len(short_content)}"
            
            # Story structure should recognize insufficient content
            structure_result = await analyze_story_structure(story_content=short_content)
            assert structure_result["confidence"] < 0.3, \
                f"Short content should score low: '{short_content}'"
            
            # Should provide explanation for low confidence
            analysis = structure_result["analysis"]
            assert "insufficient" in str(analysis).lower() or \
                   "too short" in str(analysis).lower() or \
                   "minimal" in str(analysis).lower(), \
                "Should explain why content is insufficient"
            
            # Plot threads should handle minimal content
            threads_result = await track_plot_threads(
                story_content=short_content,
                session_id=session_id
            )
            assert len(threads_result["plot_threads"]) <= 1, \
                "Short content should have minimal plot threads"
    
    @pytest.mark.asyncio
    async def test_extremely_long_content(self):
        """Test handling of extremely long content."""
        # Create very long content that might cause performance issues
        base_sentence = "This is a test sentence that will be repeated many times. "
        long_content = base_sentence * 5000  # ~50,000 words
        
        session_id = "long_content_test"
        
        # Should handle long content without timing out
        structure_result = await analyze_story_structure(story_content=long_content)
        assert isinstance(structure_result, dict), "Must handle long content"
        assert "confidence" in structure_result, "Must include confidence"
        
        # Repetitive content should score lower due to lack of structure
        assert structure_result["confidence"] < 0.5, \
            "Repetitive content should score low for structure"
        
        # Should identify repetitive pattern as an issue
        analysis = structure_result["analysis"]
        if "issues" in analysis:
            issues = analysis["issues"]
            issue_descriptions = [issue.get("description", "") for issue in issues]
            assert any("repetitive" in desc.lower() or "monotonous" in desc.lower() 
                      for desc in issue_descriptions), \
                "Should identify repetitive content as issue"
        
        # Plot thread tracking should handle long content
        threads_result = await track_plot_threads(
            story_content=long_content[:1000],  # Use truncated version for efficiency
            session_id=session_id
        )
        assert isinstance(threads_result, dict), "Must handle long content in thread tracking"
    
    @pytest.mark.asyncio
    async def test_mixed_format_content(self):
        """Test handling of content with mixed or unclear formats."""
        mixed_format_examples = [
            # HTML-like content
            "<html><body>This is a story about <b>bold</b> characters.</body></html>",
            
            # JSON-like content
            '{"story": "Once upon a time", "characters": ["hero", "villain"]}',
            
            # Markdown-like content
            "# Chapter 1\n\n**Sarah** walked down the *mysterious* hallway.\n\n## Section 2",
            
            # Code-like content
            "function story() { return 'hero saves day'; } // This is narrative",
            
            # Mixed screenplay and prose
            "FADE IN: Sarah walked down the street. She was thinking about life.\nSARAH\nWhat a day!",
        ]
        
        for i, mixed_content in enumerate(mixed_format_examples):
            session_id = f"mixed_format_{i}"
            
            # Should attempt to extract narrative content
            structure_result = await analyze_story_structure(story_content=mixed_content)
            assert isinstance(structure_result, dict), "Must handle mixed formats"
            
            # May have lower confidence but should not crash
            assert 0 <= structure_result["confidence"] <= 1, "Confidence must be in valid range"
            
            # Should attempt to identify any narrative elements
            analysis = structure_result["analysis"]
            assert isinstance(analysis, dict), "Analysis must be structured"
            
            # Thread tracking should handle mixed formats
            threads_result = await track_plot_threads(
                story_content=mixed_content,
                session_id=session_id
            )
            assert isinstance(threads_result["plot_threads"], list), \
                "Must return list even for mixed formats"
    
    @pytest.mark.asyncio
    async def test_non_english_content(self):
        """Test handling of non-English content."""
        # Note: This tests graceful handling, not necessarily correct analysis
        non_english_examples = [
            "Il était une fois une princesse dans un château lointain.",  # French
            "Es war einmal ein König in einem fernen Land.",  # German
            "昔々、遠い国にお姫様がいました。",  # Japanese
            "Жила-была принцесса в далёком королевстве.",  # Russian
        ]
        
        for i, non_english_content in enumerate(non_english_examples):
            session_id = f"non_english_{i}"
            
            # Should handle without crashing
            structure_result = await analyze_story_structure(story_content=non_english_content)
            assert isinstance(structure_result, dict), "Must handle non-English content"
            
            # May have lower confidence due to language barriers
            confidence = structure_result["confidence"]
            assert 0 <= confidence <= 1, "Confidence must be in valid range"
            
            # Should indicate language detection issues if confidence is low
            if confidence < 0.5:
                analysis = structure_result["analysis"]
                # Should provide some indication of language processing limitations
                assert isinstance(analysis, dict), "Must provide analysis structure"
    
    @pytest.mark.asyncio
    async def test_malformed_characters_and_encoding(self):
        """Test handling of malformed characters and encoding issues."""
        malformed_examples = [
            "Story with weird characters: ��� invalid encoding",
            "Text with null bytes: \x00\x00 in the middle",
            "Unicode issues: caf\u00e9 na\u00efve r\u00e9sum\u00e9 \ud83d\ude00",
            "Control characters: \x01\x02\x03 embedded in story",
        ]
        
        for i, malformed_content in enumerate(malformed_examples):
            session_id = f"malformed_{i}"
            
            try:
                # Should handle encoding issues gracefully
                structure_result = await analyze_story_structure(story_content=malformed_content)
                assert isinstance(structure_result, dict), "Must handle encoding issues"
                
                # Should clean or ignore problematic characters
                confidence = structure_result["confidence"]
                assert 0 <= confidence <= 1, "Must return valid confidence"
                
            except UnicodeError:
                # If Unicode errors occur, they should be handled gracefully
                pytest.skip("Unicode handling depends on implementation details")
    
    @pytest.mark.asyncio
    async def test_partial_analysis_quality(self):
        """Test that partial analysis provides useful information."""
        # Clarification B: Partial analysis should still be useful
        
        partial_content = """
        Sarah walked into the mysterious mansion. The door creaked behind her.
        Something was wrong here. Very wrong.
        """
        
        session_id = "partial_analysis_test"
        
        # Even with limited content, should provide some useful analysis
        structure_result = await analyze_story_structure(story_content=partial_content)
        
        # Should have moderate confidence for coherent but limited content
        assert 0.3 <= structure_result["confidence"] <= 0.7, \
            "Partial but coherent content should have moderate confidence"
        
        # Should identify what elements are present
        analysis = structure_result["analysis"]
        
        # Should recognize story elements even if incomplete
        if "elements_found" in analysis:
            elements = analysis["elements_found"]
            assert len(elements) > 0, "Should identify some story elements"
        
        # Should provide recommendations for completion
        if "recommendations" in analysis:
            recommendations = analysis["recommendations"]
            assert len(recommendations) > 0, "Should suggest how to improve/complete"
        
        # Plot thread tracking should identify what's available
        threads_result = await track_plot_threads(
            story_content=partial_content,
            session_id=session_id
        )
        
        # Should identify potential plot threads even if incomplete
        threads = threads_result["plot_threads"]
        if len(threads) > 0:
            for thread in threads:
                assert "status" in thread, "Thread must have status"
                # Partial content threads should be marked as developing/unresolved
                assert thread["status"] in ["developing", "unresolved", "incomplete"], \
                    "Partial threads should reflect incomplete status"
    
    @pytest.mark.asyncio
    async def test_error_recovery_across_tools(self):
        """Test error recovery when one tool fails but others continue."""
        # Scenario: One analysis tool encounters an error, others should continue
        
        problematic_content = "Content that might cause issues in specific tools..."
        session_id = "error_recovery_test"
        
        # Collect results from all tools, some may fail
        results = {}
        errors = {}
        
        tools_to_test = [
            ("structure", lambda: analyze_story_structure(story_content=problematic_content)),
            ("threads", lambda: track_plot_threads(story_content=problematic_content, session_id=session_id)),
            ("consistency", lambda: validate_consistency(story_content=problematic_content)),
            ("genre", lambda: apply_genre_patterns(story_content=problematic_content, target_genre="drama")),
            ("pacing", lambda: calculate_pacing(story_content=problematic_content)),
        ]
        
        for tool_name, tool_func in tools_to_test:
            try:
                result = await tool_func()
                results[tool_name] = result
            except Exception as e:
                errors[tool_name] = e
        
        # At least some tools should succeed even if others fail
        assert len(results) > 0, "At least one tool should succeed"
        
        # Tools that succeed should provide valid results
        for tool_name, result in results.items():
            assert isinstance(result, dict), f"{tool_name} must return dict"
            # Each tool has its own required fields, but all should be structured
            assert len(result) > 0, f"{tool_name} result should not be empty"
        
        # If tools fail, errors should be informative
        for tool_name, error in errors.items():
            assert isinstance(error, Exception), f"{tool_name} error should be Exception"
            assert len(str(error)) > 0, f"{tool_name} error should have message"


@pytest.mark.integration
class TestMalformedContentRecovery:
    """Integration tests for recovery mechanisms with malformed content."""
    
    @pytest.mark.asyncio
    async def test_progressive_degradation(self):
        """Test progressive degradation of analysis quality with increasingly malformed content."""
        
        content_quality_levels = [
            ("high", "Sarah discovered the ancient artifact and embarked on a heroic journey to save her village from the encroaching darkness."),
            ("medium", "Sarah found something. It was important. She had to do something about it. Things happened."),
            ("low", "Sarah. Thing. Happened. More. End."),
            ("very_low", "Sfkjh sdkfj sldkfj random words no structure whatsoever jumbled mess."),
            ("minimal", "Word word word."),
        ]
        
        previous_confidence = 1.0
        
        for quality_level, content in content_quality_levels:
            session_id = f"degradation_{quality_level}"
            
            structure_result = await analyze_story_structure(story_content=content)
            current_confidence = structure_result["confidence"]
            
            # Confidence should generally decrease with quality
            # (allowing some tolerance for analysis variations)
            assert current_confidence <= previous_confidence + 0.1, \
                f"Confidence should not increase significantly from {quality_level}"
            
            # Even poor content should return valid structure
            assert isinstance(structure_result, dict), "Must return valid structure"
            assert "analysis" in structure_result, "Must provide some analysis"
            
            previous_confidence = current_confidence
    
    @pytest.mark.asyncio
    async def test_content_preprocessing_integration(self):
        """Test integration of content preprocessing for malformed input."""
        
        content_needing_preprocessing = """
        <div>This story is embedded in HTML tags</div>
        
        Sarah walked down the &amp; street with &quot;quotes&quot; everywhere.
        
        There were [stage directions] and (parenthetical comments) throughout.
        
        The story had    excessive    whitespace   and	tabs	mixed	in.
        
        And it ended with trailing spaces...    
        """
        
        session_id = "preprocessing_test"
        
        # Analysis should handle preprocessing internally
        structure_result = await analyze_story_structure(story_content=content_needing_preprocessing)
        
        # Should extract and analyze the actual narrative content
        assert structure_result["confidence"] > 0.3, \
            "Should extract meaningful content despite formatting issues"
        
        # Should provide clean analysis despite messy input
        analysis = structure_result["analysis"]
        assert isinstance(analysis, dict), "Analysis should be well-structured"
        
        # Thread tracking should also handle preprocessing
        threads_result = await track_plot_threads(
            story_content=content_needing_preprocessing,
            session_id=session_id
        )
        
        # Should identify story elements despite formatting
        threads = threads_result["plot_threads"]
        if len(threads) > 0:
            # Threads should reference clean content, not raw HTML/formatting
            for thread in threads:
                description = thread.get("description", "")
                assert "<div>" not in description, "Should not include HTML tags"
                assert "&amp;" not in description, "Should decode HTML entities"