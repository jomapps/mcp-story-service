import pytest
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader
from src.lib.error_handler import AnalysisError

@pytest.fixture
def narrative_analyzer():
    genre_loader = GenreLoader(config_path="config/genres")
    return NarrativeAnalyzer(genre_loader)

@pytest.fixture
def sample_story():
    return """
    Chapter 1: The Beginning
    John was a detective who discovered a mysterious case. The victim was found dead in a locked room.
    He realized this was no ordinary murder - someone was playing a dangerous game.

    Chapter 2: The Investigation
    As John investigated deeper, he found clues that led to a conspiracy. The stakes were getting higher.
    Time was running out as more bodies appeared. The killer was always one step ahead.

    Chapter 3: The Revelation
    In a shocking twist, John discovered the killer was his partner. The final confrontation was inevitable.
    After a desperate chase, John managed to stop the killer and save the city.
    """

@pytest.fixture
def complex_story():
    return """
    Day 1 Morning: Sarah meets Tom at the coffee shop. Love at first sight.
    Day 1 Evening: They go on their first date. Perfect chemistry.
    Day 2 Morning: Sarah discovers Tom is married. Heartbreak ensues.
    Day 5 Afternoon: Tom leaves his wife for Sarah. Dramatic confrontation.
    Day 10 Evening: Sarah and Tom get married. Happy ending.
    """

def test_analyze_story_structure_basic(narrative_analyzer: NarrativeAnalyzer):
    """Test basic story structure analysis."""
    test_story = "A detective finds a body. He investigates. He catches the killer."
    genre = "thriller"
    story_arc = narrative_analyzer.analyze_story_structure(test_story, genre)

    assert story_arc is not None
    assert story_arc.genre == genre
    assert story_arc.title is not None
    assert story_arc.act_structure is not None
    assert story_arc.pacing_profile is not None
    assert 0.1 <= story_arc.confidence_score <= 1.0

def test_analyze_story_structure_complex(narrative_analyzer: NarrativeAnalyzer, sample_story):
    """Test complex story structure analysis."""
    genre = "thriller"
    story_arc = narrative_analyzer.analyze_story_structure(sample_story, genre)

    # Check basic structure
    assert story_arc.genre == genre
    assert len(story_arc.act_structure.act_one.key_events) > 0
    assert len(story_arc.act_structure.act_two.key_events) > 0
    assert len(story_arc.act_structure.act_three.key_events) > 0

    # Check turning points
    assert len(story_arc.act_structure.turning_points) >= 2

    # Check pacing profile
    assert len(story_arc.pacing_profile.tension_curve) > 0
    assert story_arc.pacing_profile.confidence_score > 0.1

def test_analyze_story_structure_romance(narrative_analyzer: NarrativeAnalyzer, complex_story):
    """Test romance genre analysis."""
    genre = "romance"
    story_arc = narrative_analyzer.analyze_story_structure(complex_story, genre)

    assert story_arc.genre == genre
    assert story_arc.confidence_score > 0.1

    # Should detect romantic elements
    pacing_issues = story_arc.pacing_profile.pacing_issues
    assert isinstance(pacing_issues, list)

def test_analyze_empty_story(narrative_analyzer: NarrativeAnalyzer):
    """Test error handling for empty story."""
    with pytest.raises(AnalysisError):
        narrative_analyzer.analyze_story_structure("", "thriller")

def test_analyze_invalid_genre(narrative_analyzer: NarrativeAnalyzer):
    """Test error handling for invalid genre."""
    with pytest.raises(AnalysisError):
        narrative_analyzer.analyze_story_structure("Test story", "invalid_genre")

def test_story_segmentation(narrative_analyzer: NarrativeAnalyzer, sample_story):
    """Test story segmentation functionality."""
    segments = narrative_analyzer._segment_story(sample_story)

    assert len(segments) > 1
    assert all(isinstance(segment, str) for segment in segments)
    assert all(len(segment.strip()) > 0 for segment in segments)

def test_beat_identification(narrative_analyzer: NarrativeAnalyzer, sample_story):
    """Test story beat identification."""
    segments = narrative_analyzer._segment_story(sample_story)
    beats = narrative_analyzer._identify_story_beats(sample_story, segments)

    assert isinstance(beats, dict)
    # Should identify at least some beats in a thriller story
    if beats:
        for beat_name, beat_data in beats.items():
            assert "position" in beat_data
            assert "content" in beat_data
            assert "confidence" in beat_data
            assert 0.0 <= beat_data["position"] <= 1.0
            assert 0.0 <= beat_data["confidence"] <= 1.0

def test_three_act_analysis(narrative_analyzer: NarrativeAnalyzer, sample_story):
    """Test three-act structure analysis."""
    segments = narrative_analyzer._segment_story(sample_story)
    beats = narrative_analyzer._identify_story_beats(sample_story, segments)
    act_structure = narrative_analyzer._analyze_three_act_structure(segments, beats)

    assert act_structure.act_one is not None
    assert act_structure.act_two is not None
    assert act_structure.act_three is not None

    # Check act boundaries
    assert act_structure.act_one.start_position == 0.0
    assert act_structure.act_three.end_position == 1.0
    assert act_structure.act_one.end_position <= act_structure.act_two.start_position
    assert act_structure.act_two.end_position <= act_structure.act_three.start_position

def test_pacing_analysis(narrative_analyzer: NarrativeAnalyzer, sample_story):
    """Test pacing analysis functionality."""
    segments = narrative_analyzer._segment_story(sample_story)
    beats = narrative_analyzer._identify_story_beats(sample_story, segments)
    pacing_profile = narrative_analyzer._analyze_pacing(segments, beats)

    assert len(pacing_profile.tension_curve) > 0
    assert all(0.0 <= tension <= 1.0 for tension in pacing_profile.tension_curve)
    assert isinstance(pacing_profile.pacing_issues, list)
    assert isinstance(pacing_profile.suggested_improvements, list)
    assert 0.0 <= pacing_profile.confidence_score <= 1.0
