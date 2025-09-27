"""Unit tests for consistency validation logic with malformed content handling (T049)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.services.consistency.validator import ConsistencyValidator
from src.models.story import StoryData
from src.models.analysis import AnalysisResult
from src.models.consistency_rule import ConsistencyRule


class TestConsistencyValidator:
    """Unit tests for ConsistencyValidator logic."""
    
    @pytest.fixture
    def consistency_validator(self):
        """Create ConsistencyValidator instance for testing."""
        return ConsistencyValidator()
    
    @pytest.fixture
    def consistent_story_elements(self):
        """Sample consistent story elements for testing."""
        return {
            "characters": [
                {
                    "name": "Detective Alice",
                    "role": "protagonist",
                    "introduced": "episode_1",
                    "attributes": {
                        "age": 32,
                        "rank": "Detective",
                        "experience": "8 years",
                        "personality": "methodical, determined"
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
    
    @pytest.fixture
    def inconsistent_story_elements(self):
        """Sample inconsistent story elements for testing."""
        return {
            "characters": [
                {
                    "name": "Sarah Chen",
                    "role": "detective",
                    "introduced": "episode_1",
                    "attributes": {
                        "age": 35,
                        "rank": "Detective",
                        "experience": "10 years"
                    }
                },
                {
                    "name": "Partner Mike",
                    "role": "corrupt_cop",
                    "introduced": "episode_1",
                    "attributes": {
                        "age": 42,
                        "rank": "Detective", 
                        "experience": "15 years"
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
                    "description": "Mike reveals he's been investigating too",  # CONTRADICTION
                    "episode": 4,
                    "timestamp": "day_6_morning",
                    "location": "police_station",
                    "characters": ["Partner Mike", "Sarah Chen"]
                }
            ],
            "timeline": [
                {"event": "Discovery", "day": 1, "time": "morning"},
                {"event": "Warning", "day": 1, "time": "afternoon"},
                {"event": "Revelation", "day": 6, "time": "morning"}
            ]
        }
    
    @pytest.fixture
    def malformed_story_elements(self):
        """Sample malformed story elements for testing."""
        return {
            "characters": [
                {
                    # Missing required fields
                    "role": "protagonist",
                    "attributes": "not_a_dict"  # Wrong type
                }
            ],
            "events": [
                {
                    "id": "event_1",
                    # Missing description, episode, timestamp
                    "location": "",
                    "characters": "not_a_list"  # Wrong type
                },
                "not_an_object"  # Wrong type
            ],
            "world_details": None,  # Wrong type
            "timeline": [
                {"event": "Incomplete event"}  # Missing day, time
            ]
        }
    
    @pytest.mark.asyncio
    async def test_validate_consistency_with_consistent_elements(
        self, consistency_validator, consistent_story_elements
    ):
        """Test consistency validation with well-formed consistent elements."""
        story_data = StoryData(
            content="Consistent detective story",
            metadata={
                "analysis_type": "consistency_validation",
                "story_elements": consistent_story_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "consistency_validation"
        assert "violations" in result.data
        assert "overall_consistency" in result.data
        
        violations = result.data["violations"]
        overall = result.data["overall_consistency"]
        
        # Should have few or no violations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        assert len(critical_violations) == 0
        
        # Overall score should be high
        assert "score" in overall
        assert overall["score"] >= 0.8
        
        # Confidence should be high
        assert result.confidence >= 0.75
    
    @pytest.mark.asyncio
    async def test_validate_consistency_with_plot_holes(
        self, consistency_validator, inconsistent_story_elements
    ):
        """Test detection of plot holes and logical inconsistencies."""
        story_data = StoryData(
            content="Story with plot holes and character inconsistencies",
            metadata={
                "analysis_type": "plot_hole_detection",
                "story_elements": inconsistent_story_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        
        violations = result.data["violations"]
        
        # Should detect plot hole: How did Mike know to warn conspirators?
        information_flow_violation = None
        for violation in violations:
            if "information" in violation.get("description", "").lower() or "know" in violation.get("description", "").lower():
                information_flow_violation = violation
                break
        
        assert information_flow_violation is not None
        
        # Should have appropriate severity
        assert "severity" in information_flow_violation
        assert information_flow_violation["severity"] in ["critical", "major"]
        
        # Should have suggested fix
        assert "suggested_fix" in information_flow_violation
        assert len(information_flow_violation["suggested_fix"]) > 0
        
        # Should impact confidence
        assert "confidence_impact" in information_flow_violation
        assert information_flow_violation["confidence_impact"] > 0.0
    
    @pytest.mark.asyncio
    async def test_character_consistency_validation_algorithm(
        self, consistency_validator, inconsistent_story_elements
    ):
        """Test character behavior and motivation consistency validation."""
        story_data = StoryData(
            content="Story with character contradictions",
            metadata={
                "analysis_type": "character_consistency",
                "story_elements": inconsistent_story_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Should detect character contradiction
        character_violation = None
        for violation in violations:
            if "character" in violation.get("type", "").lower() or "contradict" in violation.get("description", "").lower():
                character_violation = violation
                break
        
        if character_violation:
            # Verify character violation structure
            assert "type" in character_violation
            assert "severity" in character_violation
            assert "description" in character_violation
            assert "location" in character_violation
            assert "suggested_fix" in character_violation
            
            # Character inconsistency should be significant
            assert character_violation["severity"] in ["critical", "major"]
            
            # Should reference specific character
            desc = character_violation["description"].lower()
            assert "mike" in desc or "character" in desc
    
    @pytest.mark.asyncio
    async def test_timeline_consistency_validation_algorithm(self, consistency_validator):
        """Test timeline and chronological consistency validation."""
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
                    "timestamp": "thursday_afternoon",  # TIMELINE ERROR
                    "characters": ["John"]
                }
            ],
            "timeline": [
                {"event": "Meeting scheduled", "day": "friday", "time": "morning"},
                {"event": "Meeting attended", "day": "thursday", "time": "afternoon"}
            ]
        }
        
        story_data = StoryData(
            content="Story with timeline inconsistencies",
            metadata={"analysis_type": "timeline_validation", "story_elements": timeline_issues}
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Should detect timeline violation
        timeline_violation = None
        for violation in violations:
            if "timeline" in violation.get("type", "").lower() or "chronolog" in violation.get("description", "").lower():
                timeline_violation = violation
                break
        
        assert timeline_violation is not None
        
        # Should provide specific fix
        assert "suggested_fix" in timeline_violation
        assert len(timeline_violation["suggested_fix"]) > 0
        
        # Should have confidence impact
        assert "confidence_impact" in timeline_violation
        assert timeline_violation["confidence_impact"] > 0.0
    
    @pytest.mark.asyncio
    async def test_malformed_content_handling(
        self, consistency_validator, malformed_story_elements
    ):
        """Test handling of malformed and invalid story elements."""
        story_data = StoryData(
            content="Story with malformed elements",
            metadata={
                "analysis_type": "malformed_content_test",
                "story_elements": malformed_story_elements
            }
        )
        
        # Should handle malformed content gracefully
        result = await consistency_validator.validate_consistency(story_data)
        
        # Should still return valid result
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "consistency_validation"
        
        # Should indicate data quality issues
        violations = result.data["violations"]
        
        # Should detect malformed data violations
        malformed_violations = [
            v for v in violations 
            if "malformed" in v.get("description", "").lower() or "invalid" in v.get("description", "").lower()
        ]
        
        assert len(malformed_violations) > 0
        
        # Confidence should be significantly impacted
        assert result.confidence < 0.5
        
        # Should provide recommendations for data cleanup
        if "recommendations" in result.data:
            recommendations = result.data["recommendations"]
            rec_text = " ".join(recommendations).lower()
            assert any(keyword in rec_text for keyword in ["data", "format", "structure", "valid"])
    
    @pytest.mark.asyncio
    async def test_severity_level_assignment_algorithm(
        self, consistency_validator, inconsistent_story_elements
    ):
        """Test consistency violation severity level assignment."""
        story_data = StoryData(
            content="Story for severity testing",
            metadata={
                "analysis_type": "severity_testing",
                "story_elements": inconsistent_story_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Should have violations with different severity levels
        severities = [v.get("severity") for v in violations]
        valid_severities = ["critical", "major", "minor"]
        
        for severity in severities:
            assert severity in valid_severities
        
        # Should prioritize by severity
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        major_violations = [v for v in violations if v.get("severity") == "major"]
        minor_violations = [v for v in violations if v.get("severity") == "minor"]
        
        # Critical violations should have higher confidence impact
        for cv in critical_violations:
            assert cv.get("confidence_impact", 0) >= 0.2
        
        # Minor violations should have lower confidence impact
        for mv in minor_violations:
            assert mv.get("confidence_impact", 0) <= 0.1
    
    @pytest.mark.asyncio
    async def test_confidence_impact_calculation_algorithm(
        self, consistency_validator, inconsistent_story_elements
    ):
        """Test confidence impact calculation for violations."""
        story_data = StoryData(
            content="Story for confidence impact testing",
            metadata={
                "analysis_type": "confidence_impact",
                "story_elements": inconsistent_story_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Each violation should have confidence impact
        for violation in violations:
            assert "confidence_impact" in violation
            impact = violation["confidence_impact"]
            assert 0.0 <= impact <= 1.0
            
            # Impact should correlate with severity
            severity = violation.get("severity")
            if severity == "critical":
                assert impact >= 0.2
            elif severity == "major":
                assert impact >= 0.1
            elif severity == "minor":
                assert impact >= 0.0
        
        # Total confidence should reflect violations
        total_impact = sum(v.get("confidence_impact", 0) for v in violations)
        
        if total_impact > 0.1:
            assert result.confidence < 0.9
        if total_impact > 0.3:
            assert result.confidence < 0.7
    
    @pytest.mark.asyncio
    async def test_scoped_validation_algorithm(self, consistency_validator, inconsistent_story_elements):
        """Test validation with specific scope filtering."""
        story_data = StoryData(
            content="Story for scope-specific validation",
            metadata={
                "analysis_type": "scoped_validation",
                "story_elements": inconsistent_story_elements,
                "validation_scope": ["timeline", "character"]  # Exclude plot and world
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Should only include scoped violations
        for violation in violations:
            violation_type = violation.get("type", "").lower()
            assert violation_type in ["timeline", "character", "chronological", "behavior"]
        
        # Should still detect scoped violations
        has_timeline = any("timeline" in v.get("type", "").lower() for v in violations)
        has_character = any("character" in v.get("type", "").lower() for v in violations)
        
        # At least one of these should be detected
        assert has_timeline or has_character
    
    @pytest.mark.asyncio
    async def test_validation_algorithm_edge_cases(self, consistency_validator):
        """Test validation algorithm with edge cases."""
        # Test with empty story elements
        empty_elements = {
            "characters": [],
            "events": [],
            "world_details": [],
            "timeline": []
        }
        
        story_data = StoryData(
            content="Empty story",
            metadata={"analysis_type": "empty_test", "story_elements": empty_elements}
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        
        # Should handle gracefully
        assert isinstance(result, AnalysisResult)
        assert result.confidence < 0.5  # Low confidence for empty content
        
        # Test with single element
        single_element = {
            "characters": [{"name": "Alice", "role": "protagonist"}],
            "events": [],
            "world_details": [],
            "timeline": []
        }
        
        story_data = StoryData(
            content="Single element story",
            metadata={"analysis_type": "single_element", "story_elements": single_element}
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        assert isinstance(result, AnalysisResult)
        assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_validation_performance_with_large_datasets(self, consistency_validator):
        """Test validation performance with large story datasets."""
        # Create large dataset
        large_elements = {
            "characters": [
                {
                    "name": f"Character_{i}",
                    "role": "character",
                    "introduced": f"episode_{i % 10}",
                    "attributes": {"id": i}
                }
                for i in range(100)
            ],
            "events": [
                {
                    "id": f"event_{i}",
                    "description": f"Event {i} occurs",
                    "episode": i % 10,
                    "timestamp": f"day_{i}_morning",
                    "characters": [f"Character_{i % 100}"]
                }
                for i in range(500)
            ],
            "world_details": [
                {"aspect": f"aspect_{i}", "description": f"Detail {i}"}
                for i in range(50)
            ],
            "timeline": [
                {"event": f"Event {i}", "day": i, "time": "morning"}
                for i in range(500)
            ]
        }
        
        story_data = StoryData(
            content="Large story dataset",
            metadata={"analysis_type": "performance_test", "story_elements": large_elements}
        )
        
        import time
        start_time = time.time()
        
        result = await consistency_validator.validate_consistency(story_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time
        assert processing_time < 10.0  # Should complete within 10 seconds
        
        # Should still produce valid results
        assert isinstance(result, AnalysisResult)
        assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_consistency_rule_engine_algorithm(self, consistency_validator):
        """Test consistency rule engine and custom rule application."""
        # Story with specific consistency rules
        rule_based_elements = {
            "characters": [
                {
                    "name": "Police Chief",
                    "role": "authority",
                    "introduced": "episode_1",
                    "attributes": {"rank": "Chief", "jurisdiction": "City"}
                }
            ],
            "events": [
                {
                    "id": "event_1",
                    "description": "Chief makes arrest outside city limits",  # Violates jurisdiction
                    "episode": 1,
                    "timestamp": "day_1",
                    "location": "county_jurisdiction",
                    "characters": ["Police Chief"]
                }
            ],
            "world_details": [
                {
                    "aspect": "police_jurisdiction",
                    "description": "City police have no authority outside city limits",
                    "consistency_rule": "Characters cannot act outside their established constraints"
                }
            ]
        }
        
        story_data = StoryData(
            content="Story with rule violations",
            metadata={
                "analysis_type": "rule_engine_test",
                "story_elements": rule_based_elements
            }
        )
        
        result = await consistency_validator.validate_consistency(story_data)
        violations = result.data["violations"]
        
        # Should detect rule violation
        rule_violations = [
            v for v in violations
            if "jurisdiction" in v.get("description", "").lower() or "authority" in v.get("description", "").lower()
        ]
        
        if len(rule_violations) > 0:
            violation = rule_violations[0]
            assert "type" in violation
            assert "severity" in violation
            assert "suggested_fix" in violation
            
            # Should reference the specific rule
            assert "rule" in violation.get("description", "").lower() or "constraint" in violation.get("description", "").lower()