"""Integration test for story structure analysis scenario.

This test simulates the complete workflow of analyzing story structure
as described in the specification's quickstart scenarios.

Constitutional Compliance: Test-First Development (II), Integration Testing (IV)
"""

import pytest
from typing import Dict, Any

# These imports will fail until implementation exists - that's expected for TDD
try:
    from src.mcp.handlers.story_structure import analyze_story_structure
    from src.mcp.handlers.session import get_story_session
    from src.services.story_analyzer import StoryAnalyzer
    from src.models.story_arc import StoryArc
except ImportError:
    # Expected during TDD phase - tests must fail first
    analyze_story_structure = None
    get_story_session = None
    StoryAnalyzer = None
    StoryArc = None


@pytest.mark.integration
class TestStoryStructureAnalysisScenario:
    """Integration test for complete story structure analysis workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_story_analysis_workflow(self):
        """Test the complete story structure analysis workflow from start to finish."""
        # Scenario: User submits a story for structure analysis
        # Expected: Complete analysis with confidence scores and structure identification
        
        # Sample story content representing a three-act structure
        story_content = """
        ACT I - SETUP
        
        Sarah Miller works as a librarian in the quiet town of Millbrook.
        Her routine life involves cataloging books and helping patrons.
        
        One evening while closing, she discovers an ancient book hidden
        behind the others. The book contains strange symbols that glow
        when she touches them.
        
        ACT II - CONFRONTATION
        
        Sarah learns the book contains real magic spells. She experiments
        cautiously, starting with simple illusions and healing magic.
        
        Her newfound abilities attract the attention of Marcus, a dark
        sorcerer who has been searching for the book for decades.
        
        Marcus confronts Sarah, demanding she surrender the book.
        When she refuses, he begins targeting her friends and family.
        
        Sarah must learn to master her magic quickly to protect those
        she loves. She makes mistakes, nearly losing the book twice.
        
        The stakes escalate when Marcus kidnaps her sister Emma,
        threatening to kill her unless Sarah brings him the book.
        
        ACT III - RESOLUTION
        
        Sarah realizes she doesn't need to choose between the book and her sister.
        She can use the book's magic to defeat Marcus permanently.
        
        In the final confrontation at the old cemetery, Sarah uses everything
        she's learned to battle Marcus. The fight is difficult, testing her
        skills and resolve.
        
        Sarah emerges victorious, rescuing Emma and ensuring Marcus can never
        threaten anyone again. She decides to become the book's guardian,
        protecting others from dark magic.
        """
        
        session_id = "story_analysis_integration_test"
        
        # Step 1: Create/get session for this analysis
        session_result = await get_story_session(session_id=session_id)
        assert session_result["session_id"] == session_id
        assert "session_data" in session_result
        
        # Step 2: Analyze story structure
        analysis_result = await analyze_story_structure(story_content=story_content)
        
        # Verify analysis results meet specification requirements
        assert isinstance(analysis_result, dict), "Analysis must return structured results"
        assert "analysis" in analysis_result, "Must include detailed analysis"
        assert "confidence" in analysis_result, "Must include confidence score per FR-001"
        assert "structure_type" in analysis_result, "Must identify structure type"
        
        # Verify confidence threshold compliance (FR-001: 75% minimum)
        confidence = analysis_result["confidence"]
        assert isinstance(confidence, (int, float)), "Confidence must be numeric"
        assert 0 <= confidence <= 1, "Confidence must be normalized"
        assert confidence >= 0.75, "Well-structured story must meet 75% threshold"
        
        # Verify structure identification
        assert analysis_result["structure_type"] == "three_act", "Should identify three-act structure"
        
        # Verify detailed analysis components
        analysis = analysis_result["analysis"]
        assert "acts" in analysis, "Must provide act breakdown"
        assert len(analysis["acts"]) == 3, "Three-act structure should have 3 acts"
        
        # Verify each act has required elements
        act_one = analysis["acts"][0]
        assert "setup" in str(act_one).lower() or "act_1" in str(act_one).lower()
        assert "beats" in act_one, "Each act must identify narrative beats"
        
        # Verify narrative beats identification
        assert "beats" in analysis, "Must identify narrative beats"
        beats = analysis["beats"]
        
        # Should identify key story beats
        beat_types = [beat.get("type", "").lower() for beat in beats]
        expected_beats = ["inciting_incident", "plot_point_1", "midpoint", "climax"]
        
        found_beats = []
        for expected in expected_beats:
            if any(expected in beat_type for beat_type in beat_types):
                found_beats.append(expected)
        
        assert len(found_beats) >= 3, f"Should identify at least 3 key beats, found: {found_beats}"
    
    @pytest.mark.asyncio
    async def test_poor_structure_analysis_workflow(self):
        """Test analysis workflow with poorly structured content."""
        # Scenario: User submits content without clear structure
        # Expected: Low confidence score with actionable feedback
        
        poor_story = """
        There was a person. They did things. Some stuff happened.
        Then other stuff happened. More things occurred randomly.
        Eventually it ended somehow. The end.
        """
        
        session_id = "poor_structure_test"
        
        # Get session
        session_result = await get_story_session(session_id=session_id)
        assert session_result["session_id"] == session_id
        
        # Analyze poor structure
        analysis_result = await analyze_story_structure(story_content=poor_story)
        
        # Should handle gracefully with low confidence
        assert "confidence" in analysis_result
        assert analysis_result["confidence"] < 0.75, "Poor structure should score below threshold"
        
        # Should still provide analysis explaining issues
        assert "analysis" in analysis_result
        analysis = analysis_result["analysis"]
        
        # Should identify structural problems
        if "issues" in analysis:
            issues = analysis["issues"]
            assert len(issues) > 0, "Should identify structural issues"
        
        # Should provide recommendations
        if "recommendations" in analysis:
            recommendations = analysis["recommendations"]
            assert len(recommendations) > 0, "Should provide improvement recommendations"
    
    @pytest.mark.asyncio
    async def test_alternative_structure_detection(self):
        """Test detection of non-three-act story structures."""
        # Scenario: User submits story with hero's journey structure
        # Expected: Correct structure identification with appropriate analysis
        
        heros_journey_story = """
        ORDINARY WORLD: Luke Skywalker lives as a farm boy on Tatooine,
        dreaming of adventure beyond his mundane existence.
        
        CALL TO ADVENTURE: Princess Leia's message in R2-D2 calls Luke
        to help save the galaxy from the Empire.
        
        REFUSAL OF THE CALL: Luke initially refuses, saying he must
        help with the harvest and care for his uncle.
        
        MEETING THE MENTOR: Obi-Wan Kenobi reveals Luke's true heritage
        and begins training him in the ways of the Force.
        
        CROSSING THE THRESHOLD: After his aunt and uncle are killed,
        Luke commits to the rebellion and leaves Tatooine.
        
        TESTS AND TRIALS: Luke faces multiple challenges learning to
        use the Force and fighting alongside the rebels.
        
        ORDEAL: Luke confronts Darth Vader and learns the devastating
        truth about his father.
        
        REWARD: Luke gains greater understanding of the Force and
        his role in the galaxy's fate.
        
        THE ROAD BACK: Luke returns to complete his training and
        prepare for the final confrontation.
        
        RESURRECTION: In the final battle, Luke chooses compassion
        over revenge, saving his father's soul.
        
        RETURN WITH ELIXIR: Luke brings balance to the Force and
        peace to the galaxy.
        """
        
        session_id = "heros_journey_test"
        
        # Get session
        session_result = await get_story_session(session_id=session_id)
        assert session_result["session_id"] == session_id
        
        # Analyze hero's journey structure
        analysis_result = await analyze_story_structure(story_content=heros_journey_story)
        
        # Should achieve good confidence for well-structured story
        assert analysis_result["confidence"] >= 0.75, "Hero's journey should score well"
        
        # Should identify correct structure type
        structure_type = analysis_result["structure_type"]
        assert structure_type in ["heros_journey", "hero_journey", "monomyth"], \
            f"Should identify hero's journey structure, got: {structure_type}"
        
        # Should identify hero's journey stages
        analysis = analysis_result["analysis"]
        if "stages" in analysis:
            stages = analysis["stages"]
            expected_stages = ["ordinary_world", "call_to_adventure", "mentor", "threshold"]
            
            stage_names = [stage.get("name", "").lower().replace("_", "").replace(" ", "") 
                          for stage in stages]
            
            found_stages = []
            for expected in expected_stages:
                expected_clean = expected.replace("_", "").replace(" ", "")
                if any(expected_clean in stage_name for stage_name in stage_names):
                    found_stages.append(expected)
            
            assert len(found_stages) >= 2, f"Should identify hero's journey stages: {found_stages}"
    
    @pytest.mark.asyncio
    async def test_multi_format_story_analysis(self):
        """Test analysis of different story formats (prose, screenplay, etc.)."""
        # Scenario: User submits screenplay format
        # Expected: Format-aware analysis with appropriate structure detection
        
        screenplay_content = """
        FADE IN:
        
        EXT. CITY STREET - DAY
        
        DETECTIVE SARAH CHEN (35) walks down a busy street,
        her phone ringing insistently.
        
        SARAH
        (answering phone)
        Chen here.
        
        VOICE (V.O.)
        There's been another murder.
        Same pattern as before.
        
        Sarah's expression hardens.
        
        SARAH
        I'll be right there.
        
        She hails a taxi.
        
        INT. TAXI - CONTINUOUS
        
        Sarah stares out the window, processing the information.
        
        SARAH
        (to herself)
        Three victims. Same killer.
        What's the connection?
        
        EXT. CRIME SCENE - DAY
        
        Sarah arrives at a cordoned-off alley where FORENSICS
        TEAM members work around a covered body.
        
        SARAH
        (to forensics tech)
        What do we know?
        
        FORENSICS TECH
        Same M.O. as the others.
        Killer left another message.
        
        The tech hands Sarah a note with cryptic symbols.
        
        SARAH
        (studying the note)
        These aren't random.
        He's telling us something.
        
        FADE OUT.
        """
        
        session_id = "screenplay_format_test"
        
        # Get session
        session_result = await get_story_session(session_id=session_id)
        assert session_result["session_id"] == session_id
        
        # Analyze screenplay format
        analysis_result = await analyze_story_structure(story_content=screenplay_content)
        
        # Should handle screenplay format appropriately
        assert analysis_result["confidence"] > 0.5, "Should analyze screenplay format"
        
        # Should recognize format-specific elements
        analysis = analysis_result["analysis"]
        if "format_detected" in analysis:
            assert "screenplay" in analysis["format_detected"].lower(), \
                "Should detect screenplay format"
        
        # Should identify structural elements appropriate to format
        if "scenes" in analysis:
            scenes = analysis["scenes"]
            assert len(scenes) >= 3, "Should identify multiple scenes in screenplay"
    
    @pytest.mark.asyncio
    async def test_session_state_integration(self):
        """Test integration between story analysis and session state management."""
        # Scenario: Multiple analyses within same session should maintain state
        # Expected: Session accumulates analysis history and context
        
        session_id = "session_integration_test"
        
        # First analysis
        story_part_1 = """
        Chapter 1: Sarah discovers the mysterious artifact in her grandmother's attic.
        The crystal pendant glows when she touches it, filling her with strange energy.
        """
        
        session_result_1 = await get_story_session(session_id=session_id)
        analysis_result_1 = await analyze_story_structure(story_content=story_part_1)
        
        # Second analysis - continuation of story
        story_part_2 = story_part_1 + """
        Chapter 2: Sarah learns the pendant belonged to a line of magical guardians.
        Her grandmother's journal reveals Sarah is the next chosen guardian.
        
        Chapter 3: Dark forces attack Sarah's town, seeking the pendant's power.
        Sarah must embrace her destiny to protect those she loves.
        """
        
        session_result_2 = await get_story_session(session_id=session_id)
        analysis_result_2 = await analyze_story_structure(story_content=story_part_2)
        
        # Verify session continuity
        assert session_result_1["session_id"] == session_result_2["session_id"]
        assert session_result_1["created_at"] == session_result_2["created_at"]
        
        # Second analysis should show more complete structure
        assert analysis_result_2["confidence"] >= analysis_result_1["confidence"], \
            "More complete story should have equal or higher confidence"
        
        # Session should maintain state across analyses
        assert session_result_2["last_updated"] >= session_result_1["last_updated"]
    
    @pytest.mark.asyncio
    async def test_observability_integration(self):
        """Test observability and monitoring integration throughout workflow."""
        # Constitutional: Observability (V) - verify structured logging and metrics
        
        story_content = "Sample story for observability integration testing..."
        session_id = "observability_test"
        
        # Get session with observability
        session_result = await get_story_session(session_id=session_id)
        
        # Analyze with observability
        analysis_result = await analyze_story_structure(story_content=story_content)
        
        # Verify observability metadata is present
        observability_fields = ["metadata", "execution_time", "performance_metrics"]
        session_has_observability = any(field in session_result for field in observability_fields)
        analysis_has_observability = any(field in analysis_result for field in observability_fields)
        
        assert session_has_observability or analysis_has_observability, \
            "Workflow must include observability metadata"
        
        # Verify metrics are available for monitoring
        if "metadata" in analysis_result:
            metadata = analysis_result["metadata"]
            assert "operation_type" in metadata, "Should specify operation type"
            assert "processing_time" in metadata or "execution_time" in metadata, \
                "Should include timing information"
        
        # Verify confidence scoring is properly tracked
        assert "confidence" in analysis_result, "Confidence must be tracked for monitoring"
        assert isinstance(analysis_result["confidence"], (int, float)), \
            "Confidence must be numeric for metrics"


@pytest.mark.integration
class TestStoryAnalysisErrorHandling:
    """Integration tests for error handling in story analysis workflow."""
    
    @pytest.mark.asyncio
    async def test_graceful_failure_handling(self):
        """Test graceful handling of various failure scenarios."""
        # Scenario: Network issues, service unavailable, etc.
        # Expected: Graceful degradation with meaningful error messages
        
        # Test with extremely long content that might cause processing issues
        very_long_story = "This is a test sentence. " * 10000
        session_id = "error_handling_test"
        
        try:
            session_result = await get_story_session(session_id=session_id)
            analysis_result = await analyze_story_structure(story_content=very_long_story)
            
            # If it succeeds, should handle gracefully
            assert isinstance(analysis_result, dict), "Should return structured response"
            assert "confidence" in analysis_result, "Should include confidence even for edge cases"
            
        except Exception as e:
            # If it fails, should provide meaningful error
            assert "timeout" in str(e).lower() or "length" in str(e).lower() or \
                   "processing" in str(e).lower(), "Error should be descriptive"
    
    @pytest.mark.asyncio
    async def test_malformed_input_recovery(self):
        """Test recovery from malformed input scenarios."""
        # Clarification B: Partial analysis for malformed content
        
        malformed_inputs = [
            ("", "empty_content_test"),
            ("   \n\t   ", "whitespace_test"),
            ("{'invalid': 'json'} content", "mixed_format_test"),
        ]
        
        for content, session_suffix in malformed_inputs:
            session_id = f"malformed_{session_suffix}"
            
            session_result = await get_story_session(session_id=session_id)
            analysis_result = await analyze_story_structure(story_content=content)
            
            # Should handle malformed input gracefully
            assert isinstance(analysis_result, dict), "Must return dict for malformed input"
            assert "confidence" in analysis_result, "Must include confidence"
            assert analysis_result["confidence"] <= 0.25, "Malformed content should score very low"
            
            # Should provide explanation for low confidence
            assert "analysis" in analysis_result, "Should explain analysis results"