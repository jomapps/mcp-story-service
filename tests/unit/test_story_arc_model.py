"""Unit tests for StoryArc model with confidence validation (T047)."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.story import StoryArc, ActStructure, TurningPoint, StoryData


class TestStoryArcModel:
    """Unit tests for StoryArc model functionality."""
    
    def test_story_arc_creation_with_valid_data(self):
        """Test creating StoryArc with valid data."""
        arc_data = {
            "project_id": "test-project-001",
            "arc_type": "three_act",
            "confidence_score": 0.85,
            "act_structure": {
                "act_one": {
                    "start_position": 0.0,
                    "end_position": 0.25,
                    "purpose": "Setup and character introduction",
                    "key_events": ["protagonist introduction", "inciting incident"]
                },
                "act_two": {
                    "start_position": 0.25,
                    "end_position": 0.75,
                    "purpose": "Development and obstacles",
                    "key_events": ["first plot point", "midpoint", "second plot point"]
                },
                "act_three": {
                    "start_position": 0.75,
                    "end_position": 1.0,
                    "purpose": "Resolution and conclusion",
                    "key_events": ["climax", "resolution"]
                }
            },
            "turning_points": [
                {
                    "position": 0.25,
                    "type": "plot_point_1",
                    "description": "First major plot point",
                    "confidence": 0.9
                },
                {
                    "position": 0.5,
                    "type": "midpoint",
                    "description": "Story midpoint reversal",
                    "confidence": 0.8
                }
            ]
        }
        
        arc = StoryArc(**arc_data)
        
        assert arc.project_id == "test-project-001"
        assert arc.arc_type == "three_act"
        assert arc.confidence_score == 0.85
        assert arc.act_structure.act_one.purpose == "Setup and character introduction"
        assert len(arc.turning_points) == 2
        assert arc.turning_points[0].type == "plot_point_1"
    
    def test_story_arc_confidence_score_validation(self):
        """Test confidence score validation constraints."""
        # Valid confidence scores
        valid_scores = [0.0, 0.5, 0.75, 1.0]
        
        for score in valid_scores:
            arc = StoryArc(
                project_id="test-confidence",
                arc_type="hero_journey",
                confidence_score=score,
                act_structure=self._create_minimal_act_structure()
            )
            assert arc.confidence_score == score
        
        # Invalid confidence scores should raise validation error
        invalid_scores = [-0.1, 1.1, 2.0, -1.0]
        
        for score in invalid_scores:
            with pytest.raises(ValidationError) as exc_info:
                StoryArc(
                    project_id="test-invalid",
                    arc_type="three_act",
                    confidence_score=score,
                    act_structure=self._create_minimal_act_structure()
                )
            assert "confidence_score" in str(exc_info.value)
    
    def test_story_arc_type_validation(self):
        """Test arc type validation with allowed values."""
        valid_types = ["three_act", "hero_journey", "five_act", "seven_point"]
        
        for arc_type in valid_types:
            arc = StoryArc(
                project_id="test-type",
                arc_type=arc_type,
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure()
            )
            assert arc.arc_type == arc_type
        
        # Invalid arc type should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            StoryArc(
                project_id="test-invalid-type",
                arc_type="invalid_type",
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure()
            )
        assert "arc_type" in str(exc_info.value)
    
    def test_act_structure_position_validation(self):
        """Test act structure position validation."""
        # Valid act structure with proper positions
        valid_structure = {
            "act_one": {
                "start_position": 0.0,
                "end_position": 0.25,
                "purpose": "Setup",
                "key_events": ["opening"]
            },
            "act_two": {
                "start_position": 0.25,
                "end_position": 0.75,
                "purpose": "Development",
                "key_events": ["conflict"]
            },
            "act_three": {
                "start_position": 0.75,
                "end_position": 1.0,
                "purpose": "Resolution",
                "key_events": ["climax"]
            }
        }
        
        arc = StoryArc(
            project_id="test-positions",
            arc_type="three_act",
            confidence_score=0.8,
            act_structure=valid_structure
        )
        
        assert arc.act_structure.act_one.start_position == 0.0
        assert arc.act_structure.act_three.end_position == 1.0
        
        # Invalid positions should raise validation error
        invalid_structure = {
            "act_one": {
                "start_position": -0.1,  # Invalid: negative
                "end_position": 0.25,
                "purpose": "Setup",
                "key_events": ["opening"]
            },
            "act_two": {
                "start_position": 0.25,
                "end_position": 1.5,  # Invalid: > 1.0
                "purpose": "Development",
                "key_events": ["conflict"]
            },
            "act_three": {
                "start_position": 0.75,
                "end_position": 1.0,
                "purpose": "Resolution",
                "key_events": ["climax"]
            }
        }
        
        with pytest.raises(ValidationError):
            StoryArc(
                project_id="test-invalid-positions",
                arc_type="three_act",
                confidence_score=0.8,
                act_structure=invalid_structure
            )
    
    def test_turning_points_validation(self):
        """Test turning points validation and ordering."""
        turning_points = [
            {
                "position": 0.25,
                "type": "plot_point_1",
                "description": "First plot point",
                "confidence": 0.85
            },
            {
                "position": 0.5,
                "type": "midpoint",
                "description": "Story midpoint",
                "confidence": 0.9
            },
            {
                "position": 0.75,
                "type": "plot_point_2",
                "description": "Second plot point",
                "confidence": 0.8
            }
        ]
        
        arc = StoryArc(
            project_id="test-turning-points",
            arc_type="three_act",
            confidence_score=0.8,
            act_structure=self._create_minimal_act_structure(),
            turning_points=turning_points
        )
        
        assert len(arc.turning_points) == 3
        assert arc.turning_points[0].position == 0.25
        assert arc.turning_points[1].confidence == 0.9
        
        # Test invalid turning point confidence
        invalid_turning_points = [
            {
                "position": 0.25,
                "type": "plot_point_1",
                "description": "First plot point",
                "confidence": 1.5  # Invalid: > 1.0
            }
        ]
        
        with pytest.raises(ValidationError):
            StoryArc(
                project_id="test-invalid-turning",
                arc_type="three_act",
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure(),
                turning_points=invalid_turning_points
            )
    
    def test_story_arc_confidence_thresholds(self):
        """Test confidence threshold validation for different quality levels."""
        # High confidence (meets 75% threshold)
        high_confidence_arc = StoryArc(
            project_id="high-confidence",
            arc_type="three_act",
            confidence_score=0.85,
            act_structure=self._create_minimal_act_structure()
        )
        
        assert high_confidence_arc.meets_confidence_threshold()
        assert high_confidence_arc.get_quality_level() == "high"
        
        # Medium confidence (meets basic threshold but not high)
        medium_confidence_arc = StoryArc(
            project_id="medium-confidence",
            arc_type="three_act",
            confidence_score=0.65,
            act_structure=self._create_minimal_act_structure()
        )
        
        assert medium_confidence_arc.meets_confidence_threshold(threshold=0.6)
        assert not medium_confidence_arc.meets_confidence_threshold(threshold=0.75)
        assert medium_confidence_arc.get_quality_level() == "medium"
        
        # Low confidence
        low_confidence_arc = StoryArc(
            project_id="low-confidence",
            arc_type="three_act",
            confidence_score=0.45,
            act_structure=self._create_minimal_act_structure()
        )
        
        assert not low_confidence_arc.meets_confidence_threshold(threshold=0.75)
        assert low_confidence_arc.get_quality_level() == "low"
    
    def test_story_arc_project_isolation_validation(self):
        """Test project isolation validation for StoryArc."""
        # Valid project IDs
        valid_project_ids = [
            "project-001",
            "thriller-story-2024",
            "user_123_story",
            "multi-episode-series"
        ]
        
        for project_id in valid_project_ids:
            arc = StoryArc(
                project_id=project_id,
                arc_type="three_act",
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure()
            )
            assert arc.project_id == project_id
            assert arc.is_isolated_project()
        
        # Empty project ID should raise validation error
        with pytest.raises(ValidationError):
            StoryArc(
                project_id="",
                arc_type="three_act",
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure()
            )
        
        # None project ID should raise validation error
        with pytest.raises(ValidationError):
            StoryArc(
                project_id=None,
                arc_type="three_act",
                confidence_score=0.8,
                act_structure=self._create_minimal_act_structure()
            )
    
    def test_story_arc_serialization_and_deserialization(self):
        """Test StoryArc serialization to/from dict."""
        original_arc = StoryArc(
            project_id="serialization-test",
            arc_type="hero_journey",
            confidence_score=0.92,
            act_structure=self._create_detailed_act_structure(),
            turning_points=[
                {
                    "position": 0.25,
                    "type": "call_to_adventure",
                    "description": "Hero receives the call",
                    "confidence": 0.9
                }
            ],
            metadata={
                "genre": "fantasy",
                "target_audience": "young_adult",
                "analysis_version": "1.0"
            }
        )
        
        # Serialize to dict
        arc_dict = original_arc.model_dump()
        
        # Deserialize from dict
        reconstructed_arc = StoryArc(**arc_dict)
        
        # Verify equality
        assert reconstructed_arc.project_id == original_arc.project_id
        assert reconstructed_arc.arc_type == original_arc.arc_type
        assert reconstructed_arc.confidence_score == original_arc.confidence_score
        assert len(reconstructed_arc.turning_points) == len(original_arc.turning_points)
        assert reconstructed_arc.metadata == original_arc.metadata
    
    def test_story_arc_metadata_flexibility(self):
        """Test metadata field flexibility for different use cases."""
        # Minimal metadata
        minimal_arc = StoryArc(
            project_id="minimal-metadata",
            arc_type="three_act",
            confidence_score=0.8,
            act_structure=self._create_minimal_act_structure()
        )
        
        assert minimal_arc.metadata == {}
        
        # Rich metadata
        rich_metadata = {
            "genre": "thriller",
            "subgenre": "psychological",
            "target_audience": "adults",
            "estimated_runtime": 120,
            "character_count": 5,
            "setting": "urban_contemporary",
            "themes": ["betrayal", "redemption", "justice"],
            "analysis_timestamp": datetime.now().isoformat(),
            "confidence_factors": {
                "structure_clarity": 0.9,
                "character_development": 0.8,
                "pacing_consistency": 0.85
            }
        }
        
        rich_arc = StoryArc(
            project_id="rich-metadata",
            arc_type="three_act",
            confidence_score=0.88,
            act_structure=self._create_minimal_act_structure(),
            metadata=rich_metadata
        )
        
        assert rich_arc.metadata["genre"] == "thriller"
        assert len(rich_arc.metadata["themes"]) == 3
        assert rich_arc.metadata["confidence_factors"]["structure_clarity"] == 0.9
    
    def test_story_arc_update_operations(self):
        """Test story arc update and modification operations."""
        arc = StoryArc(
            project_id="update-test",
            arc_type="three_act",
            confidence_score=0.7,
            act_structure=self._create_minimal_act_structure()
        )
        
        # Update confidence score
        arc.confidence_score = 0.85
        assert arc.confidence_score == 0.85
        assert arc.meets_confidence_threshold()
        
        # Add turning point
        new_turning_point = TurningPoint(
            position=0.75,
            type="climax",
            description="Final confrontation",
            confidence=0.9
        )
        
        arc.turning_points.append(new_turning_point)
        assert len(arc.turning_points) == 1
        assert arc.turning_points[0].type == "climax"
        
        # Update metadata
        arc.metadata["last_updated"] = datetime.now().isoformat()
        arc.metadata["version"] = "1.1"
        
        assert "last_updated" in arc.metadata
        assert arc.metadata["version"] == "1.1"
    
    def test_story_arc_validation_edge_cases(self):
        """Test edge cases in StoryArc validation."""
        # Test with minimal valid data
        minimal_arc = StoryArc(
            project_id="edge-case-minimal",
            arc_type="three_act",
            confidence_score=0.0,  # Minimum valid confidence
            act_structure={
                "act_one": {
                    "start_position": 0.0,
                    "end_position": 0.33,
                    "purpose": "Setup",
                    "key_events": []  # Empty events list
                },
                "act_two": {
                    "start_position": 0.33,
                    "end_position": 0.66,
                    "purpose": "Development",
                    "key_events": []
                },
                "act_three": {
                    "start_position": 0.66,
                    "end_position": 1.0,
                    "purpose": "Resolution",
                    "key_events": []
                }
            }
        )
        
        assert minimal_arc.confidence_score == 0.0
        assert len(minimal_arc.turning_points) == 0
        assert minimal_arc.act_structure.act_one.key_events == []
        
        # Test with maximum valid data
        maximal_arc = StoryArc(
            project_id="edge-case-maximal",
            arc_type="seven_point",
            confidence_score=1.0,  # Maximum valid confidence
            act_structure=self._create_detailed_act_structure(),
            turning_points=[
                TurningPoint(
                    position=i * 0.1,
                    type=f"turning_point_{i}",
                    description=f"Turning point number {i}",
                    confidence=1.0
                )
                for i in range(1, 10)  # Many turning points
            ]
        )
        
        assert maximal_arc.confidence_score == 1.0
        assert len(maximal_arc.turning_points) == 9
    
    def _create_minimal_act_structure(self):
        """Helper to create minimal valid act structure."""
        return {
            "act_one": {
                "start_position": 0.0,
                "end_position": 0.25,
                "purpose": "Setup",
                "key_events": ["opening"]
            },
            "act_two": {
                "start_position": 0.25,
                "end_position": 0.75,
                "purpose": "Development",
                "key_events": ["conflict"]
            },
            "act_three": {
                "start_position": 0.75,
                "end_position": 1.0,
                "purpose": "Resolution",
                "key_events": ["climax"]
            }
        }
    
    def _create_detailed_act_structure(self):
        """Helper to create detailed act structure."""
        return {
            "act_one": {
                "start_position": 0.0,
                "end_position": 0.25,
                "purpose": "Setup and character introduction",
                "key_events": [
                    "opening hook",
                    "protagonist introduction",
                    "world establishment",
                    "inciting incident"
                ]
            },
            "act_two": {
                "start_position": 0.25,
                "end_position": 0.75,
                "purpose": "Development and escalating conflict",
                "key_events": [
                    "first plot point",
                    "rising action",
                    "midpoint reversal",
                    "complications",
                    "second plot point"
                ]
            },
            "act_three": {
                "start_position": 0.75,
                "end_position": 1.0,
                "purpose": "Climax and resolution",
                "key_events": [
                    "final confrontation",
                    "climax",
                    "falling action",
                    "resolution",
                    "denouement"
                ]
            }
        }