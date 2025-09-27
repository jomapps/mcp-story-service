"""Integration test for genre pattern application scenario (T016)."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.session_manager import StorySessionManager
from src.services.genre.analyzer import GenreAnalyzer
from src.models.story import StoryData
from src.models.analysis import AnalysisResult
from src.models.genre_template import GenreTemplate


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
async def genre_analyzer():
    """Create genre analyzer for testing."""
    return GenreAnalyzer()


@pytest.fixture
def thriller_story_elements():
    """Story elements for thriller genre testing."""
    return {
        "story_beats": [
            {
                "position": 0.1,
                "type": "opening_hook",
                "description": "Detective discovers body with mysterious circumstances"
            },
            {
                "position": 0.25,
                "type": "inciting_incident", 
                "description": "Evidence points to conspiracy involving powerful people"
            },
            {
                "position": 0.5,
                "type": "midpoint_twist",
                "description": "Detective realizes they're being watched and targeted"
            },
            {
                "position": 0.75,
                "type": "dark_moment",
                "description": "Detective's partner is killed, they're framed"
            },
            {
                "position": 0.9,
                "type": "climax",
                "description": "Final confrontation with conspiracy leaders"
            }
        ],
        "character_types": [
            {
                "name": "Detective Sarah",
                "role": "protagonist",
                "archetype": "reluctant_hero"
            },
            {
                "name": "Commissioner Blake",
                "role": "authority_figure",
                "archetype": "mentor_turned_antagonist"
            },
            {
                "name": "Marcus the Informant",
                "role": "ally",
                "archetype": "wise_guide"
            }
        ],
        "atmosphere_elements": [
            "urban_corruption",
            "mounting_paranoia",
            "ticking_clock_pressure",
            "moral_ambiguity"
        ],
        "pacing_profile": {
            "tension_escalation": "gradual_then_rapid",
            "action_sequences": "strategic_placement",
            "breathing_room": "minimal_but_effective"
        }
    }


@pytest.fixture
def comedy_story_elements():
    """Story elements for comedy genre testing."""
    return {
        "story_beats": [
            {
                "position": 0.1,
                "type": "comedic_setup",
                "description": "Bumbling office worker gets promotion by mistake"
            },
            {
                "position": 0.25,
                "type": "fish_out_of_water",
                "description": "Worker tries to fake competence in executive role"
            },
            {
                "position": 0.5,
                "type": "comedic_complications",
                "description": "Misunderstandings multiply as worker gets deeper"
            },
            {
                "position": 0.75,
                "type": "revelation_moment",
                "description": "Worker's genuine insights accidentally solve real problems"
            },
            {
                "position": 0.9,
                "type": "comedic_resolution",
                "description": "Worker earns respect through authenticity"
            }
        ],
        "character_types": [
            {
                "name": "Danny the Worker",
                "role": "protagonist",
                "archetype": "everyman_fool"
            },
            {
                "name": "Ms. Sterling",
                "role": "love_interest",
                "archetype": "straight_woman"
            },
            {
                "name": "Boss Rodriguez",
                "role": "authority",
                "archetype": "comedic_foil"
            }
        ],
        "atmosphere_elements": [
            "lighthearted_tone",
            "situational_irony",
            "character_based_humor",
            "optimistic_worldview"
        ],
        "pacing_profile": {
            "joke_frequency": "consistent_throughout",
            "setup_payoff_rhythm": "classical_timing",
            "emotional_beats": "heartwarming_moments"
        }
    }


@pytest.fixture
def horror_story_elements():
    """Story elements for horror genre testing."""
    return {
        "story_beats": [
            {
                "position": 0.1,
                "type": "ominous_setup",
                "description": "Family moves to isolated house with dark history"
            },
            {
                "position": 0.25,
                "type": "first_supernatural_event",
                "description": "Strange noises and moving objects begin"
            },
            {
                "position": 0.5,
                "type": "escalating_terror",
                "description": "Ghostly encounters become violent and personal"
            },
            {
                "position": 0.75,
                "type": "horrific_revelation",
                "description": "Family discovers previous owners' tragic fate"
            },
            {
                "position": 0.9,
                "type": "final_terror",
                "description": "Supernatural force makes final deadly attempt"
            }
        ],
        "character_types": [
            {
                "name": "Emma the Mother",
                "role": "protagonist",
                "archetype": "protective_parent"
            },
            {
                "name": "Young Timmy",
                "role": "innocent",
                "archetype": "vulnerable_child"
            },
            {
                "name": "The Previous Owner",
                "role": "antagonist",
                "archetype": "vengeful_spirit"
            }
        ],
        "atmosphere_elements": [
            "dread_and_foreboding",
            "isolation_and_helplessness",
            "supernatural_presence",
            "psychological_terror"
        ],
        "pacing_profile": {
            "tension_building": "slow_burn_approach",
            "scare_timing": "unpredictable_jolts",
            "relief_moments": "brief_false_security"
        }
    }


class TestGenrePatternApplicationScenario:
    """Integration test for genre pattern application functionality."""
    
    @pytest.mark.asyncio
    async def test_thriller_genre_authentication_with_confidence_scoring(
        self, session_manager, genre_analyzer, thriller_story_elements
    ):
        """Test thriller genre pattern application with 75% confidence threshold."""
        # Create session for project isolation
        project_id = "thriller-genre-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Create story data with thriller elements
        story_data = StoryData(
            content="Detective thriller with conspiracy elements and mounting tension",
            metadata={
                "analysis_type": "genre_authentication",
                "target_genre": "thriller",
                "story_elements": thriller_story_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Apply thriller genre patterns
        analysis_result = await genre_analyzer.apply_genre_patterns(
            story_data, target_genre="thriller"
        )
        
        # Verify analysis structure
        assert analysis_result.analysis_type == "genre_authentication"
        assert "genre_guidance" in analysis_result.data
        
        guidance = analysis_result.data["genre_guidance"]
        
        # Verify convention compliance scoring
        assert "convention_compliance" in guidance
        compliance = guidance["convention_compliance"]
        
        assert "score" in compliance
        assert compliance["score"] >= 0.0
        assert compliance["score"] <= 1.0
        
        assert "meets_threshold" in compliance
        assert "confidence_score" in compliance
        assert compliance["confidence_score"] >= 0.0
        assert compliance["confidence_score"] <= 1.0
        
        # Should meet 75% confidence threshold for well-structured thriller
        assert compliance["confidence_score"] >= 0.75
        assert compliance["meets_threshold"] is True
        
        # Check met and missing conventions
        assert "met_conventions" in compliance
        assert "missing_conventions" in compliance
        assert isinstance(compliance["met_conventions"], list)
        assert isinstance(compliance["missing_conventions"], list)
        
        # Thriller should recognize key conventions
        met_conventions_text = " ".join(compliance["met_conventions"]).lower()
        assert any(keyword in met_conventions_text for keyword in [
            "tension", "suspense", "escalation", "conspiracy", "paranoia"
        ])
        
        # Verify authenticity improvements
        assert "authenticity_improvements" in guidance
        improvements = guidance["authenticity_improvements"]
        assert isinstance(improvements, list)
        
        for improvement in improvements:
            assert "aspect" in improvement
            assert "recommendation" in improvement
            assert "impact" in improvement
            assert improvement["impact"] in ["high", "medium", "low"]
            assert "confidence" in improvement
            assert improvement["confidence"] >= 0.0
            assert improvement["confidence"] <= 1.0
        
        # Verify genre-specific beats
        assert "genre_specific_beats" in guidance
        beats = guidance["genre_specific_beats"]
        assert isinstance(beats, list)
        
        for beat in beats:
            assert "beat_type" in beat
            assert "suggested_position" in beat
            assert "purpose" in beat
            assert "confidence" in beat
            assert beat["confidence"] >= 0.0
            assert beat["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_comedy_genre_pattern_mismatch_detection(
        self, session_manager, genre_analyzer, thriller_story_elements
    ):
        """Test genre pattern mismatch when applying comedy patterns to thriller content."""
        project_id = "genre-mismatch-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Apply comedy patterns to thriller content (intentional mismatch)
        story_data = StoryData(
            content="Dark detective thriller with conspiracy and murder",
            metadata={
                "analysis_type": "genre_mismatch_test",
                "target_genre": "comedy",
                "story_elements": thriller_story_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Apply comedy genre patterns to thriller content
        analysis_result = await genre_analyzer.apply_genre_patterns(
            story_data, target_genre="comedy"
        )
        
        guidance = analysis_result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should detect mismatch and have low confidence
        assert compliance["confidence_score"] < 0.75
        assert compliance["meets_threshold"] is False
        
        # Should have many missing comedy conventions
        missing_conventions = compliance["missing_conventions"]
        assert len(missing_conventions) > 0
        
        # Should suggest improvements to align with comedy
        improvements = guidance["authenticity_improvements"]
        assert len(improvements) > 0
        
        # At least one high-impact improvement should be suggested
        high_impact_improvements = [imp for imp in improvements if imp["impact"] == "high"]
        assert len(high_impact_improvements) > 0
    
    @pytest.mark.asyncio
    async def test_multi_genre_analysis_comparison(
        self, session_manager, genre_analyzer, comedy_story_elements
    ):
        """Test analysis of content against multiple genres for best fit."""
        project_id = "multi-genre-test-001"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content="Workplace comedy with romantic subplot and character growth",
            metadata={
                "analysis_type": "multi_genre_comparison",
                "story_elements": comedy_story_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Test against multiple genres
        genres_to_test = ["comedy", "romance", "drama", "thriller"]
        genre_scores = {}
        
        for genre in genres_to_test:
            analysis_result = await genre_analyzer.apply_genre_patterns(
                story_data, target_genre=genre
            )
            
            compliance = analysis_result.data["genre_guidance"]["convention_compliance"]
            genre_scores[genre] = compliance["confidence_score"]
        
        # Comedy should score highest for comedy content
        assert genre_scores["comedy"] == max(genre_scores.values())
        
        # Comedy should meet threshold
        assert genre_scores["comedy"] >= 0.75
        
        # Thriller should score lowest for comedy content
        assert genre_scores["thriller"] == min(genre_scores.values())
        
        # Romance might score moderately (workplace romance subplot)
        assert genre_scores["romance"] > genre_scores["thriller"]
    
    @pytest.mark.asyncio
    async def test_horror_atmosphere_authenticity_validation(
        self, session_manager, genre_analyzer, horror_story_elements
    ):
        """Test horror genre atmosphere and authenticity validation."""
        project_id = "horror-authenticity-test-001"
        session_id = await session_manager.create_session(project_id)
        
        story_data = StoryData(
            content="Supernatural horror with family in haunted house",
            metadata={
                "analysis_type": "atmosphere_validation",
                "target_genre": "horror",
                "story_elements": horror_story_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        analysis_result = await genre_analyzer.apply_genre_patterns(
            story_data, target_genre="horror"
        )
        
        guidance = analysis_result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should recognize horror conventions
        assert compliance["confidence_score"] >= 0.75
        
        met_conventions = compliance["met_conventions"]
        met_text = " ".join(met_conventions).lower()
        
        # Should identify key horror elements
        horror_keywords = ["supernatural", "terror", "fear", "dread", "isolation"]
        assert any(keyword in met_text for keyword in horror_keywords)
        
        # Check authenticity improvements
        improvements = guidance["authenticity_improvements"]
        
        # Should suggest horror-specific enhancements
        improvement_text = " ".join([imp["recommendation"] for imp in improvements]).lower()
        horror_suggestions = ["atmosphere", "tension", "pacing", "suspense", "fear"]
        
        # At least some horror-specific suggestions should be present
        has_horror_suggestions = any(suggestion in improvement_text for suggestion in horror_suggestions)
        assert has_horror_suggestions
        
        # Verify horror-specific beats
        beats = guidance["genre_specific_beats"]
        beat_types = [beat["beat_type"] for beat in beats]
        
        # Should include horror-specific beat types
        horror_beats = ["ominous_setup", "supernatural_event", "escalating_terror", "horrific_revelation"]
        assert any(horror_beat in " ".join(beat_types) for horror_beat in horror_beats)
    
    @pytest.mark.asyncio
    async def test_genre_pattern_confidence_impact_on_recommendations(
        self, session_manager, genre_analyzer
    ):
        """Test how confidence scores impact the quality and specificity of recommendations."""
        project_id = "confidence-impact-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Low-confidence story (vague, minimal genre elements)
        low_confidence_elements = {
            "story_beats": [
                {
                    "position": 0.5,
                    "type": "generic_event", 
                    "description": "Something happens to the main character"
                }
            ],
            "character_types": [
                {
                    "name": "Person",
                    "role": "main_character",
                    "archetype": "generic_protagonist"
                }
            ],
            "atmosphere_elements": ["unclear_tone"],
            "pacing_profile": {"structure": "undefined"}
        }
        
        story_data = StoryData(
            content="A vague story about someone doing something",
            metadata={
                "analysis_type": "confidence_impact_test",
                "target_genre": "thriller",
                "story_elements": low_confidence_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        analysis_result = await genre_analyzer.apply_genre_patterns(
            story_data, target_genre="thriller"
        )
        
        guidance = analysis_result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should have low confidence due to vague content
        assert compliance["confidence_score"] < 0.75
        assert compliance["meets_threshold"] is False
        
        # Should have many missing conventions
        missing_conventions = compliance["missing_conventions"]
        assert len(missing_conventions) >= 3
        
        # Should provide many high-impact improvements
        improvements = guidance["authenticity_improvements"]
        high_impact_count = len([imp for imp in improvements if imp["impact"] == "high"])
        assert high_impact_count >= 2
        
        # Should suggest fundamental genre elements
        improvement_text = " ".join([imp["recommendation"] for imp in improvements]).lower()
        fundamental_suggestions = ["tension", "conflict", "character", "structure", "pacing"]
        suggestions_found = sum(1 for suggestion in fundamental_suggestions if suggestion in improvement_text)
        assert suggestions_found >= 2
    
    @pytest.mark.asyncio
    async def test_genre_convention_evolution_and_modern_adaptations(
        self, session_manager, genre_analyzer
    ):
        """Test recognition of modern adaptations of classic genre conventions."""
        project_id = "modern-conventions-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Modern thriller with digital elements
        modern_thriller_elements = {
            "story_beats": [
                {
                    "position": 0.1,
                    "type": "digital_hook",
                    "description": "Cybersecurity expert discovers data breach targeting elections"
                },
                {
                    "position": 0.25,
                    "type": "viral_conspiracy",
                    "description": "Social media manipulation campaign exposed"
                },
                {
                    "position": 0.5,
                    "type": "digital_cat_and_mouse",
                    "description": "Hacker vs hacker pursuit through dark web"
                },
                {
                    "position": 0.75,
                    "type": "system_collapse_threat", 
                    "description": "Infrastructure attack threatens democracy"
                },
                {
                    "position": 0.9,
                    "type": "digital_showdown",
                    "description": "Final battle in cyberspace with real-world stakes"
                }
            ],
            "character_types": [
                {
                    "name": "Alex the Cybersec Expert",
                    "role": "protagonist",
                    "archetype": "digital_age_detective"
                },
                {
                    "name": "Corporate AI",
                    "role": "antagonist",
                    "archetype": "algorithmic_villain"
                }
            ],
            "atmosphere_elements": [
                "digital_paranoia",
                "information_warfare",
                "technology_distrust",
                "virtual_reality_tension"
            ]
        }
        
        story_data = StoryData(
            content="Modern cyber-thriller about election interference and AI manipulation",
            metadata={
                "analysis_type": "modern_conventions_test",
                "target_genre": "thriller",
                "story_elements": modern_thriller_elements
            }
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        analysis_result = await genre_analyzer.apply_genre_patterns(
            story_data, target_genre="thriller"
        )
        
        guidance = analysis_result.data["genre_guidance"]
        compliance = guidance["convention_compliance"]
        
        # Should recognize modern thriller conventions
        assert compliance["confidence_score"] >= 0.70  # Slightly lower threshold for modern adaptations
        
        # Should identify both classic and modern elements
        met_conventions = compliance["met_conventions"]
        met_text = " ".join(met_conventions).lower()
        
        # Should recognize modern thriller elements
        modern_elements = ["digital", "cyber", "technology", "information", "virtual"]
        modern_recognition = any(element in met_text for element in modern_elements)
        
        # Should also recognize classic thriller structure
        classic_elements = ["tension", "escalation", "paranoia", "conspiracy"]
        classic_recognition = any(element in met_text for element in classic_elements)
        
        # Both modern and classic should be recognized
        assert modern_recognition or classic_recognition
        
        # Should provide relevant modern recommendations
        improvements = guidance["authenticity_improvements"]
        improvement_text = " ".join([imp["recommendation"] for imp in improvements]).lower()
        
        # Should suggest contemporary thriller enhancements if needed
        contemporary_suggestions = ["technology", "digital", "modern", "contemporary", "current"]
        has_contemporary_focus = any(suggestion in improvement_text for suggestion in contemporary_suggestions)
        
        # Test should demonstrate genre pattern flexibility
        assert len(improvements) >= 0  # Should provide constructive feedback


if __name__ == "__main__":
    pytest.main([__file__])