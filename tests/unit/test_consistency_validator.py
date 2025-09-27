import pytest
from src.services.consistency.validator import ConsistencyValidator
from src.lib.error_handler import AnalysisError

@pytest.fixture
def consistency_validator():
    return ConsistencyValidator()

@pytest.fixture
def consistent_story_elements():
    return {
        "events": [
            {
                "description": "Detective John arrives at crime scene",
                "timestamp": "day_1_morning",
                "location": "downtown",
                "characters": ["John"]
            },
            {
                "description": "John interviews witness Sarah",
                "timestamp": "day_1_afternoon",
                "location": "downtown",
                "characters": ["John", "Sarah"]
            },
            {
                "description": "John discovers crucial evidence",
                "timestamp": "day_2_morning",
                "location": "lab",
                "characters": ["John"]
            }
        ],
        "characters": [
            {
                "name": "John",
                "role": "protagonist",
                "attributes": {"age": 35, "profession": "detective"}
            },
            {
                "name": "Sarah",
                "role": "witness",
                "attributes": {"age": 28, "profession": "teacher"}
            }
        ],
        "world_details": [
            {
                "aspect": "jurisdiction",
                "consistency_rule": "Police can only arrest within city limits"
            }
        ]
    }

@pytest.fixture
def inconsistent_story_elements():
    return {
        "events": [
            {
                "description": "Event happens on day 2",
                "timestamp": "day_2_morning",
                "characters": ["Unknown_Character"]
            },
            {
                "description": "Event happens on day 1",
                "timestamp": "day_1_morning",
                "characters": ["John"]
            }
        ],
        "characters": [
            {
                "name": "John",
                "attributes": {"age": 35, "profession": "detective"}
            },
            {
                "name": "John",  # Duplicate with different attributes
                "attributes": {"age": 40, "profession": "lawyer"}
            }
        ]
    }

def test_validate_consistent_story(consistency_validator: ConsistencyValidator, consistent_story_elements):
    """Test validation with consistent story elements."""
    report = consistency_validator.validate(consistent_story_elements)

    assert report["overall_score"] > 0.7
    assert report["confidence_score"] > 0.5
    assert len(report["issues"]) == 0
    assert len(report["strengths"]) > 0
    assert isinstance(report["recommendations"], list)

def test_validate_inconsistent_timeline(consistency_validator: ConsistencyValidator):
    """Test timeline inconsistency detection."""
    story_elements = {
        "events": [
            {"description": "Event 1", "timestamp": "day_2_morning"},
            {"description": "Event 2", "timestamp": "day_1_morning"},
        ]
    }
    report = consistency_validator.validate(story_elements)

    timeline_issues = [issue for issue in report["issues"] if issue["type"] == "timeline"]
    assert len(timeline_issues) > 0
    assert report["overall_score"] < 1.0

def test_validate_character_inconsistency(consistency_validator: ConsistencyValidator, inconsistent_story_elements):
    """Test character consistency validation."""
    report = consistency_validator.validate(inconsistent_story_elements)

    character_issues = [issue for issue in report["issues"] if issue["type"] == "character"]
    plot_issues = [issue for issue in report["issues"] if issue["type"] == "plot"]

    # Should detect character attribute inconsistency and undefined character reference
    assert len(character_issues) > 0 or len(plot_issues) > 0
    assert report["overall_score"] < 0.9

def test_validate_world_consistency(consistency_validator: ConsistencyValidator):
    """Test world rules consistency validation."""
    story_elements = {
        "events": [
            {
                "description": "Police arrest suspect outside_jurisdiction",
                "location": "outside_jurisdiction"
            }
        ],
        "world_details": [
            {
                "aspect": "jurisdiction",
                "consistency_rule": "Police can only arrest within city limits"
            }
        ]
    }
    report = consistency_validator.validate(story_elements)

    world_issues = [issue for issue in report["issues"] if issue["type"] == "world"]
    assert len(world_issues) > 0

def test_validate_plot_consistency(consistency_validator: ConsistencyValidator):
    """Test plot consistency validation."""
    story_elements = {
        "events": [
            {
                "description": "Character is dead and speaks to others",
                "characters": ["Ghost"]
            }
        ],
        "characters": []
    }
    report = consistency_validator.validate(story_elements)

    plot_issues = [issue for issue in report["issues"] if issue["type"] == "plot"]
    assert len(plot_issues) > 0

def test_validate_empty_elements(consistency_validator: ConsistencyValidator):
    """Test validation with empty story elements."""
    with pytest.raises(AnalysisError):
        consistency_validator.validate({})

def test_validate_none_elements(consistency_validator: ConsistencyValidator):
    """Test validation with None elements."""
    with pytest.raises(AnalysisError):
        consistency_validator.validate(None)

def test_timestamp_comparison(consistency_validator: ConsistencyValidator):
    """Test timestamp comparison functionality."""
    # Test day-time format
    assert consistency_validator._compare_timestamps("day_1_morning", "day_1_afternoon") == -1
    assert consistency_validator._compare_timestamps("day_1_evening", "day_2_morning") == -1
    assert consistency_validator._compare_timestamps("day_2_morning", "day_1_morning") == 1

    # Test numeric timestamps
    assert consistency_validator._compare_timestamps(1, 2) == -1
    assert consistency_validator._compare_timestamps(2, 1) == 1
    assert consistency_validator._compare_timestamps(1, 1) == 0

def test_timeline_gap_detection(consistency_validator: ConsistencyValidator):
    """Test timeline gap detection."""
    events = [
        {"timestamp": "day_1_morning"},
        {"timestamp": "day_5_afternoon"}  # Large gap
    ]
    gaps = consistency_validator._detect_timeline_gaps(events)
    assert len(gaps) > 0

def test_cause_effect_analysis(consistency_validator: ConsistencyValidator):
    """Test cause and effect analysis."""
    events = [
        {"description": "John kills the villain"},
        {"description": "Everyone celebrates"}  # No death consequences
    ]
    issues = consistency_validator._analyze_cause_effect(events)
    assert len(issues) > 0

def test_recommendation_generation(consistency_validator: ConsistencyValidator):
    """Test recommendation generation."""
    issues = [
        {"type": "timeline", "severity": "critical"},
        {"type": "character", "severity": "warning"}
    ]
    story_elements = {"events": [], "characters": []}

    recommendations = consistency_validator._generate_recommendations(issues, story_elements)
    assert len(recommendations) > 0
    assert any("timeline" in rec.lower() for rec in recommendations)

def test_confidence_calculation(consistency_validator: ConsistencyValidator):
    """Test confidence score calculation."""
    # High confidence scenario
    story_elements = {
        "events": [{"desc": "event"} for _ in range(5)],
        "characters": [{"name": f"char{i}"} for i in range(3)],
        "world_details": [{"aspect": "rule"}]
    }
    confidence = consistency_validator._calculate_confidence_score([], story_elements)
    assert confidence > 0.7

    # Low confidence scenario
    story_elements = {"events": [], "characters": [], "world_details": []}
    confidence = consistency_validator._calculate_confidence_score([], story_elements)
    assert confidence < 0.7
