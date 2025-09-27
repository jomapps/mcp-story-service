import pytest
from src.services.consistency.validator import ConsistencyValidator

@pytest.fixture
def consistency_validator():
    return ConsistencyValidator()

def test_validate_consistency(consistency_validator: ConsistencyValidator):
    """
    Tests the validate method with consistent data.
    """
    story_elements = {
        "events": [
            {"description": "Event 1", "timestamp": 1},
            {"description": "Event 2", "timestamp": 2},
        ]
    }
    report = consistency_validator.validate(story_elements)
    assert len(report["issues"]) == 0
    assert report["overall_score"] == 1.0

def test_validate_consistency_with_inconsistency(consistency_validator: ConsistencyValidator):
    """
    Tests the validate method with inconsistent data.
    """
    story_elements = {
        "events": [
            {"description": "Event 1", "timestamp": 2},
            {"description": "Event 2", "timestamp": 1},
        ]
    }
    report = consistency_validator.validate(story_elements)
    assert len(report["issues"]) == 1
    assert report["issues"][0]["type"] == "timeline"
    assert report["overall_score"] < 1.0

def test_validate_consistency_with_malformed_content(consistency_validator: ConsistencyValidator):
    """
    Tests the validate method with malformed content.
    """
    story_elements = {}
    report = consistency_validator.validate(story_elements)
    assert len(report["issues"]) == 0
    assert report["overall_score"] == 1.0
