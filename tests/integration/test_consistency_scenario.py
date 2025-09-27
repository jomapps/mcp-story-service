"""Integration test for consistency validation scenario (T015)."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.services.session_manager import StorySessionManager
from src.services.consistency.validator import ConsistencyValidator
from src.models.story import StoryData
from src.models.analysis import AnalysisResult


@pytest.fixture
async def session_manager():
    """Create session manager for testing."""
    manager = StorySessionManager(workspace_dir="test_workspaces")
    yield manager
    # Cleanup after test
    try:
        active_sessions = await manager.list_active_sessions()
        for session in active_sessions:
            await manager.terminate_session(session.session_id)
    except Exception:
        pass


@pytest.fixture
async def consistency_validator():
    """Create consistency validator for testing."""
    return ConsistencyValidator()


@pytest.fixture
def story_elements_with_issues():
    """Story elements containing consistency issues for testing."""
    return {
        "characters": [
            {
                "name": "Sarah Chen",
                "role": "detective", 
                "introduced": "episode_1",
                "attributes": {
                    "age": 35,
                    "rank": "Detective",
                    "experience": "10 years",
                    "personality": "methodical, determined"
                }
            },
            {
                "name": "Partner Mike",
                "role": "corrupt_cop",
                "introduced": "episode_1", 
                "attributes": {
                    "age": 42,
                    "rank": "Detective",
                    "experience": "15 years",
                    "personality": "charming, secretive"
                }
            }
        ],
        "events": [
            {
                "id": "event_1",
                "description": "Sarah discovers evidence of corruption",
                "episode": 1,
                "timestamp": "day_1_morning",
                "location": "police_station",
                "characters": ["Sarah Chen"]
            },
            {
                "id": "event_2", 
                "description": "Mike warns conspirators about discovery",
                "episode": 2,
                "timestamp": "day_1_afternoon",  # ISSUE: How did he know so quickly?
                "location": "unknown_location",
                "characters": ["Partner Mike"]
            },
            {
                "id": "event_3",
                "description": "Sarah confronts Mike about his involvement",
                "episode": 3,
                "timestamp": "day_5_evening",
                "location": "police_station",
                "characters": ["Sarah Chen", "Partner Mike"]
            },
            {
                "id": "event_4",
                "description": "Mike reveals he's been investigating too",  # CONTRADICTION
                "episode": 4,
                "timestamp": "day_6_morning",
                "location": "police_station", 
                "characters": ["Partner Mike", "Sarah Chen"]
            }
        ],
        "world_details": [
            {
                "aspect": "police_department",
                "description": "Small city department with 20 officers",
                "consistency_rule": "Information spreads quickly in small departments"
            },
            {
                "aspect": "corruption_network",
                "description": "Network includes city officials and police",
                "consistency_rule": "Network members communicate regularly"
            }
        ],
        "timeline": [
            {"event": "Discovery", "day": 1, "time": "morning"},
            {"event": "Warning", "day": 1, "time": "afternoon"},
            {"event": "Investigation continues", "day": 2, "time": "all_day"},
            {"event": "Confrontation", "day": 5, "time": "evening"},
            {"event": "Revelation", "day": 6, "time": "morning"}
        ]
    }


@pytest.fixture
def story_elements_consistent():
    """Story elements that are internally consistent."""
    return {
        "characters": [
            {
                "name": "Detective Alice",
                "role": "protagonist",
                "introduced": "episode_1",
                "attributes": {
                    "age": 32,
                    "rank": "Detective",
                    "experience": "8 years"
                }
            }
        ],
        "events": [
            {
                "id": "event_1",
                "description": "Alice receives case assignment",
                "episode": 1,
                "timestamp": "day_1_morning",
                "location": "police_station",
                "characters": ["Detective Alice"]
            },
            {
                "id": "event_2",
                "description": "Alice interviews witness",
                "episode": 1,
                "timestamp": "day_1_afternoon",
                "location": "witness_home",
                "characters": ["Detective Alice"]
            }
        ],
        "world_details": [
            {
                "aspect": "police_protocol",
                "description": "Standard investigation procedures followed",
                "consistency_rule": "Officers follow established protocols"
            }
        ],
        "timeline": [
            {"event": "Case assignment", "day": 1, "time": "morning"},
            {"event": "Witness interview", "day": 1, "time": "afternoon"}
        ]
    }


class TestConsistencyValidationScenario:
    """Integration test for consistency validation functionality."""
    
    @pytest.mark.asyncio
    async def test_plot_hole_detection_with_severity_ratings(
        self, session_manager, consistency_validator, story_elements_with_issues
    ):
        """Test detection of plot holes with appropriate severity ratings."""
        # Create session for project isolation
        project_id = "consistency-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Create story data with consistency issues
        story_data = StoryData(
            content="Story with plot holes and character inconsistencies",
            metadata={
                "analysis_type": "consistency_validation",
                "story_elements": story_elements_with_issues
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Perform consistency validation
        analysis_result = await consistency_validator.validate_consistency(story_data)
        
        # Verify analysis structure
        assert analysis_result.analysis_type == "consistency_validation"
        assert "violations" in analysis_result.data
        assert "overall_consistency" in analysis_result.data
        
        violations = analysis_result.data["violations"]
        overall = analysis_result.data["overall_consistency"]
        
        # Should detect the plot hole: How did Mike know to warn conspirators?
        information_flow_violation = None
        for violation in violations:
            if "information" in violation.get("description", "").lower() or "know" in violation.get("description", "").lower():
                information_flow_violation = violation
                break
        
        assert information_flow_violation is not None, "Should detect information flow plot hole"
        
        # Verify severity rating
        assert "severity" in information_flow_violation
        assert information_flow_violation["severity"] in ["critical", "major", "minor"]
        
        # Should be major or critical since it's a significant plot hole
        assert information_flow_violation["severity"] in ["critical", "major"]
        
        # Check for character contradiction detection
        contradiction_violation = None
        for violation in violations:
            if "contradict" in violation.get("description", "").lower() or "inconsist" in violation.get("description", "").lower():
                contradiction_violation = violation
                break
        
        if contradiction_violation:
            assert "severity" in contradiction_violation
            assert contradiction_violation["severity"] in ["critical", "major", "minor"]
        
        # Verify confidence scoring
        assert analysis_result.confidence >= 0.0
        assert analysis_result.confidence <= 1.0
        
        # Check overall consistency assessment
        assert "score" in overall
        assert overall["score"] >= 0.0
        assert overall["score"] <= 1.0
        
        # With plot holes present, score should be lower
        assert overall["score"] < 0.9
    
    @pytest.mark.asyncio
    async def test_timeline_consistency_validation(
        self, session_manager, consistency_validator
    ):
        """Test timeline and chronological consistency validation."""
        project_id = "timeline-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Story elements with timeline issues
        timeline_issues = {
            "characters": [
                {"name": "John", "role": "witness", "introduced": "episode_1"}
            ],
            "events": [
                {
                    "id": "event_1",
                    "description": "Meeting scheduled for Friday",
                    "episode": 1,
                    "timestamp": "friday_morning",
                    "characters": ["John"]
                },
                {
                    "id": "event_2",
                    "description": "John attends meeting as planned",
                    "episode": 1, 
                    "timestamp": "thursday_afternoon",  # TIMELINE ERROR: Meeting before it was scheduled
                    "characters": ["John"]
                },
                {
                    "id": "event_3",
                    "description": "Follow-up discussion about meeting",
                    "episode": 2,
                    "timestamp": "friday_evening",
                    "characters": ["John"]
                }
            ],
            "timeline": [
                {"event": "Meeting scheduled", "day": "friday", "time": "morning"},
                {"event": "Meeting attended", "day": "thursday", "time": "afternoon"},  # ISSUE
                {"event": "Follow-up", "day": "friday", "time": "evening"}
            ]
        }
        
        story_data = StoryData(
            content="Story with timeline inconsistencies",
            metadata={"analysis_type": "timeline_validation", "story_elements": timeline_issues}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Validate timeline consistency
        analysis_result = await consistency_validator.validate_consistency(story_data)
        violations = analysis_result.data["violations"]
        
        # Should detect timeline violation
        timeline_violation = None
        for violation in violations:
            if "timeline" in violation.get("type", "").lower() or "chronolog" in violation.get("description", "").lower():
                timeline_violation = violation
                break
        
        assert timeline_violation is not None, "Should detect timeline inconsistency"
        
        # Verify timeline violation details
        assert "severity" in timeline_violation
        assert timeline_violation["severity"] in ["critical", "major", "minor"]
        
        # Should suggest specific fix
        assert "suggested_fix" in timeline_violation
        assert len(timeline_violation["suggested_fix"]) > 0
        
        # Verify confidence impact
        assert "confidence_impact" in timeline_violation
        assert timeline_violation["confidence_impact"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_character_motivation_consistency(
        self, session_manager, consistency_validator
    ):
        """Test character behavior and motivation consistency validation."""
        project_id = "character-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Character with contradictory behavior
        character_issues = {
            "characters": [
                {
                    "name": "Detective Brown",
                    "role": "by_the_book_cop",
                    "introduced": "episode_1",
                    "attributes": {
                        "personality": "strictly follows rules and procedures",
                        "motivation": "uphold the law at all costs",
                        "background": "military veteran, values discipline"
                    }
                }
            ],
            "events": [
                {
                    "id": "event_1",
                    "description": "Brown refuses to bend rules for colleague",
                    "episode": 1,
                    "timestamp": "day_1",
                    "characters": ["Detective Brown"]
                },
                {
                    "id": "event_2", 
                    "description": "Brown breaks into suspect's home without warrant",  # INCONSISTENT
                    "episode": 2,
                    "timestamp": "day_2",
                    "characters": ["Detective Brown"]
                },
                {
                    "id": "event_3",
                    "description": "Brown lectures partner about following protocol",
                    "episode": 3,
                    "timestamp": "day_3",
                    "characters": ["Detective Brown"]
                }
            ]
        }
        
        story_data = StoryData(
            content="Story with character behavior inconsistencies",
            metadata={"analysis_type": "character_validation", "story_elements": character_issues}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Validate character consistency
        analysis_result = await consistency_validator.validate_consistency(story_data)
        violations = analysis_result.data["violations"]
        
        # Should detect character inconsistency
        character_violation = None
        for violation in violations:
            if "character" in violation.get("type", "").lower() or "behav" in violation.get("description", "").lower():
                character_violation = violation
                break
        
        assert character_violation is not None, "Should detect character behavior inconsistency"
        
        # Verify character violation details
        assert "severity" in character_violation
        
        # Character inconsistency should be at least major severity
        assert character_violation["severity"] in ["critical", "major"]
        
        # Should include specific location and fix suggestion
        assert "location" in character_violation
        assert "suggested_fix" in character_violation
        
        # Fix should address the contradiction
        fix_text = character_violation["suggested_fix"].lower()
        assert "motivation" in fix_text or "character" in fix_text or "consistent" in fix_text
    
    @pytest.mark.asyncio
    async def test_consistent_story_validation(
        self, session_manager, consistency_validator, story_elements_consistent
    ):
        """Test validation of a story with good consistency."""
        project_id = "consistent-test-001"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content="Well-structured story without consistency issues",
            metadata={"analysis_type": "consistency_validation", "story_elements": story_elements_consistent}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Validate consistent story
        analysis_result = await consistency_validator.validate_consistency(story_data)
        
        violations = analysis_result.data["violations"]
        overall = analysis_result.data["overall_consistency"]
        
        # Should have few or no violations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        assert len(critical_violations) == 0, "Consistent story should have no critical violations"
        
        major_violations = [v for v in violations if v.get("severity") == "major"]
        assert len(major_violations) <= 1, "Consistent story should have minimal major violations"
        
        # Overall score should be high
        assert overall["score"] >= 0.8, "Consistent story should have high consistency score"
        
        # Confidence should be high
        assert analysis_result.confidence >= 0.75, "Should meet 75% confidence threshold"
        
        # Should identify strengths
        if "strengths" in analysis_result.data:
            strengths = analysis_result.data["strengths"]
            assert isinstance(strengths, list)
            assert len(strengths) > 0
    
    @pytest.mark.asyncio
    async def test_validation_scope_filtering(
        self, session_manager, consistency_validator, story_elements_with_issues
    ):
        """Test validation with specific scope filtering."""
        project_id = "scope-test-001"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content="Story for scope-specific validation",
            metadata={
                "analysis_type": "scoped_validation",
                "story_elements": story_elements_with_issues,
                "validation_scope": ["timeline", "character"]  # Exclude plot and world
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Validate with scope filtering
        analysis_result = await consistency_validator.validate_consistency(story_data)
        violations = analysis_result.data["violations"]
        
        # Should only include timeline and character violations
        for violation in violations:
            violation_type = violation.get("type", "").lower()
            assert violation_type in ["timeline", "character", "chronological", "behavior"], \
                f"Unexpected violation type: {violation_type}"
        
        # Should still detect timeline and character issues
        has_timeline = any("timeline" in v.get("type", "").lower() for v in violations)
        has_character = any("character" in v.get("type", "").lower() for v in violations)
        
        # At least one of these should be detected given our test data
        assert has_timeline or has_character, "Should detect scoped violations"
    
    @pytest.mark.asyncio
    async def test_confidence_impact_calculation(
        self, session_manager, consistency_validator, story_elements_with_issues
    ):
        """Test that violations properly impact confidence scoring."""
        project_id = "confidence-impact-test-001"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content="Story with known consistency issues for confidence testing",
            metadata={"analysis_type": "confidence_impact", "story_elements": story_elements_with_issues}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Validate story with issues
        analysis_result = await consistency_validator.validate_consistency(story_data)
        
        violations = analysis_result.data["violations"]
        
        # Each violation should have confidence impact
        for violation in violations:
            assert "confidence_impact" in violation
            assert violation["confidence_impact"] >= 0.0
            assert violation["confidence_impact"] <= 1.0
            
            # Critical/major violations should have higher impact
            if violation.get("severity") in ["critical", "major"]:
                assert violation["confidence_impact"] >= 0.1
        
        # Total confidence should be impacted by violations
        if len(violations) > 0:
            # With violations, confidence should be below perfect score
            assert analysis_result.confidence < 1.0
            
            # Calculate expected impact
            total_impact = sum(v.get("confidence_impact", 0) for v in violations)
            
            # Confidence should reflect the cumulative impact
            if total_impact > 0.1:  # Significant violations
                assert analysis_result.confidence < 0.9


if __name__ == "__main__":
    pytest.main([__file__])