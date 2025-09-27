import pytest
from src.services.pacing.calculator import PacingCalculator
from src.lib.error_handler import AnalysisError

@pytest.fixture
def pacing_calculator():
    return PacingCalculator()

@pytest.fixture
def action_beats():
    return [
        {
            "type": "SETUP",
            "description": "Detective John sits quietly in his office, thinking about the case",
            "tension_level": 0.3
        },
        {
            "type": "INCITING_INCIDENT", 
            "description": "John gets a call about a murder - the victim was found in a locked room with no way in or out",
            "tension_level": 0.6
        },
        {
            "type": "RISING_ACTION",
            "description": "John investigates and discovers this is connected to a dangerous conspiracy that threatens the entire city",
            "tension_level": 0.7
        },
        {
            "type": "CLIMAX",
            "description": "John fights desperately against the mastermind in a final battle to save thousands of lives",
            "tension_level": 0.9
        },
        {
            "type": "RESOLUTION",
            "description": "John successfully stops the threat and the city is safe, he can finally rest",
            "tension_level": 0.4
        }
    ]

@pytest.fixture
def flat_beats():
    return [
        {
            "type": "SCENE1",
            "description": "Character talks calmly about everyday things",
            "tension_level": 0.5
        },
        {
            "type": "SCENE2", 
            "description": "Character continues talking about normal routine matters",
            "tension_level": 0.5
        },
        {
            "type": "SCENE3",
            "description": "Character discusses regular daily activities peacefully",
            "tension_level": 0.5
        }
    ]

@pytest.fixture
def varied_beats():
    return [
        {"type": "CALM", "description": "Peaceful morning scene", "tension_level": 0.2},
        {"type": "ACTION", "description": "Sudden chase scene with danger", "tension_level": 0.8},
        {"type": "REFLECTION", "description": "Character thinks quietly", "tension_level": 0.3},
        {"type": "CLIMAX", "description": "Final battle with high stakes", "tension_level": 0.9},
        {"type": "RESOLUTION", "description": "Calm ending", "tension_level": 0.3}
    ]

def test_calculate_pacing_basic(pacing_calculator: PacingCalculator, action_beats):
    """Test basic pacing calculation."""
    result = pacing_calculator.calculate_pacing(action_beats)
    
    assert "tension_curve" in result
    assert "pacing_score" in result
    assert "confidence_score" in result
    assert "rhythm_analysis" in result
    assert "recommendations" in result
    assert "genre_compliance" in result
    
    # Check value ranges
    assert 0.0 <= result["pacing_score"] <= 1.0
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert 0.0 <= result["genre_compliance"] <= 1.0
    assert len(result["tension_curve"]) == len(action_beats)

def test_calculate_pacing_empty_beats(pacing_calculator: PacingCalculator):
    """Test error handling for empty beats."""
    with pytest.raises(AnalysisError):
        pacing_calculator.calculate_pacing([])

def test_tension_curve_calculation(pacing_calculator: PacingCalculator, action_beats):
    """Test tension curve calculation."""
    tension_curve = pacing_calculator._calculate_tension_curve(action_beats)
    
    assert len(tension_curve) == len(action_beats)
    assert all(0.0 <= tension <= 1.0 for tension in tension_curve)
    
    # Should show rising tension toward climax
    climax_index = next(i for i, beat in enumerate(action_beats) if beat["type"] == "CLIMAX")
    assert tension_curve[climax_index] > 0.7  # High tension at climax

def test_content_tension_analysis(pacing_calculator: PacingCalculator):
    """Test content-based tension analysis."""
    # High tension content
    high_tension = pacing_calculator._analyze_content_tension("fight battle danger death urgent")
    assert high_tension > 0.6
    
    # Low tension content
    low_tension = pacing_calculator._analyze_content_tension("calm peaceful quiet gentle rest")
    assert low_tension < 0.5
    
    # Medium tension content
    medium_tension = pacing_calculator._analyze_content_tension("argue conflict problem worry")
    assert 0.4 <= medium_tension <= 0.7

def test_positional_tension(pacing_calculator: PacingCalculator):
    """Test positional tension calculation."""
    # Beginning should have lower tension
    beginning_tension = pacing_calculator._calculate_positional_tension(0.1)
    assert beginning_tension < 0.6
    
    # Climax area should have high tension
    climax_tension = pacing_calculator._calculate_positional_tension(0.8)
    assert climax_tension > 0.8
    
    # End should have lower tension
    end_tension = pacing_calculator._calculate_positional_tension(0.95)
    assert end_tension < 0.8

def test_rhythm_analysis(pacing_calculator: PacingCalculator, varied_beats):
    """Test rhythm analysis functionality."""
    tension_curve = [0.2, 0.8, 0.3, 0.9, 0.3]
    rhythm_analysis = pacing_calculator._analyze_rhythm(varied_beats, tension_curve)
    
    assert "fast_sections" in rhythm_analysis
    assert "slow_sections" in rhythm_analysis
    assert "balanced_sections" in rhythm_analysis
    assert "rhythm_score" in rhythm_analysis
    assert "variation_score" in rhythm_analysis
    
    assert 0.0 <= rhythm_analysis["rhythm_score"] <= 1.0
    assert 0.0 <= rhythm_analysis["variation_score"] <= 1.0

def test_flat_pacing_detection(pacing_calculator: PacingCalculator, flat_beats):
    """Test detection of flat pacing issues."""
    result = pacing_calculator.calculate_pacing(flat_beats)
    
    # Should detect flat pacing issues
    assert result["pacing_score"] < 0.7
    assert len(result["recommendations"]) > 0
    assert any("variation" in rec.lower() for rec in result["recommendations"])

def test_story_arc_evaluation(pacing_calculator: PacingCalculator):
    """Test story arc evaluation."""
    # Good arc: low -> high -> low
    good_arc = [0.3, 0.5, 0.7, 0.9, 0.4]
    arc_score = pacing_calculator._evaluate_story_arc(good_arc)
    assert arc_score > 0.6
    
    # Poor arc: flat
    poor_arc = [0.5, 0.5, 0.5, 0.5, 0.5]
    arc_score = pacing_calculator._evaluate_story_arc(poor_arc)
    assert arc_score <= 0.6

def test_pacing_recommendations(pacing_calculator: PacingCalculator, flat_beats):
    """Test pacing recommendation generation."""
    tension_curve = [0.5, 0.5, 0.5]  # Flat curve
    rhythm_analysis = {
        "fast_sections": [],
        "slow_sections": flat_beats,
        "balanced_sections": [],
        "variation_score": 0.2
    }
    
    recommendations = pacing_calculator._generate_pacing_recommendations(
        tension_curve, rhythm_analysis, flat_beats
    )
    
    assert len(recommendations) > 0
    assert any("variation" in rec.lower() for rec in recommendations)

def test_flat_sections_identification(pacing_calculator: PacingCalculator):
    """Test identification of flat tension sections."""
    flat_curve = [0.5, 0.5, 0.5, 0.8, 0.4, 0.4, 0.4]
    flat_sections = pacing_calculator._identify_flat_sections(flat_curve)
    
    assert len(flat_sections) > 0
    for section in flat_sections:
        assert "start" in section
        assert "end" in section
        assert "avg_tension" in section

def test_genre_compliance_assessment(pacing_calculator: PacingCalculator):
    """Test genre compliance assessment."""
    good_rhythm = {"rhythm_score": 0.8, "variation_score": 0.7}
    good_curve = [0.3, 0.6, 0.9, 0.4]
    
    compliance = pacing_calculator._assess_genre_compliance(good_curve, good_rhythm)
    assert compliance > 0.7
    
    poor_rhythm = {"rhythm_score": 0.3, "variation_score": 0.2}
    poor_curve = [0.5, 0.5, 0.5, 0.5]
    
    compliance = pacing_calculator._assess_genre_compliance(poor_curve, poor_rhythm)
    assert compliance < 0.8

def test_confidence_calculation(pacing_calculator: PacingCalculator):
    """Test confidence score calculation."""
    # High confidence scenario
    rich_beats = [
        {"description": "A very detailed description of the scene with lots of context and information about what's happening"},
        {"description": "Another rich description with character development and plot advancement"},
        {"description": "Complex scene with multiple elements and detailed narrative"}
    ]
    tension_curve = [0.3, 0.7, 0.5]
    
    confidence = pacing_calculator._calculate_confidence(rich_beats, tension_curve)
    assert confidence > 0.6
    
    # Low confidence scenario
    sparse_beats = [{"description": "Short"}, {"description": "Brief"}]
    sparse_curve = [0.5, 0.5]
    
    confidence = pacing_calculator._calculate_confidence(sparse_beats, sparse_curve)
    assert confidence < 0.8

def test_rhythm_score_calculation(pacing_calculator: PacingCalculator):
    """Test rhythm score calculation."""
    # Balanced rhythm
    fast_sections = [1, 2, 3]  # 30%
    slow_sections = [1, 2, 3]  # 30%
    balanced_sections = [1, 2, 3, 4]  # 40%
    total_beats = 10
    
    rhythm_score = pacing_calculator._calculate_rhythm_score(
        fast_sections, slow_sections, balanced_sections, total_beats
    )
    assert rhythm_score > 0.8  # Should be close to ideal

def test_variation_score_calculation(pacing_calculator: PacingCalculator):
    """Test tension variation score calculation."""
    # Good variation
    good_curve = [0.2, 0.5, 0.8, 0.6, 0.3]
    variation_score = pacing_calculator._calculate_variation_score(good_curve)
    assert variation_score > 0.5
    
    # Poor variation (flat)
    flat_curve = [0.5, 0.5, 0.5, 0.5, 0.5]
    variation_score = pacing_calculator._calculate_variation_score(flat_curve)
    assert variation_score < 0.7
