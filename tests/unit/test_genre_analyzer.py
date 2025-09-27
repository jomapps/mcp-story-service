import pytest
from src.services.genre.analyzer import GenreAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.fixture
def genre_analyzer():
    genre_loader = GenreLoader(config_path="config/genres")
    return GenreAnalyzer(genre_loader)

def test_analyze_genre(genre_analyzer: GenreAnalyzer):
    """
    Tests the analyze_genre method.
    """
    story_beats = []
    character_types = []
    genre = "thriller"
    report = genre_analyzer.analyze_genre(story_beats, character_types, genre)

    assert report is not None
    assert "convention_compliance" in report
    assert report["convention_compliance"]["score"] >= 0
    assert report["convention_compliance"]["meets_threshold"] is not None

def test_analyze_genre_with_unknown_genre(genre_analyzer: GenreAnalyzer):
    """
    Tests the analyze_genre method with an unknown genre.
    """
    with pytest.raises(ValueError):
        genre_analyzer.analyze_genre([], [], "unknown-genre")
