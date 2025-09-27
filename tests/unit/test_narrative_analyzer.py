import pytest
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.lib.genre_loader import GenreLoader

@pytest.fixture
def narrative_analyzer():
    genre_loader = GenreLoader(config_path="config/genres")
    return NarrativeAnalyzer(genre_loader)

def test_analyze_story_structure(narrative_analyzer: NarrativeAnalyzer):
    """
    Tests the analyze_story_structure method.
    """
    test_story = "A simple test story."
    genre = "thriller"
    story_arc = narrative_analyzer.analyze_story_structure(test_story, genre)

    assert story_arc is not None
    assert story_arc.genre == genre
    assert story_arc.act_structure.confidence_score >= 0.75
    assert story_arc.pacing_profile.confidence_score >= 0.75
    assert story_arc.confidence_score >= 0.75
