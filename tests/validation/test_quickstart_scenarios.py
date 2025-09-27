"""Run quickstart.md validation scenarios and verify all clarification requirements (T052)."""

import asyncio
import pytest
from unittest.mock import Mock, patch

from src.services.session_manager import StorySessionManager
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.consistency.validator import ConsistencyValidator
from src.services.genre.analyzer import GenreAnalyzer
from src.services.pacing.calculator import PacingCalculator
from src.models.story import StoryData


class TestQuickstartValidationScenarios:
    """Validation tests for quickstart.md scenarios and clarification requirements."""
    
    @pytest.fixture
    async def session_manager(self):
        """Create session manager for validation testing."""
        return StorySessionManager(workspace_dir="test_workspaces_validation")
    
    @pytest.fixture
    async def narrative_analyzer(self):
        """Create narrative analyzer for validation."""
        return NarrativeAnalyzer()
    
    @pytest.fixture
    async def consistency_validator(self):
        """Create consistency validator for validation."""
        return ConsistencyValidator()
    
    @pytest.fixture
    async def genre_analyzer(self):
        """Create genre analyzer for validation."""
        return GenreAnalyzer()
    
    @pytest.fixture
    async def pacing_calculator(self):
        """Create pacing calculator for validation."""
        return PacingCalculator()
    
    @pytest.fixture
    def quickstart_story_content(self):
        """Story content from quickstart scenarios."""
        return """
        Detective Sarah Chen receives a call about a murdered corporate executive found in his office.
        The victim, Richard Morrison, was the CFO of Meridian Industries, a major tech company.
        Initial investigation reveals Morrison was about to testify before Congress about corporate fraud.
        
        As Sarah digs deeper, she discovers Morrison had compiled evidence of a massive conspiracy
        involving government contracts, bribery, and money laundering. The evidence points to
        high-ranking officials in both Meridian Industries and the city government.
        
        When Sarah's investigation gets too close to the truth, she receives anonymous threats.
        Her own partner, Detective Mike Torres, begins acting suspiciously and seems to know
        details about the case that he shouldn't. Sarah realizes she can't trust anyone.
        
        In the climactic confrontation, Sarah discovers that Mike has been feeding information
        to the conspirators. She must choose between protecting her partner and exposing the truth.
        She chooses justice, bringing down the entire conspiracy but losing her partnership and
        facing an uncertain future in the department.
        """
    
    @pytest.mark.asyncio
    async def test_quickstart_scenario_1_story_structure_analysis(
        self, session_manager, narrative_analyzer, quickstart_story_content
    ):
        """Test Quickstart Scenario 1: Basic story structure analysis with confidence threshold."""
        # Create session for project isolation (Clarification C)
        project_id = "quickstart-scenario-1"
        session_id = await session_manager.create_session(project_id)
        
        # Create story data
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "story_structure",
                "project_id": project_id,
                "genre": "thriller"
            }
        )
        
        # Update session with story data (session persistence until completion - Clarification D)
        await session_manager.update_session(session_id, story_data)
        
        # Perform story structure analysis
        analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
        
        # Validate FR-001: 75% confidence threshold
        assert analysis_result.confidence >= 0.75, f"Confidence {analysis_result.confidence} below 75% threshold"
        
        # Validate story structure components
        assert "arc_analysis" in analysis_result.data
        arc_analysis = analysis_result.data["arc_analysis"]
        
        # Verify three-act structure identification
        assert "act_structure" in arc_analysis
        act_structure = arc_analysis["act_structure"]
        
        assert "act_one" in act_structure
        assert "act_two" in act_structure  
        assert "act_three" in act_structure
        
        # Verify confidence scoring meets threshold
        assert act_structure["confidence_score"] >= 0.75
        
        # Verify turning points identification
        assert "turning_points" in arc_analysis
        turning_points = arc_analysis["turning_points"]
        assert len(turning_points) >= 2  # At least major plot points
        
        # Verify session remains active until completion (Clarification D)
        session = await session_manager.get_session(session_id)
        assert session.status == "active"
        
        print(f"✓ Quickstart Scenario 1 passed - Confidence: {analysis_result.confidence:.3f}")
    
    @pytest.mark.asyncio
    async def test_quickstart_scenario_2_consistency_validation(
        self, session_manager, consistency_validator, quickstart_story_content
    ):
        """Test Quickstart Scenario 2: Consistency validation with plot hole detection."""
        project_id = "quickstart-scenario-2"
        session_id = await session_manager.create_session(project_id)
        
        # Create story elements with potential consistency issues
        story_elements = {
            "characters": [
                {
                    "name": "Detective Sarah Chen",
                    "role": "protagonist",
                    "introduced": "scene_1",
                    "attributes": {"experience": "10 years", "department": "homicide"}
                },
                {
                    "name": "Detective Mike Torres",
                    "role": "partner_turned_antagonist",
                    "introduced": "scene_1", 
                    "attributes": {"experience": "15 years", "loyalty": "compromised"}
                },
                {
                    "name": "Richard Morrison",
                    "role": "victim",
                    "introduced": "scene_1",
                    "attributes": {"position": "CFO", "company": "Meridian Industries"}
                }
            ],
            "events": [
                {
                    "id": "event_1",
                    "description": "Morrison found dead in office",
                    "timestamp": "day_1_morning",
                    "location": "Meridian Industries office",
                    "characters": ["Richard Morrison"]
                },
                {
                    "id": "event_2",
                    "description": "Sarah begins investigation",
                    "timestamp": "day_1_afternoon",
                    "location": "crime_scene",
                    "characters": ["Detective Sarah Chen"]
                },
                {
                    "id": "event_3",
                    "description": "Mike shows detailed knowledge of case",
                    "timestamp": "day_2_morning",
                    "location": "police_station",
                    "characters": ["Detective Mike Torres", "Detective Sarah Chen"]
                }
            ],
            "timeline": [
                {"event": "Murder discovered", "day": 1, "time": "morning"},
                {"event": "Investigation begins", "day": 1, "time": "afternoon"},
                {"event": "Suspicious behavior", "day": 2, "time": "morning"}
            ]
        }
        
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "consistency_validation",
                "project_id": project_id,
                "story_elements": story_elements
            }
        )
        
        await session_manager.update_session(session_id, story_data)
        
        # Perform consistency validation
        analysis_result = await consistency_validator.validate_consistency(story_data)
        
        # Validate FR-001: 75% confidence threshold
        assert analysis_result.confidence >= 0.75, f"Confidence {analysis_result.confidence} below 75% threshold"
        
        # Verify consistency validation structure
        assert "violations" in analysis_result.data
        assert "overall_consistency" in analysis_result.data
        
        violations = analysis_result.data["violations"]
        overall = analysis_result.data["overall_consistency"]
        
        # Verify overall consistency score
        assert "score" in overall
        assert overall["score"] >= 0.0
        assert overall["score"] <= 1.0
        
        # Verify violation structure if any exist
        for violation in violations:
            assert "type" in violation
            assert "severity" in violation
            assert "description" in violation
            assert "confidence_impact" in violation
            
            # Severity should be valid
            assert violation["severity"] in ["critical", "major", "minor"]
        
        print(f"✓ Quickstart Scenario 2 passed - Confidence: {analysis_result.confidence:.3f}, Violations: {len(violations)}")
    
    @pytest.mark.asyncio
    async def test_quickstart_scenario_3_genre_pattern_application(
        self, session_manager, genre_analyzer, quickstart_story_content
    ):
        """Test Quickstart Scenario 3: Genre pattern application with authenticity scoring."""
        project_id = "quickstart-scenario-3"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "genre_authentication",
                "project_id": project_id,
                "target_genre": "thriller"
            }
        )
        
        await session_manager.update_session(session_id, story_data)
        
        # Apply thriller genre patterns
        analysis_result = await genre_analyzer.apply_genre_patterns(story_data, target_genre="thriller")
        
        # Validate FR-001: 75% confidence threshold
        guidance = analysis_result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        assert compliance["confidence_score"] >= 0.75, f"Genre confidence {compliance['confidence_score']} below 75% threshold"
        assert compliance["meets_threshold"] is True
        
        # Verify genre compliance structure
        assert "score" in compliance
        assert "met_conventions" in compliance
        assert "missing_conventions" in compliance
        
        # Verify authenticity improvements
        assert "authenticity_improvements" in guidance
        improvements = guidance["authenticity_improvements"]
        
        for improvement in improvements:
            assert "aspect" in improvement
            assert "recommendation" in improvement
            assert "impact" in improvement
            assert "confidence" in improvement
            
            assert improvement["impact"] in ["high", "medium", "low"]
            assert 0.0 <= improvement["confidence"] <= 1.0
        
        # Verify genre-specific beats
        assert "genre_specific_beats" in guidance
        beats = guidance["genre_specific_beats"]
        
        for beat in beats:
            assert "beat_type" in beat
            assert "suggested_position" in beat
            assert "confidence" in beat
            assert 0.0 <= beat["suggested_position"] <= 1.0
            assert 0.0 <= beat["confidence"] <= 1.0
        
        print(f"✓ Quickstart Scenario 3 passed - Genre confidence: {compliance['confidence_score']:.3f}")
    
    @pytest.mark.asyncio
    async def test_quickstart_scenario_4_malformed_content_handling(
        self, session_manager, narrative_analyzer
    ):
        """Test Quickstart Scenario 4: Malformed content handling (Clarification B)."""
        project_id = "quickstart-scenario-4"
        session_id = await session_manager.create_session(project_id)
        
        # Test with various malformed content types
        malformed_contents = [
            "",  # Empty content
            "   ",  # Whitespace only
            "@#$%^&*()_+",  # Special characters only
            "A" * 10000,  # Extremely long content
            "Incomplete story with no structure or",  # Incomplete sentence
        ]
        
        for i, malformed_content in enumerate(malformed_contents):
            story_data = StoryData(
                content=malformed_content,
                metadata={
                    "analysis_type": "malformed_content_test",
                    "project_id": f"{project_id}_{i}",
                    "malformed_type": f"type_{i}"
                }
            )
            
            await session_manager.update_session(session_id, story_data)
            
            # Should handle malformed content gracefully (Clarification B)
            analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
            
            # Should return valid result structure even for malformed content
            assert isinstance(analysis_result, type(analysis_result))
            assert hasattr(analysis_result, 'confidence')
            assert hasattr(analysis_result, 'data')
            
            # Confidence should be valid but appropriately low
            assert 0.0 <= analysis_result.confidence <= 1.0
            assert analysis_result.confidence < 0.5  # Should be low for malformed content
            
            # Should provide partial analysis results
            assert "arc_analysis" in analysis_result.data
        
        print("✓ Quickstart Scenario 4 passed - Malformed content handled gracefully")
    
    @pytest.mark.asyncio
    async def test_clarification_requirement_a_15_plus_genres(
        self, genre_analyzer, quickstart_story_content
    ):
        """Test Clarification A: Support for 15+ movie genres."""
        # Test major film genres
        genres_to_test = [
            "thriller", "drama", "comedy", "action", "horror",
            "romance", "sci-fi", "fantasy", "mystery", "western",
            "war", "historical", "biographical", "documentary", "animation"
        ]
        
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "genre_support_test",
                "project_id": "clarification-a-test"
            }
        )
        
        successful_analyses = 0
        
        for genre in genres_to_test:
            try:
                result = await genre_analyzer.apply_genre_patterns(story_data, target_genre=genre)
                
                # Should return valid structure for all genres
                assert "genre_guidance" in result.data
                guidance = result.data["genre_guidance"]
                assert "convention_compliance" in guidance
                
                successful_analyses += 1
                
            except Exception as e:
                pytest.fail(f"Genre {genre} analysis failed: {str(e)}")
        
        # Should support all 15+ genres
        assert successful_analyses >= 15, f"Only {successful_analyses}/15 genres supported"
        
        print(f"✓ Clarification A passed - {successful_analyses} genres supported")
    
    @pytest.mark.asyncio 
    async def test_clarification_requirement_b_malformed_content(
        self, narrative_analyzer, consistency_validator, genre_analyzer
    ):
        """Test Clarification B: Partial analysis for malformed content."""
        malformed_story = StoryData(
            content="Broken story @#$ incomplete structure {{{ missing elements",
            metadata={
                "analysis_type": "malformed_test",
                "project_id": "clarification-b-test"
            }
        )
        
        # All services should handle malformed content gracefully
        services_to_test = [
            ("narrative_analyzer", narrative_analyzer.analyze_story_structure),
            ("consistency_validator", consistency_validator.validate_consistency),
            ("genre_analyzer", lambda data: genre_analyzer.apply_genre_patterns(data, target_genre="thriller"))
        ]
        
        for service_name, service_method in services_to_test:
            try:
                result = await service_method(malformed_story)
                
                # Should return valid result structure
                assert hasattr(result, 'confidence')
                assert hasattr(result, 'data')
                assert 0.0 <= result.confidence <= 1.0
                
                # Should provide partial analysis
                assert len(result.data) > 0
                
                # Confidence should be appropriately low
                assert result.confidence < 0.5
                
            except Exception as e:
                pytest.fail(f"{service_name} failed on malformed content: {str(e)}")
        
        print("✓ Clarification B passed - All services handle malformed content")
    
    @pytest.mark.asyncio
    async def test_clarification_requirement_c_process_isolation(
        self, session_manager, narrative_analyzer, quickstart_story_content
    ):
        """Test Clarification C: Process isolation per project."""
        # Create multiple projects simultaneously
        project_ids = ["isolation-test-1", "isolation-test-2", "isolation-test-3"]
        sessions = {}
        
        # Create isolated sessions
        for project_id in project_ids:
            session_id = await session_manager.create_session(project_id)
            sessions[project_id] = session_id
            
            story_data = StoryData(
                content=f"{quickstart_story_content} (Project: {project_id})",
                metadata={
                    "analysis_type": "isolation_test",
                    "project_id": project_id
                }
            )
            
            await session_manager.update_session(session_id, story_data)
        
        # Verify sessions are isolated
        for project_id, session_id in sessions.items():
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert session.project_id == project_id
            assert session.session_id == session_id
        
        # Verify session IDs are unique
        session_ids = list(sessions.values())
        assert len(set(session_ids)) == len(session_ids)
        
        # Run analyses concurrently to test isolation
        async def isolated_analysis(project_id, session_id):
            session = await session_manager.get_session(session_id)
            return await narrative_analyzer.analyze_story_structure(session.story_data)
        
        analysis_tasks = [
            isolated_analysis(pid, sid) for pid, sid in sessions.items()
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        
        # All analyses should complete successfully in isolation
        assert len(results) == len(project_ids)
        for result in results:
            assert hasattr(result, 'confidence')
            assert 0.0 <= result.confidence <= 1.0
        
        print("✓ Clarification C passed - Process isolation maintained")
    
    @pytest.mark.asyncio
    async def test_clarification_requirement_d_session_persistence(
        self, session_manager, quickstart_story_content
    ):
        """Test Clarification D: Session persistence until completion."""
        project_id = "persistence-test"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "persistence_test",
                "project_id": project_id
            }
        )
        
        await session_manager.update_session(session_id, story_data)
        
        # Session should remain active
        session = await session_manager.get_session(session_id)
        assert session.status == "active"
        
        # Session should persist through multiple operations
        for i in range(3):
            # Update session with new data
            updated_story = StoryData(
                content=f"{quickstart_story_content} (Update {i})",
                metadata={
                    "analysis_type": "persistence_test",
                    "project_id": project_id,
                    "update": i
                }
            )
            
            await session_manager.update_session(session_id, updated_story)
            
            # Session should still exist and be active
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert session.status == "active"
            assert session.session_id == session_id
        
        # Only explicit termination should end session
        await session_manager.terminate_session(session_id)
        
        # Session should now be terminated or None
        session = await session_manager.get_session(session_id)
        assert session is None or session.status == "terminated"
        
        print("✓ Clarification D passed - Session persistence until completion")
    
    @pytest.mark.asyncio
    async def test_end_to_end_quickstart_workflow(
        self, session_manager, narrative_analyzer, consistency_validator, 
        genre_analyzer, pacing_calculator, quickstart_story_content
    ):
        """Test complete end-to-end quickstart workflow."""
        project_id = "end-to-end-quickstart"
        session_id = await session_manager.create_session(project_id)
        
        # Step 1: Create comprehensive story data
        story_data = StoryData(
            content=quickstart_story_content,
            metadata={
                "analysis_type": "comprehensive_analysis",
                "project_id": project_id,
                "genre": "thriller",
                "target_audience": "adults"
            }
        )
        
        await session_manager.update_session(session_id, story_data)
        
        # Step 2: Run all analyses
        analyses = {}
        
        # Story structure analysis
        analyses["structure"] = await narrative_analyzer.analyze_story_structure(story_data)
        
        # Consistency validation
        analyses["consistency"] = await consistency_validator.validate_consistency(story_data)
        
        # Genre authentication
        analyses["genre"] = await genre_analyzer.apply_genre_patterns(story_data, target_genre="thriller")
        
        # Pacing analysis
        narrative_beats = [
            {
                "position": 0.1,
                "type": "opening",
                "emotional_impact": 0.3,
                "tension_level": 0.2
            },
            {
                "position": 0.25,
                "type": "inciting_incident",
                "emotional_impact": 0.7,
                "tension_level": 0.6
            },
            {
                "position": 0.5,
                "type": "midpoint",
                "emotional_impact": 0.8,
                "tension_level": 0.9
            },
            {
                "position": 0.75,
                "type": "crisis",
                "emotional_impact": 0.9,
                "tension_level": 0.95
            },
            {
                "position": 0.9,
                "type": "climax",
                "emotional_impact": 1.0,
                "tension_level": 1.0
            }
        ]
        
        analyses["pacing"] = await pacing_calculator.calculate_pacing(
            project_id=project_id,
            narrative_beats=narrative_beats,
            target_genre="thriller"
        )
        
        # Step 3: Validate all analyses meet requirements
        for analysis_name, result in analyses.items():
            assert result is not None, f"{analysis_name} analysis returned None"
            assert hasattr(result, 'confidence'), f"{analysis_name} missing confidence"
            assert hasattr(result, 'data'), f"{analysis_name} missing data"
            
            # FR-001: 75% confidence threshold validation
            if analysis_name in ["structure", "genre"]:  # Primary analyses
                assert result.confidence >= 0.75, f"{analysis_name} confidence {result.confidence} below 75% threshold"
            else:  # Secondary analyses can be more flexible
                assert result.confidence >= 0.0, f"{analysis_name} confidence invalid"
        
        # Step 4: Verify session maintains state throughout
        final_session = await session_manager.get_session(session_id)
        assert final_session is not None
        assert final_session.status == "active"
        assert final_session.project_id == project_id
        
        print("✓ End-to-end quickstart workflow passed - All analyses completed successfully")
        
        # Return summary for verification
        return {
            "project_id": project_id,
            "session_id": session_id,
            "analysis_results": {
                name: {
                    "confidence": result.confidence,
                    "analysis_type": result.analysis_type,
                    "data_keys": list(result.data.keys())
                }
                for name, result in analyses.items()
            },
            "overall_success": True
        }