import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.mcp.server import server
from src.services.session_manager import SessionManager

@pytest.fixture
def sample_story_content():
    return """
    Detective Sarah Chen arrived at the crime scene on a rainy Tuesday morning. 
    The victim, a prominent businessman, was found dead in his locked office.
    
    As Sarah investigated, she discovered this was no ordinary murder.
    The killer had left cryptic clues pointing to a larger conspiracy.
    
    Racing against time, Sarah uncovered a plot that threatened the entire city.
    In a final confrontation, she faced the mastermind and saved thousands of lives.
    """

@pytest.fixture
def sample_story_elements():
    return {
        "events": [
            {
                "description": "Detective arrives at crime scene",
                "timestamp": "day_1_morning",
                "location": "office building",
                "characters": ["Sarah"]
            },
            {
                "description": "Discovery of conspiracy clues",
                "timestamp": "day_1_afternoon", 
                "location": "office building",
                "characters": ["Sarah"]
            },
            {
                "description": "Final confrontation with mastermind",
                "timestamp": "day_2_evening",
                "location": "warehouse",
                "characters": ["Sarah", "Mastermind"]
            }
        ],
        "characters": [
            {
                "name": "Sarah",
                "role": "protagonist",
                "attributes": {"profession": "detective", "age": 35}
            },
            {
                "name": "Mastermind",
                "role": "antagonist", 
                "attributes": {"profession": "criminal", "age": 45}
            }
        ],
        "world_details": [
            {
                "aspect": "jurisdiction",
                "consistency_rule": "Police operate within city limits"
            }
        ]
    }

@pytest.mark.asyncio
async def test_create_session_integration():
    """Test session creation through MCP server."""
    # Mock the session manager
    with patch('src.mcp.server.session_manager') as mock_session_manager:
        mock_session_manager.create_session.return_value = "test_session_123"
        
        # Call the MCP tool
        result = await server.call_tool("create_session", {
            "project_id": "test_project",
            "description": "Test story project"
        })
        
        assert result is not None
        mock_session_manager.create_session.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_story_structure_integration(sample_story_content):
    """Test story structure analysis through MCP server."""
    with patch('src.mcp.server.story_structure_handler') as mock_handler:
        # Mock the handler response
        mock_handler.analyze_story_structure.return_value = {
            "story_arc": {
                "title": "Detective Story",
                "genre": "thriller",
                "confidence_score": 0.85,
                "act_structure": {
                    "act_one": {"key_events": ["Crime discovered"]},
                    "act_two": {"key_events": ["Investigation deepens"]},
                    "act_three": {"key_events": ["Final confrontation"]}
                }
            }
        }
        
        result = await server.call_tool("analyze_story_structure", {
            "project_id": "test_project",
            "story_content": sample_story_content,
            "genre": "thriller"
        })
        
        assert result is not None
        assert "story_arc" in result
        mock_handler.analyze_story_structure.assert_called_once()

@pytest.mark.asyncio
async def test_validate_consistency_integration(sample_story_elements):
    """Test consistency validation through MCP server."""
    with patch('src.mcp.server.consistency_handler') as mock_handler:
        mock_handler.validate_consistency.return_value = {
            "consistency_report": {
                "overall_score": 0.9,
                "confidence_score": 0.85,
                "issues": [],
                "strengths": ["Good timeline consistency"],
                "recommendations": []
            }
        }
        
        result = await server.call_tool("validate_consistency", {
            "project_id": "test_project",
            "story_elements": sample_story_elements
        })
        
        assert result is not None
        assert "consistency_report" in result
        mock_handler.validate_consistency.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_genre_patterns_integration():
    """Test genre pattern analysis through MCP server."""
    story_beats = [
        {"type": "INCITING_INCIDENT", "description": "Crime discovered"},
        {"type": "CLIMAX", "description": "Final confrontation"}
    ]
    character_types = [
        {"name": "Detective", "archetype": "Hero"}
    ]
    
    with patch('src.mcp.server.genre_handler') as mock_handler:
        mock_handler.analyze_genre_patterns.return_value = {
            "genre_analysis": {
                "convention_compliance": {
                    "score": 0.8,
                    "meets_threshold": True,
                    "confidence_score": 0.85
                },
                "authenticity_improvements": ["Add more tension"],
                "genre_specific_beats": []
            }
        }
        
        result = await server.call_tool("analyze_genre_patterns", {
            "project_id": "test_project",
            "story_beats": story_beats,
            "character_types": character_types,
            "target_genre": "thriller"
        })
        
        assert result is not None
        assert "genre_analysis" in result
        mock_handler.analyze_genre_patterns.assert_called_once()

@pytest.mark.asyncio
async def test_calculate_pacing_integration():
    """Test pacing calculation through MCP server."""
    narrative_beats = [
        {"type": "SETUP", "description": "Calm beginning", "tension_level": 0.3},
        {"type": "CLIMAX", "description": "Intense finale", "tension_level": 0.9}
    ]
    
    with patch('src.mcp.server.pacing_handler') as mock_handler:
        mock_handler.calculate_pacing.return_value = {
            "pacing_analysis": {
                "tension_curve": [0.3, 0.9],
                "pacing_score": 0.75,
                "confidence_score": 0.8,
                "rhythm_analysis": {
                    "fast_sections": [],
                    "slow_sections": [],
                    "balanced_sections": []
                },
                "recommendations": ["Good pacing variation"]
            }
        }
        
        result = await server.call_tool("calculate_pacing", {
            "project_id": "test_project", 
            "narrative_beats": narrative_beats
        })
        
        assert result is not None
        assert "pacing_analysis" in result
        mock_handler.calculate_pacing.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling_integration():
    """Test error handling in MCP server integration."""
    with patch('src.mcp.server.story_structure_handler') as mock_handler:
        # Mock an error
        mock_handler.analyze_story_structure.side_effect = Exception("Analysis failed")
        
        with pytest.raises(Exception):
            await server.call_tool("analyze_story_structure", {
                "project_id": "test_project",
                "story_content": "",
                "genre": "thriller"
            })

@pytest.mark.asyncio
async def test_session_isolation():
    """Test that different sessions are properly isolated."""
    with patch('src.mcp.server.session_manager') as mock_session_manager:
        # Create two different sessions
        mock_session_manager.create_session.side_effect = ["session_1", "session_2"]
        
        session1 = await server.call_tool("create_session", {
            "project_id": "project_1",
            "description": "First project"
        })
        
        session2 = await server.call_tool("create_session", {
            "project_id": "project_2", 
            "description": "Second project"
        })
        
        # Sessions should be different
        assert session1 != session2
        assert mock_session_manager.create_session.call_count == 2

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    with patch('src.mcp.server.story_structure_handler') as mock_handler:
        mock_handler.analyze_story_structure.return_value = {
            "story_arc": {"title": "Test", "confidence_score": 0.8}
        }
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(3):
            task = server.call_tool("analyze_story_structure", {
                "project_id": f"project_{i}",
                "story_content": f"Story content {i}",
                "genre": "thriller"
            })
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        assert all(result is not None for result in results)
        assert mock_handler.analyze_story_structure.call_count == 3

@pytest.mark.asyncio
async def test_malformed_input_handling():
    """Test handling of malformed input data."""
    with patch('src.mcp.server.consistency_handler') as mock_handler:
        # Should handle malformed input gracefully
        mock_handler.validate_consistency.side_effect = ValueError("Invalid input")
        
        with pytest.raises(ValueError):
            await server.call_tool("validate_consistency", {
                "project_id": "test_project",
                "story_elements": "invalid_data"  # Should be dict, not string
            })

@pytest.mark.asyncio
async def test_end_to_end_story_analysis(sample_story_content, sample_story_elements):
    """Test complete end-to-end story analysis workflow."""
    with patch('src.mcp.server.session_manager') as mock_session, \
         patch('src.mcp.server.story_structure_handler') as mock_structure, \
         patch('src.mcp.server.consistency_handler') as mock_consistency, \
         patch('src.mcp.server.genre_handler') as mock_genre:
        
        # Mock all handlers
        mock_session.create_session.return_value = "test_session"
        mock_structure.analyze_story_structure.return_value = {
            "story_arc": {"title": "Test Story", "confidence_score": 0.8}
        }
        mock_consistency.validate_consistency.return_value = {
            "consistency_report": {"overall_score": 0.9}
        }
        mock_genre.analyze_genre_patterns.return_value = {
            "genre_analysis": {"convention_compliance": {"score": 0.8}}
        }
        
        # Execute workflow
        session = await server.call_tool("create_session", {
            "project_id": "test_project",
            "description": "End-to-end test"
        })
        
        structure_result = await server.call_tool("analyze_story_structure", {
            "project_id": "test_project",
            "story_content": sample_story_content,
            "genre": "thriller"
        })
        
        consistency_result = await server.call_tool("validate_consistency", {
            "project_id": "test_project",
            "story_elements": sample_story_elements
        })
        
        # All steps should succeed
        assert session is not None
        assert structure_result is not None
        assert consistency_result is not None
        
        # Verify all handlers were called
        mock_session.create_session.assert_called_once()
        mock_structure.analyze_story_structure.assert_called_once()
        mock_consistency.validate_consistency.assert_called_once()
