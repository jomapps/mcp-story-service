import pytest
from pathlib import Path
from src.services.genre.analyzer import GenreAnalyzer
from src.lib.genre_loader import GenreLoader
from src.lib.error_handler import AnalysisError

@pytest.fixture
def genre_analyzer():
    config_path = Path(__file__).resolve().parent.parent.parent / "config" / "genres"
    genre_loader = GenreLoader(config_path=str(config_path))
    return GenreAnalyzer(genre_loader)

@pytest.fixture
def thriller_story_beats():
    return [
        {
            "type": "INCITING_INCIDENT",
            "description": "Detective John discovers a murder with high stakes - the victim was about to expose a dangerous conspiracy"
        },
        {
            "type": "SETBACK",
            "description": "John realizes he's being chased by the killers and time is running out"
        },
        {
            "type": "TWIST",
            "description": "John discovers his partner is the mastermind behind the conspiracy"
        },
        {
            "type": "CLIMAX",
            "description": "Final deadly confrontation between John and his partner with the city's fate at stake"
        }
    ]

@pytest.fixture
def thriller_characters():
    return [
        {"name": "John", "role": "protagonist", "archetype": "Detective"},
        {"name": "Partner", "role": "antagonist", "archetype": "Mastermind Villain"},
        {"name": "Victim", "role": "catalyst", "archetype": "Informant"}
    ]

@pytest.fixture
def romance_story_beats():
    return [
        {
            "type": "MEET_CUTE",
            "description": "Sarah and Tom meet at a coffee shop, instant attraction and chemistry"
        },
        {
            "type": "CONFLICT",
            "description": "Sarah discovers Tom is engaged to someone else, heartbreak ensues"
        },
        {
            "type": "RESOLUTION",
            "description": "Tom breaks off engagement and proposes to Sarah, love conquers all"
        }
    ]

@pytest.fixture
def romance_characters():
    return [
        {"name": "Sarah", "role": "protagonist", "archetype": "Romantic Lead"},
        {"name": "Tom", "role": "love_interest", "archetype": "Romantic Lead"},
        {"name": "Fiancee", "role": "obstacle", "archetype": "Rival"}
    ]

def test_analyze_thriller_genre(genre_analyzer: GenreAnalyzer, thriller_story_beats, thriller_characters):
    """Test thriller genre analysis with appropriate content."""
    target_genre = "thriller"
    report = genre_analyzer.analyze_genre(thriller_story_beats, thriller_characters, target_genre)

    # Check basic structure
    assert "convention_compliance" in report
    assert "authenticity_improvements" in report
    assert "genre_specific_beats" in report

    # Check convention compliance
    compliance = report["convention_compliance"]
    assert compliance["score"] > 0.2  # Should detect some thriller elements
    assert compliance["confidence_score"] > 0.5
    assert isinstance(compliance["met_conventions"], list)
    assert isinstance(compliance["missing_conventions"], list)

def test_analyze_romance_genre(genre_analyzer: GenreAnalyzer, romance_story_beats, romance_characters):
    """Test romance genre analysis with appropriate content."""
    target_genre = "romance"
    report = genre_analyzer.analyze_genre(romance_story_beats, romance_characters, target_genre)

    compliance = report["convention_compliance"]
    assert compliance["score"] > 0.3  # Should detect some romantic elements
    assert compliance["confidence_score"] > 0.5

def test_analyze_empty_genre(genre_analyzer: GenreAnalyzer):
    """Test error handling for empty genre."""
    with pytest.raises(AnalysisError):
        genre_analyzer.analyze_genre([], [], "")

def test_analyze_invalid_genre(genre_analyzer: GenreAnalyzer, thriller_story_beats, thriller_characters):
    """Test error handling for invalid genre."""
    with pytest.raises(AnalysisError):
        genre_analyzer.analyze_genre(thriller_story_beats, thriller_characters, "invalid_genre")

def test_content_pattern_analysis(genre_analyzer: GenreAnalyzer, thriller_story_beats, thriller_characters):
    """Test content pattern analysis functionality."""
    content_analysis = genre_analyzer._analyze_content_patterns(thriller_story_beats, thriller_characters, "thriller")

    assert "keyword_matches" in content_analysis
    assert "character_matches" in content_analysis
    assert "plot_matches" in content_analysis
    assert "atmosphere_score" in content_analysis

    # Thriller content should match thriller patterns
    assert content_analysis["keyword_matches"] > 0
    assert content_analysis["atmosphere_score"] >= 0.0

def test_high_stakes_detection(genre_analyzer: GenreAnalyzer, thriller_story_beats):
    """Test high stakes element detection."""
    content_analysis = {"keyword_matches": 3}
    result = genre_analyzer._check_high_stakes(thriller_story_beats, content_analysis)
    assert result is True  # Thriller beats should have high stakes

def test_romantic_elements_detection(genre_analyzer: GenreAnalyzer, romance_story_beats, romance_characters):
    """Test romantic elements detection."""
    content_analysis = {"keyword_matches": 2}
    result = genre_analyzer._check_romantic_elements(romance_story_beats, romance_characters, content_analysis)
    assert result is True  # Romance content should have romantic elements

def test_confidence_calculation(genre_analyzer: GenreAnalyzer):
    """Test genre analysis confidence calculation."""
    content_analysis = {
        "keyword_matches": 5,
        "total_keywords": 10,
        "character_matches": 2,
        "total_character_patterns": 4
    }

    confidence = genre_analyzer._calculate_genre_confidence(content_analysis, 8, 4)
    assert 0.1 <= confidence <= 0.95
